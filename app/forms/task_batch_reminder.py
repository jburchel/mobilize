from flask_wtf import FlaskForm
from wtforms import SelectField, BooleanField, SelectMultipleField, widgets
from wtforms.validators import DataRequired

class MultiCheckboxField(SelectMultipleField):
    """Custom multi-checkbox field for selecting multiple tasks."""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class TaskBatchReminderForm(FlaskForm):
    """Form for batch updating task reminder settings."""
    task_ids = MultiCheckboxField('Select Tasks', coerce=int)
    reminder_option = SelectField('Reminder', choices=[
        ('none', 'None'),
        ('on_due_date', 'On Due Date'),
        ('1_day_before', '1 Day Before'),
        ('2_days_before', '2 Days Before'),
        ('1_week_before', '1 Week Before')
    ], default='none', validators=[DataRequired()])
    google_calendar_sync_enabled = BooleanField('Sync with Google Calendar', default=False) 