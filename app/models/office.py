from datetime import datetime
from app.extensions import db
from app.models.base import Base

# Association table for User-Office many-to-many relationship
user_offices = db.Table('user_offices',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('office_id', db.Integer, db.ForeignKey('offices.id'), primary_key=True),
    db.Column('role', db.String(20), nullable=False),
    db.Column('assigned_at', db.DateTime, nullable=False, default=db.func.current_timestamp())
)

class Office(Base):
    """Office model for storing office information."""
    __tablename__ = 'offices'
    
    # Basic Information
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    office_hours = db.Column(db.String(200), nullable=True)
    timezone = db.Column(db.String(50), default='America/New_York')
    is_active = db.Column(db.Boolean, default=True)
    
    # Office Settings and Preferences
    settings = db.Column(db.JSON)  # General office settings
    notification_settings = db.Column(db.JSON)  # Office-wide notification preferences
    
    # Google Workspace Integration
    workspace_domain = db.Column(db.String(255))  # e.g., "yourorg.com"
    calendar_sync_enabled = db.Column(db.Boolean, default=True)
    meet_integration_enabled = db.Column(db.Boolean, default=True)
    drive_integration_enabled = db.Column(db.Boolean, default=True)
    oauth_settings = db.Column(db.JSON)  # Workspace-level OAuth configuration
    
    # Relationships
    users = db.relationship('User', back_populates='office', lazy='dynamic')
    churches = db.relationship('Church', back_populates='office', lazy='dynamic', overlaps="contacts")
    communications = db.relationship('Communication', back_populates='office', lazy='dynamic')
    
    def __repr__(self):
        return f'<Office {self.name}>'
    
    def to_dict(self):
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
    def user_count(self):
        """Get the number of active users in this office."""
        return self.users.filter_by(is_active=True).count()
    
    @property
    def church_count(self):
        """Get the number of churches in this office."""
        return self.churches.count()
    
    def get_admin_users(self):
        """Get all admin users for this office."""
        return self.users.filter_by(role='office_admin', is_active=True).all()
    
    def has_google_workspace_integration(self):
        """Check if office has Google Workspace integration configured."""
        return bool(self.workspace_domain and self.oauth_settings) 