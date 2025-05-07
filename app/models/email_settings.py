"""Email settings model."""

# No json import needed
from app.extensions import db
from app.models.base import Base

class EmailSettings(Base):
    """Email settings model for storing organization-wide email configuration."""
    __tablename__ = 'email_settings'

    # Basic settings
    mail_default_sender = db.Column(db.String(255), nullable=True)
    email_signature = db.Column(db.Text, nullable=True)
    
    # SMTP settings (if not using Gmail)
    smtp_enabled = db.Column(db.Boolean, default=False, nullable=False)
    smtp_server = db.Column(db.String(255), nullable=True)
    smtp_port = db.Column(db.Integer, nullable=True)
    smtp_username = db.Column(db.String(255), nullable=True)
    smtp_password = db.Column(db.String(255), nullable=True)
    smtp_use_tls = db.Column(db.Boolean, default=True, nullable=False)
    
    # Stats
    sent_today = db.Column(db.Integer, default=0, nullable=False)
    sent_week = db.Column(db.Integer, default=0, nullable=False)
    bounced = db.Column(db.Integer, default=0, nullable=False)
    failed = db.Column(db.Integer, default=0, nullable=False)
    delivery_rate = db.Column(db.Float, default=100.0, nullable=False)
    
    def __repr__(self):
        return f"<EmailSettings(id='{self.id}')>"
    
    def to_dict(self):
        """Convert settings to dictionary."""
        return {
            'id': self.id,
            'mail_default_sender': self.mail_default_sender,
            'email_signature': self.email_signature,
            'smtp_enabled': self.smtp_enabled,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'smtp_username': self.smtp_username,
            'smtp_password': '••••••••••' if self.smtp_password else None,  # Mask password
            'smtp_use_tls': self.smtp_use_tls,
            'sent_today': self.sent_today,
            'sent_week': self.sent_week,
            'bounced': self.bounced,
            'failed': self.failed,
            'delivery_rate': self.delivery_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_settings(cls):
        """Get the email settings or create default if not exists."""
        settings = cls.query.first()
        if not settings:
            settings = cls(
                mail_default_sender='Mobilize App <info@mobilize-app.org>',
                email_signature='<p>Blessings,<br>The Team at Mobilize App</p>',
                smtp_enabled=False,
                smtp_server='',
                smtp_port=587,
                smtp_username='',
                smtp_password='',
                smtp_use_tls=True,
                sent_today=0,
                sent_week=0,
                bounced=0,
                failed=0,
                delivery_rate=100.0
            )
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def update_from_form(self, form_data):
        """Update settings from form data."""
        self.mail_default_sender = form_data.get('mail_default_sender', '')
        self.email_signature = form_data.get('email_signature', '')
        
        # Only update these if SMTP is being configured
        if 'smtp_enabled' in form_data:
            self.smtp_enabled = True
            self.smtp_server = form_data.get('smtp_server', '')
            self.smtp_port = int(form_data.get('smtp_port', 587))
            self.smtp_username = form_data.get('smtp_username', '')
            
            # Only update password if provided (not empty)
            if form_data.get('smtp_password'):
                self.smtp_password = form_data.get('smtp_password')
                
            self.smtp_use_tls = 'smtp_use_tls' in form_data
        else:
            self.smtp_enabled = False
        
        db.session.commit()
        return self
