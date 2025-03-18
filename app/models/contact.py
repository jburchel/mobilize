from datetime import datetime
from app.models.base import Contact

class ContactModel(Contact):
    """Contact model for storing contact information."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'contact_model'
    }
    
    def to_dict(self):
        """Convert contact to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'address': self.address_street,
            'city': self.address_city,
            'state': self.address_state,
            'zip_code': self.address_zip,
            'country': self.address_country,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 