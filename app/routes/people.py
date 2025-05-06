from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.models.person import Person
from app.models.church import Church
from app.models.communication import Communication
from app.models.task import Task
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.forms.person import PersonForm
from app.extensions import db
from app.utils.decorators import office_required
from datetime import datetime
import os
import pandas as pd
import uuid

people_bp = Blueprint('people', __name__, template_folder='../templates/people')

@people_bp.route('/')
@login_required
@office_required
def index():
    """Show list of all people with pagination and search functionality."""
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of records per page
    search_query = request.args.get('q', '')
    
    # Create base query
    query = Person.query
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        query = query.filter_by(office_id=current_user.office_id)
    
    # Apply search filter if provided
    if search_query:
        search_term = f'%{search_query}%'
        query = query.filter(
            or_(
                Person.first_name.ilike(search_term),
                Person.last_name.ilike(search_term),
                Person.email.ilike(search_term),
                Person.phone.ilike(search_term),
                Person.people_pipeline.ilike(search_term)
            )
        )
    
    # Using pagination to limit the number of records fetched
    pagination = query.order_by(Person.last_name, Person.first_name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    people = pagination.items
    
    # Get the main pipeline for proper pipeline stages
    # Check for both 'person' and 'people' pipeline types since both are used
    main_pipeline = Pipeline.query.filter(
        Pipeline.is_main_pipeline,
        Pipeline.pipeline_type.in_(['person', 'people'])
    ).first()
    
    if main_pipeline:
        # Get pipeline stages for all people in the current page
        person_ids = [p.id for p in people]
        pipeline_contacts = PipelineContact.query.filter(
            PipelineContact.contact_id.in_(person_ids),
            PipelineContact.pipeline_id == main_pipeline.id
        ).all()
        
        # Create a mapping of person_id to pipeline stage
        pipeline_stages = {}
        for pc in pipeline_contacts:
            if pc.current_stage:
                pipeline_stages[pc.contact_id] = pc.current_stage.name
        
        # Attach pipeline stage to each person object
        for person in people:
            person.current_pipeline_stage = pipeline_stages.get(person.id, 'Not in Pipeline')
    
    # Pass data to template with pagination info
    return render_template('people/list.html', 
                          people=people,
                          pagination=pagination,
                          search_query=search_query,
                          page_title="People Management")

@people_bp.route('/new', methods=['GET', 'POST'])
@login_required
@office_required
def create():
    """Create a new person."""
    form = PersonForm()
    
    # Get church choices for the form
    if current_user.is_super_admin():
        form.church_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Church.query.all()]
    else:
        form.church_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Church.query.filter_by(office_id=current_user.office_id).all()]
    
    if form.validate_on_submit():
        person = Person(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            country=form.country.data,
            title=form.title.data,
            marital_status=form.marital_status.data,
            spouse_first_name=form.spouse_first_name.data,
            spouse_last_name=form.spouse_last_name.data,
            date_of_birth=form.date_of_birth.data,
            church_role=form.church_role.data,
            is_primary_contact=form.is_primary_contact.data,
            virtuous=form.virtuous.data,
            info_given=form.info_given.data,
            desired_service=form.desired_service.data,
            reason_closed=form.reason_closed.data,
            date_closed=form.date_closed.data,
            tags=form.tags.data if hasattr(form, 'tags') else None,
            notes=form.notes.data,
            type='person',  # Explicitly set type for the polymorphic model
            office_id=current_user.office_id,
            user_id=current_user.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Set status based on pipeline status
        if form.pipeline_status.data:
            person.status = form.pipeline_status.data
        else:
            person.status = 'active'  # Default status
        
        # Handle church relationship
        if form.church_id.data and form.church_id.data != 0:
            person.church_id = form.church_id.data
        
        # Handle profile image upload
        if form.profile_image.data:
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join('app', 'static', 'uploads', 'profiles')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            filename = f"{uuid.uuid4()}.{form.profile_image.data.filename.split('.')[-1]}"
            filepath = os.path.join(upload_dir, filename)
            
            # Save the file
            form.profile_image.data.save(filepath)
            
            # Store the path in the database
            person.profile_image = f"/static/uploads/profiles/{filename}"
        
        db.session.add(person)
        db.session.commit()
        
        # Handle main pipeline assignment
        if form.people_pipeline.data:
            # Get the main pipeline for people
            main_pipeline = Pipeline.query.filter_by(
                pipeline_type='person',
                is_main_pipeline=True,
                office_id=person.office_id
            ).first()
            
            if main_pipeline:
                # Find the selected stage
                selected_stage = None
                for stage in main_pipeline.stages:
                    if stage.name == form.people_pipeline.data:
                        selected_stage = stage
                        break
                
                if not selected_stage:
                    # No matching stage found, try to find by the stage value directly
                    stage_value = form.people_pipeline.data
                    for stage in main_pipeline.stages:
                        if stage.name.upper() == stage_value.upper():
                            selected_stage = stage
                            break
                
                if selected_stage:
                    # Add person to pipeline
                    pipeline_contact = PipelineContact(
                        contact_id=person.id,
                        pipeline_id=main_pipeline.id,
                        current_stage_id=selected_stage.id,
                        entered_at=datetime.now()
                    )
                    db.session.add(pipeline_contact)
        
        flash('Person created successfully', 'success')
        return redirect(url_for('people.show', id=person.id))
    
    return render_template('people/form.html', form=form)

@people_bp.route('/<int:id>')
@login_required
@office_required
def show(id):
    """Show a specific person."""
    person = Person.query.get_or_404(id)
    
    # Check permissions (allow super admins to view any person)
    if not current_user.is_super_admin() and person.office_id != current_user.office_id:
        flash('You do not have permission to view this person', 'danger')
        return redirect(url_for('people.index'))
    
    # Get person's church if associated
    church = None
    if person.church_id:
        church = Church.query.get(person.church_id)
    
    # Get communications and tasks for this person
    communications = Communication.query.filter_by(person_id=person.id).order_by(Communication.date.desc()).all()
    tasks = Task.query.filter_by(person_id=person.id).order_by(Task.due_date).all()
    
    return render_template('people/view.html', 
                          person=person, 
                          church=church,
                          communications=communications,
                          tasks=tasks,
                          page_title=f"{person.first_name} {person.last_name}")

@people_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@office_required
def edit(id):
    """Edit a specific person."""
    person = Person.query.get_or_404(id)
    
    # Check permissions (allow super admins to edit any person)
    if not current_user.is_super_admin() and person.office_id != current_user.office_id:
        flash('You do not have permission to edit this person', 'danger')
        return redirect(url_for('people.index'))
    
    form = PersonForm(obj=person)
    
    # Get church choices for the form
    if current_user.is_super_admin():
        form.church_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Church.query.all()]
    else:
        form.church_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Church.query.filter_by(office_id=current_user.office_id).all()]
    
    if form.validate_on_submit():
        person.first_name = form.first_name.data
        person.last_name = form.last_name.data
        person.email = form.email.data
        person.phone = form.phone.data
        person.address = form.address.data
        person.city = form.city.data
        person.state = form.state.data
        person.zip_code = form.zip_code.data
        person.country = form.country.data
        person.notes = form.notes.data
        
        # Additional form fields that were missing
        person.title = form.title.data
        person.marital_status = form.marital_status.data
        person.spouse_first_name = form.spouse_first_name.data
        person.spouse_last_name = form.spouse_last_name.data
        person.date_of_birth = form.date_of_birth.data
        person.church_role = form.church_role.data
        person.is_primary_contact = form.is_primary_contact.data
        person.virtuous = form.virtuous.data
        person.info_given = form.info_given.data
        person.desired_service = form.desired_service.data
        person.reason_closed = form.reason_closed.data
        person.date_closed = form.date_closed.data
        person.tags = form.tags.data if hasattr(form, 'tags') else None
        
        # Update status based on pipeline status
        if form.pipeline_status.data:
            person.status = form.pipeline_status.data
        else:
            person.status = 'active'  # Default status
            
        person.updated_at = datetime.now()
        
        # Handle church relationship
        if form.church_id.data and form.church_id.data != 0:
            person.church_id = form.church_id.data
        else:
            person.church_id = None
        
        # Handle profile image upload
        if form.profile_image.data:
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join('app', 'static', 'uploads', 'profiles')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            filename = f"{uuid.uuid4()}.{form.profile_image.data.filename.split('.')[-1]}"
            filepath = os.path.join(upload_dir, filename)
            
            # Delete old profile image if exists
            if person.profile_image:
                old_filepath = os.path.join('app', person.profile_image.lstrip('/'))
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
            
            # Save the new file
            form.profile_image.data.save(filepath)
            
            # Store the path in the database
            person.profile_image = f"/static/uploads/profiles/{filename}"
        
        # Handle main pipeline assignment
        if form.people_pipeline.data:
            # Get the main pipeline for people
            main_pipeline = Pipeline.query.filter_by(
                pipeline_type='person',
                is_main_pipeline=True,
                office_id=person.office_id
            ).first()
            
            if main_pipeline:
                # Find the selected stage
                selected_stage = None
                for stage in main_pipeline.stages:
                    if stage.name == form.people_pipeline.data:
                        selected_stage = stage
                        break
                
                if not selected_stage:
                    # No matching stage found, try to find by the stage value directly
                    stage_value = form.people_pipeline.data
                    for stage in main_pipeline.stages:
                        if stage.name.upper() == stage_value.upper():
                            selected_stage = stage
                            break
                
                if selected_stage:
                    # Check if person is already in this pipeline
                    pipeline_contact = PipelineContact.query.filter_by(
                        contact_id=person.id,
                        pipeline_id=main_pipeline.id
                    ).first()
                    
                    if pipeline_contact:
                        # Update existing pipeline contact
                        pipeline_contact.move_to_stage(
                            selected_stage.id, 
                            user_id=current_user.id,
                            notes="Updated from person edit form"
                        )
                    else:
                        # Add person to pipeline
                        pipeline_contact = PipelineContact(
                            contact_id=person.id,
                            pipeline_id=main_pipeline.id,
                            current_stage_id=selected_stage.id,
                            entered_at=datetime.now()
                        )
                        db.session.add(pipeline_contact)
        
        db.session.commit()
        
        flash('Person updated successfully', 'success')
        return redirect(url_for('people.show', id=person.id))
    
    return render_template('people/form.html', form=form, person=person)

