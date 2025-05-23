
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file, Response
from flask_login import login_required, current_user
from sqlalchemy import or_
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
    form = PersonForm()
    
    # Get church choices for the form
    if current_user.is_super_admin():
        form.church_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Church.query.all()]
    else:
        form.church_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Church.query.filter_by(office_id=current_user.office_id).all()]
    
    if form.validate_on_submit():
        try:
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
            
            # Set pipeline_stage field directly
            if form.people_pipeline.data:
                person.pipeline_stage = form.people_pipeline.data
                person.people_pipeline = form.people_pipeline.data
                
            db.session.add(person)
            db.session.commit()
            
            flash('Person created successfully', 'success')
            return redirect(url_for('people.show', id=person.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating person: {str(e)}")
            flash(f"Error creating person: {str(e)}", 'danger')
    
    return render_template('people/form.html', form=form)

@people_bp.route('/<int:id>')
@login_required
@office_required
def show(id):
    """Show a specific person."""
    try:
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
        
        return render_template('people/detail.html', 
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
    """Edit a specific person."""
    try:
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
            # Update basic fields
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
            person.title = form.title.data
            person.marital_status = form.marital_status.data
            person.spouse_first_name = form.spouse_first_name.data
            person.spouse_last_name = form.spouse_last_name.data
            person.birthday = form.date_of_birth.data
            person.church_role = form.church_role.data
            person.is_primary_contact = form.is_primary_contact.data
            person.virtuous = form.virtuous.data
            person.info_given = form.info_given.data
            person.desired_service = form.desired_service.data
            person.reason_closed = form.reason_closed.data
            person.date_closed = form.date_closed.data
            person.tags = form.tags.data if hasattr(form, 'tags') else None
            person.assigned_to = form.assigned_to.data
            person.priority = form.priority.data
            person.source = form.source.data
            
            # Update status based on pipeline status
            if form.pipeline_status.data:
                person.status = form.pipeline_status.data
            
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
            
            # Update pipeline fields directly
            if form.people_pipeline.data:
                person.people_pipeline = form.people_pipeline.data
                person.pipeline_stage = form.people_pipeline.data
            
            # Save changes
            db.session.commit()
            
            flash('Person updated successfully', 'success')
            return redirect(url_for('people.show', id=person.id))
        
        return render_template('people/form.html', form=form, person=person)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error editing person {id}: {str(e)}")
        flash(f'Error updating person: {str(e)}', 'danger')
        return redirect(url_for('people.index'))

@people_bp.route('/<int:id>', methods=['GET'])
@login_required
@office_required
def show(id):
    """Show a specific person."""
    try:
        person = Person.query.get_or_404(id)
        
        # Check permissions (allow super admins to view any person)
        if not current_user.is_super_admin() and person.office_id != current_user.office_id:
            flash('You do not have permission to view this person', 'danger')
            return redirect(url_for('people.index'))
        
        # Get pipeline information if available
        pipeline_info = None
        if hasattr(person, 'pipeline_stage') and person.pipeline_stage:
            person.current_pipeline_stage = person.pipeline_stage
        else:
            person.current_pipeline_stage = 'Not in Pipeline'
        
        return render_template('people/show.html', 
                            person=person,
                            page_title=f'{person.first_name} {person.last_name}')
    except Exception as e:
        current_app.logger.error(f"Error showing person {id}: {str(e)}")
        flash(f'Error loading person details: {str(e)}', 'danger')
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
