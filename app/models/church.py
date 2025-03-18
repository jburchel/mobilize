from app.extensions import db
from app.models.base import Contact

class Church(Contact):
    """Model for representing a church in the system."""
    __tablename__ = 'churches'
    __mapper_args__ = {
        'polymorphic_identity': 'church'
    }

    id = db.Column(db.Integer, db.ForeignKey('contacts.id'), primary_key=True)
    location = db.Column(db.String(200))
    main_contact_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    senior_pastor_name = db.Column(db.String(100))
    associate_pastor_name = db.Column(db.String(100))
    denomination = db.Column(db.String(100))
    weekly_attendance = db.Column(db.Integer)
    website = db.Column(db.String(200))

    def __repr__(self):
        return f"<Church {self.name}>"

    def to_dict(self):
        """Convert the church to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'main_contact_id': self.main_contact_id,
            'senior_pastor_name': self.senior_pastor_name,
            'associate_pastor_name': self.associate_pastor_name,
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 