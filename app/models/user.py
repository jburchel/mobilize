from datetime import datetime
from flask_login import UserMixin
from app import db
from app.models.base import BaseModel

class User(UserMixin, BaseModel):
    """User model for authentication and user management."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    firebase_uid = db.Column(db.String(128), nullable=False, unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    job_title = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    timezone = db.Column(db.String(50), default='America/New_York')
    email_signature = db.Column(db.Text)
    profile_picture_url = db.Column(db.String(255))
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='standard_user')
    google_refresh_token = db.Column(db.Text)
    preferences = db.Column(db.JSON)
    notification_settings = db.Column(db.JSON)
    theme_preferences = db.Column(db.JSON)

    # Relationships
    tasks = db.relationship('Task', backref='assigned_user', lazy=True, foreign_keys='Task.user_id')
    communications = db.relationship('Communication', backref='sender', lazy=True, foreign_keys='Communication.user_id')
    email_signatures = db.relationship('EmailSignature', backref='user', lazy=True, foreign_keys='EmailSignature.user_id')
    google_tokens = db.relationship('GoogleToken', backref='user', lazy=True, foreign_keys='GoogleToken.user_id')

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', name='{self.first_name} {self.last_name}')>"

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'job_title': self.job_title,
            'phone': self.phone,
            'timezone': self.timezone,
            'role': self.role,
            'is_active': self.is_active,
            'profile_picture_url': self.profile_picture_url,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 