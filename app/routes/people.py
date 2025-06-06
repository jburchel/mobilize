from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file, make_response
from flask_login import login_required, current_user
from sqlalchemy import or_, text
from sqlalchemy.orm import joinedload
from datetime import datetime
import os
import pandas as pd
import uuid
import time
import io

from app.models.person import Person
from app.models.church import Church
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.forms.person import PersonForm
from app.extensions import db
from app.utils.decorators import office_required

# Create blueprint
people_bp = Blueprint('people', __name__)

@people_bp.route('/')
@login_required
@office_required
def index():
    """List all people."""
    # Get the 'assigned' parameter from the request
    assigned_filter = request.args.get('assigned', '')
    show_assigned = assigned_filter == 'me'
    
    current_app.logger.info(f"Index route called with assigned_filter={assigned_filter}, show_assigned={show_assigned}")
    
    # Simple query to get all people without complex joins
    try:
        # Start with a base query
        if current_user.is_super_admin():
            query = Person.query
        else:
            query = Person.query.filter_by(office_id=current_user.office_id)
        
        # Apply assigned filter if requested
        if show_assigned:
            current_app.logger.info(f"Filtering people assigned to {current_user.username}")
            # Try different ways to match the assigned_to field
            # First, check if assigned_to matches username
            query = query.filter(Person.assigned_to == current_user.username)
            
            # Log the SQL query for debugging
            current_app.logger.info(f"SQL Query: {query}")
        
        # Get the results ordered by name
        people = query.order_by(Person.last_name, Person.first_name).all()
        current_app.logger.info(f"Found {len(people)} people matching the criteria")
        
        # Preload pipeline data to avoid N+1 query problem
        try:
            # First, get the main pipeline
            main_pipeline = Pipeline.query.filter_by(pipeline_type="people", is_main_pipeline=True).first()
            if main_pipeline:
                # Get all pipeline contacts for these people in one query
                person_ids = [person.id for person in people]
                pipeline_contacts = PipelineContact.query.filter(
                    PipelineContact.contact_id.in_(person_ids),
                    PipelineContact.pipeline_id == main_pipeline.id
                ).all()
                
                # Create a lookup dictionary for quick access
                contact_stage_map = {}
                stage_ids = set()
                for pc in pipeline_contacts:
                    contact_stage_map[pc.contact_id] = pc.current_stage_id
                    if pc.current_stage_id:
                        stage_ids.add(pc.current_stage_id)
                
                # Get all stages in one query
                stages = PipelineStage.query.filter(PipelineStage.id.in_(stage_ids)).all()
                stage_name_map = {stage.id: stage.name for stage in stages}
                
                # Create a dictionary to store pipeline stage data
                pipeline_stages = {}
                for person in people:
                    if person.id in contact_stage_map and contact_stage_map[person.id] in stage_name_map:
                        pipeline_stages[person.id] = stage_name_map[contact_stage_map[person.id]]
                    else:
                        pipeline_stages[person.id] = person.pipeline_stage or 'Not in Pipeline'
        except Exception as e:
            current_app.logger.error(f"Error preloading pipeline data: {str(e)}")
            # Fall back to using the stored pipeline_stage
            pipeline_stages = {}
            for person in people:
                pipeline_stages[person.id] = person.pipeline_stage or 'Not in Pipeline'
        
        return render_template('people/list.html', 
                            people=people,
                            pipeline_stages=pipeline_stages,
                            show_assigned=show_assigned,
                            page_title='People')
    except Exception as e:
        current_app.logger.error(f"Error listing people: {str(e)}")
        flash(f"Error loading people: {str(e)}", 'danger')
        return render_template('people/list.html', 
                            people=[],
                            page_title='People')

