from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.models.person import Person
from app.models.church import Church
from app.extensions import db
from app.utils.decorators import admin_required
from sqlalchemy import or_
from datetime import datetime

assignments_bp = Blueprint('assignments', __name__, template_folder='../templates/assignments')

@assignments_bp.route('/')
@login_required
@admin_required
def index():
    """Show assignment management page."""
    # Get all users that can be assigned to
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    # For office admins, only show users in their office
    if not current_user.is_super_admin():
        users = [u for u in users if u.office_id == current_user.office_id]
    
    return render_template('assignments/index.html', 
                          users=users,
                          page_title="Assignment Management")

@assignments_bp.route('/test')
@login_required
@admin_required
def test_assignment():
    """Test page for assignment functionality."""
    # Get all active users
    users_query = User.query.filter_by(is_active=True)
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        users_query = users_query.filter_by(office_id=current_user.office_id)
    
    users = users_query.all()
    
    # Get unassigned people
    unassigned_people_query = Person.query.filter(
        (Person.assigned_to.is_(None)) | 
        (Person.assigned_to == '') | 
        ~Person.assigned_to.in_([u.username for u in users])
    )
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        unassigned_people_query = unassigned_people_query.filter_by(office_id=current_user.office_id)
    
    unassigned_people = unassigned_people_query.all()
    
    return render_template(
        'assignments/test.html',
        users=users,
        unassigned_people=unassigned_people
    )


@assignments_bp.route('/people-simple')
@login_required
@admin_required
def people_assignments_simple():
    """Show people assignment management page with simplified interface."""
    # Get all active users
    users_query = User.query.filter_by(is_active=True)
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        users_query = users_query.filter_by(office_id=current_user.office_id)
    
    users = users_query.all()
    
    # Get unassigned people
    unassigned_people_query = Person.query.filter(
        (Person.assigned_to.is_(None)) | 
        (Person.assigned_to == '') | 
        ~Person.assigned_to.in_([u.username for u in users])
    )
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        unassigned_people_query = unassigned_people_query.filter_by(office_id=current_user.office_id)
    
    unassigned_people = unassigned_people_query.all()
    
    return render_template(
        'assignments/people_simple.html',
        users=users,
        unassigned_people=unassigned_people,
        page_title="People Assignments"
    )


@assignments_bp.route('/churches-simple')
@login_required
@admin_required
def churches_assignments_simple():
    """Show churches assignment management page with simplified interface."""
    # Get all active users
    users_query = User.query.filter_by(is_active=True)
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        users_query = users_query.filter_by(office_id=current_user.office_id)
    
    users = users_query.all()
    
    # Get unassigned churches
    unassigned_churches_query = Church.query.filter(
        (Church.assigned_to.is_(None)) | 
        (Church.assigned_to == '') | 
        ~Church.assigned_to.in_([u.username for u in users])
    )
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        unassigned_churches_query = unassigned_churches_query.filter_by(office_id=current_user.office_id)
    
    unassigned_churches = unassigned_churches_query.all()
    
    return render_template(
        'assignments/churches_simple.html',
        users=users,
        unassigned_churches=unassigned_churches,
        page_title="Church Assignments"
    )

@assignments_bp.route('/people')
@login_required
@admin_required
def people_assignments():
    """Show people assignment management page."""
    # Get all users that can be assigned to
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    # For office admins, only show users in their office
    if not current_user.is_super_admin():
        users = [u for u in users if u.office_id == current_user.office_id]
    
    # Get unassigned people - handle multiple ways the field might be empty or invalid
    # First get all usernames to check against
    all_usernames = [user.username for user in users]
    current_app.logger.info(f'Valid usernames: {all_usernames}')
    
    # Get all people who either have no assignment or have an invalid assignment
    unassigned_query = Person.query.filter(or_(
        Person.assigned_to == 'UNASSIGNED', 
        Person.assigned_to == '', 
        Person.assigned_to.is_(None),
        ~Person.assigned_to.in_(all_usernames)  # Not in valid usernames
    ))
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        unassigned_query = unassigned_query.filter_by(office_id=current_user.office_id)
    
    unassigned_people = unassigned_query.all()
    current_app.logger.info(f'Found {len(unassigned_people)} unassigned people')
    
    return render_template('assignments/people.html', 
                          users=users,
                          unassigned_people=unassigned_people,
                          page_title="People Assignments")

