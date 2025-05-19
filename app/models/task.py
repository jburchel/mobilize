from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Boolean, JSON, ForeignKey, Date, Text, Integer, DateTime, Column, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import Base
import enum

class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskType(enum.Enum):
    GENERAL = "general"
    FOLLOW_UP = "follow_up"
    MEETING = "meeting"
    CALL = "call"
    EMAIL = "email"

class Task(Base):
    """Task model."""
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(
            TaskStatus,
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enums: [e.value for e in enums],
            validate_strings=True
        ),
        default=TaskStatus.PENDING
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(
            TaskPriority,
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enums: [e.value for e in enums],
            validate_strings=True
        ),
        default=TaskPriority.MEDIUM
    )
    type: Mapped[TaskType] = mapped_column(
        Enum(
            TaskType,
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enums: [e.value for e in enums],
            validate_strings=True
        ),
        default=TaskType.GENERAL
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    due_time: Mapped[Optional[str]] = mapped_column(String(10))  # Store time as HH:MM format
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Google Calendar integration fields
    google_calendar_event_id: Mapped[Optional[str]] = mapped_column(String, unique=True)
    google_calendar_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Reminder fields
    reminder_option: Mapped[Optional[str]] = mapped_column(String(50))
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Foreign keys
    person_id: Mapped[Optional[int]] = mapped_column(ForeignKey('people.id'))
    church_id: Mapped[Optional[int]] = mapped_column(ForeignKey('churches.id'))
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), default='UNASSIGNED')
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
    office_id: Mapped[Optional[int]] = mapped_column(ForeignKey('offices.id'))
    
    # Relationships
    assigned_user = relationship("User", back_populates="assigned_tasks", primaryjoin="User.username==Task.assigned_to", foreign_keys=[assigned_to])
    owner = relationship("User", back_populates="owned_tasks", foreign_keys=[owner_id])
    person = relationship("Person", back_populates="tasks")
    church = relationship("Church", back_populates="tasks")
    created_by_user = relationship("User", back_populates="created_tasks", foreign_keys=[created_by])
    office = relationship("Office", back_populates="tasks")
    
    def __init__(self, **kwargs):
        """Initialize a new Task."""
        super(Task, self).__init__(**kwargs)
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        """Return string representation."""
        return f'<Task {self.id}: {self.title}>'

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'priority': self.priority.value if self.priority else None,
            'type': self.type.value if self.type else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'due_time': self.due_time,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'person_id': self.person_id,
            'church_id': self.church_id,
            'assigned_to': self.assigned_to,
            'owner_id': self.owner_id,
            'created_by': self.created_by,
            'office_id': self.office_id,
            'google_calendar_event_id': self.google_calendar_event_id,
            'google_calendar_sync_enabled': self.google_calendar_sync_enabled,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'reminder_option': self.reminder_option,
            'reminder_sent': self.reminder_sent,
            # Include related objects if they're loaded
            'person': self.person.to_dict() if hasattr(self, 'person') and self.person else None,
            'church': self.church.to_dict() if hasattr(self, 'church') and self.church else None,
            'assigned_user': self.assigned_user.to_dict() if hasattr(self, 'assigned_user') and self.assigned_user else None,
            'owner': self.owner.to_dict() if hasattr(self, 'owner') and self.owner else None,
            'created_by_user': self.created_by_user.to_dict() if hasattr(self, 'created_by_user') and self.created_by_user else None
        }

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