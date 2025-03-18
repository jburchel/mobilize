from datetime import datetime
from app.extensions import db
from app.models.base import Contact, MARITAL_STATUS_CHOICES, PEOPLE_PIPELINE_CHOICES, PRIORITY_CHOICES, ASSIGNED_TO_CHOICES, SOURCE_CHOICES

class Person(Contact):
    """Model for representing a person in the system."""
    __tablename__ = 'people'
    __mapper_args__ = {
        'polymorphic_identity': 'person'
    }

    id = db.Column(db.Integer, db.ForeignKey('contacts.id'), primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    spouse_first_name = db.Column(db.String(100))
    spouse_last_name = db.Column(db.String(100))
    church_role = db.Column(db.String(100))
    church_id = db.Column(db.Integer, db.ForeignKey('churches.id'))
    virtuous = db.Column(db.Boolean, default=False)
    title = db.Column(db.String(100))
    home_country = db.Column(db.String(100))
    marital_status = db.Column(db.String(100))
    people_pipeline = db.Column(db.String(100))
    priority = db.Column(db.String(100))
    assigned_to = db.Column(db.String(100))
    source = db.Column(db.String(100))
    referred_by = db.Column(db.String(100))
    info_given = db.Column(db.Text)
    desired_service = db.Column(db.Text)
    reason_closed = db.Column(db.Text)
    date_closed = db.Column(db.Date)
    
    # Relationships
    tasks = db.relationship("Task", back_populates="person")
    communications = db.relationship("Communication", back_populates="person")
    
    def __repr__(self):
        return f"<Person {self.first_name} {self.last_name}>"

    def full_name(self):
        """Return the person's full name."""
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        """Convert the person to a dictionary."""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'spouse_first_name': self.spouse_first_name,
            'spouse_last_name': self.spouse_last_name,
            'church_role': self.church_role,
            'church_id': self.church_id,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'notes': self.notes,
            'office_id': self.office_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 