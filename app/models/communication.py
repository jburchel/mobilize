from datetime import datetime
from app import db
from app.models.base import BaseModel

class Communication(BaseModel):
    """Communication model for tracking interactions with people and churches."""
    __tablename__ = 'communications'

    type = db.Column(db.String, nullable=False)  # Email, SMS, Phone, Letter
    message = db.Column(db.String, nullable=False)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    direction = db.Column(db.String(50), nullable=False, default='outbound')  # 'inbound' or 'outbound'
    
    # Gmail integration fields
    gmail_message_id = db.Column(db.String, nullable=True)
    gmail_thread_id = db.Column(db.String, nullable=True)
    email_status = db.Column(db.String, nullable=True)  # 'sent', 'draft', 'failed', etc.
    subject = db.Column(db.String, nullable=True)  # Email subject
    attachments = db.Column(db.String, nullable=True)  # JSON string of attachment info
    last_synced_at = db.Column(db.DateTime, nullable=True)  # Timestamp for last sync

    # Relationships
    person = db.relationship("Person", back_populates="communications")
    church = db.relationship("Church", back_populates="communications")

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
            'direction': self.direction,
            'gmail_message_id': self.gmail_message_id,
            'gmail_thread_id': self.gmail_thread_id,
            'email_status': self.email_status,
            'subject': self.subject,
            'attachments': self.attachments,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 