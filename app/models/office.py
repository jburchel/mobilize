from datetime import datetime
from app import db
from app.models.base import BaseModel

# Association table for User-Office many-to-many relationship
user_offices = db.Table('user_offices',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('office_id', db.Integer, db.ForeignKey('offices.id'), primary_key=True),
    db.Column('role', db.String(20), nullable=False),
    db.Column('assigned_at', db.DateTime, nullable=False, default=db.func.current_timestamp())
)

class Office(BaseModel):
    """Office model for storing office information."""
    __tablename__ = 'offices'
    
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    office_hours = db.Column(db.String(200), nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Office {self.name}>'
    
    def to_dict(self):
        """Convert office to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'country': self.country,
            'office_hours': self.office_hours,
            'capacity': self.capacity,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 