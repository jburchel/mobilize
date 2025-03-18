from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr

# Constants for choices
CHURCH_PIPELINE_CHOICES = [
    ('PROMOTION', 'PROMOTION'), ('INFORMATION', 'INFORMATION'), ('INVITATION', 'INVITATION'),
    ('CONFIRMATION', 'CONFIRMATION'), ('EN42', 'EN42'), ('AUTOMATION', 'AUTOMATION')
]

PRIORITY_CHOICES = [
    ('URGENT', 'URGENT'), ('HIGH', 'HIGH'), ('MEDIUM', 'MEDIUM'), ('LOW', 'LOW')
]

ASSIGNED_TO_CHOICES = [
    ('BILL JONES', 'BILL JONES'), ('JASON MODOMO', 'JASON MODOMO'), ('KEN KATAYAMA', 'KEN KATAYAMA'),
    ('MATTHEW RULE', 'MATTHEW RULE'), ('CHIP ATKINSON', 'CHIP ATKINSON'), ('RACHEL LIVELY', 'RACHEL LIVELY'),
    ('JIM BURCHEL', 'JIM BURCHEL'), ('JILL WALKER', 'JILL WALKER'), ('KARINA RAMPIN', 'KARINA RAMPIN'),
    ('UNASSIGNED', 'UNASSIGNED')
]

SOURCE_CHOICES = [
    ('WEBFORM', 'WEBFORM'), ('INCOMING CALL', 'INCOMING CALL'), ('EMAIL', 'EMAIL'),
    ('SOCIAL MEDIA', 'SOCIAL MEDIA'), ('COLD CALL', 'COLD CALL'), ('PERSPECTIVES', 'PERSPECTIVES'),
    ('REFERAL', 'REFERAL'), ('OTHER', 'OTHER'), ('UNKNOWN', 'UNKNOWN')
]

MARITAL_STATUS_CHOICES = [
    ('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'),
    ('widowed', 'Widowed'), ('separated', 'Separated'), ('unknown', 'Unknown'),
    ('engaged', 'Engaged')
]

PEOPLE_PIPELINE_CHOICES = [
    ('PROMOTION', 'PROMOTION'), ('INFORMATION', 'INFORMATION'), ('INVITATION', 'INVITATION'),
    ('CONFIRMATION', 'CONFIRMATION'), ('AUTOMATION', 'AUTOMATION')
]

STATE_CHOICES = [
    ('al', 'AL'), ('ak', 'AK'), ('az', 'AZ'), ('ar', 'AR'), ('ca', 'CA'),('co', 'CO'),('ct', 'CT'),('de', 'DE'), 
    ('fl', 'FL'), ('ga', 'GA'), ('hi', 'HI'), ('id', 'ID'), ('il', 'IL'), ('in', 'IN'), ('ia', 'IA'), ('ks', 'KS'), 
    ('ky', 'KY'), ('la', 'LA'), ('me', 'ME'), ('md', 'MD'), ('ma', 'MA'), ('mi', 'MI'), ('mn', 'MN'), ('ms', 'MS'), 
    ('mo', 'MO'), ('mt', 'MT'), ('ne', 'NE'), ('nv', 'NV'), ('nh', 'NH'), ('nj', 'NJ'), ('nm', 'NM'), ('ny', 'NY'), 
    ('nc', 'NC'), ('nd', 'ND'), ('oh', 'OH'), ('ok', 'OK'), ('or', 'OR'), ('pa', 'PA'), ('ri', 'RI'), ('sc', 'SC'), 
    ('sd', 'SD'), ('tn', 'TN'), ('tx', 'TX'), ('ut', 'UT'), ('vt', 'VT'), ('va', 'VA'), ('wa', 'WA'), ('wv', 'WV'), 
    ('wi', 'WI'), ('wy', 'WY'), ('dc', 'DC')
]

PREFERRED_CONTACT_METHODS = [
    ('email', 'Email'), ('phone', 'Phone'), ('text', 'Text'), ('facebook_messenger', 'Facebook Messenger'),
    ('whatsapp', 'Whatsapp'), ('groupme', 'Groupme'), ('signal', 'Signal'), ('other', 'Other')
]

ROLE_CHOICES = [
    ('super_admin', 'Super Admin'),
    ('office_admin', 'Office Admin'),
    ('standard_user', 'Standard User'),
    ('limited_user', 'Limited User')
]

class TimestampMixin:
    """Mixin for adding timestamp fields to models."""
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class BaseModel(db.Model):
    """Base model class that includes common attributes and methods."""
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

class Contact(BaseModel):
    """Base model for entities that can be contacted (Person, Church, etc.)."""
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))  # Discriminator column
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    notes = db.Column(db.Text)

    # Office relationship
    @declared_attr
    def office_id(cls):
        return db.Column(db.Integer, db.ForeignKey('offices.id'))

    @declared_attr
    def office(cls):
        return db.relationship("Office", back_populates="contacts")

    __mapper_args__ = {
        'polymorphic_identity': 'contact',
        'polymorphic_on': type
    }

    def get_name(self):
        """Get display name for the contact, handling both church and person cases"""
        if self.type == 'church':
            return self.church_name or f"{self.first_name} {self.last_name} (Church Contact)" or "Unnamed Church"
        else:
            return f"{self.first_name} {self.last_name}".strip() or "Unnamed Contact"
    
    def __str__(self):
        return self.get_name() 