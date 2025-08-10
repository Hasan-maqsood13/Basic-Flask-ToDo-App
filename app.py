from flask import Flask, render_template, url_for, redirect, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import re

app = Flask(__name__)
app.secret_key = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modules
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_complete = db.Column(db.Boolean, default=False) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        # --- Validation ---
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for('register'))

        # Username: letters only, 6–20 chars
        if not re.match(r'^[a-zA-Z]{6,20}$', username):
            flash("Username must be 6–20 letters (no numbers or special characters).", "error")
            return redirect(url_for('register'))

        # Email basic check
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash("Invalid email address.", "error")
            return redirect(url_for('register'))

        # Password: 8–16 chars, must include letters, numbers, and special characters
        if not re.match(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,16}$', password):
            flash("Password must be 8–16 characters long and include letters, numbers, and special characters.", "error")
            return redirect(url_for('register'))

        # Check for duplicate username/email
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for('register'))

        # Save user
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if not email or not password:
            flash("email and password are required.", "error")
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with this email.", "error")
            return redirect(url_for('login'))

        if user.password != password:
            flash("Incorrect password.", "error")
            return redirect(url_for('login'))

        session['user_id'] = user.id
        flash("Logged in successfully!", "success")
        return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out.", "success")
    return redirect(url_for('login'))


@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form['description'].strip()

        if not title:
            flash("Title is required.", "error")
            return redirect(url_for('home'))

        task = Task(title=title, description=description, user_id=session['user_id'])
        db.session.add(task)
        db.session.commit()
        flash("Task added.", "success")
        return redirect(url_for('home'))

    # Get latest tasks first
    tasks = Task.query.filter_by(user_id=session['user_id']).order_by(Task.created_at.desc()).all()
    return render_template('home.html', tasks=tasks)


# Route to delete a task
@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        flash("Unauthorized action.", "error")
        return redirect(url_for('home'))

    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "success")
    return redirect(url_for('home'))


# Route to update a task
@app.route('/edit/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        flash("Unauthorized action.", "error")
        return redirect(url_for('home'))

    title = request.form['title'].strip()
    description = request.form['description'].strip()

    if not title:
        flash("Title is required.", "error")
        return redirect(url_for('home'))

    task.title = title
    task.description = description
    db.session.commit()
    flash("Task updated.", "success")
    return redirect(url_for('home'))



if __name__ == '__main__':
    if not os.path.exists('todo.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True, port=8000)
