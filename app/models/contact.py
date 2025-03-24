from datetime import datetime
from app.models.base import Contact
from app.extensions import db
from sqlalchemy.ext.hybrid import hybrid_property

class ContactModel(Contact):
    """Model for contacts (churches and people)."""
    
    # Add any fields specific to ContactModel here
    
    __mapper_args__ = {
        'polymorphic_identity': 'contact_model'
    }

    @hybrid_property
    def contact_model_first_name(self):
        return self.first_name
        
    @contact_model_first_name.setter
    def contact_model_first_name(self, value):
        self.first_name = value
        
    @hybrid_property
    def contact_model_last_name(self):
        return self.last_name
        
    @contact_model_last_name.setter
    def contact_model_last_name(self, value):
        self.last_name = value

    def __repr__(self):
        return f"<Contact {self.get_name()}>"

    def get_name(self):
        """Get display name for the contact, handling both church and person cases"""
        if self.type == 'church':
            return self.church_name or f"{self.first_name} {self.last_name} (Church Contact)" or "Unnamed Church"
        else:
            return super().get_name()
    
    def __str__(self):
        return self.get_name()
    
    def to_dict(self):
        """Convert contact to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
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
            'office_id': self.office_id
        })
        return base_dict 