@assignments_bp.route('/churches')
@login_required
@admin_required
def churches_assignments():
    """Show churches assignment management page."""
    # Get all users that can be assigned to
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    # For office admins, only show users in their office
    if not current_user.is_super_admin():
        users = [u for u in users if u.office_id == current_user.office_id]
    
    # Get unassigned churches - handle multiple ways the field might be empty or invalid
    # First get all usernames to check against
    all_usernames = [user.username for user in users]
    current_app.logger.info(f'Valid usernames for churches: {all_usernames}')
    
    # Get all churches who either have no assignment or have an invalid assignment
    unassigned_query = Church.query.filter(or_(
        Church.assigned_to == 'UNASSIGNED', 
        Church.assigned_to == '', 
        Church.assigned_to.is_(None),
        ~Church.assigned_to.in_(all_usernames)  # Not in valid usernames
    ))
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        unassigned_query = unassigned_query.filter_by(office_id=current_user.office_id)
    
    unassigned_churches = unassigned_query.all()
    current_app.logger.info(f'Found {len(unassigned_churches)} unassigned churches')
    
    return render_template('assignments/churches.html', 
                          users=users,
                          unassigned_churches=unassigned_churches,
                          page_title="Church Assignments")

@assignments_bp.route('/assign-people', methods=['POST'])
@login_required
@admin_required
def assign_people():
    """Assign people to a user."""
    # Get form data
    user_id = request.form.get('user_id')
    
    # Try both formats of person_ids to ensure compatibility
    person_ids = request.form.getlist('person_ids[]') or request.form.getlist('person_ids')
    
    # Debug logging
    current_app.logger.info(f'Form submission received - user_id: {user_id}')
    current_app.logger.info(f'Form submission received - person_ids: {person_ids}')
    current_app.logger.info(f'Form data: {dict(request.form)}')
    
    # Validate required data
    if not user_id:
        current_app.logger.error('Missing user_id in form data')
        flash('Please select a user to assign people to', 'danger')
        return redirect(url_for('assignments.people_assignments'))
    
    if not person_ids:
        current_app.logger.error('Missing person_ids in form data')
        flash('Please select at least one person to assign', 'danger')
        return redirect(url_for('assignments.people_assignments'))
    
    try:
        # Get the user to assign to
        user = User.query.get(user_id)
        if not user:
            flash('Selected user not found', 'danger')
            return redirect(url_for('assignments.people_assignments'))
        
        # Check if office admin is trying to assign to users outside their office
        if not current_user.is_super_admin() and user.office_id != current_user.office_id:
            flash('You can only assign to users in your office', 'danger')
            return redirect(url_for('assignments.people_assignments'))
        
        # Get the people to assign
        people_query = Person.query.filter(Person.id.in_(person_ids))
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            people_query = people_query.filter_by(office_id=current_user.office_id)
        
        people = people_query.all()
        
        # Assign people to the user
        for person in people:
            person.assigned_to = user.username
            person.updated_at = datetime.now()
        
        db.session.commit()
        
        flash(f'{len(people)} people assigned to {user.full_name}', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error assigning people: {str(e)}')
        flash(f'Error assigning people: {str(e)}', 'danger')
    
    return redirect(url_for('assignments.people_assignments'))
    


@assignments_bp.route('/assign-churches', methods=['POST'])
@login_required
@admin_required
def assign_churches():
    """Assign churches to a user."""
    # Get form data
    user_id = request.form.get('user_id')
    
    # Try both formats of church_ids to ensure compatibility
    church_ids = request.form.getlist('church_ids[]') or request.form.getlist('church_ids')
    
    # Debug logging
    current_app.logger.info(f'Form submission received - user_id: {user_id}')
    current_app.logger.info(f'Form submission received - church_ids: {church_ids}')
    current_app.logger.info(f'Form data: {dict(request.form)}')
    
    # Validate required data
    if not user_id:
        current_app.logger.error('Missing user_id in form data')
        flash('Please select a user to assign churches to', 'danger')
        return redirect(url_for('assignments.churches_assignments'))
    
    if not church_ids:
        current_app.logger.error('Missing church_ids in form data')
        flash('Please select at least one church to assign', 'danger')
        return redirect(url_for('assignments.churches_assignments'))
    
    try:
        # Get the user to assign to
        user = User.query.get(user_id)
        if not user:
            flash('Selected user not found', 'danger')
            return redirect(url_for('assignments.churches_assignments'))
        
        # Check if office admin is trying to assign to users outside their office
        if not current_user.is_super_admin() and user.office_id != current_user.office_id:
            flash('You can only assign to users in your office', 'danger')
            return redirect(url_for('assignments.churches_assignments'))
        
        # Get the churches to assign
        churches_query = Church.query.filter(Church.id.in_(church_ids))
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            churches_query = churches_query.filter_by(office_id=current_user.office_id)
        
        churches = churches_query.all()
        
        # Assign churches to the user
        for church in churches:
            church.assigned_to = user.username
            church.updated_at = datetime.now()
        
        db.session.commit()
        
        flash(f'{len(churches)} churches assigned to {user.full_name}', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error assigning churches: {str(e)}')
        flash(f'Error assigning churches: {str(e)}', 'danger')
    
    return redirect(url_for('assignments.churches_assignments'))

@assignments_bp.route('/get-user-people/<int:user_id>')
@login_required
@admin_required
def get_user_people(user_id):
    """Get people assigned to a specific user."""
    try:
        # Get the user
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f'User {user_id} not found')
            return jsonify({'error': 'User not found'}), 404
        
        # Check if office admin is trying to view users outside their office
        if not current_user.is_super_admin() and user.office_id != current_user.office_id:
            return jsonify({'error': 'You can only view users in your office'}), 403
        
        # Get people assigned to this user - handle case sensitivity and empty values
        # Use a more flexible match to catch potential case differences or partial matches
        current_app.logger.info(f'Looking for people assigned to user {user.username}')
        
        # Try multiple query approaches to find assigned people
        # First try exact match
        people_query1 = Person.query.filter(Person.assigned_to == user.username)
        # Then try case-insensitive match
        people_query2 = Person.query.filter(Person.assigned_to.ilike(user.username))
        # Then try partial match
        people_query3 = Person.query.filter(Person.assigned_to.ilike(f'%{user.username}%'))
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            people_query1 = people_query1.filter_by(office_id=current_user.office_id)
            people_query2 = people_query2.filter_by(office_id=current_user.office_id)
            people_query3 = people_query3.filter_by(office_id=current_user.office_id)
        
        # Try each query in sequence
        people = people_query1.all()
        current_app.logger.info(f'Exact match found {len(people)} people')
        
        if not people:
            people = people_query2.all()
            current_app.logger.info(f'Case-insensitive match found {len(people)} people')
        
        if not people:
            people = people_query3.all()
            current_app.logger.info(f'Partial match found {len(people)} people')
        
        # Convert to dict for JSON response with error handling
        people_list = []
        for p in people:
            try:
                # Handle different property access patterns
                name = ""
                if hasattr(p, 'name') and p.name:
                    name = p.name
                else:
                    name = f"{p.first_name or ''} {p.last_name or ''}".strip()
                    if not name:
                        name = "Unnamed Person"
                
                email = p.email if hasattr(p, 'email') and p.email else ''
                phone = p.phone if hasattr(p, 'phone') and p.phone else ''
                pipeline = p.people_pipeline if hasattr(p, 'people_pipeline') and p.people_pipeline else ''
                
                people_list.append({
                    'id': p.id,
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'pipeline': pipeline
                })
                current_app.logger.info(f'Found assigned person: {p.id} - {name}')
            except Exception as err:
                current_app.logger.error(f'Error processing person {p.id if hasattr(p, "id") else "unknown"}: {str(err)}')
        
        return jsonify(people_list)
    except Exception as e:
        current_app.logger.error(f'Error in get_user_people: {str(e)}')
        return jsonify({'error': str(e)}), 500

@assignments_bp.route('/get-user-churches/<int:user_id>')
@login_required
@admin_required
def get_user_churches(user_id):
    """Get churches assigned to a specific user."""
    try:
        # Get the user
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f'User {user_id} not found')
            return jsonify({'error': 'User not found'}), 404
        
        # Check if office admin is trying to view users outside their office
        if not current_user.is_super_admin() and user.office_id != current_user.office_id:
            return jsonify({'error': 'You can only view users in your office'}), 403
        
        # Get churches assigned to this user - handle case sensitivity and empty values
        current_app.logger.info(f'Looking for churches assigned to user {user.username}')
        
        # Try multiple query approaches to find assigned churches
        # First try exact match by username
        churches_query1 = Church.query.filter(Church.assigned_to == user.username)
        # Then try case-insensitive match by username
        churches_query2 = Church.query.filter(Church.assigned_to.ilike(user.username))
        # Then try partial match by username
        churches_query3 = Church.query.filter(Church.assigned_to.ilike(f'%{user.username}%'))
        # Also try to find churches where the owner_id matches the user's ID
        churches_query4 = Church.query.filter(Church.owner_id == user.id)
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            churches_query1 = churches_query1.filter_by(office_id=current_user.office_id)
            churches_query2 = churches_query2.filter_by(office_id=current_user.office_id)
            churches_query3 = churches_query3.filter_by(office_id=current_user.office_id)
            churches_query4 = churches_query4.filter_by(office_id=current_user.office_id)
        
        # Try each query in sequence
        churches = churches_query1.all()
        current_app.logger.info(f'Exact match found {len(churches)} churches')
        
        if not churches:
            churches = churches_query2.all()
            current_app.logger.info(f'Case-insensitive match found {len(churches)} churches')
        
        if not churches:
            churches = churches_query3.all()
            current_app.logger.info(f'Partial match found {len(churches)} churches')
            
        if not churches:
            churches = churches_query4.all()
            current_app.logger.info(f'Owner ID match found {len(churches)} churches')
        
        # Convert to dict for JSON response with error handling
        churches_list = []
        for c in churches:
            try:
                name = c.name if hasattr(c, 'name') and c.name else 'Unnamed Church'
                location = c.location if hasattr(c, 'location') and c.location else ''
                phone = c.phone if hasattr(c, 'phone') and c.phone else ''
                email = c.email if hasattr(c, 'email') and c.email else ''
                
                churches_list.append({
                    'id': c.id,
                    'name': name,
                    'location': location,
                    'phone': phone,
                    'email': email
                })
                current_app.logger.info(f'Found assigned church: {c.id} - {name}')
            except Exception as err:
                current_app.logger.error(f'Error processing church {c.id if hasattr(c, "id") else "unknown"}: {str(err)}')
        
        return jsonify(churches_list)
    except Exception as e:
        current_app.logger.error(f'Error in get_user_churches: {str(e)}')
        return jsonify({'error': str(e)}), 500

