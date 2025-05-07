"""Google Workspace settings model."""

# No datetime import needed
from app.extensions import db
from app.models.base import Base
import json

class GoogleWorkspaceSettings(Base):
    """Google Workspace settings model for storing organization-wide Google integration settings."""
    __tablename__ = 'google_workspace_settings'

    # Basic settings
    enabled = db.Column(db.Boolean, default=False, nullable=False)
    domain = db.Column(db.String(255), nullable=True)
    client_id = db.Column(db.String(255), nullable=True)
    client_secret = db.Column(db.String(255), nullable=True)
    redirect_uri = db.Column(db.String(255), nullable=True)
    admin_email = db.Column(db.String(255), nullable=True)
    
    # Sync settings
    sync_frequency = db.Column(db.String(50), default='daily', nullable=False)  # 'hourly', 'daily', 'weekly'
    last_sync = db.Column(db.DateTime, nullable=True)  # Uses SQLAlchemy's DateTime type
    
    # Scopes as a JSON string
    scopes = db.Column(db.Text, nullable=True)
    
    # Stats
    connected_users = db.Column(db.Integer, default=0, nullable=False)
    synced_users = db.Column(db.Integer, default=0, nullable=False)
    synced_groups = db.Column(db.Integer, default=0, nullable=False)
    synced_events = db.Column(db.Integer, default=0, nullable=False)
    
    def __repr__(self):
        return f"<GoogleWorkspaceSettings(domain='{self.domain}')>"
    
    def to_dict(self):
        """Convert settings to dictionary."""
        scopes_list = []
        if self.scopes:
            try:
                scopes_list = json.loads(self.scopes)
            except json.JSONDecodeError:
                pass
                
        return {
            'id': self.id,
            'enabled': self.enabled,
            'domain': self.domain,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'admin_email': self.admin_email,
            'sync_frequency': self.sync_frequency,
            'last_sync': self.last_sync,
            'scopes': scopes_list,
            'connected_users': self.connected_users,
            'synced_users': self.synced_users,
            'synced_groups': self.synced_groups,
            'synced_events': self.synced_events,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_settings(cls):
        """Get the Google Workspace settings or create default if not exists."""
        settings = cls.query.first()
        if not settings:
            settings = cls(
                enabled=False,
                domain='',
                client_id='',
                client_secret='',
                redirect_uri='',
                admin_email='',
                sync_frequency='daily',
                scopes=json.dumps(['calendar', 'contacts', 'drive'])
            )
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def update_from_form(self, form_data):
        """Update settings from form data."""
        self.enabled = 'enabled' in form_data
        self.domain = form_data.get('domain', '')
        self.client_id = form_data.get('client_id', '')
        
        # Only update client secret if provided (not empty)
        if form_data.get('client_secret'):
            self.client_secret = form_data.get('client_secret')
            
        self.redirect_uri = form_data.get('redirect_uri', '')
        self.admin_email = form_data.get('admin_email', '')
        self.sync_frequency = form_data.get('sync_frequency', 'daily')
        
        # Handle scopes (checkboxes)
        scopes = form_data.getlist('scopes') if hasattr(form_data, 'getlist') else form_data.get('scopes', [])
        self.scopes = json.dumps(scopes)
        
        db.session.commit()
        return self
