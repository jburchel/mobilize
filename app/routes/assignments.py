from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
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
    users = User.query.filter_by(is_active=True).all()
    
    # For office admins, only show users in their office
    if not current_user.is_super_admin():
        users = [u for u in users if u.office_id == current_user.office_id]
    
    return render_template('assignments/index.html', 
                          users=users,
                          page_title="Assignment Management")

@assignments_bp.route('/people')
@login_required
@admin_required
def people_assignments():
    """Show people assignment management page."""
    # Get all users that can be assigned to
    users = User.query.filter_by(is_active=True).all()
    
    # For office admins, only show users in their office
    if not current_user.is_super_admin():
        users = [u for u in users if u.office_id == current_user.office_id]
    
    # Get unassigned people
    unassigned_query = Person.query.filter(or_(Person.assigned_to == 'UNASSIGNED', Person.assigned_to is None))
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        unassigned_query = unassigned_query.filter_by(office_id=current_user.office_id)
    
    unassigned_people = unassigned_query.all()
    
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
    users = User.query.filter_by(is_active=True).all()
    
    # For office admins, only show users in their office
    if not current_user.is_super_admin():
        users = [u for u in users if u.office_id == current_user.office_id]
    
    # Get unassigned churches
    unassigned_query = Church.query.filter(or_(Church.assigned_to == 'UNASSIGNED', Church.assigned_to is None))
    
    # Filter by office for non-super admins
    if not current_user.is_super_admin():
        unassigned_query = unassigned_query.filter_by(office_id=current_user.office_id)
    
    unassigned_churches = unassigned_query.all()
    
    return render_template('assignments/churches.html', 
                          users=users,
                          unassigned_churches=unassigned_churches,
                          page_title="Church Assignments")

@assignments_bp.route('/assign-people', methods=['POST'])
@login_required
@admin_required
def assign_people():
    """Assign people to a user."""
    user_id = request.form.get('user_id')
    person_ids = request.form.getlist('person_ids[]')
    
    if not user_id or not person_ids:
        flash('Missing required data for assignment', 'danger')
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
        flash(f'Error assigning people: {str(e)}', 'danger')
    
    return redirect(url_for('assignments.people_assignments'))

@assignments_bp.route('/assign-churches', methods=['POST'])
@login_required
@admin_required
def assign_churches():
    """Assign churches to a user."""
    user_id = request.form.get('user_id')
    church_ids = request.form.getlist('church_ids[]')
    
    if not user_id or not church_ids:
        flash('Missing required data for assignment', 'danger')
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
            return jsonify({'error': 'User not found'}), 404
        
        # Check if office admin is trying to view users outside their office
        if not current_user.is_super_admin() and user.office_id != current_user.office_id:
            return jsonify({'error': 'You can only view users in your office'}), 403
        
        # Get people assigned to this user
        people_query = Person.query.filter_by(assigned_to=user.username)
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            people_query = people_query.filter_by(office_id=current_user.office_id)
        
        people = people_query.all()
        
        # Convert to dict for JSON response
        people_list = [{
            'id': p.id,
            'name': p.name,
            'email': p.email,
            'phone': p.phone,
            'pipeline': p.people_pipeline
        } for p in people]
        
        return jsonify(people_list)
    except Exception as e:
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
        
        # Check if office admin is trying to view users outside their office
        if not current_user.is_super_admin() and user.office_id != current_user.office_id:
            return jsonify({'error': 'You can only view users in your office'}), 403
        
        # Get churches assigned to this user
        churches_query = Church.query.filter_by(assigned_to=user.username)
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            churches_query = churches_query.filter_by(office_id=current_user.office_id)
        
        churches = churches_query.all()
        
        # Convert to dict for JSON response
        churches_list = [{
            'id': c.id,
            'name': c.name,
            'location': c.location,
            'phone': c.phone,
            'email': c.email
        } for c in churches]
        
        return jsonify(churches_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@assignments_bp.route('/unassign-people', methods=['POST'])
@login_required
@admin_required
def unassign_people():
    """Unassign people from a user."""
    person_ids = request.form.getlist('person_ids[]')
    
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
        flash(f'Error unassigning people: {str(e)}', 'danger')
    
    return redirect(url_for('assignments.people_assignments'))

@assignments_bp.route('/unassign-churches', methods=['POST'])
@login_required
@admin_required
def unassign_churches():
    """Unassign churches from a user."""
    church_ids = request.form.getlist('church_ids[]')
    
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
        flash(f'Error unassigning churches: {str(e)}', 'danger')
    
    return redirect(url_for('assignments.churches_assignments'))
