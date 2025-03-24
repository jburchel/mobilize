from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.church import Church
from app.models.person import Person
from app.models.office import Office
from app.forms.church import ChurchForm
from app.forms.import_form import ImportForm, FieldMappingForm
from app.extensions import db
from datetime import datetime
import os
import pandas as pd
import uuid

churches_bp = Blueprint('churches', __name__, template_folder='../templates/churches')

@churches_bp.route('/')
@churches_bp.route('/list')
@login_required
def list():
    """Display list of churches."""
    # Fetch churches from database, filter by current user's office
    churches = Church.query.filter_by(office_id=current_user.office_id).all()
    return render_template('churches/list.html', 
                          churches=churches, 
                          page_title="Churches Management")

@churches_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new church."""
    form = ChurchForm()
    
    # Populate select fields
    form.main_contact_id.choices = [(0, 'None')] + [(p.id, f"{p.first_name} {p.last_name}") 
                                                 for p in Person.query.filter_by(office_id=current_user.office_id).all()]
    
    if form.validate_on_submit():
        church = Church()
        
        # Basic Church Information
        church.name = form.name.data
        church.location = form.location.data
        
        # Contact Information
        church.email = form.email.data
        church.phone = form.phone.data
        church.website = form.website.data
        
        # Pastor Information
        church.senior_pastor_name = form.senior_pastor_name.data
        church.associate_pastor_name = form.associate_pastor_name.data
        
        # Denomination and Size
        church.denomination = form.denomination.data
        church.weekly_attendance = form.weekly_attendance.data
        
        # Main Contact Person
        if form.main_contact_id.data and form.main_contact_id.data > 0:
            church.main_contact_id = form.main_contact_id.data
        
        # Address Information
        church.address = form.address.data
        church.city = form.city.data
        church.state = form.state.data
        church.zip_code = form.zip_code.data
        church.country = form.country.data
        
        # Notes
        church.notes = form.notes.data
        
        # Set office ID and owner ID
        church.office_id = current_user.office_id
        church.owner_id = current_user.id
        
        # Handle profile image (logo) upload
        if form.profile_image.data:
            # Create directories if they don't exist
            upload_folder = os.path.join('app', 'static', 'uploads', 'churches')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique filename
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{form.profile_image.data.filename}"
            filepath = os.path.join(upload_folder, filename)
            
            # Save the file
            form.profile_image.data.save(filepath)
            
            # Store the relative path in the database
            church.profile_image = f"uploads/churches/{filename}"
        
        # Save to database
        db.session.add(church)
        db.session.commit()
        
        flash('Church added successfully!', 'success')
        return redirect(url_for('churches.list'))
    
    # For GET request or if form validation fails, display the form
    return render_template('churches/form.html', 
                          form=form,
                          church=None, 
                          page_title="Add Church")

@churches_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing church."""
    church = Church.query.get_or_404(id)
    
    # Security check - ensure the church belongs to the current user's office
    if church.office_id != current_user.office_id:
        flash('You do not have permission to edit this church.', 'danger')
        return redirect(url_for('churches.list'))
    
    form = ChurchForm(obj=church)
    
    # Populate select fields
    form.main_contact_id.choices = [(0, 'None')] + [(p.id, f"{p.first_name} {p.last_name}") 
                                                 for p in Person.query.filter_by(office_id=current_user.office_id).all()]
    
    if form.validate_on_submit():
        # Basic Church Information
        church.name = form.name.data
        church.location = form.location.data
        
        # Contact Information
        church.email = form.email.data
        church.phone = form.phone.data
        church.website = form.website.data
        
        # Pastor Information
        church.senior_pastor_name = form.senior_pastor_name.data
        church.associate_pastor_name = form.associate_pastor_name.data
        
        # Denomination and Size
        church.denomination = form.denomination.data
        church.weekly_attendance = form.weekly_attendance.data
        
        # Main Contact Person
        if form.main_contact_id.data and form.main_contact_id.data > 0:
            church.main_contact_id = form.main_contact_id.data
        else:
            church.main_contact_id = None
        
        # Address Information
        church.address = form.address.data
        church.city = form.city.data
        church.state = form.state.data
        church.zip_code = form.zip_code.data
        church.country = form.country.data
        
        # Notes
        church.notes = form.notes.data
        
        # Handle profile image (logo) upload
        if form.profile_image.data:
            # Create directories if they don't exist
            upload_folder = os.path.join('app', 'static', 'uploads', 'churches')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique filename
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{form.profile_image.data.filename}"
            filepath = os.path.join(upload_folder, filename)
            
            # Save the file
            form.profile_image.data.save(filepath)
            
            # Delete old profile image if it exists
            if church.profile_image:
                old_filepath = os.path.join('app', 'static', church.profile_image)
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
            
            # Store the relative path in the database
            church.profile_image = f"uploads/churches/{filename}"
        
        # Save changes
        db.session.commit()
        
        flash('Church updated successfully!', 'success')
        return redirect(url_for('churches.view', id=church.id))
    
    # For GET request or if form validation fails, display the form with existing data
    return render_template('churches/form.html', 
                          form=form,
                          church=church, 
                          page_title=f"Edit {church.name}")

