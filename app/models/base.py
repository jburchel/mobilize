from datetime import datetime, UTC
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.constants import (
    STATE_CHOICES, PREFERRED_CONTACT_METHODS, ROLE_CHOICES,
    CHURCH_PIPELINE_CHOICES, PRIORITY_CHOICES, ASSIGNED_TO_CHOICES,
    SOURCE_CHOICES, MARITAL_STATUS_CHOICES, PEOPLE_PIPELINE_CHOICES
)

class TimestampMixin:
    """Mixin for adding timestamp fields to models."""
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class Base(db.Model):
    """Base model class that includes common fields."""
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def save(self):
        """Save the model instance to the database."""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Delete the model instance from the database."""
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs):
        """Update model instance with the provided keyword arguments."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    first_name = db.Column(db.String(50), name='first_name')
    last_name = db.Column(db.String(50), name='last_name')
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    country = db.Column(db.String(100))
    notes = db.Column(db.Text)
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    image = db.Column(db.String, nullable=True)
    preferred_contact_method = db.Column(db.String(100), nullable=True)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    date_modified = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    google_contact_id = db.Column(db.String(255), nullable=True)
    has_conflict = db.Column(db.Boolean, default=False)
    conflict_data = db.Column(db.JSON, nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    office = db.relationship("Office", back_populates="contacts")
    user = db.relationship("User", back_populates="contacts")
    
    __mapper_args__ = {
        'polymorphic_identity': 'contact',
        'polymorphic_on': type
    }
    
    @property
    def contact_type(self):
        """Return contact type (person or church) based on the 'type' column"""
        if hasattr(self, 'type') and self.type:
            if self.type.lower() in ('church', 'churches'):
                return 'church'
            else:
                return 'person'
        return 'person'  # Default to person if type is unknown
    
    @hybrid_property
    def contact_first_name(self):
        return self.first_name
        
    @contact_first_name.setter
    def contact_first_name(self, value):
        self.first_name = value
        
    @hybrid_property
    def contact_last_name(self):
        return self.last_name
        
    @contact_last_name.setter
    def contact_last_name(self, value):
        self.last_name = value

    def __repr__(self):
        return f"<Contact {self.get_name()}>"

    def get_name(self):
        """Get display name for the contact"""
        return f"{self.first_name} {self.last_name}".strip() or "Unnamed Contact"
    
    def __str__(self):
        return self.get_name()
    
    def to_dict(self):
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