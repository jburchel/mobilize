from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Boolean, Text, DateTime
from sqlalchemy.orm import relationship, declarative_base, scoped_session, sessionmaker
from contextlib import contextmanager
from marshmallow import Schema, fields, validate, ValidationError, pre_load, post_load
from datetime import datetime
import os
import logging

Base = declarative_base()

def get_image_path(instance, filename):
    return os.path.join('contact_images', str(instance.id), filename)

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

# New constants for role choices
ROLE_CHOICES = [
    ('super_admin', 'Super Admin'),
    ('office_admin', 'Office Admin'),
    ('standard_user', 'Standard User'),
    ('limited_user', 'Limited User')
]

# Base Schema for shared fields
class ContactsSchema(Schema):
    id = fields.Int(dump_only=True)
    church_name = fields.Str(allow_none=True)
    first_name = fields.Str(allow_none=True)
    last_name = fields.Str(allow_none=True)
    image = fields.Str(allow_none=True)
    preferred_contact_method = fields.Str(validate=validate.OneOf([x[0] for x in PREFERRED_CONTACT_METHODS]))
    phone = fields.Str()
    email = fields.Email()
    street_address = fields.Str(allow_none=True)
    city = fields.Str(allow_none=True)
    state = fields.Str(validate=validate.OneOf([x[0] for x in STATE_CHOICES]), allow_none=True)
    zip_code = fields.Str(allow_none=True)
    initial_notes = fields.Str(allow_none=True)
    date_created = fields.Date(dump_only=True)
    date_modified = fields.Date(dump_only=True)
    google_resource_name = fields.Str(allow_none=True)

