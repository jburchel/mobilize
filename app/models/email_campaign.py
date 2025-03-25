from datetime import datetime
import json
from app.extensions import db
from app.models.base import Base


class EmailCampaign(Base):
    """Model for bulk email campaigns."""
    __tablename__ = 'email_campaigns'

    # Campaign details
    name = db.Column(db.String(100), nullable=False)  # Campaign name
    description = db.Column(db.Text, nullable=True)  # Campaign description
    status = db.Column(db.String(50), nullable=False, default='draft')  # Status: draft, scheduled, sending, completed, cancelled
    
    # Email content
    subject = db.Column(db.String(255), nullable=False)  # Email subject
    content = db.Column(db.Text, nullable=False)  # Email content (HTML)
    
    # Schedule
    scheduled_at = db.Column(db.DateTime, nullable=True)  # When the campaign is scheduled to send
    sent_at = db.Column(db.DateTime, nullable=True)  # When the campaign was actually sent
    
    # Recipient data
    recipient_count = db.Column(db.Integer, default=0)  # Number of recipients
    recipient_filter = db.Column(db.Text, nullable=True)  # JSON-encoded filter criteria for selecting recipients
    
    # Tracking data
    sent_count = db.Column(db.Integer, default=0)  # Number of emails actually sent
    open_count = db.Column(db.Integer, default=0)  # Number of recipients who opened
    click_count = db.Column(db.Integer, default=0)  # Number of recipients who clicked
    bounce_count = db.Column(db.Integer, default=0)  # Number of emails that bounced
    
    # Foreign keys
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=True)  # Template used, if any
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # User who created the campaign
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=False)  # Office the campaign belongs to
    
    # Relationships
    template = db.relationship("EmailTemplate")
    creator = db.relationship("User", foreign_keys=[created_by])
    office = db.relationship("Office", backref="email_campaigns")
    
    def __repr__(self):
        return f"<EmailCampaign(name='{self.name}', status='{self.status}')>"
    
    def get_recipient_filter(self):
        """Get recipient filter as a dictionary."""
        if self.recipient_filter:
            try:
                return json.loads(self.recipient_filter)
            except:
                return {}
        return {}
    
    def set_recipient_filter(self, filter_dict):
        """Set recipient filter from a dictionary."""
        if filter_dict:
            self.recipient_filter = json.dumps(filter_dict)
        else:
            self.recipient_filter = None
    
    def update_stats(self):
        """Update campaign statistics based on tracking data."""
        from app.models.email_tracking import EmailTracking
        
        tracking = EmailTracking.query.filter_by(bulk_send_id=str(self.id)).all()
        
        self.sent_count = len(tracking)
        self.open_count = sum(1 for t in tracking if t.open_count > 0)
        self.click_count = sum(1 for t in tracking if t.click_count > 0)
        self.bounce_count = sum(1 for t in tracking if t.status == 'bounced')
    
    def to_dict(self):
        """Convert email campaign to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'subject': self.subject,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'recipient_count': self.recipient_count,
            'recipient_filter': self.get_recipient_filter(),
            'sent_count': self.sent_count,
            'open_count': self.open_count,
            'click_count': self.click_count,
            'bounce_count': self.bounce_count,
            'template_id': self.template_id,
            'created_by': self.created_by,
            'office_id': self.office_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 