@people_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@office_required
def delete(id):
    """Delete a specific person."""
    person = Person.query.get_or_404(id)
    
    # Check permissions (allow super admins to delete any person)
    if not current_user.is_super_admin() and person.office_id != current_user.office_id:
        flash('You do not have permission to delete this person', 'danger')
        return redirect(url_for('people.index'))
    
    # Delete profile image if exists
    if person.profile_image:
        filepath = os.path.join('app', person.profile_image.lstrip('/'))
        if os.path.exists(filepath):
            os.remove(filepath)
    
    # Delete the person
    db.session.delete(person)
    db.session.commit()
    
    flash('Person deleted successfully', 'success')
    return redirect(url_for('people.index'))

@people_bp.route('/add_note/<int:id>', methods=['POST'])
@login_required
@office_required
def add_note(id):
    """Add a note to a person."""
    person = Person.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_super_admin() and person.office_id != current_user.office_id:
        flash('You do not have permission to add notes to this person', 'danger')
        return redirect(url_for('people.index'))
    
    content = request.form.get('content', '')
    
    if content:
        # Add note to existing notes or create new notes
        if person.notes:
            person.notes = f"{person.notes}\n\n{datetime.now().strftime('%Y-%m-%d %H:%M')} - {current_user.full_name}:\n{content}"
        else:
            person.notes = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} - {current_user.full_name}:\n{content}"
        
        person.updated_at = datetime.now()
        db.session.commit()
        
        flash('Note added successfully', 'success')
    else:
        flash('Note cannot be empty', 'warning')
    
    return redirect(url_for('people.show', id=person.id))