class PersonSchema(ContactsSchema):
    id = fields.Int(dump_only=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    email = fields.Email(allow_none=True)
    phone = fields.Str(allow_none=True)
    address = fields.Str(allow_none=True)
    city = fields.Str(allow_none=True)
    state = fields.Str(allow_none=True)
    zip_code = fields.Str(allow_none=True)
    google_contact_id = fields.Str(allow_none=True)
    last_synced_at = fields.DateTime(allow_none=True)
    pipeline_id = fields.Int(allow_none=True)
    pipeline_stage_id = fields.Int(allow_none=True)
    church_id = fields.Int(allow_none=True)
    reason_closed = fields.Str(allow_none=True)
    date_closed = fields.Date(allow_none=True)
    user_id = fields.Str(allow_none=True)
    office_id = fields.Int(allow_none=True)
    virtuous = fields.Boolean()
    church_role = fields.Str(validate=validate.OneOf(['admin', 'user', 'guest', 'Contact']))
    affiliated_church = fields.Int(allow_none=True)
    spouse_first_name = fields.Str(allow_none=True)
    spouse_last_name = fields.Str(allow_none=True)
    title = fields.Str(allow_none=True)
    home_country = fields.Str(allow_none=True)
    marital_status = fields.Str(validate=validate.OneOf([x[0] for x in MARITAL_STATUS_CHOICES]), allow_none=True)
    children = fields.Str(allow_none=True)
    anniversary = fields.Date(allow_none=True)
    birthday = fields.Date(allow_none=True)
    referred_by = fields.Str(allow_none=True)
    info_given = fields.Str(allow_none=True)
    desired_service = fields.Str(allow_none=True)

class ChurchSchema(ContactsSchema):
    church_name = fields.Str(required=True)
    location = fields.Str(allow_none=True)
    main_contact_id = fields.Int(allow_none=True)
    virtuous = fields.Bool()
    senior_pastor_first_name = fields.Str(allow_none=True)
    senior_pastor_last_name = fields.Str(allow_none=True)
    senior_pastor_phone = fields.Str(allow_none=True)
    senior_pastor_email = fields.Email(allow_none=True)
    missions_pastor_first_name = fields.Str(allow_none=True)
    missions_pastor_last_name = fields.Str(allow_none=True)
    mission_pastor_phone = fields.Str(allow_none=True)
    mission_pastor_email = fields.Email(allow_none=True)
    primary_contact_first_name = fields.Str(allow_none=True)
    primary_contact_last_name = fields.Str(allow_none=True)
    primary_contact_phone = fields.Str(allow_none=True)
    primary_contact_email = fields.Email(allow_none=True)
    website = fields.URL(allow_none=True)
    denomination = fields.Str(allow_none=True)
    congregation_size = fields.Int(allow_none=True)
    church_pipeline = fields.Str(validate=validate.OneOf([x[0] for x in CHURCH_PIPELINE_CHOICES]))
    priority = fields.Str(validate=validate.OneOf([x[0] for x in PRIORITY_CHOICES]))
    assigned_to = fields.Str(validate=validate.OneOf([x[0] for x in ASSIGNED_TO_CHOICES]))
    source = fields.Str(validate=validate.OneOf([x[0] for x in SOURCE_CHOICES]))
    referred_by = fields.Str(allow_none=True)
    info_given = fields.Str(allow_none=True)
    reason_closed = fields.Str(allow_none=True)
    year_founded = fields.Int(allow_none=True)
    date_closed = fields.Date(allow_none=True)
    office_id = fields.Int(allow_none=True)
    office = fields.Nested('OfficeSchema', dump_only=True)

class TaskSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    due_date = fields.Date(allow_none=True)
    status = fields.Str(required=True, validate=validate.OneOf(['open', 'in_progress', 'completed', 'overdue']))
    person_id = fields.Int(allow_none=True)
    church_id = fields.Int(allow_none=True)
    user_id = fields.Str(allow_none=True)
    google_calendar_event_id = fields.Str(allow_none=True)
    google_calendar_sync_enabled = fields.Boolean()
    last_synced_at = fields.DateTime(allow_none=True)
    office_id = fields.Int(allow_none=True)

    @pre_load
    def process_dates(self, data, **kwargs):
        due_date = data.get('due_date')
        logger = logging.getLogger(__name__)
        
        # Handle None or empty string
        if not due_date:
            logger.info("No due date provided, setting to None")
            data['due_date'] = None
            return data
            
        if isinstance(due_date, str):
            try:
                # Try to parse date in MM/DD/YYYY format
                logger.info(f"Processing due_date: {due_date}")
                
                # Strip any whitespace
                due_date = due_date.strip()
                
                # If empty after stripping, set to None
                if not due_date:
                    data['due_date'] = None
                    return data
                
                # Parse the date to validate it
                parsed_date = datetime.strptime(due_date, '%m/%d/%Y').date()
                logger.info(f"Successfully parsed date: {parsed_date}")
                
                # Keep the string format for now
                data['due_date'] = due_date
            except ValueError as e:
                logger.error(f"Date parsing error: {e} for input '{due_date}'")
                raise ValidationError({'due_date': ['Please enter a valid date in MM/DD/YYYY format']})
        return data
        
    @post_load
    def format_dates(self, data, **kwargs):
        due_date = data.get('due_date')
        if due_date and isinstance(due_date, str):
            try:
                # Convert string date to Python date object for database storage
                data['due_date'] = datetime.strptime(due_date, '%m/%d/%Y').date()
            except ValueError:
                # This should never happen as we've already validated in pre_load
                pass
        return data

class CommunicationSchema(Schema):
    id = fields.Int(dump_only=True)
    comm_type = fields.Str(required=True, validate=validate.OneOf(['Email', 'SMS', 'Phone', 'Letter']))
    message = fields.Str(required=True)
    date_sent = fields.DateTime(required=True)
    person_id = fields.Int(allow_none=True)
    church_id = fields.Int(allow_none=True)
    user_id = fields.Str(allow_none=True)
    direction = fields.Str(required=True, validate=validate.OneOf(['inbound', 'outbound']))
    office_id = fields.Int(allow_none=True)

# New schemas for admin features
class PermissionSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class OfficeSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    address = fields.Str(allow_none=True)
    city = fields.Str(allow_none=True)
    state = fields.Str(validate=validate.OneOf([x[0] for x in STATE_CHOICES]), allow_none=True)
    zip_code = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True)
    email = fields.Email(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class UserOfficeSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Str(required=True)
    office_id = fields.Int(required=True)
    role = fields.Str(validate=validate.OneOf([x[0] for x in ROLE_CHOICES]), required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    office = fields.Nested(OfficeSchema, dump_only=True)

# Initialize schemas
person_schema = PersonSchema()
church_schema = ChurchSchema()
task_schema = TaskSchema()
communication_schema = CommunicationSchema()
permission_schema = PermissionSchema()
office_schema = OfficeSchema()
user_office_schema = UserOfficeSchema()

class Contacts(Base):
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    church_name = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    image = Column(String, nullable=True)
    preferred_contact_method = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String, nullable=True)
    street_address = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    zip_code = Column(String(10), nullable=True)
    initial_notes = Column(Text, nullable=True)
    date_created = Column(Date, nullable=True)
    date_modified = Column(Date, nullable=True)
    google_resource_name = Column(String, unique=True, nullable=True)
    
    type = Column(String(50))  # Discriminator column
    
    __mapper_args__ = {
        'polymorphic_identity': 'contact',
        'polymorphic_on': type
    }
    
    def get_name(self):
        """Get display name for the contact, handling both church and person cases"""
        if self.type == 'church':
            # For churches, use church_name if available
            return self.church_name or f"{self.first_name} {self.last_name} (Church Contact)" or "Unnamed Church"
        else:
            # For people
            return f"{self.first_name} {self.last_name}".strip() or "Unnamed Contact"
    
    def __str__(self):
        return self.get_name()

class Person(Contacts):
    __tablename__ = 'people'
    
    id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), primary_key=True)
    church_role = Column(String)
    church_id = Column(Integer, ForeignKey('churches.id'))
    spouse_first_name = Column(String(100))
    spouse_last_name = Column(String(100))
    virtuous = Column(Boolean)
    title = Column(String(100))
    home_country = Column(String(100))
    marital_status = Column(String(100))
    people_pipeline = Column(String(100))
    priority = Column(String(100))
    assigned_to = Column(String(100))
    source = Column(String(100))
    referred_by = Column(String(100))
    info_given = Column(Text)
    desired_service = Column(Text)
    reason_closed = Column(Text)
    date_closed = Column(Date)
    user_id = Column(String(128), nullable=True)
    office_id = Column(Integer, nullable=True)
    
    church = relationship("Church", back_populates="people", foreign_keys=[church_id])
    tasks = relationship("Task", back_populates="person")
    communications = relationship("Communication", back_populates="person")
    
    __mapper_args__ = {
        'polymorphic_identity': 'person',
    }
    
    def __repr__(self):
        return f"<Person(name='{self.first_name} {self.last_name}', email='{self.email}')>"