@people_bp.route('/new', methods=['GET', 'POST'])
@login_required
@office_required
def create():
    """Create a new person."""
    try:
        form = PersonForm()
        
        # Get church choices for the form
        if current_user.is_super_admin():
            form.church_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Church.query.all()]
        else:
            form.church_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Church.query.filter_by(office_id=current_user.office_id).all()]
        
        if form.validate_on_submit():
            current_app.logger.info("Creating new person using direct SQL approach")
            
            # Handle profile image upload first
            profile_image_path = None
            if form.profile_image.data:
                try:
                    # Create upload directory if it doesn't exist
                    upload_dir = os.path.join('app', 'static', 'uploads', 'profiles')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Generate unique filename
                    filename = f"{uuid.uuid4()}.{form.profile_image.data.filename.split('.')[-1]}"
                    filepath = os.path.join(upload_dir, filename)
                    
                    # Save the file
                    form.profile_image.data.save(filepath)
                    
                    # Store the path
                    profile_image_path = f"/static/uploads/profiles/{filename}"
                    current_app.logger.info(f"Saved profile image to {filepath}")
                except Exception as img_error:
                    current_app.logger.error(f"Error saving profile image: {str(img_error)}")
            
            # Set status based on pipeline status
            status = form.pipeline_status.data if form.pipeline_status.data else 'active'
            
            # Set assigned_to
            assigned_to = form.assigned_to.data if form.assigned_to.data else current_user.username
            
            # Handle church relationship
            church_id = form.church_id.data if form.church_id.data and form.church_id.data != 0 else None
            
            # Set pipeline stage and people_pipeline
            pipeline_stage = form.people_pipeline.data if form.people_pipeline.data else None
            people_pipeline = pipeline_stage  # Same value for both fields
            
            # Get tags
            tags = form.tags.data if hasattr(form, 'tags') and form.tags.data else None
            
            # First, insert into contacts table
            try:
                # Use direct SQL to insert into contacts table
                contacts_sql = text("""
                INSERT INTO contacts (
                    type, first_name, last_name, email, phone, address, city, state, zip_code, country,
                    notes, office_id, user_id, image, created_at, updated_at
                ) VALUES (
                    :type, :first_name, :last_name, :email, :phone, :address, :city, :state, :zip_code, :country,
                    :notes, :office_id, :user_id, :image, :created_at, :updated_at
                ) RETURNING id
                """)
                
                contacts_params = {
                    'type': 'person',
                    'first_name': form.first_name.data,
                    'last_name': form.last_name.data,
                    'email': form.email.data,
                    'phone': form.phone.data,
                    'address': form.address.data,
                    'city': form.city.data,
                    'state': form.state.data,
                    'zip_code': form.zip_code.data,
                    'country': form.country.data,
                    'notes': form.notes.data,
                    'office_id': current_user.office_id,
                    'user_id': current_user.id,
                    'image': profile_image_path,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                # Disable triggers to prevent recursive operations that cause stack depth issues
                db.session.execute(text("SET session_replication_role = 'replica'"))
                
                try:
                    # Execute the contacts insert and get the new ID
                    result = db.session.execute(contacts_sql, contacts_params)
                    contact_id = result.scalar()
                    
                    current_app.logger.info(f"Created new contact with ID {contact_id}")
                    
                    # Now insert into people table
                    people_sql = text("""
                    INSERT INTO people (
                        id, title, marital_status, spouse_first_name, spouse_last_name, birthday,
                        church_id, church_role, is_primary_contact, virtuous, info_given, desired_service,
                        reason_closed, date_closed, tags, assigned_to, priority, source, status,
                        people_pipeline, pipeline_stage
                    ) VALUES (
                        :id, :title, :marital_status, :spouse_first_name, :spouse_last_name, :birthday,
                        :church_id, :church_role, :is_primary_contact, :virtuous, :info_given, :desired_service,
                        :reason_closed, :date_closed, :tags, :assigned_to, :priority, :source, :status,
                        :people_pipeline, :pipeline_stage
                    )
                    """)
                    
                    people_params = {
                        'id': contact_id,
                        'title': form.title.data,
                        'marital_status': form.marital_status.data,
                        'spouse_first_name': form.spouse_first_name.data,
                        'spouse_last_name': form.spouse_last_name.data,
                        'birthday': form.date_of_birth.data,
                        'church_id': church_id,
                        'church_role': form.church_role.data,
                        'is_primary_contact': form.is_primary_contact.data,
                        'virtuous': form.virtuous.data,
                        'info_given': form.info_given.data,
                        'desired_service': form.desired_service.data,
                        'reason_closed': form.reason_closed.data,
                        'date_closed': form.date_closed.data,
                        'tags': tags,
                        'assigned_to': assigned_to,
                        'priority': form.priority.data,
                        'source': form.source.data,
                        'status': status,
                        'people_pipeline': people_pipeline,
                        'pipeline_stage': pipeline_stage
                    }
                    
                    # Execute the people insert
                    db.session.execute(people_sql, people_params)
                    
                    # Re-enable triggers
                    db.session.execute(text("SET session_replication_role = 'origin'"))
                    
                    # Commit the transaction
                    db.session.commit()
                    
                    current_app.logger.info(f"Successfully created new person with ID {contact_id}")
                    
                    flash('Person created successfully', 'success')
                    return redirect(url_for('people.show', id=contact_id))
                except Exception as e:
                    # Make sure to re-enable triggers even if there's an error
                    db.session.execute(text("SET session_replication_role = 'origin'"))
                    db.session.rollback()
                    current_app.logger.error(f"SQL Error creating person: {str(e)}")
                    flash(f"Error creating person: {str(e)}", 'danger')
                    return render_template('people/form.html', form=form)
                
            except Exception as sql_error:
                db.session.rollback()
                current_app.logger.error(f"SQL Error creating person: {str(sql_error)}")
                flash(f"Error creating person: {str(sql_error)}", 'danger')
                return render_template('people/form.html', form=form)
        
        return render_template('people/form.html', form=form)
    except Exception as e:
        current_app.logger.error(f"Error creating person: {str(e)}")
        flash(f"Error creating person: {str(e)}", 'danger')
        return render_template('people/form.html', form=form)

@people_bp.route('/<int:id>')
@login_required
@office_required
def show(id):
    """Show a specific person."""
    try:
        # Use a simple query without complex joins
        person = Person.query.get_or_404(id)
        
        # Check permissions (allow super admins to view all)
        if not current_user.is_super_admin() and person.office_id != current_user.office_id:
            flash('You do not have permission to view this person', 'danger')
            return redirect(url_for('people.index'))
        
        # Set pipeline stage for display
        if person.pipeline_stage:
            pipeline_info = {
                'current_stage': person.pipeline_stage,
                'pipeline_name': 'Main Pipeline'
            }
        else:
            pipeline_info = None
        
        # Load tasks associated with this person
        from app.models.task import Task
        tasks = Task.query.filter_by(person_id=id).all()
        
        # Get communications if any
        communications = []  # Placeholder for communications if implemented
        
        page_title = f"{person.first_name} {person.last_name}"
        
        return render_template('people/view.html', 
                            person=person,
                            pipeline_info=pipeline_info,
                            tasks=tasks,
                            communications=communications,
                            page_title=page_title)
    except Exception as e:
        current_app.logger.error(f"Error showing person {id}: {str(e)}")
        flash(f"Error loading person details: {str(e)}", 'danger')
        return redirect(url_for('people.index'))


@people_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@office_required
def edit(id):
    """Edit a specific person - using direct SQL to avoid stack depth issues."""
    try:
        # Get the person with minimal relationships loaded
        person = db.session.query(Person).filter(Person.id == id).first()
        if not person:
            flash('Person not found', 'danger')
            return redirect(url_for('people.index'))
        
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
            # Instead of updating the object directly, use a direct SQL update
            # to avoid triggering complex recursive operations
            try:
                # Collect all the data to update
                update_data = {
                    'first_name': form.first_name.data,
                    'last_name': form.last_name.data,
                    'email': form.email.data,
                    'phone': form.phone.data,
                    'address': form.address.data,
                    'city': form.city.data,
                    'state': form.state.data,
                    'zip_code': form.zip_code.data,
                    'country': form.country.data,
                    'notes': form.notes.data,
                    'title': form.title.data,
                    'marital_status': form.marital_status.data,
                    'spouse_first_name': form.spouse_first_name.data,
                    'spouse_last_name': form.spouse_last_name.data,
                    'birthday': form.date_of_birth.data,
                    'church_role': form.church_role.data,
                    'is_primary_contact': form.is_primary_contact.data,
                    'virtuous': form.virtuous.data,
                    'info_given': form.info_given.data,
                    'desired_service': form.desired_service.data,
                    'reason_closed': form.reason_closed.data,
                    'date_closed': form.date_closed.data,
                    'assigned_to': form.assigned_to.data,
                    'priority': form.priority.data,
                    'source': form.source.data,
                    'updated_at': datetime.now()
                }
                
                # Handle tags separately since it might be None
                if hasattr(form, 'tags'):
                    update_data['tags'] = form.tags.data
                
                # Update status based on pipeline status
                if form.pipeline_status.data:
                    update_data['status'] = form.pipeline_status.data
                else:
                    update_data['status'] = 'active'  # Default status
                
                # Handle church relationship
                if form.church_id.data and form.church_id.data != 0:
                    update_data['church_id'] = form.church_id.data
                else:
                    update_data['church_id'] = None
                
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
                    update_data['profile_image'] = f"/static/uploads/profiles/{filename}"
                
                # Simple pipeline stage update - just update the fields directly
                if form.people_pipeline.data:
                    update_data['people_pipeline'] = form.people_pipeline.data
                    update_data['pipeline_stage'] = form.people_pipeline.data
                
                
                # Use a direct SQL update to avoid triggering complex recursive operations
                # This bypasses the ORM and any triggers that might be causing the stack depth issue
                
                # Separate fields into contacts table and people table
                contacts_fields = [
                    'email', 'phone', 'address', 'city', 'state', 'zip_code', 'country', 'notes',
                    'updated_at'
                ]
                
                # Create separate update dictionaries for each table
                contacts_update = {}
                people_update = {}
                
                for key, value in update_data.items():
                    if key in contacts_fields:
                        contacts_update[key] = value
                    else:
                        people_update[key] = value
                
                # Update the contacts table first
                if contacts_update:
                    contacts_sql_parts = []
                    contacts_params = {}
                    
                    for key, value in contacts_update.items():
                        contacts_sql_parts.append(f"{key} = :{key}")
                        contacts_params[key] = value
                    
                    contacts_params['person_id'] = id
                    
                    contacts_sql = text(f"UPDATE contacts SET {', '.join(contacts_sql_parts)} WHERE id = (SELECT id FROM people WHERE id = :person_id)")
                    
                    
                    # Execute the contacts update with triggers disabled
                    # First, disable triggers
                    db.session.execute(text("SET session_replication_role = 'replica'"))
                    
                    # Execute the contacts update
                    db.session.execute(contacts_sql, contacts_params)
                # Update the people table next
                if people_update:
                    people_sql_parts = []
                    people_params = {}
                    
                    for key, value in people_update.items():
                        people_sql_parts.append(f"{key} = :{key}")
                        people_params[key] = value
                    
                    people_params['person_id'] = id
                    
                    people_sql = text(f"UPDATE people SET {', '.join(people_sql_parts)} WHERE id = :person_id")
                    
                    # Execute the people update
                    db.session.execute(people_sql, people_params)
                
                # Re-enable triggers
                db.session.execute(text("SET session_replication_role = 'origin'"))

                # Commit the transaction
                db.session.commit()

                # Log the success
                current_app.logger.info(f"Successfully updated person {id} using direct SQL")
                flash('Person updated successfully', 'success')
                return redirect(url_for('people.show', id=person.id))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"SQL Error updating person {id}: {str(e)}")
                flash(f'Error updating person: {str(e)}', 'danger')
                return render_template('people/form.html', form=form, person=person)
        
        return render_template('people/form.html', form=form, person=person)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error editing person {id}: {str(e)}")
        flash(f'Error updating person: {str(e)}', 'danger')
        return redirect(url_for('people.index'))
