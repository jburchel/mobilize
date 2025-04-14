from app.extensions import db
from app.models.base import Contact
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import orm
from datetime import date
from app.models.constants import (
    CHURCH_PIPELINE_CHOICES, PRIORITY_CHOICES, ASSIGNED_TO_CHOICES, SOURCE_CHOICES
)

class Church(Contact):
    """Model for representing a church in the system."""
    __tablename__ = 'churches'
    
    id = db.Column(db.Integer, db.ForeignKey('contacts.id'), primary_key=True)
    name = db.Column(db.String(200))
    location = db.Column(db.String(200))
    main_contact_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=True)
    senior_pastor_name = db.Column(db.String(100))
    denomination = db.Column(db.String(100))
    weekly_attendance = db.Column(db.Integer)
    website = db.Column(db.String(200))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Fields migrated from old model
    virtuous = db.Column(db.Boolean, default=False)
    senior_pastor_phone = db.Column(db.String(50))
    senior_pastor_email = db.Column(db.String())
    missions_pastor_first_name = db.Column(db.String(100))
    missions_pastor_last_name = db.Column(db.String(100))
    mission_pastor_phone = db.Column(db.String(50))
    mission_pastor_email = db.Column(db.String())
    church_pipeline = db.Column(db.String(100), default='INFORMATION')  # Uses CHURCH_PIPELINE_CHOICES
    priority = db.Column(db.String(100), default='MEDIUM')  # Uses PRIORITY_CHOICES
    assigned_to = db.Column(db.String(100), default='UNASSIGNED')  # Uses ASSIGNED_TO_CHOICES
    source = db.Column(db.String(100), default='UNKNOWN')  # Uses SOURCE_CHOICES
    referred_by = db.Column(db.String(100))
    info_given = db.Column(db.Text)
    reason_closed = db.Column(db.Text)
    year_founded = db.Column(db.Integer)
    date_closed = db.Column(db.Date)
    
    __mapper_args__ = {
        'polymorphic_identity': 'church',
        'inherit_condition': Contact.id == id
    }
    
    # Relationships
    owner = orm.relationship(
        'User',
        back_populates='owned_churches',
        foreign_keys=[owner_id],
        primaryjoin='User.id==Church.owner_id'
    )
    
    main_contact = db.relationship(
        'Person',
        foreign_keys=[main_contact_id],
        backref=db.backref('primary_for_churches', lazy='dynamic'),
        primaryjoin='Church.main_contact_id==Person.id'
    )
    
    @hybrid_property
    def church_first_name(self):
        return self.name
        
    @church_first_name.setter
    def church_first_name(self, value):
        self.name = value
        
    @hybrid_property
    def church_last_name(self):
        return None
        
    @church_last_name.setter
    def church_last_name(self, value):
        pass  # Churches don't use last_name
    
    def __repr__(self):
        return f"<Church {self.name}>"

    def get_name(self):
        """Get display name for the church"""
        return self.name or "Unnamed Church"

    def to_dict(self):
        """Convert the church to a dictionary."""
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
            'church_pipeline': self.church_pipeline,
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
        
    def debug_members(self):
        """Debug method to check church members"""
        from app.models.person import Person
        direct_query = Person.query.filter_by(church_id=self.id).all()
        print(f"Debug - Church ID: {self.id}, Name: {self.name}")
        print(f"Debug - Direct query found {len(direct_query)} members")
        for p in direct_query:
            print(f"Debug - Member: {p.name}, Role: {p.church_role}, Email: {p.email}")
        
        backref_query = self.church_members if hasattr(self, 'church_members') else []
        print(f"Debug - Backref query found {len(backref_query)} members")
        for p in backref_query:
            print(f"Debug - Backref Member: {p.name}, Role: {p.church_role}, Email: {p.email}")
        
        return direct_query 