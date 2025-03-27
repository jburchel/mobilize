from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.church import Church
from app.models.person import Person
from app.models.office import Office
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.forms.church import ChurchForm
from app.forms.import_form import ImportForm, FieldMappingForm
from app.extensions import db
from datetime import datetime
import os
import pandas as pd
import uuid
from sqlalchemy import or_
from app.utils.decorators import office_required

churches_bp = Blueprint('churches', __name__, template_folder='../templates/churches')

@churches_bp.route('/')
@login_required
@office_required
def index():
    """Show list of all churches."""
    # For super admins, show all churches across all offices
    if current_user.is_super_admin():
        churches = Church.query.all()
    else:
        churches = Church.query.filter_by(office_id=current_user.office_id).all()
    return render_template('churches/index.html', churches=churches)

@churches_bp.route('/new', methods=['GET', 'POST'])
@login_required
@office_required
def create():
    """Create a new church."""
    form = ChurchForm()
    
    # Load contact person choices
    if current_user.is_super_admin():
        form.main_contact_id.choices = [(0, 'None')] + [(p.id, f"{p.first_name} {p.last_name}") 
                                                         for p in Person.query.all()]
    else:
        form.main_contact_id.choices = [(0, 'None')] + [(p.id, f"{p.first_name} {p.last_name}") 
                                                         for p in Person.query.filter_by(office_id=current_user.office_id).all()]
    
    if form.validate_on_submit():
        church = Church(
            name=form.name.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zipcode=form.zip_code.data,
            country=form.country.data,
            phone=form.phone.data,
            email=form.email.data,
            website=form.website.data,
            location=form.location.data,
            senior_pastor_name=form.senior_pastor_name.data,
            senior_pastor_phone=form.senior_pastor_phone.data,
            senior_pastor_email=form.senior_pastor_email.data,
            associate_pastor_name=form.associate_pastor_name.data,
            missions_pastor_first_name=form.missions_pastor_first_name.data,
            missions_pastor_last_name=form.missions_pastor_last_name.data,
            mission_pastor_phone=form.mission_pastor_phone.data,
            mission_pastor_email=form.mission_pastor_email.data,
            primary_contact_first_name=form.primary_contact_first_name.data,
            primary_contact_last_name=form.primary_contact_last_name.data,
            primary_contact_phone=form.primary_contact_phone.data,
            primary_contact_email=form.primary_contact_email.data,
            denomination=form.denomination.data,
            weekly_attendance=form.weekly_attendance.data,
            priority=form.priority.data,
            assigned_to=form.assigned_to.data,
            source=form.source.data,
            virtuous=form.virtuous.data,
            referred_by=form.referred_by.data,
            info_given=form.info_given.data,
            reason_closed=form.reason_closed.data,
            year_founded=form.year_founded.data,
            date_closed=form.date_closed.data,
            notes=form.notes.data,
            tags=form.tags.data,
            type='church',  # Explicitly set type for the polymorphic model
            office_id=current_user.office_id,
            user_id=current_user.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Handle contact person relationship
        if form.main_contact_id.data and form.main_contact_id.data != 0:
            church.main_contact_id = form.main_contact_id.data
        
        # Handle profile image upload
        if form.profile_image.data:
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join('app', 'static', 'uploads', 'churches')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            filename = f"{uuid.uuid4()}.{form.profile_image.data.filename.split('.')[-1]}"
            filepath = os.path.join(upload_dir, filename)
            
            # Save the file
            form.profile_image.data.save(filepath)
            
            # Store the path in the database
            church.profile_image = f"/static/uploads/churches/{filename}"
        
        db.session.add(church)
        db.session.commit()
        
        # Handle main pipeline assignment
        if form.church_pipeline.data:
            # Get the main pipeline for churches
            main_pipeline = Pipeline.query.filter_by(
                pipeline_type='church',
                is_main_pipeline=True,
                office_id=church.office_id
            ).first()
            
            if main_pipeline:
                # Find the selected stage
                selected_stage = None
                for stage in main_pipeline.stages:
                    if stage.name == form.church_pipeline.data:
                        selected_stage = stage
                        break
                
                if not selected_stage:
                    # No matching stage found, try to find by the stage value directly
                    stage_value = form.church_pipeline.data
                    for stage in main_pipeline.stages:
                        if stage.name.upper() == stage_value.upper():
                            selected_stage = stage
                            break
                
                if selected_stage:
                    # Add church to pipeline
                    pipeline_contact = PipelineContact(
                        contact_id=church.id,
                        pipeline_id=main_pipeline.id,
                        current_stage_id=selected_stage.id,
                        entered_at=datetime.now()
                    )
                    db.session.add(pipeline_contact)
        
        flash('Church created successfully', 'success')
        return redirect(url_for('churches.show', id=church.id))
    
    return render_template('churches/form.html', form=form)

@churches_bp.route('/<int:id>')
@login_required
@office_required
def show(id):
    """Show a specific church."""
    church = Church.query.get_or_404(id)
    
    # Check access permissions (allow super admins to view all)
    if not current_user.is_super_admin() and church.office_id != current_user.office_id:
        flash('You do not have permission to view this church', 'danger')
        return redirect(url_for('churches.index'))
    
    # Get the contact person if specified
    contact_person = None
    if church.main_contact_id:
        contact_person = Person.query.get(church.main_contact_id)
    
    # Get people associated with this church
    church.people = Person.query.filter_by(church_id=church.id).all()
    
    return render_template('churches/detail.html', church=church, contact_person=contact_person)

@churches_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@office_required
def edit(id):
    """Edit a specific church."""
    church = Church.query.get_or_404(id)
    
    # Check modification permissions (allow super admins to edit all)
    if not current_user.is_super_admin() and church.office_id != current_user.office_id:
        flash('You do not have permission to edit this church', 'danger')
        return redirect(url_for('churches.index'))
    
    form = ChurchForm(obj=church)
    
    # Load contact person choices
    if current_user.is_super_admin():
        form.main_contact_id.choices = [(0, 'None')] + [(p.id, f"{p.first_name} {p.last_name}") 
                                                         for p in Person.query.all()]
    else:
        form.main_contact_id.choices = [(0, 'None')] + [(p.id, f"{p.first_name} {p.last_name}") 
                                                         for p in Person.query.filter_by(office_id=current_user.office_id).all()]
    
    if form.validate_on_submit():
        church.name = form.name.data
        church.address = form.address.data
        church.city = form.city.data
        church.state = form.state.data
        church.zipcode = form.zip_code.data
        church.country = form.country.data
        church.phone = form.phone.data
        church.email = form.email.data
        church.website = form.website.data
        church.location = form.location.data
        church.senior_pastor_name = form.senior_pastor_name.data
        church.senior_pastor_phone = form.senior_pastor_phone.data
        church.senior_pastor_email = form.senior_pastor_email.data
        church.associate_pastor_name = form.associate_pastor_name.data
        church.missions_pastor_first_name = form.missions_pastor_first_name.data
        church.missions_pastor_last_name = form.missions_pastor_last_name.data
        church.mission_pastor_phone = form.mission_pastor_phone.data
        church.mission_pastor_email = form.mission_pastor_email.data
        church.primary_contact_first_name = form.primary_contact_first_name.data
        church.primary_contact_last_name = form.primary_contact_last_name.data
        church.primary_contact_phone = form.primary_contact_phone.data
        church.primary_contact_email = form.primary_contact_email.data
        church.denomination = form.denomination.data
        church.weekly_attendance = form.weekly_attendance.data
        church.priority = form.priority.data
        church.assigned_to = form.assigned_to.data
        church.source = form.source.data
        church.virtuous = form.virtuous.data
        church.referred_by = form.referred_by.data
        church.info_given = form.info_given.data
        church.reason_closed = form.reason_closed.data
        church.year_founded = form.year_founded.data
        church.date_closed = form.date_closed.data
        church.notes = form.notes.data
        church.tags = form.tags.data
        church.updated_at = datetime.now()
        
        # Handle contact person relationship
        if form.main_contact_id.data and form.main_contact_id.data != 0:
            church.main_contact_id = form.main_contact_id.data
        else:
            church.main_contact_id = None
        
        # Handle profile image upload
        if form.profile_image.data:
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join('app', 'static', 'uploads', 'churches')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            filename = f"{uuid.uuid4()}.{form.profile_image.data.filename.split('.')[-1]}"
            filepath = os.path.join(upload_dir, filename)
            
            # Delete old profile image if exists
            if church.profile_image:
                old_filepath = os.path.join('app', church.profile_image.lstrip('/'))
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
            
            # Save the new file
            form.profile_image.data.save(filepath)
            
            # Store the path in the database
            church.profile_image = f"/static/uploads/churches/{filename}"
        
        # Handle main pipeline assignment
        if form.church_pipeline.data:
            # Get the main pipeline for churches
            main_pipeline = Pipeline.query.filter_by(
                pipeline_type='church',
                is_main_pipeline=True,
                office_id=church.office_id
            ).first()
            
            if main_pipeline:
                # Find the selected stage
                selected_stage = None
                for stage in main_pipeline.stages:
                    if stage.name == form.church_pipeline.data:
                        selected_stage = stage
                        break
                
                if not selected_stage:
                    # No matching stage found, try to find by the stage value directly
                    stage_value = form.church_pipeline.data
                    for stage in main_pipeline.stages:
                        if stage.name.upper() == stage_value.upper():
                            selected_stage = stage
                            break
                
                if selected_stage:
                    # Check if church is already in this pipeline
                    pipeline_contact = PipelineContact.query.filter_by(
                        contact_id=church.id,
                        pipeline_id=main_pipeline.id
                    ).first()
                    
                    if pipeline_contact:
                        # Update existing pipeline contact
                        pipeline_contact.move_to_stage(
                            selected_stage.id, 
                            user_id=current_user.id,
                            notes=f"Updated from church edit form"
                        )
                    else:
                        # Add church to pipeline
                        pipeline_contact = PipelineContact(
                            contact_id=church.id,
                            pipeline_id=main_pipeline.id,
                            current_stage_id=selected_stage.id,
                            entered_at=datetime.now()
                        )
                        db.session.add(pipeline_contact)
        
        db.session.commit()
        
        flash('Church updated successfully', 'success')
        return redirect(url_for('churches.show', id=church.id))
    
    return render_template('churches/form.html', form=form, church=church)

@churches_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@office_required
def delete(id):
    """Delete a specific church."""
    church = Church.query.get_or_404(id)
    
    # Check deletion permissions (allow super admins to delete all)
    if not current_user.is_super_admin() and church.office_id != current_user.office_id:
        flash('You do not have permission to delete this church', 'danger')
        return redirect(url_for('churches.index'))
    
    # Delete the church
    db.session.delete(church)
    db.session.commit()
    
    flash('Church deleted successfully', 'success')
    return redirect(url_for('churches.index'))

@churches_bp.route('/<int:id>/set-primary-contact', methods=['POST'])
@login_required
@office_required
def set_primary_contact(id):
    """Set the primary contact for a church."""
    church = Church.query.get_or_404(id)
    
    # Check modification permissions (allow super admins to edit all)
    if not current_user.is_super_admin() and church.office_id != current_user.office_id:
        flash('You do not have permission to modify this church', 'danger')
        return redirect(url_for('churches.index'))
    
    main_contact_id = request.form.get('main_contact_id')
    
    if main_contact_id:
        # Verify that the person exists and belongs to this church
        person = Person.query.filter_by(id=main_contact_id, church_id=church.id).first()
        
        if person:
            # Set this person as the primary contact
            church.main_contact_id = person.id
            db.session.commit()
            flash(f'{person.full_name} set as primary contact for {church.name}', 'success')
        else:
            flash('Selected person does not exist or is not associated with this church', 'danger')
    else:
        flash('No contact selected', 'warning')
    
    return redirect(url_for('churches.show', id=church.id))

@churches_bp.route('/search')
@login_required
@office_required
def search():
    """Search for churches by name."""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'churches': []})
    
    # For super admins, search across all offices
    if current_user.is_super_admin():
        churches = Church.query.filter(
            or_(
                Church.name.ilike(f'%{query}%'),
                Church.denomination.ilike(f'%{query}%'),
                Church.pastor_name.ilike(f'%{query}%')
            )
        ).limit(10).all()
    else:
        # For regular users, filter by office_id
        churches = Church.query.filter(
            Church.office_id == current_user.office_id,
            or_(
                Church.name.ilike(f'%{query}%'),
                Church.denomination.ilike(f'%{query}%'),
                Church.pastor_name.ilike(f'%{query}%')
            )
        ).limit(10).all()
    
    # Format the location based on city, state, and country
    def format_location(church):
        if church.location:
            return church.location
            
        city = church.city or ''
        state = church.state or ''
        country = church.country or ''
        
        if not city:
            return ""
            
        # For US addresses
        if country in ('United States', 'USA', 'US') or not country:
            if state:
                return f"{city}, {state}"
            return city
            
        # For Canadian addresses
        if country in ('Canada', 'CA'):
            if state:
                return f"{city}, {state}"
            return city
            
        # For all other countries
        return f"{city}, {country}" if country else city
    
    result = [
        {
            'id': c.id,
            'name': c.name,
            'address': format_location(c)
        } for c in churches
    ]
    
    return jsonify({'churches': result})

@churches_bp.route('/add_note/<int:id>', methods=['POST'])
@login_required
def add_note(id):
    """Add a note to a church."""
    church = Church.query.get_or_404(id)
    
    # Security check - ensure the church belongs to the current user's office
    if church.office_id != current_user.office_id:
        flash('You do not have permission to add notes to this church.', 'danger')
        return redirect(url_for('churches.index'))
    
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
    
    return redirect(url_for('churches.show', id=church.id))

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
        
        return redirect(url_for('churches.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error during import: {str(e)}', 'danger')
        return redirect(url_for('churches.import_churches')) 