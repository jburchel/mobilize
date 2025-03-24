from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.base import Base
from sqlalchemy import orm

# User roles enum
USER_ROLES = ['super_admin', 'office_admin', 'user']

class User(UserMixin, Base):
    """User model for authentication and authorization."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    firebase_uid = db.Column(db.String(128), unique=True, nullable=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    profile_image = db.Column(db.String(255))
    job_title = db.Column(db.String(100))
    department = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), nullable=False, default='standard_user')
    last_login = db.Column(db.DateTime)
    preferences = db.Column(db.JSON)
    notification_settings = db.Column(db.JSON)
    google_refresh_token = db.Column(db.String(255))
    google_calendar_sync = db.Column(db.Boolean, default=True)
    google_meet_enabled = db.Column(db.Boolean, default=True)
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=True)
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=True)

    # Relationships
    office = db.relationship('Office', back_populates='users')
    person = db.relationship('Person', backref=db.backref('associated_user', uselist=False), foreign_keys=[person_id])
    tasks = db.relationship('Task', overlaps="assigned_user,tasks", primaryjoin="User.id == foreign(Task.assigned_to)")
    owned_tasks = db.relationship('Task', back_populates='owner', foreign_keys='Task.owner_id')
    communications = db.relationship('Communication', back_populates='sender', foreign_keys='Communication.user_id')
    owned_communications = db.relationship('Communication', back_populates='owner', foreign_keys='Communication.owner_id')
    email_signatures = db.relationship('EmailSignature', back_populates='user')
    google_tokens = db.relationship('GoogleToken', back_populates='user')
    contacts = db.relationship('Contact', back_populates='user', foreign_keys='Contact.user_id')
    owned_churches = orm.relationship(
        'Church',
        back_populates='owner',
        foreign_keys='[Church.owner_id]',
        primaryjoin='User.id==Church.owner_id'
    )

    def __init__(self, username=None, email=None, role='standard_user', office_id=None, password=None,
                 first_name=None, last_name=None, firebase_uid=None, id=None, **kwargs):
        """Initialize a new User instance."""
        super().__init__()
        if id is not None:
            self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.office_id = office_id
        self.first_name = first_name
        self.last_name = last_name
        self.firebase_uid = firebase_uid
        if password:
            self.set_password(password)
        
        # Set any additional attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_password(self, password):
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'profile_image': self.profile_image,
            'job_title': self.job_title,
            'department': self.department,
            'is_active': self.is_active,
            'role': self.role,
            'office_id': self.office_id,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    def is_admin(self):
        """Check if user is an admin (either super_admin or office_admin)."""
        return self.role in ['super_admin', 'office_admin']

    def is_super_admin(self):
        """Check if user is a super admin."""
        return self.role == 'super_admin'

    def can_manage_office(self, office_id):
        """Check if user can manage a specific office."""
        return self.is_super_admin() or (self.is_admin() and self.office_id == office_id)

    def get_owned_records_count(self):
        """Get count of all records owned by this user."""
        return {
            'churches': self.owned_churches.count(),
            'communications': self.owned_communications.count(),
            'tasks': self.owned_tasks.count()
        } 