# datetime is used in type annotations
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, JSON, ForeignKey, Table, Column, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import Base

# Import models using TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from app.models.user import User
    from app.models.church import Church
    from app.models.communication import Communication
    from app.models.base import Contact
    from app.models.task import Task

# Association table for User-Office many-to-many relationship
user_offices = Table(
    'user_offices',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('office_id', Integer, ForeignKey('offices.id'), primary_key=True),
    Column('role', String(20), nullable=False),
    Column('assigned_at', DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP'))
)

class Office(Base):
    """Office model for storing office information."""
    __tablename__ = 'offices'
    
    # Basic Information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    office_hours: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default='America/New_York')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Office Settings and Preferences
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # General office settings
    notification_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Office-wide notification preferences
    
    # Google Workspace Integration
    workspace_domain: Mapped[Optional[str]] = mapped_column(String(255))  # e.g., "yourorg.com"
    calendar_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    meet_integration_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    drive_integration_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    oauth_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Workspace-level OAuth configuration
    
    # Relationships
    users: Mapped[List["User"]] = relationship('User', back_populates='office', lazy='dynamic')
    churches: Mapped[List["Church"]] = relationship('Church', back_populates='office', lazy='dynamic', overlaps="contacts")
    communications: Mapped[List["Communication"]] = relationship('Communication', back_populates='office', lazy='dynamic')
    contacts: Mapped[List["Contact"]] = relationship('Contact', back_populates='office', lazy='dynamic')
    tasks: Mapped[List["Task"]] = relationship('Task', back_populates='office', lazy='dynamic', overlaps="assigned_tasks")
    
    def __repr__(self) -> str:
        return f'<Office {self.name}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert office to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'country': self.country,
            'office_hours': self.office_hours,
            'timezone': self.timezone,
            'is_active': self.is_active,
            'workspace_domain': self.workspace_domain,
            'calendar_sync_enabled': self.calendar_sync_enabled,
            'meet_integration_enabled': self.meet_integration_enabled,
            'drive_integration_enabled': self.drive_integration_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def user_count(self) -> int:
        """Get the number of active users in this office."""
        return self.users.filter_by(is_active=True).count()
    
    @property
    def church_count(self) -> int:
        """Get the number of churches in this office."""
        return self.churches.count()
    
    def get_admin_users(self) -> List["User"]:
        """Get all admin users for this office."""
        return self.users.filter_by(role='office_admin', is_active=True).all()
    
    def has_google_workspace_integration(self) -> bool:
        """Check if office has Google Workspace integration configured."""
        return bool(self.workspace_domain and self.oauth_settings) 