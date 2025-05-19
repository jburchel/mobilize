from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, SelectField, EmailField, TelField, URLField, BooleanField, DateField
from wtforms.validators import DataRequired, Email, Optional, Length, NumberRange
from app.models.constants import STATE_CHOICES, CHURCH_PIPELINE_CHOICES, PRIORITY_CHOICES, SOURCE_CHOICES
from app.models.user import User
from app.extensions import db

class ChurchForm(FlaskForm):
    """Form for creating and editing a church."""
    
    # Basic Church Information
    name = StringField('Church Name', validators=[DataRequired(), Length(max=200)])
    location = StringField('Location', validators=[Optional(), Length(max=200)])
    
    # Contact Information
    email = EmailField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = TelField('Phone', validators=[Optional(), Length(max=20)])
    website = URLField('Website', validators=[Optional(), Length(max=200)])
    
    # Pastor Information
    senior_pastor_first_name = StringField('Senior Pastor First Name', validators=[Optional(), Length(max=100)])
    senior_pastor_last_name = StringField('Senior Pastor Last Name', validators=[Optional(), Length(max=100)])
    senior_pastor_phone = TelField('Senior Pastor Phone', validators=[Optional(), Length(max=50)])
    senior_pastor_email = EmailField('Senior Pastor Email', validators=[Optional(), Email()])
    
    # Missions Pastor Information
    missions_pastor_first_name = StringField('Missions Pastor First Name', validators=[Optional(), Length(max=100)])
    missions_pastor_last_name = StringField('Missions Pastor Last Name', validators=[Optional(), Length(max=100)])
    mission_pastor_phone = TelField('Missions Pastor Phone', validators=[Optional(), Length(max=50)])
    mission_pastor_email = EmailField('Missions Pastor Email', validators=[Optional(), Email()])
    
    # Primary Contact Selection (replaces individual primary contact fields)
    main_contact_id = SelectField('Main Contact Person', validators=[Optional()], coerce=int)
    
    # Denomination and Size
    denomination = StringField('Denomination', validators=[Optional(), Length(max=100)])
    weekly_attendance = IntegerField('Weekly Attendance', validators=[Optional(), NumberRange(min=0)])
    
    # Pipeline and Tracking
    church_pipeline = SelectField('Main Pipeline Stage', 
                                choices=[('', 'Select Stage')] + CHURCH_PIPELINE_CHOICES, 
                                validators=[Optional()])
    priority = SelectField('Priority', 
                          choices=[('', 'Select Priority')] + PRIORITY_CHOICES, 
                          validators=[Optional()])
    assigned_to = SelectField('Assigned To', 
                             choices=[], 
                             validators=[Optional()], coerce=int)
    
    def __init__(self, *args, **kwargs):
        super(ChurchForm, self).__init__(*args, **kwargs)
        # Dynamically load users from database
        users = User.query.filter_by(is_active=True).order_by(User.first_name).all()
        self.assigned_to.choices = [(0, 'Unassigned')] + [(user.id, f"{user.first_name} {user.last_name}") for user in users]
    source = SelectField('Source', 
                        choices=[('', 'Select Source')] + SOURCE_CHOICES, 
                        validators=[Optional()])
    
    # Additional Fields
    virtuous = BooleanField('Virtuous', default=False)
    referred_by = StringField('Referred By', validators=[Optional(), Length(max=100)])
    info_given = TextAreaField('Information Given', validators=[Optional()])
    reason_closed = TextAreaField('Reason Closed', validators=[Optional()])
    year_founded = IntegerField('Year Founded', validators=[Optional(), NumberRange(min=1500, max=2100)])
    date_closed = DateField('Date Closed', validators=[Optional()], format='%Y-%m-%d')
    
    # Address Information
    address = StringField('Street Address', validators=[Optional(), Length(max=200)])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    state = SelectField('State', choices=[('', 'Select State')] + STATE_CHOICES, validators=[Optional()])
    zip_code = StringField('ZIP Code', validators=[Optional(), Length(max=10)])
    country = StringField('Country', validators=[Optional(), Length(max=100)])
    
    # Church Logo
    profile_image = FileField('Church Logo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    
    # Additional Information
    notes = TextAreaField('Notes', validators=[Optional()]) 
    tags = StringField('Tags', validators=[Optional()], description='Separate tags with commas') 