@people_bp.route('/import', methods=['GET', 'POST'])
@login_required
@office_required
def import_people():
    """Import people from CSV or Excel file."""
    from app.forms.import_form import ImportForm, FieldMappingForm
    
    import_form = ImportForm()
    mapping_form = FieldMappingForm()
    
    if request.method == 'POST':
        if 'submit_file' in request.form and import_form.validate_on_submit():
            file = import_form.file.data
            filename = f"temp_{uuid.uuid4()}.csv"
            filepath = os.path.join('temp', filename)
            
            # Create temp directory if it doesn't exist
            os.makedirs('temp', exist_ok=True)
            
            # Save the uploaded file
            file.save(filepath)
            
            try:
                # Try to read the file
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(filepath)
                elif file.filename.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(filepath)
                else:
                    os.remove(filepath)
                    flash('Unsupported file format. Please upload a CSV or Excel file.', 'danger')
                    return redirect(url_for('people.import_people'))
                
                # Store columns in session for mapping form
                columns = df.columns.tolist()
                session['import_columns'] = columns
                session['import_filepath'] = filepath
                
                # Pre-populate mapping form with best guesses
                column_map = {}
                for field in mapping_form:
                    if field.name not in ('csrf_token', 'submit'):
                        best_match = None
                        field_name = field.name.replace('_mapping', '')
                        
                        # Look for exact matches
                        for col in columns:
                            if col.lower().replace(' ', '_') == field_name.lower():
                                best_match = col
                                break
                        
                        # Look for partial matches if no exact match found
                        if not best_match:
                            for col in columns:
                                if field_name.lower() in col.lower():
                                    best_match = col
                                    break
                        
                        if best_match:
                            column_map[field.name] = best_match
                
                return render_template('people/import_mapping.html', 
                                    form=mapping_form,
                                    columns=columns,
                                    column_map=column_map,
                                    page_title="Map Import Fields")
            
            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                flash(f'Error reading file: {str(e)}', 'danger')
                return redirect(url_for('people.import_people'))
        
        elif 'submit_mapping' in request.form and mapping_form.validate_on_submit():
            filepath = session.get('import_filepath')
            
            if not filepath or not os.path.exists(filepath):
                flash('Import file not found. Please upload again.', 'danger')
                return redirect(url_for('people.import_people'))
            
            try:
                # Read the file
                if filepath.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)
                
                # Get field mappings
                mappings = {}
                for field in mapping_form:
                    if field.name.endswith('_mapping') and field.data:
                        field_name = field.name.replace('_mapping', '')
                        mappings[field_name] = field.data
                
                # Process import
                imported = 0
                updated = 0
                skipped = 0
                errors = 0
                
                for _, row in df.iterrows():
                    try:
                        # Check if person exists by email
                        email = row[mappings.get('email')] if mappings.get('email') else None
                        
                        if email and isinstance(email, str) and Person.query.filter_by(email=email, office_id=current_user.office_id).first():
                            # Update existing person
                            person = Person.query.filter_by(email=email, office_id=current_user.office_id).first()
                            
                            # Update fields
                            if mappings.get('first_name') and not pd.isna(row[mappings['first_name']]):
                                person.first_name = row[mappings['first_name']]
                            
                            if mappings.get('last_name') and not pd.isna(row[mappings['last_name']]):
                                person.last_name = row[mappings['last_name']]
                            
                            if mappings.get('phone') and not pd.isna(row[mappings['phone']]):
                                person.phone = str(row[mappings['phone']])
                            
                            if mappings.get('address') and not pd.isna(row[mappings['address']]):
                                person.address = row[mappings['address']]
                            
                            if mappings.get('city') and not pd.isna(row[mappings['city']]):
                                person.city = row[mappings['city']]
                            
                            if mappings.get('state') and not pd.isna(row[mappings['state']]):
                                person.state = row[mappings['state']]
                            
                            if mappings.get('zipcode') and not pd.isna(row[mappings['zipcode']]):
                                person.zip_code = str(row[mappings['zipcode']])
                            
                            if mappings.get('country') and not pd.isna(row[mappings['country']]):
                                person.country = row[mappings['country']]
                            
                            if mappings.get('notes') and not pd.isna(row[mappings['notes']]):
                                person.notes = row[mappings['notes']]
                            
                            person.updated_at = datetime.now()
                            updated += 1
                        
                        elif mappings.get('first_name') and mappings.get('last_name'):
                            # Create new person
                            first_name = row[mappings['first_name']] if not pd.isna(row[mappings['first_name']]) else ''
                            last_name = row[mappings['last_name']] if not pd.isna(row[mappings['last_name']]) else ''
                            
                            if first_name or last_name:
                                person = Person(
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=email if email and not pd.isna(email) else None,
                                    phone=str(row[mappings['phone']]) if mappings.get('phone') and not pd.isna(row[mappings['phone']]) else None,
                                    address=row[mappings['address']] if mappings.get('address') and not pd.isna(row[mappings['address']]) else None,
                                    city=row[mappings['city']] if mappings.get('city') and not pd.isna(row[mappings['city']]) else None,
                                    state=row[mappings['state']] if mappings.get('state') and not pd.isna(row[mappings['state']]) else None,
                                    zip_code=str(row[mappings['zipcode']]) if mappings.get('zipcode') and not pd.isna(row[mappings['zipcode']]) else None,
                                    country=row[mappings['country']] if mappings.get('country') and not pd.isna(row[mappings['country']]) else None,
                                    notes=row[mappings['notes']] if mappings.get('notes') and not pd.isna(row[mappings['notes']]) else None,
                                    status='active',
                                    type='person',
                                    office_id=current_user.office_id,
                                    user_id=current_user.id,
                                    created_at=datetime.now(),
                                    updated_at=datetime.now()
                                )
                                
                                db.session.add(person)
                                imported += 1
                            else:
                                skipped += 1
                        else:
                            skipped += 1
                    
                    except Exception:
                        errors += 1
                        continue
                
                # Commit all changes
                db.session.commit()
                
                # Clean up
                if os.path.exists(filepath):
                    os.remove(filepath)
                if 'import_filepath' in session:
                    session.pop('import_filepath')
                if 'import_columns' in session:
                    session.pop('import_columns')
                
                flash(f'Import completed: {imported} imported, {updated} updated, {skipped} skipped, {errors} errors', 'success')
                return redirect(url_for('people.index'))
            
            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                flash(f'Error during import: {str(e)}', 'danger')
                return redirect(url_for('people.import_people'))
    
    return render_template('people/import.html', 
                          form=import_form,
                          page_title="Import People")

