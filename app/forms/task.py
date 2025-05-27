from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, BooleanField
from wtforms.validators import DataRequired, Optional, Length
from flask_wtf.file import FileField, FileAllowed

class TaskForm(FlaskForm):
    """Form for creating and updating tasks."""
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    due_date = DateField('Due Date', format='%Y-%m-%d', validators=[Optional()])
    due_time = StringField('Due Time', validators=[Optional()])
    assigned_to = SelectField('Assigned To', coerce=int, validators=[Optional()])
    contact_type = SelectField('Contact Type', choices=[
        ('', 'None'),
        ('person', 'Person'),
        ('church', 'Church')
    ], default='')
    person_id = SelectField('Person', coerce=int, validators=[Optional()])
    church_id = SelectField('Church', coerce=int, validators=[Optional()])
    reminder_option = SelectField('Reminder', choices=[
        ('none', 'None'),
        ('on_due_date', 'On Due Date'),
        ('1_day_before', '1 Day Before'),
        ('2_days_before', '2 Days Before'),
        ('1_week_before', '1 Week Before')
    ], default='none')
    google_calendar_sync_enabled = BooleanField('Sync with Google Calendar', default=False) 