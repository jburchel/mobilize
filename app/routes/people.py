from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.person import Person
from app.models.church import Church
from app.models.user import User
from app.models.office import Office
from app.forms.person import PersonForm
from app.extensions import db
from datetime import datetime
import os

people_bp = Blueprint('people', __name__, template_folder='../templates/people')

@people_bp.route('/')
@people_bp.route('/list')
@login_required
def list():
    """Display list of people/contacts."""
    # Fetch people from database, filter by current user's office
    people = Person.query.filter_by(office_id=current_user.office_id).all()
    return render_template('people/list.html', 
                          people=people, 
                          page_title="People Management")

@people_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new person/contact."""
    form = PersonForm()

    # Populate select fields
    form.church_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Church.query.filter_by(office_id=current_user.office_id).all()]
    form.assigned_to.choices = [(0, 'Unassigned')] + [(u.id, f"{u.first_name} {u.last_name}") for u in User.query.filter_by(office_id=current_user.office_id).all()]
    
    if form.validate_on_submit():
        person = Person()
        
        # Populate basic info
        person.first_name = form.first_name.data
        person.last_name = form.last_name.data
        person.email = form.email.data
        person.phone = form.phone.data
        
        # Populate additional personal info
        person.spouse_first_name = form.spouse_first_name.data
        person.spouse_last_name = form.spouse_last_name.data
        
        # Populate address information
        person.address = form.address.data
        person.city = form.city.data
        person.state = form.state.data
        person.zip_code = form.zip_code.data
        person.country = form.country.data
        
        # Handle church & role
        if form.church_id.data and int(form.church_id.data) > 0:
            person.church_id = form.church_id.data
            # If this person is being set as primary contact, unset any other primary contacts
            if form.is_primary_contact.data:
                Person.query.filter_by(
                    church_id=person.church_id,
                    is_primary_contact=True
                ).update({'is_primary_contact': False})
        else:
            person.church_id = None
            form.is_primary_contact.data = False  # Can't be primary contact without a church
        person.church_role = form.church_role.data
        person.is_primary_contact = form.is_primary_contact.data
        
        # Populate pipeline information
        person.pipeline_status = form.pipeline_status.data
        person.pipeline_stage = form.pipeline_stage.data
        person.priority = form.priority.data
        person.source = form.source.data
        if form.assigned_to.data and int(form.assigned_to.data) > 0:
            person.assigned_to = str(form.assigned_to.data)
        else:
            person.assigned_to = None
        
        # Notes and tags
        person.notes = form.notes.data
        
        # Set office ID to current user's office
        person.office_id = current_user.office_id
        
        # Handle profile image upload
        if form.profile_image.data:
            # Create directories if they don't exist
            upload_folder = os.path.join('app', 'static', 'uploads', 'profiles')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique filename
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{form.profile_image.data.filename}"
            filepath = os.path.join(upload_folder, filename)
            
            # Save the file
            form.profile_image.data.save(filepath)
            
            # Store the relative path in the database
            person.profile_image = f"uploads/profiles/{filename}"
        
        # Save to database
        db.session.add(person)
        db.session.commit()
        
        flash('Person added successfully!', 'success')
        return redirect(url_for('people.list'))
    
    # For GET request or if form validation fails, display the form
    return render_template('people/form.html', 
                          form=form,
                          person=None, 
                          page_title="Add Person")

@people_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing person/contact."""
    person = Person.query.get_or_404(id)
    
    # Security check - ensure the person belongs to the current user's office
    if person.office_id != current_user.office_id:
        flash('You do not have permission to edit this person.', 'danger')
        return redirect(url_for('people.list'))
    
    form = PersonForm(obj=person)
    
    # Populate select fields
    form.church_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Church.query.filter_by(office_id=current_user.office_id).all()]
    form.assigned_to.choices = [(0, 'Unassigned')] + [(u.id, f"{u.first_name} {u.last_name}") for u in User.query.filter_by(office_id=current_user.office_id).all()]
    
    # If assigned_to is a string (user ID), convert to int for the form
    if person.assigned_to and person.assigned_to.isdigit():
        form.assigned_to.data = int(person.assigned_to)
    
    if form.validate_on_submit():
        # Update basic info
        person.first_name = form.first_name.data
        person.last_name = form.last_name.data
        person.email = form.email.data
        person.phone = form.phone.data
        
        # Update additional personal info
        person.spouse_first_name = form.spouse_first_name.data
        person.spouse_last_name = form.spouse_last_name.data
        
        # Update address information
        person.address = form.address.data
        person.city = form.city.data
        person.state = form.state.data
        person.zip_code = form.zip_code.data
        person.country = form.country.data
        
        # Handle church & role
        if form.church_id.data and int(form.church_id.data) > 0:
            # If church is changing and person was primary contact, unset primary contact
            if person.church_id != form.church_id.data and person.is_primary_contact:
                person.is_primary_contact = False
            
            person.church_id = form.church_id.data
            # If this person is being set as primary contact, unset any other primary contacts
            if form.is_primary_contact.data:
                Person.query.filter(
                    Person.church_id == person.church_id,
                    Person.id != person.id,
                    Person.is_primary_contact == True
                ).update({'is_primary_contact': False})
        else:
            person.church_id = None
            form.is_primary_contact.data = False  # Can't be primary contact without a church
        person.church_role = form.church_role.data
        person.is_primary_contact = form.is_primary_contact.data
        
        # Update pipeline information
        person.pipeline_status = form.pipeline_status.data
        person.pipeline_stage = form.pipeline_stage.data
        person.priority = form.priority.data
        person.source = form.source.data
        if form.assigned_to.data and int(form.assigned_to.data) > 0:
            person.assigned_to = str(form.assigned_to.data)
        else:
            person.assigned_to = None
        
        # Update notes and tags
        person.notes = form.notes.data
        
        # Handle profile image upload
        if form.profile_image.data:
            # Create directories if they don't exist
            upload_folder = os.path.join('app', 'static', 'uploads', 'profiles')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique filename
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{form.profile_image.data.filename}"
            filepath = os.path.join(upload_folder, filename)
            
            # Save the file
            form.profile_image.data.save(filepath)
            
            # Delete old profile image if it exists
            if person.profile_image:
                old_filepath = os.path.join('app', 'static', person.profile_image)
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
            
            # Store the relative path in the database
            person.profile_image = f"uploads/profiles/{filename}"
        
        # Save changes
        db.session.commit()
        
        flash('Person updated successfully!', 'success')
        return redirect(url_for('people.view', id=person.id))
    
    # For GET request or if form validation fails, display the form with existing data
    return render_template('people/form.html', 
                          form=form,
                          person=person, 
                          page_title=f"Edit {person.first_name} {person.last_name}")

