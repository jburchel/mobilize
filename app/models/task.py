from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Boolean, JSON, ForeignKey, Date, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import Base
from app.models.constants import TASK_STATUS_CHOICES, TASK_PRIORITY_CHOICES, REMINDER_CHOICES

class Task(Base):
    """Task model for tracking tasks related to people and churches."""
    __tablename__ = 'tasks'

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    due_date: Mapped[Optional[datetime]] = mapped_column(Date)
    due_time: Mapped[Optional[str]] = mapped_column(String)  # Store time as HH:MM format
    
    # Changed from reminder_time to be more specific about what this stores
    due_time_details: Mapped[Optional[str]] = mapped_column(String)  # Store additional time details if needed
    
    # New field for reminder options using the constants
    reminder_option: Mapped[Optional[str]] = mapped_column(String, nullable=True, default='none')  # Uses REMINDER_CHOICES
    
    priority: Mapped[str] = mapped_column(String, default='medium')  # Uses TASK_PRIORITY_CHOICES
    status: Mapped[str] = mapped_column(String, nullable=False, default='pending')  # Uses TASK_STATUS_CHOICES
    category: Mapped[Optional[str]] = mapped_column(String)
    assigned_to: Mapped[Optional[str]] = mapped_column(String)  # Store user ID or email
    contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey('contacts.id'))
    person_id: Mapped[Optional[int]] = mapped_column(ForeignKey('people.id'))
    church_id: Mapped[Optional[int]] = mapped_column(ForeignKey('churches.id'))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    office_id: Mapped[Optional[int]] = mapped_column(ForeignKey('offices.id'), nullable=True)
    
    # Completion tracking
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completion_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Google Calendar integration fields
    google_calendar_event_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    google_calendar_sync_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    person = relationship("Person", foreign_keys=[person_id], back_populates="tasks")
    church = relationship("Church", foreign_keys=[church_id], back_populates="tasks")
    assigned_user = relationship('User', 
                               primaryjoin="foreign(Task.assigned_to) == User.id",
                               backref='assigned_tasks',
                               overlaps="tasks",
                               viewonly=True)
    owner = relationship('User', foreign_keys=[owner_id],
                        back_populates='owned_tasks')
    created_by_user = relationship('User', foreign_keys=[created_by],
                                 back_populates='created_tasks',
                                 viewonly=True)

    def __repr__(self) -> str:
        return f"<Task(title='{self.title}', due_date='{self.due_date}')>"

    def get_reminder_display(self) -> str:
        """Return a human-readable representation of the reminder option."""
        reminder_map = {
            '15_min': '15 minutes before',
            '30_min': '30 minutes before',
            '1_hour': '1 hour before',
            '2_hours': '2 hours before',
            '1_day': '1 day before',
            '3_days': '3 days before',
            '1_week': '1 week before',
            'none': 'No reminder'
        }
        return reminder_map.get(self.reminder_option, 'No reminder')

    def to_dict(self) -> Dict[str, Any]:
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