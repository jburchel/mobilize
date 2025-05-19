from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DateField, SelectField, EmailField, TelField, BooleanField
from wtforms.validators import DataRequired, Email, Optional, Length
from app.models.constants import (
    STATE_CHOICES, PEOPLE_PIPELINE_CHOICES, MARITAL_STATUS_CHOICES,
    PRIORITY_CHOICES, SOURCE_CHOICES, CHURCH_ROLE_CHOICES
)
from app.models.user import User

class PersonForm(FlaskForm):
    """Form for creating and editing a person."""
    
    # Personal Information
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    email = EmailField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = TelField('Phone', validators=[Optional(), Length(max=20)])
    
    # Additional Personal Info
    title = StringField('Title', validators=[Optional(), Length(max=100)])
    marital_status = SelectField('Marital Status', 
                               choices=[('', 'Select Status')] + MARITAL_STATUS_CHOICES, 
                               validators=[Optional()])
    spouse_first_name = StringField('Spouse First Name', validators=[Optional(), Length(max=100)])
    spouse_last_name = StringField('Spouse Last Name', validators=[Optional(), Length(max=100)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()], format='%Y-%m-%d')
    profile_image = FileField('Profile Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    
    # Address Information
    address = StringField('Street Address', validators=[Optional(), Length(max=200)])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    state = SelectField('State', choices=[('', 'Select State')] + STATE_CHOICES, validators=[Optional()])
    zip_code = StringField('ZIP Code', validators=[Optional(), Length(max=10)])
    country = StringField('Country', validators=[Optional(), Length(max=100)])
    
    # Church & Role
    church_id = SelectField('Church', validators=[Optional()], coerce=int)
    church_role = SelectField('Church Role', 
                           choices=[('', 'Select Role')] + CHURCH_ROLE_CHOICES,
                           validators=[Optional()])
    is_primary_contact = BooleanField('Primary Contact for Church', default=False)
    
    # Pipeline Information from Old Model
    people_pipeline = SelectField('Main Pipeline Stage', 
                               choices=[('', 'Select Stage')] + PEOPLE_PIPELINE_CHOICES, 
                               validators=[Optional()])
    virtuous = BooleanField('Virtuous', default=False)
    
    # Pipeline Information from New Model
    pipeline_status = SelectField('Pipeline Status', validators=[Optional()],
                               choices=[
                                   ('', 'Select Status'),
                                   ('active', 'Active'),
                                   ('inactive', 'Inactive'),
                                   ('closed', 'Closed')
                               ])
    
    # Common Pipeline Fields  
    priority = SelectField('Priority', 
                       choices=[('', 'Select Priority')] + PRIORITY_CHOICES, 
                       validators=[Optional()])
    source = SelectField('Source', 
                      choices=[('', 'Select Source')] + SOURCE_CHOICES, 
                      validators=[Optional()])
    assigned_to = SelectField('Assigned To', 
                           choices=[], 
                           validators=[Optional()], coerce=int)
    
    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        # Dynamically load users from database
        users = User.query.filter_by(is_active=True).order_by(User.first_name).all()
        self.assigned_to.choices = [(0, 'Unassigned')] + [(user.id, f"{user.first_name} {user.last_name}") for user in users]
    referred_by = StringField('Referred By', validators=[Optional(), Length(max=100)])
    
    # Additional fields from old model
    info_given = TextAreaField('Information Given', validators=[Optional()])
    desired_service = TextAreaField('Desired Service', validators=[Optional()])
    
    # For closed contacts
    reason_closed = TextAreaField('Reason Closed', validators=[Optional()])
    date_closed = DateField('Date Closed', validators=[Optional()], format='%Y-%m-%d')
    
    # Additional Notes
    notes = TextAreaField('Notes', validators=[Optional()])
    tags = StringField('Tags', validators=[Optional()], description='Separate tags with commas') 