class Church(Contacts):
    __tablename__ = 'churches'
    
    id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), primary_key=True)
    location = Column(String)
    main_contact_id = Column(Integer, ForeignKey('people.id'))
    virtuous = Column(Boolean)
    senior_pastor_first_name = Column(String(100))
    senior_pastor_last_name = Column(String(100))
    senior_pastor_phone = Column(String(50))
    senior_pastor_email = Column(String)
    missions_pastor_first_name = Column(String(100))
    missions_pastor_last_name = Column(String(100))
    mission_pastor_phone = Column(String(50))
    mission_pastor_email = Column(String)
    primary_contact_first_name = Column(String(100))
    primary_contact_last_name = Column(String(100))
    primary_contact_phone = Column(String(50))
    primary_contact_email = Column(String)
    website = Column(String)
    denomination = Column(String(100))
    congregation_size = Column(Integer)
    church_pipeline = Column(String(100))
    priority = Column(String(100))
    assigned_to = Column(String(100))
    source = Column(String(100))
    referred_by = Column(String(100))
    info_given = Column(Text)
    reason_closed = Column(Text)
    year_founded = Column(Integer)
    date_closed = Column(Date)
    office_id = Column(Integer, ForeignKey('offices.id'), nullable=True)
    
    people = relationship("Person", back_populates="church", foreign_keys=[Person.church_id])
    tasks = relationship("Task", back_populates="church")
    communications = relationship("Communication", back_populates="church")
    main_contact = relationship("Person", foreign_keys=[main_contact_id], backref="churches_main_contact")
    office = relationship("Office", back_populates="churches")
    
    __mapper_args__ = {
        'polymorphic_identity': 'church',
    }
    
    def __repr__(self):
        return f"<Church(id={self.id}, name='{self.church_name}')>"

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    due_date = Column(Date)
    due_time = Column(String, nullable=True)  # Store time as HH:MM format
    reminder_time = Column(String, nullable=True)  # Store reminder time as HH:MM format
    priority = Column(String)
    status = Column(String)
    person_id = Column(Integer, ForeignKey('people.id'))
    church_id = Column(Integer, ForeignKey('churches.id'))
    user_id = Column(String(128), nullable=True)  # Add user_id column
    office_id = Column(Integer, nullable=True)
    # Google Calendar integration fields
    google_calendar_event_id = Column(String, unique=True, nullable=True)
    google_calendar_sync_enabled = Column(Boolean)
    last_synced_at = Column(DateTime, nullable=True)

    person = relationship("Person", back_populates="tasks")
    church = relationship("Church", back_populates="tasks")

    def __repr__(self):
        return f"<Task(title='{self.title}', due_date='{self.due_date}')>"