@people_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@office_required
def delete(id):
    """Delete a specific person."""
    try:
        # Start measuring execution time for performance monitoring
        start_time = time.time()
        current_app.logger.info(f"Starting deletion of person with ID {id}")
        
        # Get the person to delete
        person = Person.query.get_or_404(id)
        current_app.logger.info(f"Found person: {person.first_name} {person.last_name}")
        
        # Check permissions (allow super admins to delete any person)
        if not current_user.is_super_admin() and person.office_id != current_user.office_id:
            flash('You do not have permission to delete this person', 'danger')
            return redirect(url_for('people.index'))
        
        # Delete profile image files if they exist
        if hasattr(person, 'profile_image') and person.profile_image:
            filepath = os.path.join('app', person.profile_image.lstrip('/'))
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    current_app.logger.info(f"Deleted profile image: {filepath}")
                except OSError as e:
                    current_app.logger.warning(f"Failed to delete profile image: {str(e)}")
        elif hasattr(person, 'image') and person.image:
            filepath = os.path.join('app', person.image.lstrip('/'))
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    current_app.logger.info(f"Deleted image: {filepath}")
                except OSError as e:
                    current_app.logger.warning(f"Failed to delete image: {str(e)}")
        
        # 1. Update any churches where this person is the main contact
        try:
            # Use direct SQL to avoid SQLAlchemy ORM issues
            db.session.execute(
                text("UPDATE churches SET main_contact_id = NULL WHERE main_contact_id = :person_id"),
                {"person_id": id}
            )
            current_app.logger.info(f"Updated churches where person {id} was main contact")
        except Exception as e:
            current_app.logger.warning(f"Error updating churches: {str(e)}")
        
        # 2. Delete pipeline contacts for this person
        try:
            # Use direct SQL to avoid SQLAlchemy ORM issues
            db.session.execute(
                text("DELETE FROM pipeline_contacts WHERE contact_id = :person_id"),
                {"person_id": id}
            )
            current_app.logger.info(f"Deleted pipeline contacts for person {id}")
        except Exception as e:
            current_app.logger.warning(f"Error deleting pipeline contacts: {str(e)}")
        
        # 3. Delete the person
        person_name = f"{person.first_name} {person.last_name}"
        db.session.delete(person)
        db.session.commit()
        current_app.logger.info(f"Successfully deleted person {person_name}")
        
        # Log performance metrics
        execution_time = time.time() - start_time
        current_app.logger.info(f"Person deletion completed in {execution_time:.2f} seconds")
        
        flash('Person deleted successfully', 'success')
        return redirect(url_for('people.index'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting person: {str(e)}')
        flash(f'Error deleting person: {str(e)}', 'danger')
        return redirect(url_for('people.index'))

@people_bp.route('/<int:id>/add_note', methods=['POST'])
@login_required
@office_required
def add_note(id):
    """Add a note to a person."""
    try:
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
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error adding note to person: {str(e)}')
        flash(f'Error adding note: {str(e)}', 'danger')
        return redirect(url_for('people.show', id=person.id))

@people_bp.route('/<int:id>/update_notes', methods=['POST'])
@login_required
@office_required
def update_notes(id):
    """Update a person's notes."""
    try:
        person = Person.query.get_or_404(id)
        
        # Check permissions
        if not current_user.is_super_admin() and person.office_id != current_user.office_id:
            flash('You do not have permission to update notes for this person', 'danger')
            return redirect(url_for('people.index'))
        
        # Get the updated notes from the form
        notes = request.form.get('notes', '')
        
        # Update the person's notes
        person.notes = notes
        
        # Add an edit record at the bottom if notes were changed
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        edit_note = f"[Notes edited by {current_user.full_name} on {timestamp}]"
        
        if person.notes:
            person.notes = f"{person.notes}\n\n{edit_note}"
        else:
            person.notes = edit_note
        
        person.updated_at = datetime.now()
        db.session.commit()
        flash('Notes updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating notes: {str(e)}')
        flash(f'Error updating notes: {str(e)}', 'danger')
    
    return redirect(url_for('people.show', id=id))



@people_bp.route('/import', methods=['POST'])
@login_required
@office_required
def import_people():
    """Import people from a CSV file."""
    try:
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('people.index'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('people.index'))
        
        if not file.filename.endswith('.csv'):
            flash('File must be a CSV', 'danger')
            return redirect(url_for('people.index'))
        
        # Process CSV file
        df = pd.read_csv(file)
        
        # Check if header row should be skipped
        if 'header_row' not in request.form:
            # No header row, add default column names
            df.columns = ['first_name', 'last_name', 'email', 'phone', 'address', 'city', 'state', 'zip_code', 'country']
        
        # Process each row
        success_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Create a new person
                person = Person(
                    first_name=row.get('first_name', ''),
                    last_name=row.get('last_name', ''),
                    email=row.get('email', ''),
                    phone=row.get('phone', ''),
                    address=row.get('address', ''),
                    city=row.get('city', ''),
                    state=row.get('state', ''),
                    zip_code=row.get('zip_code', ''),
                    country=row.get('country', ''),
                    type='person',
                    office_id=current_user.office_id,
                    user_id=current_user.id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    status='active'
                )
                
                db.session.add(person)
                success_count += 1
            except Exception as e:
                current_app.logger.error(f"Error importing person: {str(e)}")
                error_count += 1
        
        db.session.commit()
        
        flash(f'Successfully imported {success_count} people. {error_count} errors.', 'success')
        return redirect(url_for('people.index'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error importing people: {str(e)}")
        flash(f'Error importing people: {str(e)}', 'danger')
        return redirect(url_for('people.index'))


@people_bp.route('/export', methods=['GET'])
@login_required
@office_required
def export_people():
    """Export people to CSV or Excel format."""
    try:
        # Get export format
        export_format = request.args.get('format', 'csv')
        include_notes = 'include_notes' in request.args
        # include_tasks parameter is reserved for future implementation
        # when task export functionality is added
        
        # Start with a base query
        if current_user.is_super_admin():
            query = Person.query
        else:
            query = Person.query.filter_by(office_id=current_user.office_id)
            
        # Get all people
        people = query.order_by(Person.last_name, Person.first_name).all()
        
        # Create a DataFrame from the people data
        data = []
        for person in people:
            person_data = {
                'ID': person.id,
                'First Name': person.first_name,
                'Last Name': person.last_name,
                'Email': person.email,
                'Phone': person.phone,
                'Address': person.address,
                'City': person.city,
                'State': person.state,
                'Zip': person.zip_code,
                'Country': person.country,
                'Pipeline Stage': person.pipeline_stage,
                'Priority': person.priority,
                'Assigned To': person.assigned_to,
                'Created': person.date_created.strftime('%Y-%m-%d') if person.date_created else '',
                'Last Updated': person.date_modified.strftime('%Y-%m-%d') if person.date_modified else ''
            }
            
            # Include notes if requested
            if include_notes and person.notes:
                person_data['Notes'] = person.notes
                
            data.append(person_data)
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export based on requested format
        if export_format == 'excel':
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='People', index=False)
                
            output.seek(0)
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'people_export_{timestamp}.xlsx'
            )
        else:  # Default to CSV
            # Create CSV in memory
            output = io.StringIO()
            df.to_csv(output, index=False)
            
            response = make_response(output.getvalue())
            response.headers['Content-Disposition'] = f'attachment; filename=people_export_{timestamp}.csv'
            response.headers['Content-Type'] = 'text/csv'
            return response
            
    except Exception as e:
        current_app.logger.error(f'Error exporting people: {str(e)}')
        flash(f'Error exporting people: {str(e)}', 'danger')
        return redirect(url_for('people.index'))

@people_bp.route('/search', methods=['GET'])
@login_required
@office_required
def search():
    """Search people based on query parameters"""
    # Log request details for debugging
    current_app.logger.info(f"Search request received: {request.args}")
    
    search_term = request.args.get('q', '').strip()
    pipeline_filter = request.args.get('pipeline', '')
    priority_filter = request.args.get('priority', '')
    assigned_filter = request.args.get('assigned', '')
    
    # Start with a base query for Person
    query = Person.query
    
    # Apply text search filter if provided
    if search_term:
        # Check if the search term matches any pipeline stage
        pipeline_match = False
        
        # Check for pipeline stage match
        pipeline_stages = ['PROMOTION', 'INFORMATION', 'INVITATION', 'CONFIRMATION', 'EN42', 'AUTOMATION']
        for stage in pipeline_stages:
            if stage.upper() in search_term.upper():
                query = query.filter(Person.people_pipeline == stage)
                pipeline_match = True
                break
        
        # If no pipeline match, search other fields
        if not pipeline_match:
            query = query.filter(
                or_(
                    Person.first_name.ilike(f'%{search_term}%'),
                    Person.last_name.ilike(f'%{search_term}%'),
                    Person.email.ilike(f'%{search_term}%'),
                    Person.phone.ilike(f'%{search_term}%'),
                    Person.address.ilike(f'%{search_term}%'),
                    Person.city.ilike(f'%{search_term}%'),
                    Person.state.ilike(f'%{search_term}%')
                )
            )
    
    # Apply pipeline filter if provided
    if pipeline_filter:
        query = query.filter(Person.people_pipeline == pipeline_filter)
    
    # Apply priority filter if provided
    if priority_filter:
        query = query.filter(Person.priority == priority_filter)
        
    # Apply assignment filter if requested
    if assigned_filter == 'me':
        query = query.filter(Person.assigned_to == current_user.full_name)
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        query = query.filter(Person.office_id == current_user.office_id)
    
    try:
        # Get results with increased limit
        people = query.limit(50).all()
        
        # Debug output
        current_app.logger.info(f"Search query: {search_term}")
        current_app.logger.info(f"Found {len(people)} people matching criteria")
        
        # Convert people to dictionaries with all necessary fields for display
        people_dicts = []
        for person in people:
            try:
                person_dict = person.to_dict()
                
                # Add pipeline stage information
                if person.people_pipeline:
                    person_dict['pipeline_stage'] = person.people_pipeline
                else:
                    person_dict['pipeline_stage'] = 'Not in Pipeline'
                
                # Add church information if available
                if person.church_id:
                    church = Church.query.get(person.church_id)
                    if church:
                        person_dict['church'] = {
                            'id': church.id,
                            'name': church.name
                        }
                
                people_dicts.append(person_dict)
            except Exception as e:
                current_app.logger.error(f"Error processing person {person.id}: {str(e)}")
                # Continue with next person
        
        # Log the response we're about to send
        current_app.logger.info(f"Returning {len(people_dicts)} people in search results")
        return jsonify(people_dicts)
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        return jsonify({"error": str(e)}), 500
