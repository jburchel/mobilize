from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
from app.utils.decorators import office_required
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app.models.church import Church
from app.models.person import Person
from app.models.pipeline import Pipeline, PipelineContact, PipelineStage
# Task model is used in relationship but not directly imported here
from app.extensions import db
from app.forms.church import ChurchForm
from app.forms.import_form import ImportForm, FieldMappingForm
# Import json for JSON responses
import pandas as pd
import uuid
from sqlalchemy import or_

churches_bp = Blueprint('churches', __name__, template_folder='../templates/churches')

@churches_bp.route('/')
@login_required
@office_required
def index():
    """Show list of all churches with optimized loading using server-side pagination and search."""
    from sqlalchemy.orm import joinedload
    from app.models.pipeline import Pipeline, PipelineContact, PipelineStage
    from datetime import datetime
    from sqlalchemy import or_
    import time
    
    # Generate a unique request ID for tracking performance
    request_id = int(time.time() * 1000)
    
    # Start timing for performance monitoring
    start_time = datetime.now()
    print(f"[{request_id}] Churches page request started at {start_time}")
    
    # Get pagination parameters - use a smaller page size like the people page
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Match the people page pagination size for better performance
    search_query = request.args.get('q', '')
    
    # Build the base query with eager loading of only essential relationships
    query = Church.query.options(
        joinedload(Church.main_contact)  # Eager load main contact
    )
    
    # Apply office filter for non-super admins
    if not current_user.is_super_admin():
        query = query.filter_by(office_id=current_user.office_id)
    
    # Apply search filter if provided - similar to people page
    if search_query:
        search_term = f'%{search_query}%'
        query = query.filter(
            or_(
                Church.name.ilike(search_term),
                Church.city.ilike(search_term),
                Church.state.ilike(search_term),
                Church.denomination.ilike(search_term),
                Church.email.ilike(search_term),
                Church.phone.ilike(search_term)
            )
        )
    
    # Order by name for consistency
    query = query.order_by(Church.name)
    
    # Execute the query with pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    churches = pagination.items
    
    # Log query time
    query_time = datetime.now()
    query_duration = (query_time - start_time).total_seconds()
    print(f"[{request_id}] Churches query completed in {query_duration:.2f} seconds")
    
    # Get church IDs for efficient pipeline lookup
    church_ids = [church.id for church in churches]
    
    # Get the main pipeline for churches
    main_pipeline = Pipeline.query.filter(
        Pipeline.pipeline_type == 'church',
        Pipeline.is_main_pipeline
    )
    
    # Apply office filter for non-super admins
    if not current_user.is_super_admin():
        main_pipeline = main_pipeline.filter_by(office_id=current_user.office_id)
    
    main_pipeline = main_pipeline.first()
    
    pipeline_start = datetime.now()
    # Only process pipeline data if we have a main pipeline and churches
    if main_pipeline and churches:
        # Optimize pipeline data loading with a single join query
        pipeline_data = db.session.query(
            PipelineContact.contact_id,
            PipelineStage.name.label('stage_name')
        ).join(
            PipelineStage,
            PipelineContact.current_stage_id == PipelineStage.id
        ).filter(
            PipelineContact.contact_id.in_(church_ids),
            PipelineContact.pipeline_id == main_pipeline.id
        ).all()
        
        # Create a mapping of church_id to stage_name
        pipeline_stages = {contact_id: stage_name for contact_id, stage_name in pipeline_data}
        
        # Attach pipeline stage names to churches to avoid template queries
        for church in churches:
            # Pre-compute values to avoid method calls in template
            church.cached_pipeline_stage = pipeline_stages.get(church.id)
            church.cached_name = church.get_name()
    
    pipeline_duration = (datetime.now() - pipeline_start).total_seconds()
    print(f"[{request_id}] Pipeline data processing completed in {pipeline_duration:.2f} seconds")
    
    # Log total processing time
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    print(f"[{request_id}] Churches page fully processed in {total_duration:.2f} seconds")
    
    return render_template('churches/index.html', churches=churches, pagination=pagination, search_query=search_query)

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
        try:
            church = Church(
                name=form.name.data,
                address=form.address.data,
                city=form.city.data,
                state=form.state.data,
                zip_code=form.zip_code.data,
                country=form.country.data,
                phone=form.phone.data,
                email=form.email.data,
                website=form.website.data,
                location=form.location.data,
                senior_pastor_name=(f"{form.senior_pastor_first_name.data} {form.senior_pastor_last_name.data}").strip(),
                senior_pastor_phone=form.senior_pastor_phone.data,
                senior_pastor_email=form.senior_pastor_email.data,
                missions_pastor_first_name=form.missions_pastor_first_name.data,
                missions_pastor_last_name=form.missions_pastor_last_name.data,
                mission_pastor_phone=form.mission_pastor_phone.data,
                mission_pastor_email=form.mission_pastor_email.data,
                denomination=form.denomination.data,
                weekly_attendance=form.weekly_attendance.data,
                priority=form.priority.data,
                assigned_to=form.assigned_to.data if form.assigned_to.data else current_user.username,
                source=form.source.data,
                virtuous=form.virtuous.data,
                referred_by=form.referred_by.data,
                info_given=form.info_given.data,
                reason_closed=form.reason_closed.data,
                year_founded=form.year_founded.data,
                date_closed=form.date_closed.data,
                notes=form.notes.data,
                type='church',  # Explicitly set type for the polymorphic model
                office_id=current_user.office_id,
                user_id=current_user.id,
                owner_id=current_user.id,  # Ensure owner_id is set to the current user's ID
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
                        db.session.commit()
            
            flash('Church created successfully', 'success')
            return redirect(url_for('churches.show', id=church.id))
        except Exception as error:
            db.session.rollback()
            current_app.logger.error(f"Error creating church: {str(error)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"error": "Internal server error"}), 500
            flash(f'Error creating church: {str(error)}', 'danger')
            return render_template('churches/form.html', form=form)
    
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
    
    # Get all people for the add member modal
    if current_user.is_super_admin():
        people = Person.query.order_by(Person.first_name, Person.last_name).all()
    else:
        people = Person.query.filter_by(office_id=current_user.office_id).order_by(Person.first_name, Person.last_name).all()
    
    # Get church roles for the modal
    from app.models.constants import CHURCH_ROLE_CHOICES
    
    return render_template('churches/detail.html', 
                          church=church, 
                          contact_person=contact_person,
                          people=people,
                          church_roles=CHURCH_ROLE_CHOICES)

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
    
    # Fill form with existing church data
    form.name.data = church.name
    form.address.data = church.address
    form.city.data = church.city
    form.state.data = church.state
    form.zip_code.data = church.zip_code
    form.country.data = church.country
    form.phone.data = church.phone
    form.email.data = church.email
    form.website.data = church.website
    form.location.data = church.location
    
    # Handle senior pastor name (split into first and last if possible)
    if church.senior_pastor_name:
        name_parts = church.senior_pastor_name.split(' ', 1)
        if len(name_parts) > 1:
            form.senior_pastor_first_name.data = name_parts[0]
            form.senior_pastor_last_name.data = name_parts[1]
        else:
            form.senior_pastor_first_name.data = name_parts[0]
            form.senior_pastor_last_name.data = ""
    
    form.senior_pastor_phone.data = church.senior_pastor_phone
    form.senior_pastor_email.data = church.senior_pastor_email
    form.missions_pastor_first_name.data = church.missions_pastor_first_name
    form.missions_pastor_last_name.data = church.missions_pastor_last_name
    form.mission_pastor_phone.data = church.mission_pastor_phone
    form.mission_pastor_email.data = church.mission_pastor_email
    
    if form.validate_on_submit():
        try:
            church.name = form.name.data
            church.address = form.address.data
            church.city = form.city.data
            church.state = form.state.data
            church.zip_code = form.zip_code.data
            church.country = form.country.data
            church.phone = form.phone.data
            church.email = form.email.data
            church.website = form.website.data
            church.location = form.location.data
            
            # Combine first and last name into single senior pastor name field
            church.senior_pastor_name = (f"{form.senior_pastor_first_name.data} {form.senior_pastor_last_name.data}").strip()
            
            church.senior_pastor_phone = form.senior_pastor_phone.data
            church.senior_pastor_email = form.senior_pastor_email.data
            church.missions_pastor_first_name = form.missions_pastor_first_name.data
            church.missions_pastor_last_name = form.missions_pastor_last_name.data
            church.mission_pastor_phone = form.mission_pastor_phone.data
            church.mission_pastor_email = form.mission_pastor_email.data
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
                                notes="Updated from church edit form"
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
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating church {id}: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"error": "Internal server error"}), 500
            flash(f'Error updating church: {str(e)}', 'danger')
            return render_template('churches/form.html', form=form, church=church)
    
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
            flash('Person not found or not a member of this church', 'danger')
    else:
        flash('No person selected', 'danger')
    
    return redirect(url_for('churches.show', id=church.id))

