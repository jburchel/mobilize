from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required
from datetime import datetime
from app.models.user import User
from app.models.person import Person
from app.models.church import Church
from app.extensions import db
from app.utils.decorators import admin_required

simple_assignments_bp = Blueprint('simple_assignments', __name__)

@simple_assignments_bp.route('/simple-assignments')
@login_required
@admin_required
def simple_assignments_page():
    """Render a simplified assignments page."""
    # Get all users
    users = User.query.all()
    
    # Get unassigned people
    unassigned_people = Person.query.filter(Person.assigned_to.is_(None)).all()
    
    # Get unassigned churches
    unassigned_churches = Church.query.filter(Church.assigned_to.is_(None)).all()
    
    return render_template('simple_assignments.html',
                          users=users,
                          unassigned_people=unassigned_people,
                          unassigned_churches=unassigned_churches,
                          page_title="Simple Assignments")

@simple_assignments_bp.route('/simple-assign-people', methods=['POST'])
@login_required
@admin_required
def simple_assign_people():
    """Simple form-based assignment of people."""
    try:
        # Get form data
        user_id = request.form.get('user_id')
        person_ids = request.form.getlist('person_ids')
        
        current_app.logger.info(f"Assigning people {person_ids} to user {user_id}")
        
        if not user_id:
            flash('Please select a user', 'danger')
            return redirect(url_for('simple_assignments.simple_assignments_page'))
        
        if not person_ids:
            flash('Please select at least one person', 'danger')
            return redirect(url_for('simple_assignments.simple_assignments_page'))
        
        # Get the user
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('simple_assignments.simple_assignments_page'))
        
        # Assign people
        for person_id in person_ids:
            person = Person.query.get(person_id)
            if person:
                person.assigned_to = user.username
                person.updated_at = datetime.now()
        
        db.session.commit()
        flash(f'Successfully assigned {len(person_ids)} people to {user.full_name}', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in simple assignment: {str(e)}')
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('simple_assignments.simple_assignments_page'))

@simple_assignments_bp.route('/simple-assign-churches', methods=['POST'])
@login_required
@admin_required
def simple_assign_churches():
    """Simple form-based assignment of churches."""
    try:
        # Get form data
        user_id = request.form.get('user_id')
        church_ids = request.form.getlist('church_ids')
        
        current_app.logger.info(f"Assigning churches {church_ids} to user {user_id}")
        
        if not user_id:
            flash('Please select a user', 'danger')
            return redirect(url_for('simple_assignments.simple_assignments_page'))
        
        if not church_ids:
            flash('Please select at least one church', 'danger')
            return redirect(url_for('simple_assignments.simple_assignments_page'))
        
        # Get the user
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('simple_assignments.simple_assignments_page'))
        
        # Assign churches
        for church_id in church_ids:
            church = Church.query.get(church_id)
            if church:
                church.assigned_to = user.username
                church.updated_at = datetime.now()
        
        db.session.commit()
        flash(f'Successfully assigned {len(church_ids)} churches to {user.full_name}', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in simple assignment: {str(e)}')
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('simple_assignments.simple_assignments_page'))