@people_bp.route('/view/<int:id>')
@login_required
def view(id):
    """View details of a specific person/contact."""
    person = Person.query.get_or_404(id)
    
    # Security check - ensure the person belongs to the current user's office
    if person.office_id != current_user.office_id:
        flash('You do not have permission to view this person.', 'danger')
        return redirect(url_for('people.list'))
    
    # Get related tasks and communications
    from app.models.task import Task
    from app.models.communication import Communication
    
    tasks = Task.query.filter_by(person_id=person.id).order_by(Task.due_date).all()
    communications = Communication.query.filter_by(person_id=person.id).order_by(Communication.date.desc()).all()
    
    return render_template('people/view.html', 
                          person=person,
                          tasks=tasks,
                          communications=communications,
                          page_title=f"{person.first_name} {person.last_name}")

@people_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a person/contact."""
    person = Person.query.get_or_404(id)
    
    # Security check - ensure the person belongs to the current user's office
    if person.office_id != current_user.office_id:
        flash('You do not have permission to delete this person.', 'danger')
        return redirect(url_for('people.list'))
    
    # Delete the person
    db.session.delete(person)
    db.session.commit()
    
    flash('Person deleted successfully!', 'success')
    return redirect(url_for('people.list'))

@people_bp.route('/add_note/<int:id>', methods=['POST'])
@login_required
def add_note(id):
    """Add a note to a person."""
    person = Person.query.get_or_404(id)
    
    # Security check - ensure the person belongs to the current user's office
    if person.office_id != current_user.office_id:
        flash('You do not have permission to add notes to this person.', 'danger')
        return redirect(url_for('people.list'))
    
    content = request.form.get('content', '')
    if content:
        # Append the new note to existing notes, adding a timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if person.notes:
            person.notes = f"{person.notes}\n\n{timestamp} - {current_user.full_name}:\n{content}"
        else:
            person.notes = f"{timestamp} - {current_user.full_name}:\n{content}"
        
        db.session.commit()
        flash('Note added successfully!', 'success')
    else:
        flash('Note cannot be empty!', 'warning')
    
    return redirect(url_for('people.view', id=person.id))

@people_bp.route('/import', methods=['POST'])
@login_required
def import_people():
    """Import people from CSV file."""
    # CSV import functionality would go here
    flash('People imported successfully!', 'success')
    return redirect(url_for('people.list')) 