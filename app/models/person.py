from datetime import datetime, UTC
from app.extensions import db
from app.models.base import Contact
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.constants import (
    MARITAL_STATUS_CHOICES, PEOPLE_PIPELINE_CHOICES, PRIORITY_CHOICES, 
    ASSIGNED_TO_CHOICES, SOURCE_CHOICES
)

class Person(Contact):
    """Person model for tracking individual contacts."""
    __tablename__ = 'people'
    __mapper_args__ = {
        'polymorphic_identity': 'person'
    }

    id = db.Column(db.Integer, db.ForeignKey('contacts.id'), primary_key=True)
    first_name = db.Column(db.String(100), name='first_name')
    last_name = db.Column(db.String(100), name='last_name')
    
    # Fields from old model
    spouse_first_name = db.Column(db.String(100))
    spouse_last_name = db.Column(db.String(100))
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'), nullable=True)
    church_role = db.Column(db.String(100))
    is_primary_contact = db.Column(db.Boolean, default=False)
    
    # Additional fields from old model
    virtuous = db.Column(db.Boolean, default=False)
    title = db.Column(db.String(100))
    marital_status = db.Column(db.String(100))  # Uses MARITAL_STATUS_CHOICES
    referred_by = db.Column(db.String(100))
    info_given = db.Column(db.Text)
    desired_service = db.Column(db.Text)
    
    # Tracking fields from new model
    last_contact = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    next_contact = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='active')  # active, inactive, archived
    google_contact_id = db.Column(db.String, nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    
    # Pipeline fields - combining old and new approaches
    people_pipeline = db.Column(db.String(100), default='INFORMATION')  # Uses PEOPLE_PIPELINE_CHOICES
    pipeline_status = db.Column(db.String(50), nullable=True)  # From new model
    pipeline_stage = db.Column(db.String(50), nullable=True)  # From new model
    priority = db.Column(db.String(50), default='MEDIUM')  # Uses PRIORITY_CHOICES
    assigned_to = db.Column(db.String(50), default='UNASSIGNED')  # Uses ASSIGNED_TO_CHOICES
    source = db.Column(db.String(50), default='UNKNOWN')  # Uses SOURCE_CHOICES
    reason_closed = db.Column(db.Text)
    date_closed = db.Column(db.Date)

    # Ensure explicit relationships
    church = db.relationship("Church", foreign_keys=[church_id], backref="church_members")
    tasks = db.relationship("Task", backref=db.backref("task_person", lazy="joined"), primaryjoin="Task.person_id==Person.id")
    communications = db.relationship("Communication", backref=db.backref("comm_person", lazy="joined"), primaryjoin="Communication.person_id==Person.id")

    @hybrid_property
    def person_first_name(self):
        return self.first_name
        
    @person_first_name.setter
    def person_first_name(self, value):
        self.first_name = value
        
    @hybrid_property
    def person_last_name(self):
        return self.last_name
        
    @person_last_name.setter
    def person_last_name(self, value):
        self.last_name = value
        
    @hybrid_property
    def name(self):
        """Combines first_name and last_name with a space in between."""
        return f"{self.first_name} {self.last_name}".strip() or "Unnamed Person"
        
    @hybrid_property
    def full_name(self):
        """Alias for name property"""
        return self.name
    
    @hybrid_property
    def initials(self):
        """Get the initials (first letter of first name and first letter of last name)"""
        initials = ""
        if self.first_name:
            initials += self.first_name[0].upper()
        if self.last_name:
            initials += self.last_name[0].upper()
        return initials if initials else "?"

    def __repr__(self):
        return f"<Person(name='{self.first_name} {self.last_name}', email='{self.email}')>"

    def get_name(self):
        """Get display name for the person."""
        return f"{self.first_name} {self.last_name}".strip() or "Unnamed Person"

    def to_dict(self):
        """Convert person to dictionary."""
        return {
            **super().to_dict(),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'spouse_first_name': self.spouse_first_name,
            'spouse_last_name': self.spouse_last_name,
            'church_id': self.church_id,
            'church_role': self.church_role,  # Updated field name in dictionary
            'is_primary_contact': self.is_primary_contact,
            'virtuous': self.virtuous,
            'title': self.title,
            'marital_status': self.marital_status,
            'referred_by': self.referred_by,
            'info_given': self.info_given,
            'desired_service': self.desired_service,
            'last_contact': self.last_contact.isoformat() if self.last_contact else None,
            'next_contact': self.next_contact.isoformat() if self.next_contact else None,
            'status': self.status,
            'google_contact_id': self.google_contact_id,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'people_pipeline': self.people_pipeline,
            'pipeline_status': self.pipeline_status,
            'pipeline_stage': self.pipeline_stage,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'source': self.source,
            'reason_closed': self.reason_closed,
            'date_closed': self.date_closed.isoformat() if self.date_closed else None
        } 