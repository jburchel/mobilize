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
def people():
    """Show people assignment management page."""
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
        'assignments/people.html',
        users=users,
        unassigned_people=unassigned_people,
        page_title="People Assignments"
    )

@assignments_bp.route('/churches')
@login_required
@admin_required
def churches():
    """Show churches assignment management page."""
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
        'assignments/churches.html',
        users=users,
        unassigned_churches=unassigned_churches,
        page_title="Church Assignments"
    )

@assignments_bp.route('/assign-people', methods=['POST'])
@login_required
@admin_required
def assign_people():
    """Assign people to a user."""
    try:
        # Get form data
        user_id = request.form.get('user_id')
        person_ids = request.form.getlist('person_ids')
        
        # Debug logging
        current_app.logger.info(f"Form data - user_id: {user_id}, person_ids: {person_ids}")
        
        # Validate form data
        if not user_id:
            flash('Please select a user', 'danger')
            return redirect(url_for('assignments.people'))
        
        if not person_ids:
            flash('Please select at least one person', 'danger')
            return redirect(url_for('assignments.people'))
        
        # Get the user
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('assignments.people'))
        
        # Assign people
        count = 0
        for person_id in person_ids:
            person = Person.query.get(person_id)
            if person:
                person.assigned_to = user.username
                person.updated_at = datetime.now()
                count += 1
        
        db.session.commit()
        flash(f'Successfully assigned {count} people to {user.full_name}', 'success')
        
        return redirect(url_for('assignments.people'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in assign_people: {str(e)}')
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('assignments.people'))

@assignments_bp.route('/assign-churches', methods=['POST'])
@login_required
@admin_required
def assign_churches():
    """Assign churches to a user."""
    try:
        # Get form data
        user_id = request.form.get('user_id')
        church_ids = request.form.getlist('church_ids')
        
        # Debug logging
        current_app.logger.info(f"Form data - user_id: {user_id}, church_ids: {church_ids}")
        
        # Validate form data
        if not user_id:
            flash('Please select a user', 'danger')
            return redirect(url_for('assignments.churches'))
        
        if not church_ids:
            flash('Please select at least one church', 'danger')
            return redirect(url_for('assignments.churches'))
        
        # Get the user
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('assignments.churches'))
        
        # Assign churches
        count = 0
        for church_id in church_ids:
            church = Church.query.get(church_id)
            if church:
                church.assigned_to = user.username
                church.updated_at = datetime.now()
                count += 1
        
        db.session.commit()
        flash(f'Successfully assigned {count} churches to {user.full_name}', 'success')
        
        return redirect(url_for('assignments.churches'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in assign_churches: {str(e)}')
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('assignments.churches'))

@assignments_bp.route('/get-user-people/<int:user_id>')
@login_required
@admin_required
def get_user_people(user_id):
    """Get people assigned to a specific user."""
    try:
        # Get the user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get people assigned to this user
        people_query = Person.query.filter_by(assigned_to=user.username)
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            people_query = people_query.filter_by(office_id=current_user.office_id)
        
        people = people_query.all()
        
        # Format the response
        people_data = []
        for person in people:
            people_data.append({
                'id': person.id,
                'full_name': person.full_name,
                'email': person.email,
                'phone': person.phone,
                'city': person.city,
                'state': person.state,
                'updated_at': person.updated_at.strftime('%Y-%m-%d %H:%M:%S') if person.updated_at else None
            })
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name
            },
            'people': people_data
        })
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
            return jsonify({'error': 'User not found'}), 404
        
        # Get churches assigned to this user
        churches_query = Church.query.filter_by(assigned_to=user.username)
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            churches_query = churches_query.filter_by(office_id=current_user.office_id)
        
        churches = churches_query.all()
        
        # Format the response
        churches_data = []
        for church in churches:
            churches_data.append({
                'id': church.id,
                'name': church.name,
                'city': church.city,
                'state': church.state,
                'pastor': church.pastor,
                'updated_at': church.updated_at.strftime('%Y-%m-%d %H:%M:%S') if church.updated_at else None
            })
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name
            },
            'churches': churches_data
        })
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
        return redirect(url_for('assignments.people'))
    
    try:
        # Get the people to unassign
        people_query = Person.query.filter(Person.id.in_(person_ids))
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            people_query = people_query.filter_by(office_id=current_user.office_id)
        
        people = people_query.all()
        
        # Unassign people
        for person in people:
            person.assigned_to = None
            person.updated_at = datetime.now()
        
        db.session.commit()
        
        flash(f'{len(people)} people unassigned', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error unassigning people: {str(e)}')
        flash(f'Error unassigning people: {str(e)}', 'danger')
    
    return redirect(url_for('assignments.people'))

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
        return redirect(url_for('assignments.churches'))
    
    try:
        # Get the churches to unassign
        churches_query = Church.query.filter(Church.id.in_(church_ids))
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            churches_query = churches_query.filter_by(office_id=current_user.office_id)
        
        churches = churches_query.all()
        
        # Unassign churches
        for church in churches:
            church.assigned_to = None
            church.updated_at = datetime.now()
        
        db.session.commit()
        
        flash(f'{len(churches)} churches unassigned', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error unassigning churches: {str(e)}')
        flash(f'Error unassigning churches: {str(e)}', 'danger')
    
    return redirect(url_for('assignments.churches'))

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
    # Detailed request debugging
    current_app.logger.info('=== ASSIGN PEOPLE REQUEST DETAILS ===')
    current_app.logger.info(f'Request method: {request.method}')
    current_app.logger.info(f'Content type: {request.content_type}')
    current_app.logger.info(f'Form data keys: {list(request.form.keys())}')
    
    # Temporarily bypass CSRF token check for debugging
    if 'csrf_token' not in request.form:
        current_app.logger.warning('CSRF token missing, but continuing for debugging')
    # Log CSRF token if present
    if 'csrf_token' in request.form:
        token_value = request.form.get('csrf_token')
        current_app.logger.info(f'CSRF token found: {token_value[:10]}...')
    
    # Get form data
    user_id = request.form.get('user_id')
    current_app.logger.info(f'User ID from form: {user_id}')
    
    # Try both formats of person_ids and log results
    person_ids_brackets = request.form.getlist('person_ids[]')
    person_ids_no_brackets = request.form.getlist('person_ids')
    person_ids = person_ids_brackets or person_ids_no_brackets
    current_app.logger.info(f'Final person_ids: {person_ids}, length: {len(person_ids)}')
    
    # Validate required data
    if not user_id:
        current_app.logger.error('Missing user_id in form data')
        flash('Please select a user to assign people to', 'danger')
        return redirect(url_for('assignments.people_assignments'))
    
    if not person_ids:
        current_app.logger.error('Missing person_ids in form data')
        flash('Please select at least one person to assign', 'danger')
        return redirect(url_for('assignments.people_assignments'))
    
    # Create a new session for this operation to avoid connection pool issues
    session = db.create_scoped_session()
    
    try:
        # Get the user to assign to
        current_app.logger.info(f'Looking up user with ID: {user_id}')
        user = session.query(User).get(user_id)
        if not user:
            current_app.logger.error(f'User with ID {user_id} not found')
            flash('Selected user not found', 'danger')
            return redirect(url_for('assignments.people_assignments'))
        
        # Check if office admin is trying to assign to users outside their office
        if not current_user.is_super_admin() and user.office_id != current_user.office_id:
            current_app.logger.error(f'Office mismatch: current user office {current_user.office_id}, target user office {user.office_id}')
            flash('You can only assign to users in your office', 'danger')
            return redirect(url_for('assignments.people_assignments'))
        
        # Convert string IDs to integers for the query
        try:
            person_id_ints = [int(pid) for pid in person_ids]
        except ValueError as ve:
            current_app.logger.error(f'Error converting person IDs to integers: {str(ve)}')
            flash('Invalid person IDs provided', 'danger')
            return redirect(url_for('assignments.people_assignments'))
        
        # Use a more efficient query approach with fewer connections
        query = session.query(Person).filter(Person.id.in_(person_id_ints))
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            query = query.filter_by(office_id=current_user.office_id)
        
        # Update all records in a single query to reduce database load
        updated_count = query.update({
            Person.assigned_to: user.username,
            Person.updated_at: datetime.now()
        }, synchronize_session=False)
        
        current_app.logger.info(f'Updated {updated_count} people assignments')
        session.commit()
        
        flash(f'{updated_count} people assigned to {user.full_name}', 'success')
        current_app.logger.info(f'Successfully assigned {updated_count} people to {user.username}')
    except Exception as e:
        session.rollback()
        current_app.logger.error(f'Error assigning people: {str(e)}')
        current_app.logger.error(f'Error details: {type(e).__name__}')
        current_app.logger.exception('Full traceback:')
        flash(f'Error assigning people: {str(e)}', 'danger')
    finally:
        # Ensure the session is closed to return connection to pool
        try:
            session.close()
        except Exception as e:
            current_app.logger.error(f'Error closing session: {str(e)}')

    
    return redirect(url_for('assignments.people_assignments'))
    


@assignments_bp.route('/assign-churches', methods=['POST'])
@login_required
@admin_required
def assign_churches():
    """Assign churches to a user."""
    # Detailed request debugging
    current_app.logger.info('=== ASSIGN CHURCHES REQUEST DETAILS ===')
    current_app.logger.info(f'Request method: {request.method}')
    current_app.logger.info(f'Content type: {request.content_type}')
    current_app.logger.info(f'Form data keys: {list(request.form.keys())}')
    
    # Temporarily bypass CSRF token check for debugging
    if 'csrf_token' not in request.form:
        current_app.logger.warning('CSRF token missing, but continuing for debugging')
    # Log CSRF token if present
    if 'csrf_token' in request.form:
        token_value = request.form.get('csrf_token')
        current_app.logger.info(f'CSRF token found: {token_value[:10]}...')
    
    # Get form data
    user_id = request.form.get('user_id')
    current_app.logger.info(f'User ID from form: {user_id}')
    
    # Try both formats of church_ids and log results
    church_ids_brackets = request.form.getlist('church_ids[]')
    church_ids_no_brackets = request.form.getlist('church_ids')
    church_ids = church_ids_brackets or church_ids_no_brackets
    current_app.logger.info(f'Final church_ids: {church_ids}, length: {len(church_ids)}')
    
    # Validate required data
    if not user_id:
        current_app.logger.error('Missing user_id in form data')
        flash('Please select a user to assign churches to', 'danger')
        return redirect(url_for('assignments.churches_assignments'))
    
    if not church_ids:
        current_app.logger.error('Missing church_ids in form data')
        flash('Please select at least one church to assign', 'danger')
        return redirect(url_for('assignments.churches_assignments'))
    
    # Create a new session for this operation to avoid connection pool issues
    session = db.create_scoped_session()
    
    try:
        # Get the user to assign to
        current_app.logger.info(f'Looking up user with ID: {user_id}')
        user = session.query(User).get(user_id)
        if not user:
            current_app.logger.error(f'User with ID {user_id} not found')
            flash('Selected user not found', 'danger')
            return redirect(url_for('assignments.churches_assignments'))
        
        # Check if office admin is trying to assign to users outside their office
        if not current_user.is_super_admin() and user.office_id != current_user.office_id:
            current_app.logger.error(f'Office mismatch: current user office {current_user.office_id}, target user office {user.office_id}')
            flash('You can only assign to users in your office', 'danger')
            return redirect(url_for('assignments.churches_assignments'))
        
        # Convert string IDs to integers for the query
        try:
            church_id_ints = [int(cid) for cid in church_ids]
        except ValueError as ve:
            current_app.logger.error(f'Error converting church IDs to integers: {str(ve)}')
            flash('Invalid church IDs provided', 'danger')
            return redirect(url_for('assignments.churches_assignments'))
        
        # Use a more efficient query approach with fewer connections
        query = session.query(Church).filter(Church.id.in_(church_id_ints))
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            query = query.filter_by(office_id=current_user.office_id)
        
        # Update all records in a single query to reduce database load
        updated_count = query.update({
            Church.assigned_to: user.username,
            Church.updated_at: datetime.now()
        }, synchronize_session=False)
        
        current_app.logger.info(f'Updated {updated_count} church assignments')
        session.commit()
        
        flash(f'{updated_count} churches assigned to {user.full_name}', 'success')
        current_app.logger.info(f'Successfully assigned {updated_count} churches to {user.username}')
    except Exception as e:
        session.rollback()
        current_app.logger.error(f'Error assigning churches: {str(e)}')
        current_app.logger.error(f'Error details: {type(e).__name__}')
        current_app.logger.exception('Full traceback:')
        flash(f'Error assigning churches: {str(e)}', 'danger')
    finally:
        # Ensure the session is closed to return connection to pool
        try:
            session.close()
        except Exception as e:
            current_app.logger.error(f'Error closing session: {str(e)}')

    
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

            church_ids = request.form.getlist('church_ids')
            
            # Debug logging
            current_app.logger.info(f"Form data - user_id: {user_id}, church_ids: {church_ids}")
            
            # Validate form data
            if not user_id:
                flash('Please select a user', 'danger')
                return redirect(url_for('assignments.churches'))
            
            if not church_ids:
                flash('Please select at least one church', 'danger')
                return redirect(url_for('assignments.churches'))
            
            # Get the user
            user = User.query.get(user_id)
            if not user:
                flash('User not found', 'danger')
                return redirect(url_for('assignments.churches'))
            
            # Assign churches
            count = 0
            for church_id in church_ids:
                church = Church.query.get(church_id)
                if church:
                    church.assigned_to = user.username
                    church.updated_at = datetime.now()
                    count += 1
            
            db.session.commit()
            flash(f'Successfully assigned {count} churches to {user.full_name}', 'success')
        
        return redirect(url_for('assignments.churches'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in assign_churches: {str(e)}')
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('assignments.churches'))

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
