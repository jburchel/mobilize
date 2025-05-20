from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required
from datetime import datetime
from app.models.user import User
from app.models.person import Person
from app.models.church import Church
from app.extensions import db
from app.utils.decorators import admin_required

direct_assignments_bp = Blueprint('direct_assignments', __name__)

@direct_assignments_bp.route('/direct-assignments')
@login_required
@admin_required
def direct_assignments_page():
    """Render a simplified assignments page that uses direct links instead of forms."""
    # Get all users
    users = User.query.all()
    
    # Get unassigned people
    unassigned_people = Person.query.filter(Person.assigned_to.is_(None)).all()
    
    # Get unassigned churches
    unassigned_churches = Church.query.filter(Church.assigned_to.is_(None)).all()
    
    return render_template('direct_assignments.html',
                          users=users,
                          unassigned_people=unassigned_people,
                          unassigned_churches=unassigned_churches,
                          page_title="Direct Assignments")

@direct_assignments_bp.route('/direct-assign-person/<int:person_id>/to/<int:user_id>')
@login_required
@admin_required
def direct_assign_person(person_id, user_id):
    """Directly assign a person to a user via a simple GET request."""
    try:
        # Get the user and person
        user = User.query.get(user_id)
        person = Person.query.get(person_id)
        
        if not user or not person:
            flash('User or person not found', 'danger')
            return redirect(url_for('direct_assignments.direct_assignments_page'))
        
        # Assign the person
        person.assigned_to = user.username
        person.updated_at = datetime.now()
        db.session.commit()
        
        flash(f'Successfully assigned {person.full_name} to {user.full_name}', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in direct assignment: {str(e)}')
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('direct_assignments.direct_assignments_page'))

@direct_assignments_bp.route('/direct-assign-church/<int:church_id>/to/<int:user_id>')
@login_required
@admin_required
def direct_assign_church(church_id, user_id):
    """Directly assign a church to a user via a simple GET request."""
    try:
        # Get the user and church
        user = User.query.get(user_id)
        church = Church.query.get(church_id)
        
        if not user or not church:
            flash('User or church not found', 'danger')
            return redirect(url_for('direct_assignments.direct_assignments_page'))
        
        # Assign the church
        church.assigned_to = user.username
        church.updated_at = datetime.now()
        db.session.commit()
        
        flash(f'Successfully assigned {church.name} to {user.full_name}', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in direct assignment: {str(e)}')
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('direct_assignments.direct_assignments_page'))
