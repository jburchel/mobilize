from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file, Response
from flask_login import login_required, current_user
from sqlalchemy import or_, text
from sqlalchemy.orm import joinedload
from datetime import datetime
import os
import pandas as pd
import uuid

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
    # Simple query to get all people without complex joins
    try:
        if current_user.is_super_admin():
            people = Person.query.order_by(Person.last_name, Person.first_name).all()
        else:
            people = Person.query.filter_by(office_id=current_user.office_id).order_by(Person.last_name, Person.first_name).all()
        
        # Set a default pipeline stage for display
        for person in people:
            if person.pipeline_stage:
                person.current_pipeline_stage = person.pipeline_stage
            else:
                person.current_pipeline_stage = 'Not in Pipeline'
        
        return render_template('people/list.html', 
                            people=people,
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
                birthday=form.date_of_birth.data,
                church_role=form.church_role.data,
                is_primary_contact=form.is_primary_contact.data,
                virtuous=form.virtuous.data,
                info_given=form.info_given.data,
                desired_service=form.desired_service.data,
                reason_closed=form.reason_closed.data,
                date_closed=form.date_closed.data,
                tags=form.tags.data if hasattr(form, 'tags') else None,
                notes=form.notes.data,
                assigned_to=form.assigned_to.data if form.assigned_to.data else current_user.username,
                priority=form.priority.data,
                source=form.source.data,
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
            
            # CRITICAL FIX: Set pipeline_stage field directly first
            if form.people_pipeline.data:
                person.pipeline_stage = form.people_pipeline.data
                # Also set the people_pipeline field for backward compatibility
                person.people_pipeline = form.people_pipeline.data
                
            db.session.add(person)
            db.session.commit()
            
            # Simplified pipeline processing
            if form.people_pipeline.data:
                # Just log that we're skipping complex pipeline processing
                current_app.logger.info(f"Skipping complex pipeline processing for person {person.id}")
            
            flash('Person created successfully', 'success')
            return redirect(url_for('people.show', id=person.id))
        
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
        
        page_title = f"{person.first_name} {person.last_name}"
        
        return render_template('people/view.html', 
                            person=person,
                            pipeline_info=pipeline_info,
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
        person = Person.query.get_or_404(id)
        
        # Check permissions (allow super admins to delete any person)
        if not current_user.is_super_admin() and person.office_id != current_user.office_id:
            flash('You do not have permission to delete this person', 'danger')
            return redirect(url_for('people.index'))
        
        # Check for CSRF token
        if 'csrf_token' not in request.form:
            flash('CSRF token missing', 'danger')
            return redirect(url_for('people.index'))
        
        # Delete profile image if exists
        if person.profile_image:
            filepath = os.path.join('app', person.profile_image.lstrip('/'))
            if os.path.exists(filepath):
                os.remove(filepath)
        
        # First, remove any pipeline associations
        pipeline_contacts = PipelineContact.query.filter_by(contact_id=person.id).all()
        for pc in pipeline_contacts:
            db.session.delete(pc)
        
        # If person is a main contact for any churches, remove that relationship
        churches = Church.query.filter_by(main_contact_id=person.id).all()
        for church in churches:
            church.main_contact_id = None
        
        # Delete the person
        db.session.delete(person)
        db.session.commit()
        
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
