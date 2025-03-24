from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import BooleanField, SelectField, FormField, FieldList, StringField
from wtforms.validators import DataRequired, Optional

class FieldMappingForm(FlaskForm):
    """Form for mapping a single field from import file to database field."""
    field = SelectField('Field Mapping', validators=[Optional()], default='')
    
    def __init__(self, *args, label=None, **kwargs):
        super(FieldMappingForm, self).__init__(*args, **kwargs)
        self.label = label or self.field.label
        
    class Meta:
        # No CSRF for this subform
        csrf = False

class ImportForm(FlaskForm):
    """Form for importing data from CSV or Excel files."""
    file = FileField('Select File', validators=[
        FileRequired('Please select a file to import.'),
        FileAllowed(['csv', 'xlsx', 'xls'], 'CSV or Excel files only!')
    ])
    
    skip_header = BooleanField('Skip Header Row', default=True)
    update_existing = BooleanField('Update Existing Records', default=False)
    
    # field_mapping will be populated dynamically in the view 