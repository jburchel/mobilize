from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db
from app.models.constants import (
    STATE_CHOICES, PREFERRED_CONTACT_METHODS, ROLE_CHOICES,
    CHURCH_PIPELINE_CHOICES, PRIORITY_CHOICES, ASSIGNED_TO_CHOICES,
    SOURCE_CHOICES, MARITAL_STATUS_CHOICES, PEOPLE_PIPELINE_CHOICES
)

class TimestampMixin:
    """Mixin for adding timestamp fields to models."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

class Base(db.Model):
    """Base model class that includes common fields."""
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def save(self) -> None:
        """Save the model instance to the database."""
        db.session.add(self)
        db.session.commit()

    def delete(self) -> None:
        """Delete the model instance from the database."""
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs) -> None:
        """Update model instance with the provided keyword arguments."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()

class Contact(db.Model):
    """Base contact model for both Person and Church contacts."""
    __tablename__ = 'contacts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50))
    first_name: Mapped[Optional[str]] = mapped_column(String(50))
    last_name: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(200))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(2))
    zip_code: Mapped[Optional[str]] = mapped_column(String(10))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    office_id: Mapped[int] = mapped_column(ForeignKey('offices.id'), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
    image: Mapped[Optional[str]] = mapped_column(String)
    preferred_contact_method: Mapped[Optional[str]] = mapped_column(String(100))
    date_created: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    date_modified: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    google_contact_id: Mapped[Optional[str]] = mapped_column(String(255))
    has_conflict: Mapped[bool] = mapped_column(Boolean, default=False)
    conflict_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships with type hints
    office = relationship("Office", back_populates="contacts")
    user = relationship("User", back_populates="contacts")
    
    __mapper_args__ = {
        'polymorphic_identity': 'contact',
        'polymorphic_on': type
    }
    
    @property
    def contact_type(self) -> str:
        """Return contact type (person or church) based on the 'type' column"""
        if hasattr(self, 'type') and self.type:
            if self.type.lower() in ('church', 'churches'):
                return 'church'
            else:
                return 'person'
        return 'person'  # Default to person if type is unknown
    
    @hybrid_property
    def contact_first_name(self) -> Optional[str]:
        return self.first_name
        
    @contact_first_name.setter
    def contact_first_name(self, value: Optional[str]) -> None:
        self.first_name = value
        
    @hybrid_property
    def contact_last_name(self) -> Optional[str]:
        return self.last_name
        
    @contact_last_name.setter
    def contact_last_name(self, value: Optional[str]) -> None:
        self.last_name = value

    def __repr__(self) -> str:
        return f"<Contact {self.get_name()}>"

    def get_name(self) -> str:
        """Get display name for the contact"""
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or "Unnamed Contact"
    
    def __str__(self) -> str:
        return self.get_name()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contact to dictionary."""
        return {
            'id': self.id,
            'type': self.type,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'country': self.country,
            'notes': self.notes,
            'office_id': self.office_id,
            'user_id': self.user_id,
            'image': self.image,
            'preferred_contact_method': self.preferred_contact_method,
            'date_created': self.date_created.isoformat() if self.date_created else None,
            'date_modified': self.date_modified.isoformat() if self.date_modified else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 