from datetime import datetime, timezone
from app.extensions import db
from app.models.base import Base

class Communication(Base):
    """Communication model for tracking interactions with people and churches."""
    __tablename__ = 'communications'

    type = db.Column(db.String, nullable=False)  # Email, SMS, Phone, Letter
    message = db.Column(db.String, nullable=False)
    date_sent = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=False)
    direction = db.Column(db.String(50), nullable=False, default='outbound')  # 'inbound' or 'outbound'
    sender = db.Column(db.String(255), nullable=True)  # Added to match database schema
    
    # Gmail integration fields
    gmail_message_id = db.Column(db.String, nullable=True)
    gmail_thread_id = db.Column(db.String, nullable=True)
    email_status = db.Column(db.String, nullable=True)  # 'sent', 'draft', 'failed', etc.
    subject = db.Column(db.String, nullable=True)  # Email subject
    attachments = db.Column(db.String, nullable=True)  # JSON string of attachment info
    last_synced_at = db.Column(db.DateTime, nullable=True)  # Timestamp for last sync
    
    # Video conference fields
    google_meet_link = db.Column(db.String, nullable=True)  # For video conference calls
    google_calendar_event_id = db.Column(db.String, nullable=True)  # Reference to calendar event

    # Relationships
    person = db.relationship("Person", foreign_keys=[person_id], back_populates="communications")
    user = db.relationship('User', foreign_keys=[user_id], backref='received_communications')
    owner = db.relationship('User', foreign_keys=[owner_id], backref='created_communications')

    def __repr__(self):
        return f"<Communication(type='{self.type}', date_sent='{self.date_sent}')>"

    def to_dict(self):
        """Convert communication to dictionary."""
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'date_sent': self.date_sent.isoformat() if self.date_sent else None,
            'date': self.date.isoformat() if self.date else None,
            'person_id': self.person_id,
            'church_id': self.church_id,
            'user_id': self.user_id,
            'owner_id': self.owner_id,
            'office_id': self.office_id,
            'direction': self.direction,
            'sender': self.sender,
            'gmail_message_id': self.gmail_message_id,
            'gmail_thread_id': self.gmail_thread_id,
            'email_status': self.email_status,
            'subject': self.subject,
            'attachments': self.attachments,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 