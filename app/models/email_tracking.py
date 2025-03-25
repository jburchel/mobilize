from datetime import datetime
from app.extensions import db
from app.models.base import Base


class EmailTracking(Base):
    """Model for tracking email sends and interactions."""
    __tablename__ = 'email_tracking'

    # Core fields
    email_subject = db.Column(db.String(255), nullable=False)  # Subject of the email
    recipient_email = db.Column(db.String(255), nullable=False)  # Recipient's email address
    status = db.Column(db.String(50), nullable=False, default='sent')  # Status: sent, delivered, opened, clicked, bounced, etc.
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # When the email was sent
    
    # Tracking data
    opened_at = db.Column(db.DateTime, nullable=True)  # When the email was first opened
    open_count = db.Column(db.Integer, default=0)  # Number of times the email was opened
    last_opened_at = db.Column(db.DateTime, nullable=True)  # Last time the email was opened
    
    clicked_at = db.Column(db.DateTime, nullable=True)  # When a link was first clicked
    click_count = db.Column(db.Integer, default=0)  # Number of link clicks
    last_clicked_at = db.Column(db.DateTime, nullable=True)  # Last time a link was clicked
    
    # Technical data
    message_id = db.Column(db.String(255), nullable=True)  # Email message ID for tracking
    tracking_pixel = db.Column(db.String(255), nullable=True)  # Unique identifier for the tracking pixel
    
    # Foreign keys
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=True)  # Template used, if any
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # User who sent the email
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=True)  # Person record, if available
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=False)  # Office the email belongs to
    
    # For bulk emails
    bulk_send_id = db.Column(db.String(50), nullable=True)  # Group ID for tracking bulk sends
    
    # Relationships
    template = db.relationship("EmailTemplate", backref="sent_emails")
    sender = db.relationship("User", backref="sent_emails")
    person = db.relationship("Person", backref="received_emails")
    office = db.relationship("Office", backref="sent_emails")
    
    def __repr__(self):
        return f"<EmailTracking(id='{self.id}', recipient='{self.recipient_email}', status='{self.status}')>"
    
    def mark_opened(self):
        """Mark the email as opened."""
        now = datetime.utcnow()
        if not self.opened_at:
            self.opened_at = now
        self.last_opened_at = now
        self.open_count += 1
        self.status = 'opened'
    
    def mark_clicked(self):
        """Mark the email as clicked."""
        now = datetime.utcnow()
        if not self.clicked_at:
            self.clicked_at = now
        self.last_clicked_at = now
        self.click_count += 1
        self.status = 'clicked'
    
    def to_dict(self):
        """Convert email tracking to dictionary."""
        return {
            'id': self.id,
            'email_subject': self.email_subject,
            'recipient_email': self.recipient_email,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'open_count': self.open_count,
            'last_opened_at': self.last_opened_at.isoformat() if self.last_opened_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'click_count': self.click_count,
            'last_clicked_at': self.last_clicked_at.isoformat() if self.last_clicked_at else None,
            'template_id': self.template_id,
            'sender_id': self.sender_id,
            'person_id': self.person_id,
            'office_id': self.office_id,
            'bulk_send_id': self.bulk_send_id
        } 