@churches_bp.route('/view/<int:id>')
@login_required
def view(id):
    """View details of a specific church."""
    church = Church.query.get_or_404(id)
    
    # Security check - ensure the church belongs to the current user's office
    if church.office_id != current_user.office_id:
        flash('You do not have permission to view this church.', 'danger')
        return redirect(url_for('churches.list'))
    
    # Get church members (people with this church_id)
    from app.models.person import Person
    church.people = Person.query.filter_by(church_id=church.id).all()
    
    # Get tasks for this church
    from app.models.task import Task
    tasks = Task.query.filter_by(church_id=church.id).order_by(Task.due_date).all()
    
    # Get communications for this church
    from app.models.communication import Communication
    communications = Communication.query.filter_by(church_id=church.id).order_by(Communication.date.desc()).all()
    
    return render_template('churches/detail.html', 
                          church=church,
                          tasks=tasks,
                          communications=communications,
                          page_title=f"{church.name}")

@churches_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a church."""
    church = Church.query.get_or_404(id)
    
    # Security check - ensure the church belongs to the current user's office
    if church.office_id != current_user.office_id:
        flash('You do not have permission to delete this church.', 'danger')
        return redirect(url_for('churches.list'))
    
    # Delete profile image if it exists
    if hasattr(church, 'profile_image') and church.profile_image:
        filepath = os.path.join('app', 'static', church.profile_image)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    # Delete the church
    db.session.delete(church)
    db.session.commit()
    
    flash('Church deleted successfully!', 'success')
    return redirect(url_for('churches.list'))

@churches_bp.route('/add_note/<int:id>', methods=['POST'])
@login_required
def add_note(id):
    """Add a note to a church."""
    church = Church.query.get_or_404(id)
    
    # Security check - ensure the church belongs to the current user's office
    if church.office_id != current_user.office_id:
        flash('You do not have permission to add notes to this church.', 'danger')
        return redirect(url_for('churches.list'))
    
    content = request.form.get('content', '')
    if content:
        # Append the new note to existing notes, adding a timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if church.notes:
            church.notes = f"{church.notes}\n\n{timestamp} - {current_user.full_name}:\n{content}"
        else:
            church.notes = f"{timestamp} - {current_user.full_name}:\n{content}"
        
        db.session.commit()
        flash('Note added successfully!', 'success')
    else:
        flash('Note cannot be empty!', 'warning')
    
    return redirect(url_for('churches.view', id=church.id))

@churches_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_churches():
    """Import churches from CSV or Excel file."""
    form = ImportForm()
    
    # Initialize field mapping choices
    church_fields = [
        ('name', 'Church Name'),
        ('location', 'Location'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('website', 'Website'),
        ('senior_pastor_name', 'Senior Pastor'),
        ('associate_pastor_name', 'Associate Pastor'),
        ('denomination', 'Denomination'),
        ('weekly_attendance', 'Weekly Attendance'),
        ('address', 'Street Address'),
        ('city', 'City'),
        ('state', 'State'),
        ('zip_code', 'ZIP Code'),
        ('country', 'Country'),
        ('notes', 'Notes'),
        ('tags', 'Tags')
    ]
    form.field_mapping = [FieldMappingForm(label=field_label) for field_key, field_label in church_fields]
    
    if form.validate_on_submit():
        try:
            file = form.file.data
            filename = secure_filename(file.filename)
            file_extension = filename.rsplit('.', 1)[1].lower()
            
            # Save file temporarily
            temp_filepath = os.path.join('app', 'static', 'temp', f"{uuid.uuid4()}.{file_extension}")
            os.makedirs(os.path.dirname(temp_filepath), exist_ok=True)
            file.save(temp_filepath)
            
            # Read file based on extension
            if file_extension == 'csv':
                df = pd.read_csv(temp_filepath)
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(temp_filepath)
            else:
                flash('Unsupported file format. Please upload CSV or Excel file.', 'danger')
                return redirect(url_for('churches.import_churches'))
            
            # Skip header if specified
            if form.skip_header.data and len(df) > 0:
                df = df.iloc[1:]
            
            # Get column names for preview
            columns = df.columns.tolist()
            
            # Store data in session for preview and processing
            session['import_data'] = {
                'filepath': temp_filepath,
                'columns': columns,
                'update_existing': form.update_existing.data,
                'field_mapping': {field_key: field_form.data for field_key, field_label in church_fields 
                                for field_form in form.field_mapping}
            }
            
            # Redirect to preview page
            return redirect(url_for('churches.preview_import'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(url_for('churches.import_churches'))
    
    return render_template('churches/import.html', 
                         form=form,
                         page_title="Import Churches")

@churches_bp.route('/import/preview', methods=['GET', 'POST'])
@login_required
def preview_import():
    """Preview and confirm church import."""
    if 'import_data' not in session:
        flash('No import data found. Please upload a file first.', 'warning')
        return redirect(url_for('churches.import_churches'))
    
    import_data = session.get('import_data')
    filepath = import_data.get('filepath')
    
    # Check if file exists
    if not os.path.exists(filepath):
        flash('Import file not found. Please upload again.', 'danger')
        return redirect(url_for('churches.import_churches'))
    
    try:
        # Read file based on extension
        file_extension = filepath.rsplit('.', 1)[1].lower()
        if file_extension == 'csv':
            df = pd.read_csv(filepath)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(filepath)
        
        # Process form submission (confirm import)
        if request.method == 'POST':
            return process_church_import(df, import_data)
        
        # Prepare preview data
        preview_data = df.head(5).to_dict('records')
        
        return render_template('churches/import_preview.html',
                             preview_data=preview_data,
                             columns=import_data.get('columns'),
                             field_mapping=import_data.get('field_mapping'),
                             page_title="Preview Import")
        
    except Exception as e:
        flash(f'Error processing preview: {str(e)}', 'danger')
        return redirect(url_for('churches.import_churches'))

def process_church_import(df, import_data):
    """Process the actual import of churches."""
    field_mapping = import_data.get('field_mapping', {})
    update_existing = import_data.get('update_existing', False)
    
    try:
        # Track statistics
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Map data from file to church fields
                church_data = {}
                for field, column in field_mapping.items():
                    if column and column in row:
                        church_data[field] = row[column]
                
                # Check required fields
                if not church_data.get('name'):
                    stats['skipped'] += 1
                    continue
                
                # Check if church exists when updating
                existing_church = None
                if update_existing:
                    # Try to find by name
                    existing_church = Church.query.filter_by(
                        name=church_data.get('name'),
                        office_id=current_user.office_id
                    ).first()
                
                if existing_church:
                    # Update existing church
                    for field, value in church_data.items():
                        if value is not None and hasattr(existing_church, field):
                            setattr(existing_church, field, value)
                    stats['updated'] += 1
                else:
                    # Create new church
                    new_church = Church(
                        office_id=current_user.office_id,
                        owner_id=current_user.id,
                        **church_data
                    )
                    db.session.add(new_church)
                    stats['created'] += 1
                
            except Exception as e:
                stats['errors'] += 1
                continue
        
        # Commit all changes
        db.session.commit()
        
        # Clean up the temporary file
        if os.path.exists(import_data.get('filepath')):
            os.remove(import_data.get('filepath'))
        
        # Clear session data
        if 'import_data' in session:
            session.pop('import_data')
        
        # Display results
        flash(f"Import complete: {stats['created']} created, {stats['updated']} updated, "
              f"{stats['skipped']} skipped, {stats['errors']} errors", 'success')
        
        return redirect(url_for('churches.list'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error during import: {str(e)}', 'danger')
        return redirect(url_for('churches.import_churches')) 