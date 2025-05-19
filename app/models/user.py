from datetime import datetime
from typing import Optional, List, Dict, Any
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import String, Integer, Boolean, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from app.extensions import db
from app.models.base import Base

# User roles enum
USER_ROLES = ['super_admin', 'office_admin', 'user']

class User(UserMixin, Base):
    """User model for authentication and authorization."""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(128))
    firebase_uid: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(64))
    last_name: Mapped[Optional[str]] = mapped_column(String(64))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    profile_image: Mapped[Optional[str]] = mapped_column(String(255))
    job_title: Mapped[Optional[str]] = mapped_column(String(100))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_login: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default='standard_user')
    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey('roles.id'))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    notification_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    google_refresh_token: Mapped[Optional[str]] = mapped_column(String(255))
    google_calendar_sync: Mapped[bool] = mapped_column(Boolean, default=True)
    google_meet_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_sync_contacts_only: Mapped[bool] = mapped_column(Boolean, default=False)
    office_id: Mapped[Optional[int]] = mapped_column(ForeignKey('offices.id'))
    person_id: Mapped[Optional[int]] = mapped_column(ForeignKey('people.id'))

    # Relationships with type hints
    office = relationship('Office', back_populates='users')
    role_obj = relationship('Role', foreign_keys=[role_id])
    person = relationship(
        'Person',
        back_populates='associated_user',
        foreign_keys=[person_id],
        single_parent=True
    )
    assigned_tasks = relationship(
        'Task',
        primaryjoin="User.username == foreign(Task.assigned_to)",
        back_populates='assigned_user',
        viewonly=True  # Make this a viewonly relationship since there's no actual FK
    )
    owned_tasks = relationship(
        'Task',
        back_populates='owner',
        foreign_keys='Task.owner_id',
        cascade='all, delete-orphan'
    )
    created_tasks = relationship(
        'Task',
        back_populates='created_by_user',
        foreign_keys='Task.created_by',
        lazy='dynamic'
    )
    communications = relationship(
        'Communication',
        backref='user_sender',
        foreign_keys='Communication.user_id'
    )
    owned_communications = relationship(
        'Communication',
        back_populates='owner',
        foreign_keys='Communication.owner_id',
        cascade='all, delete-orphan'
    )
    email_signatures = relationship(
        'EmailSignature',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    google_tokens = relationship(
        'GoogleToken',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    contacts = relationship(
        'Contact',
        back_populates='user',
        foreign_keys='Contact.user_id',
        cascade='all, delete-orphan'
    )
    owned_churches = relationship(
        'Church',
        back_populates='owner',
        foreign_keys='Church.owner_id',
        primaryjoin='User.id==Church.owner_id',
        cascade='all, delete-orphan'
    )

    def __init__(self, username: Optional[str] = None, email: Optional[str] = None,
                 role: str = 'standard_user', office_id: Optional[int] = None,
                 password: Optional[str] = None, first_name: Optional[str] = None,
                 last_name: Optional[str] = None, firebase_uid: Optional[str] = None,
                 id: Optional[int] = None, **kwargs) -> None:
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

    def set_password(self, password: str) -> None:
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.username}>'

    def to_dict(self) -> Dict[str, Any]:
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
            'first_login': self.first_login,
            'role': self.role,
            'office_id': self.office_id,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'google_calendar_sync': self.google_calendar_sync,
            'google_meet_enabled': self.google_meet_enabled,
            'email_sync_contacts_only': self.email_sync_contacts_only
        }

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()
        
    @property
    def name(self) -> str:
        """Get user's username as name for compatibility."""
        return self.username

    def is_admin(self) -> bool:
        """Check if user is an admin (either super_admin or office_admin)."""
        return self.role in ['super_admin', 'office_admin']

    def is_super_admin(self) -> bool:
        """Check if user is a super admin."""
        return self.role == 'super_admin'

    def can_manage_office(self, office_id: int) -> bool:
        """Check if user can manage a specific office."""
        return self.is_super_admin() or (self.is_admin() and self.office_id == office_id)

    def get_owned_records_count(self) -> Dict[str, int]:
        """Get count of all records owned by this user."""
        return {
            'churches': len(self.owned_churches),
            'communications': len(self.owned_communications),
            'tasks': len(self.owned_tasks)
        }

    def count_owned_records(self, record_type: str) -> int:
        """Count owned records of a specific type."""
        from app.models.person import Person
        from sqlalchemy import func
        from app.extensions import db
        
        if record_type == 'churches':
            return len(self.owned_churches)
        elif record_type == 'communications':
            return len(self.owned_communications)
        elif record_type == 'tasks':
            return len(self.owned_tasks)
        elif record_type == 'people':
            # Count people records where this user is the owner (using user_id field)
            return db.session.query(func.count(Person.id)).filter(Person.user_id == self.id).scalar() or 0
        return 0 