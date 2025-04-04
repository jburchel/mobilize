from datetime import datetime
from app.extensions import db
from app.models.base import Base
from app.models.constants import TASK_STATUS_CHOICES, TASK_PRIORITY_CHOICES, REMINDER_CHOICES

class Task(Base):
    """Task model for tracking tasks related to people and churches."""
    __tablename__ = 'tasks'

    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    due_date = db.Column(db.Date)
    due_time = db.Column(db.String)  # Store time as HH:MM format
    
    # Changed from reminder_time to be more specific about what this stores
    due_time_details = db.Column(db.String)  # Store additional time details if needed
    
    # New field for reminder options using the constants
    reminder_option = db.Column(db.String, nullable=True, default='none')  # Uses REMINDER_CHOICES
    
    priority = db.Column(db.String, default='medium')  # Uses TASK_PRIORITY_CHOICES
    status = db.Column(db.String, nullable=False, default='pending')  # Uses TASK_STATUS_CHOICES
    category = db.Column(db.String)
    assigned_to = db.Column(db.String)  # Store user ID or email
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=True)
    
    # Completion tracking
    completed_date = db.Column(db.DateTime, nullable=True)
    completion_notes = db.Column(db.Text, nullable=True)
    
    # Google Calendar integration fields
    google_calendar_event_id = db.Column(db.String, unique=True, nullable=True)
    google_calendar_sync_enabled = db.Column(db.Boolean, default=False, nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    person = db.relationship("Person", foreign_keys=[person_id], viewonly=True)
    assigned_user = db.relationship('User', 
                                   primaryjoin="foreign(Task.assigned_to) == User.id",
                                   backref=db.backref('assigned_tasks', lazy='dynamic'),
                                   overlaps="tasks",
                                   viewonly=True)
    created_by_user = db.relationship('User', foreign_keys=[created_by],
                                     backref=db.backref('created_tasks', lazy='dynamic'),
                                     viewonly=True)

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
            'due_time_details': self.due_time_details,
            'reminder_option': self.reminder_option,
            'priority': self.priority,
            'status': self.status,
            'category': self.category,
            'assigned_to': self.assigned_to,
            'contact_id': self.contact_id,
            'person_id': self.person_id,
            'church_id': self.church_id,
            'created_by': self.created_by,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'completion_notes': self.completion_notes,
            'owner_id': self.owner_id,
            'google_calendar_event_id': self.google_calendar_event_id,
            'google_calendar_sync_enabled': self.google_calendar_sync_enabled,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 