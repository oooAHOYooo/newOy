import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///admin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookmarks = db.relationship('Bookmark', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def __repr__(self):
        return f'<User {self.username}>'

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Bookmark user={self.user_id}, item_id={self.item_id}, item_type={self.item_type}>"

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    src = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(100), nullable=False)  # MIME type
    thumbnail = db.Column(db.String(500))
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Video {self.title}>'

def recreate_database():
    # Delete existing database file if it exists
    if os.path.exists('instance/admin.db'):
        os.remove('instance/admin.db')
        print("Existing database file removed.")

    # Create all tables
    with app.app_context():
        db.create_all()
        print("Database tables created.")

        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True,
            is_active=True
        )
        admin.set_password('admin')  # Change this in production!
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")

if __name__ == '__main__':
    recreate_database() 