@churches_bp.route('/<int:id>/add-member', methods=['POST'])
@login_required
@office_required
def add_member(id):
    """Add an existing person as a member of this church."""
    church = Church.query.get_or_404(id)
    
    # Check modification permissions (allow super admins to edit all)
    if not current_user.is_super_admin() and church.office_id != current_user.office_id:
        flash('You do not have permission to modify this church', 'danger')
        return redirect(url_for('churches.index'))
    
    person_id = request.form.get('person_id')
    church_role = request.form.get('church_role')
    set_primary = request.form.get('set_primary') == 'true'
    
    if not person_id:
        flash('No person selected', 'danger')
        return redirect(url_for('churches.show', id=church.id))
    
    # Verify the person exists
    person = Person.query.get(person_id)
    
    if not person:
        flash('Person not found', 'danger')
        return redirect(url_for('churches.show', id=church.id))
    
    # Check if person is already a member
    if person.church_id == church.id:
        # Just update the role if provided
        if church_role:
            person.church_role = church_role
            db.session.commit()
            flash(f"{person.full_name}'s role updated to {church_role}", 'success')
    else:
        # Add person to this church
        person.church_id = church.id
        if church_role:
            person.church_role = church_role
        
        db.session.commit()
        flash(f'{person.full_name} added as a member of {church.name}', 'success')
    
    # Set as primary contact if requested
    if set_primary:
        church.main_contact_id = person.id
        db.session.commit()
        flash(f'{person.full_name} set as primary contact for {church.name}', 'success')
    
    return redirect(url_for('churches.show', id=church.id))

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
        ('missions_pastor_first_name', 'Mission Pastor'),
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
                
                # Remove fields that don't exist in the Church model
                if 'tags' in church_data:
                    church_data.pop('tags')
                
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

