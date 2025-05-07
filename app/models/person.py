from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Boolean, Date, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db
from app.models.base import Contact
from app.models.constants import (
    MARITAL_STATUS_CHOICES, PEOPLE_PIPELINE_CHOICES, PRIORITY_CHOICES, 
    ASSIGNED_TO_CHOICES, SOURCE_CHOICES
)

from app.models.pipeline import PipelineContact, Pipeline, PipelineStage
class Person(Contact):
    """Person model for tracking individual contacts."""
    __tablename__ = 'people'
    __mapper_args__ = {
        'polymorphic_identity': 'person'
    }

    id: Mapped[int] = mapped_column(ForeignKey('contacts.id'), primary_key=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    
    # Fields from old model
    spouse_first_name: Mapped[Optional[str]] = mapped_column(String(100))
    spouse_last_name: Mapped[Optional[str]] = mapped_column(String(100))
    church_id: Mapped[Optional[int]] = mapped_column(ForeignKey('churches.id'))
    church_role: Mapped[Optional[str]] = mapped_column(String(100))
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Additional fields from old model
    virtuous: Mapped[bool] = mapped_column(Boolean, default=False)
    title: Mapped[Optional[str]] = mapped_column(String(50))
    marital_status: Mapped[Optional[str]] = mapped_column(String(50))
    birthday: Mapped[Optional[datetime]] = mapped_column(Date)
    anniversary: Mapped[Optional[datetime]] = mapped_column(Date)
    occupation: Mapped[Optional[str]] = mapped_column(String(100))
    employer: Mapped[Optional[str]] = mapped_column(String(100))
    interests: Mapped[Optional[str]] = mapped_column(Text)
    skills: Mapped[Optional[str]] = mapped_column(Text)
    languages: Mapped[Optional[str]] = mapped_column(Text)
    facebook: Mapped[Optional[str]] = mapped_column(String(100))
    twitter: Mapped[Optional[str]] = mapped_column(String(100))
    linkedin: Mapped[Optional[str]] = mapped_column(String(100))
    instagram: Mapped[Optional[str]] = mapped_column(String(100))
    website: Mapped[Optional[str]] = mapped_column(String(200))
    referred_by: Mapped[Optional[str]] = mapped_column(String(100))
    info_given: Mapped[Optional[str]] = mapped_column(Text)
    desired_service: Mapped[Optional[str]] = mapped_column(Text)
    
    # Tracking fields from new model
    last_contact: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    next_contact: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(50), default='active')
    google_contact_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Pipeline fields - combining old and new approaches
    people_pipeline: Mapped[str] = mapped_column(String(100), default='INFORMATION')
    pipeline_status: Mapped[Optional[str]] = mapped_column(String(50))
    pipeline_stage: Mapped[Optional[str]] = mapped_column(String(50))
    priority: Mapped[str] = mapped_column(String(50), default='MEDIUM')
    assigned_to: Mapped[str] = mapped_column(String(50), default='UNASSIGNED')
    source: Mapped[str] = mapped_column(String(50), default='UNKNOWN')
    reason_closed: Mapped[Optional[str]] = mapped_column(String(255))
    date_closed: Mapped[Optional[datetime]] = mapped_column(DateTime)
    tags: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships with type hints
    church = relationship(
        "Church",
        foreign_keys=[church_id],
        back_populates="church_members"
    )
    communications = relationship(
        "Communication",
        back_populates="person",
        primaryjoin="Communication.person_id==Person.id"
    )
    associated_user = relationship(
        "User",
        back_populates="person",
        uselist=False,
        foreign_keys="User.person_id"
    )
    primary_for_churches = relationship(
        "Church",
        back_populates="main_contact",
        foreign_keys="Church.main_contact_id"
    )
    tasks = relationship(
        "Task",
        back_populates="person",
        cascade="all, delete-orphan"
    )

    @hybrid_property
    def person_first_name(self) -> Optional[str]:
        return self.first_name
        
    @person_first_name.setter
    def person_first_name(self, value: Optional[str]) -> None:
        self.first_name = value
        
    @hybrid_property
    def person_last_name(self) -> Optional[str]:
        return self.last_name
        
    @person_last_name.setter
    def person_last_name(self, value: Optional[str]) -> None:
        self.last_name = value
        
    @hybrid_property
    def name(self) -> str:
        """Combines first_name and last_name with a space in between."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or "Unnamed Person"
        
    @hybrid_property
    def full_name(self) -> str:
        """Alias for name property"""
        return self.name
    
    @hybrid_property
    def initials(self) -> str:
        """Get the initials (first letter of first name and first letter of last name)"""
        initials = ""
        if self.first_name:
            initials += self.first_name[0].upper()
        if self.last_name:
            initials += self.last_name[0].upper()
        return initials if initials else "?"

    
    @property
    def pipeline_id(self):
        """Virtual property to handle queries that expect a pipeline_id column."""
        # Get the pipeline entry for this contact
        pipeline_contact = db.session.query(PipelineContact).filter_by(
            contact_id=self.id
        ).first()
        return pipeline_contact.pipeline_id if pipeline_contact else None
                
    @property
    def pipeline_stage_id(self):
        """Virtual property to handle queries that expect a pipeline_stage_id column."""
        # Get the pipeline entry for this contact
        pipeline_contact = db.session.query(PipelineContact).filter_by(
            contact_id=self.id
        ).first()
        return pipeline_contact.current_stage_id if pipeline_contact else None

    @property
    def main_pipeline_stage(self):
        main_pipeline = Pipeline.query.filter_by(pipeline_type="people", is_main_pipeline=True).first()
        if not main_pipeline:
            return None
        pipeline_contact = PipelineContact.query.filter_by(
            contact_id=self.id,
            pipeline_id=main_pipeline.id
        ).first()
        if pipeline_contact and pipeline_contact.current_stage_id:
            stage = PipelineStage.query.get(pipeline_contact.current_stage_id)
            return stage.name if stage else None
        return None

    def __repr__(self) -> str:
        return f"<Person(name='{self.first_name} {self.last_name}', email='{self.email}')>"

    def get_name(self) -> str:
        """Get display name for the person.
        
        Checks both the person fields and the contact fields to ensure we display a name
        even if data is stored inconsistently between tables.
        """
        # First try the person's own fields
        person_first = self.first_name
        person_last = self.last_name
        
        # If either is missing, try to get from the contact fields
        # This is necessary because the data might be stored in either table due to inheritance
        contact_first = super().first_name if hasattr(super(), 'first_name') else None
        contact_last = super().last_name if hasattr(super(), 'last_name') else None
        
        # Use the first non-null value from either table
        first_name = person_first or contact_first or ''
        last_name = person_last or contact_last or ''
        
        return f"{first_name} {last_name}".strip() or "Unnamed Person"

    def to_dict(self) -> Dict[str, Any]:
        """Convert person to dictionary."""
        return {
            **super().to_dict(),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'spouse_first_name': self.spouse_first_name,
            'spouse_last_name': self.spouse_last_name,
            'church_id': self.church_id,
            'church_role': self.church_role,
            'is_primary_contact': self.is_primary_contact,
            'virtuous': self.virtuous,
            'title': self.title,
            'marital_status': self.marital_status,
            'birthday': self.birthday.isoformat() if self.birthday else None,
            'anniversary': self.anniversary.isoformat() if self.anniversary else None,
            'occupation': self.occupation,
            'employer': self.employer,
            'interests': self.interests,
            'skills': self.skills,
            'languages': self.languages,
            'facebook': self.facebook,
            'twitter': self.twitter,
            'linkedin': self.linkedin,
            'instagram': self.instagram,
            'website': self.website,
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
            'date_closed': self.date_closed.isoformat() if self.date_closed else None,
            'tags': self.tags
        } 