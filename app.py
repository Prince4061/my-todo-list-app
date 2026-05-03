from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Security key session manage karne ke liye zaroori hai
app.config['SECRET_KEY'] = 'kuch_bhi_secret_key_rakh_lo' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 1. New User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False) # Mobile number unique hona chahiye
    password = db.Column(db.String(200), nullable=False) # Password hamesha hash karke save karenge
    tasks = db.relationship('Task', backref='owner', lazy=True) # User ke saare tasks link karne ke liye

# 2. Updated Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Kis user ka task hai

with app.app_context():
    db.create_all()

# --- AUTHENTICATION ROUTES ---

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        password = request.form.get('password')

        # Check agar user pehle se exist karta hai
        existing_user = User.query.filter_by(mobile=mobile).first()
        if existing_user:
            return "User already exists! Please login."

        # Password ko secure banakar save karna
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, mobile=mobile, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        password = request.form.get('password')

        user = User.query.filter_by(mobile=mobile).first()

        # Check agar user hai aur password match ho raha hai
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # Session mein user login ho gaya
            session['user_name'] = user.name
            return redirect(url_for('index'))
        else:
            return "Invalid Mobile Number or Password"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None) # Session destroy kar do
    session.pop('user_name', None)
    return redirect(url_for('login'))

# --- TODO ROUTES (Updated to be user-specific) ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login')) # Agar login nahi hai toh login page par bhejo
    return render_template('index.html', name=session['user_name'])

@app.route('/tasks', methods=['GET'])
def get_tasks():
    if 'user_id' not in session:
        return jsonify([])
    # Sirf ushi user ke tasks laao jo login hai
    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    return jsonify([{'id': t.id, 'content': t.content, 'completed': t.completed} for t in tasks])

@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    new_task = Task(content=data['content'], user_id=session['user_id'])
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'id': new_task.id, 'content': new_task.content, 'completed': new_task.completed})

@app.route('/toggle/<int:id>', methods=['PUT'])
def toggle_task(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    task = Task.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    task.completed = not task.completed
    db.session.commit()
    return jsonify({'message': 'Task updated'})

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_task(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    task = Task.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted'})

if __name__ == '__main__':
    app.run(debug=True)