@assignments_bp.route('/unassign-people', methods=['POST'])
@login_required
@admin_required
def unassign_people():
    """Unassign people from a user."""
    # Try both formats of form data
    person_ids = request.form.getlist('person_ids[]')
    if not person_ids:
        person_ids = request.form.getlist('person_ids')
    
    current_app.logger.info(f'Unassigning people: person_ids={person_ids}')
    
    if not person_ids:
        flash('No people selected for unassignment', 'danger')
        return redirect(url_for('assignments.people_assignments'))
    
    try:
        # Get the people to unassign
        people_query = Person.query.filter(Person.id.in_(person_ids))
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            people_query = people_query.filter_by(office_id=current_user.office_id)
        
        people = people_query.all()
        
        # Unassign people
        for person in people:
            person.assigned_to = 'UNASSIGNED'
            person.updated_at = datetime.now()
        
        db.session.commit()
        
        flash(f'{len(people)} people unassigned', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error unassigning people: {str(e)}')
        flash(f'Error unassigning people: {str(e)}', 'danger')
    
    return redirect(url_for('assignments.people_assignments'))

@assignments_bp.route('/unassign-churches', methods=['POST'])
@login_required
@admin_required
def unassign_churches():
    """Unassign churches from a user."""
    # Try both formats of form data
    church_ids = request.form.getlist('church_ids[]')
    if not church_ids:
        church_ids = request.form.getlist('church_ids')
    
    current_app.logger.info(f'Unassigning churches: church_ids={church_ids}')
    
    if not church_ids:
        flash('No churches selected for unassignment', 'danger')
        return redirect(url_for('assignments.churches_assignments'))
    
    try:
        # Get the churches to unassign
        churches_query = Church.query.filter(Church.id.in_(church_ids))
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            churches_query = churches_query.filter_by(office_id=current_user.office_id)
        
        churches = churches_query.all()
        
        # Unassign churches
        for church in churches:
            church.assigned_to = 'UNASSIGNED'
            church.updated_at = datetime.now()
        
        db.session.commit()
        
        flash(f'{len(churches)} churches unassigned', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error unassigning churches: {str(e)}')
        flash(f'Error unassigning churches: {str(e)}', 'danger')
    
    return redirect(url_for('assignments.churches_assignments'))
