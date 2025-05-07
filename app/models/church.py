from datetime import date
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Boolean, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db
from app.models.base import Contact
from app.models.constants import (
    CHURCH_PIPELINE_CHOICES, PRIORITY_CHOICES, ASSIGNED_TO_CHOICES, SOURCE_CHOICES
)
from app.models.pipeline import Pipeline, PipelineContact, PipelineStage
from app.models.person import Person

from app.models.pipeline import PipelineContact
class Church(Contact):
    """Model for representing a church in the system."""
    __tablename__ = 'churches'
    
    id: Mapped[int] = mapped_column(ForeignKey('contacts.id'), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(200))
    location: Mapped[Optional[str]] = mapped_column(String(200))
    main_contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey('people.id'))
    senior_pastor_name: Mapped[Optional[str]] = mapped_column(String(100))
    denomination: Mapped[Optional[str]] = mapped_column(String(100))
    weekly_attendance: Mapped[Optional[int]] = mapped_column(Integer)
    website: Mapped[Optional[str]] = mapped_column(String(200))
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    
    # Fields migrated from old model
    virtuous: Mapped[bool] = mapped_column(Boolean, default=False)
    senior_pastor_phone: Mapped[Optional[str]] = mapped_column(String(50))
    senior_pastor_email: Mapped[Optional[str]] = mapped_column(String)
    missions_pastor_first_name: Mapped[Optional[str]] = mapped_column(String(100))
    missions_pastor_last_name: Mapped[Optional[str]] = mapped_column(String(100))
    mission_pastor_phone: Mapped[Optional[str]] = mapped_column(String(50))
    mission_pastor_email: Mapped[Optional[str]] = mapped_column(String)
    priority: Mapped[str] = mapped_column(String(100), default='MEDIUM')
    assigned_to: Mapped[str] = mapped_column(String(100), default='UNASSIGNED')
    source: Mapped[str] = mapped_column(String(100), default='UNKNOWN')
    referred_by: Mapped[Optional[str]] = mapped_column(String(100))
    info_given: Mapped[Optional[str]] = mapped_column(Text)
    reason_closed: Mapped[Optional[str]] = mapped_column(Text)
    year_founded: Mapped[Optional[int]] = mapped_column(Integer)
    date_closed: Mapped[Optional[date]] = mapped_column(Date)
    
    __mapper_args__ = {
        'polymorphic_identity': 'church',
        'inherit_condition': Contact.id == id
    }
    
    # Relationships with type hints
    owner = relationship(
        'User',
        back_populates='owned_churches',
        foreign_keys=[owner_id],
        primaryjoin='User.id==Church.owner_id'
    )
    
    main_contact = relationship(
        'Person',
        foreign_keys=[main_contact_id],
        back_populates='primary_for_churches',
        primaryjoin='Church.main_contact_id==Person.id'
    )

    church_members = relationship(
        'Person',
        back_populates='church',
        foreign_keys='Person.church_id',
        lazy='dynamic'
    )

    tasks = relationship(
        'Task',
        back_populates='church',
        cascade='all, delete-orphan'
    )
    
    @hybrid_property
    def church_first_name(self) -> Optional[str]:
        return self.name
        
    @church_first_name.setter
    def church_first_name(self, value: Optional[str]) -> None:
        self.name = value
        
    @hybrid_property
    def church_last_name(self) -> None:
        return None
        
    @church_last_name.setter
    def church_last_name(self, value: Optional[str]) -> None:
        pass  # Churches don't use last_name
    
    
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
        from app.models.pipeline import Pipeline, PipelineContact, PipelineStage
        main_pipeline = Pipeline.query.filter_by(pipeline_type="church", is_main_pipeline=True).first()
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
        return f"<Church {self.name}>"

    def get_name(self) -> str:
        """Get display name for the church
        
        Checks both the church fields and the contact fields to ensure we display a name
        even if data is stored inconsistently between tables.
        """
        # First try the church's own name field
        church_name = self.name
        
        # If missing, try to get from the contact fields
        # This is necessary because the data might be stored in either table due to inheritance
        contact_name = super().first_name if hasattr(super(), 'first_name') else None
        
        # Use the first non-null value from either table
        name = church_name or contact_name or ''
        
        return name or "Unnamed Church"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the church to a dictionary."""
        # Get the main pipeline stage
        main_pipeline = Pipeline.query.filter_by(
            pipeline_type='church',
            is_main_pipeline=True,
            office_id=self.office_id
        ).first()
        
        pipeline_stage = None
        if main_pipeline:
            pipeline_contact = PipelineContact.query.filter_by(
                contact_id=self.id,
                pipeline_id=main_pipeline.id
            ).first()
            if pipeline_contact and pipeline_contact.current_stage:
                pipeline_stage = pipeline_contact.current_stage.name
        
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'senior_pastor_name': self.senior_pastor_name,
            'denomination': self.denomination,
            'weekly_attendance': self.weekly_attendance,
            'website': self.website,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'notes': self.notes,
            'office_id': self.office_id,
            'owner_id': self.owner_id,
            'virtuous': self.virtuous,
            'senior_pastor_phone': self.senior_pastor_phone,
            'senior_pastor_email': self.senior_pastor_email,
            'missions_pastor_first_name': self.missions_pastor_first_name,
            'missions_pastor_last_name': self.missions_pastor_last_name,
            'mission_pastor_phone': self.mission_pastor_phone,
            'mission_pastor_email': self.mission_pastor_email,
            'pipeline_stage': pipeline_stage,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'source': self.source,
            'referred_by': self.referred_by,
            'info_given': self.info_given,
            'reason_closed': self.reason_closed,
            'year_founded': self.year_founded,
            'date_closed': self.date_closed.isoformat() if self.date_closed else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
    def debug_members(self) -> List['Person']:
        """Debug method to check church members"""
        direct_query = Person.query.filter_by(church_id=self.id).all()
        print(f"Debug - Church ID: {self.id}, Name: {self.name}")
        print(f"Debug - Direct query found {len(direct_query)} members")
        for p in direct_query:
            print(f"Debug - Member: {p.name}, Role: {p.church_role}, Email: {p.email}")
        
        backref_query = list(self.church_members)
        print(f"Debug - Backref query found {len(backref_query)} members")
        for p in backref_query:
            print(f"Debug - Backref Member: {p.name}, Role: {p.church_role}, Email: {p.email}")
        
        return direct_query 