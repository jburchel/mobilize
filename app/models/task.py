from datetime import datetime
from app import db
from app.models.base import BaseModel

class Task(BaseModel):
    """Task model for tracking tasks related to people and churches."""
    __tablename__ = 'tasks'

    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    due_date = db.Column(db.Date)
    due_time = db.Column(db.String)  # Store time as HH:MM format
    reminder_time = db.Column(db.String)  # Store reminder time as HH:MM format
    priority = db.Column(db.String)
    status = db.Column(db.String, nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Google Calendar integration fields
    google_calendar_event_id = db.Column(db.String, unique=True, nullable=True)
    google_calendar_sync_enabled = db.Column(db.Boolean, default=False, nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    person = db.relationship("Person", back_populates="tasks")
    church = db.relationship("Church", back_populates="tasks")

    def __repr__(self):
        return f"<Task(title='{self.title}', due_date='{self.due_date}')>"

    def to_dict(self):
        """Convert task to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'due_time': self.due_time,
            'reminder_time': self.reminder_time,
            'priority': self.priority,
            'status': self.status,
            'person_id': self.person_id,
            'church_id': self.church_id,
            'user_id': self.user_id,
            'google_calendar_event_id': self.google_calendar_event_id,
            'google_calendar_sync_enabled': self.google_calendar_sync_enabled,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 