@people_bp.route('/search', methods=['GET'])
@login_required
@office_required
def search():
    """Search people based on query parameters"""
    search_term = request.args.get('q', '').strip().upper()
    
    # Start with a base query for Person
    query = Person.query
    
    # Apply text search filter if provided
    if search_term:
        # First check if the search term matches any pipeline stage or priority
        pipeline_match = False
        priority_match = False
        
        # Check for pipeline stage match
        pipeline_stages = ['PROMOTION', 'INFORMATION', 'INVITATION', 'CONFIRMATION', 'AUTOMATION']
        for stage in pipeline_stages:
            if stage in search_term:
                query = query.outerjoin(PipelineContact, Person.id == PipelineContact.contact_id) \
                           .outerjoin(PipelineStage, PipelineContact.current_stage_id == PipelineStage.id) \
                           .filter(PipelineStage.name == stage)
                pipeline_match = True
                break
        
        # Check for priority match
        priorities = ['URGENT', 'HIGH', 'MEDIUM', 'LOW']
        for priority in priorities:
            if priority in search_term:
                query = query.filter(Person.priority == priority)
                priority_match = True
                break
        
        # If no pipeline or priority match, search other fields
        if not pipeline_match and not priority_match:
            query = query.filter(
                or_(
                    Person.first_name.ilike(f'%{search_term}%'),
                    Person.last_name.ilike(f'%{search_term}%'),
                    Person.email.ilike(f'%{search_term}%'),
                    Person.phone.ilike(f'%{search_term}%')
                )
            )
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        query = query.filter(Person.office_id == current_user.office_id)
    
    # Get results and ensure we limit the query
    people = query.limit(50).all()
    
    # Debug output
    print(f"Search query: {search_term}")
    print(f"Found {len(people)} people matching criteria")
    
    # Convert people to dictionaries with all necessary fields for display
    people_dicts = []
    for person in people:
        person_dict = person.to_dict()
        
        # Get the main pipeline stage for the person
        # Check for both 'person' and 'people' pipeline types since both are used
        main_pipeline = Pipeline.query.filter(
            Pipeline.is_main_pipeline,
            Pipeline.pipeline_type.in_(['person', 'people']),
            Pipeline.office_id == person.office_id
        ).first()
        
        if main_pipeline:
            pipeline_contact = PipelineContact.query.filter_by(
                contact_id=person.id,
                pipeline_id=main_pipeline.id
            ).first()
            
            if pipeline_contact and pipeline_contact.current_stage:
                person_dict['people_pipeline'] = pipeline_contact.current_stage.name
        
        # Make sure we have all fields that the UI template needs
        person_dict['full_name'] = f"{person.first_name} {person.last_name}"
        person_dict['role'] = getattr(person, 'church_role', 'Contact')
        
        people_dicts.append(person_dict)
    
    return jsonify(people_dicts) 