@churches_bp.route('/search', methods=['GET'])
@login_required
@office_required
def search():
    """Search churches based on query parameters"""
    search_term = request.args.get('q', '').strip().upper()
    
    # Start with a base query for Church
    query = Church.query
    
    # Apply text search filter if provided
    if search_term:
        # First check if the search term matches any pipeline stage or denomination
        pipeline_match = False
        denomination_match = False
        
        # Check for pipeline stage match
        pipeline_stages = ['PROMOTION', 'INFORMATION', 'INVITATION', 'CONFIRMATION', 'EN42', 'AUTOMATION']
        for stage in pipeline_stages:
            if stage in search_term:
                query = query.join(PipelineContact, Church.id == PipelineContact.contact_id) \
                           .join(PipelineStage, PipelineContact.current_stage_id == PipelineStage.id) \
                           .join(Pipeline, Pipeline.id == PipelineContact.pipeline_id) \
                           .filter(Pipeline.is_main_pipeline == True) \
                           .filter(PipelineStage.name == stage)
                pipeline_match = True
                break
        
        # Check for denomination match
        denominations = ['BAPTIST', 'CATHOLIC', 'LUTHERAN', 'METHODIST', 'NON-DENOMINATIONAL', 'PRESBYTERIAN']
        for denomination in denominations:
            if denomination in search_term:
                query = query.filter(Church.denomination.ilike(f'%{denomination}%'))
                denomination_match = True
                break
        
        # If no pipeline or denomination match, search other fields
        if not pipeline_match and not denomination_match:
            query = query.filter(
                or_(
                    Church.name.ilike(f'%{search_term}%'),
                    Church.email.ilike(f'%{search_term}%'),
                    Church.phone.ilike(f'%{search_term}%'),
                    Church.location.ilike(f'%{search_term}%')
                )
            )
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        query = query.filter(Church.office_id == current_user.office_id)
    
    # Get results with increased limit
    churches = query.limit(50).all()
    
    # Debug output
    print(f"Search query: {search_term}")
    print(f"Found {len(churches)} churches matching criteria")
    
    # Convert churches to dictionaries with all necessary fields for display
    church_dicts = []
    for church in churches:
        church_dict = church.to_dict()
        
        # Get the main pipeline stage for the church
        main_pipeline = Pipeline.query.filter_by(
            pipeline_type='church',
            is_main_pipeline=True,
            office_id=church.office_id
        ).first()
        
        if main_pipeline:
            pipeline_contact = PipelineContact.query.filter_by(
                contact_id=church.id,
                pipeline_id=main_pipeline.id
            ).first()
            
            if pipeline_contact and pipeline_contact.current_stage:
                church_dict['pipeline_stage'] = pipeline_contact.current_stage.name
            else:
                church_dict['pipeline_stage'] = 'Not in Pipeline'
        else:
            church_dict['pipeline_stage'] = 'No Pipeline Found'
        
        # Ensure main contact information is included
        if church.main_contact_id:
            main_contact = Person.query.get(church.main_contact_id)
            if main_contact:
                church_dict['main_contact'] = {
                    'id': main_contact.id,
                    'full_name': f"{main_contact.first_name} {main_contact.last_name}"
                }
        
        church_dicts.append(church_dict)
    
    return jsonify(church_dicts) 