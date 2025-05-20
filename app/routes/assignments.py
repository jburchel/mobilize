from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.models.person import Person
from app.models.church import Church
from app.extensions import db
from app.utils.decorators import admin_required
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