class Communication(Base):
    __tablename__ = 'communications'

    id = Column(Integer, primary_key=True)
    type = Column(String)
    message = Column(String)
    date_sent = Column(DateTime, default=datetime.now)
    date = Column(DateTime, nullable=False, default=datetime.now)  # Required by the database schema
    person_id = Column(Integer, ForeignKey('people.id'))
    church_id = Column(Integer, ForeignKey('churches.id'))
    user_id = Column(String(128), nullable=True)
    office_id = Column(Integer, nullable=True)
    direction = Column(String(50), nullable=False, default='outbound')  # 'inbound' or 'outbound'
    # Gmail integration fields
    gmail_message_id = Column(String, nullable=True)
    gmail_thread_id = Column(String, nullable=True)
    email_status = Column(String, nullable=True)  # 'sent', 'draft', 'failed', etc.
    subject = Column(String, nullable=True)  # Email subject
    attachments = Column(String, nullable=True)  # JSON string of attachment info
    last_synced_at = Column(DateTime, nullable=True)  # Timestamp for last sync

    person = relationship("Person", back_populates="communications")
    church = relationship("Church", back_populates="communications")

    def __repr__(self):
        return f"<Communication(type='{self.type}', date_sent='{self.date_sent}')>"

class EmailSignature(Base):
    __tablename__ = 'email_signatures'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)  # Firebase user ID
    name = Column(String, nullable=False)  # Signature name (e.g., "Default", "Professional", "Personal")
    content = Column(Text, nullable=False)  # HTML content of the signature
    logo_url = Column(String, nullable=True)  # URL to the logo image
    is_default = Column(Boolean)  # Whether this is the default signature
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<EmailSignature(name='{self.name}', user_id='{self.user_id}')>"

# New models for admin features
class Permission(Base):
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"

class Office(Base):
    __tablename__ = 'offices'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    zip_code = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    churches = relationship("Church", back_populates="office")
    
    def __repr__(self):
        return f"<Office(id={self.id}, name='{self.name}')>"

class UserOffice(Base):
    __tablename__ = 'user_offices'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(128), nullable=False)
    office_id = Column(Integer, ForeignKey('offices.id'), nullable=False)
    role = Column(String(50), nullable=False)  # 'super_admin', 'office_admin', 'standard_user', 'limited_user'
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship
    office = relationship("Office")
    
    def __repr__(self):
        return f"<UserOffice(user_id='{self.user_id}', office_id={self.office_id}, role='{self.role}')>"

class GoogleToken(Base):
    __tablename__ = 'google_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(128), nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String)
    token_uri = Column(String)
    client_id = Column(String)
    client_secret = Column(String)
    scopes = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<GoogleToken {self.user_id}>'

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(128), primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255))
    job_title = Column(String(255))
    phone = Column(String(50))
    timezone = Column(String(50), default='America/New_York')
    email_signature = Column(Text)
    cc_myself = Column(Boolean)
    auto_sync_email = Column(Boolean)
    notify_tasks = Column(Boolean)
    notify_communications = Column(Boolean)
    notify_contacts = Column(Boolean)
    notify_system = Column(Boolean)
    notification_frequency = Column(String(20), default='daily')
    first_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', name='{self.name}')>"

class UserSchema(Schema):
    id = fields.String(required=True)
    email = fields.Email(required=True)
    name = fields.String()
    job_title = fields.String()
    phone = fields.String()
    timezone = fields.String()
    email_signature = fields.String()
    cc_myself = fields.Boolean()
    auto_sync_email = fields.Boolean()
    notify_tasks = fields.Boolean()
    notify_communications = fields.Boolean()
    notify_contacts = fields.Boolean()
    notify_system = fields.Boolean()
    notification_frequency = fields.String()
    first_login = fields.DateTime(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

user_schema = UserSchema()

# Use explicit path to instance folder to ensure consistency
engine = create_engine('sqlite:///instance/mobilize_crm.db')
Base.metadata.create_all(engine)

# Create a scoped session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
