from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Office, User
from app.models.office import user_offices
from app.utils.decorators import admin_required
from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash
import random

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/offices', methods=['GET', 'POST'])
@login_required
@admin_required
def offices():
    if current_user.role != 'super_admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    offices = Office.query.all()
    
    # Handle add office form submission
    if request.method == 'POST' and request.args.get('action') == 'add':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('contact_email')  # Form field is contact_email but model field is email
        phone = request.form.get('contact_phone')  # Form field is contact_phone but model field is phone
        location_str = request.form.get('location', '')
        timezone = request.form.get('timezone')
        
        # Validate required fields
        if not all([name, email]):
            flash('Office name and email are required', 'danger')
            return redirect(url_for('admin.offices'))
        
        # Check if office already exists
        existing_office = Office.query.filter_by(name=name).first()
        if existing_office:
            flash('An office with this name already exists', 'danger')
            return redirect(url_for('admin.offices'))
        
        # Parse location if provided
        city = state = country = ""
        if location_str:
            location_parts = location_str.split(',')
            if len(location_parts) >= 1:
                city = location_parts[0].strip()
            if len(location_parts) >= 2:
                state = location_parts[1].strip()
            if len(location_parts) >= 3:
                country = location_parts[2].strip()
        
        # Create new office
        new_office = Office(
            name=name,
            email=email,
            phone=phone,
            city=city,
            state=state,
            country=country,
            timezone=timezone
        )
        
        try:
            db.session.add(new_office)
            db.session.commit()
            flash('Office added successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding office: {str(e)}', 'danger')
        
        return redirect(url_for('admin.offices'))
    
    return render_template('admin/offices.html', offices=offices)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Render the admin dashboard page."""
    user_count = User.query.count()
    office_count = Office.query.count()
    return render_template('admin/dashboard.html', user_count=user_count, office_count=office_count)

@admin_bp.route('/offices/<int:office_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_office(office_id):
    """Edit an existing office."""
    office = Office.query.get_or_404(office_id)
    
    if request.method == 'POST':
        office.name = request.form.get('name')
        
        # Handle location fields
        location_str = request.form.get('location', '')
        if location_str:
            location_parts = location_str.split(',')
            if len(location_parts) >= 1:
                office.city = location_parts[0].strip()
            if len(location_parts) >= 2:
                office.state = location_parts[1].strip()
            if len(location_parts) >= 3:
                office.country = location_parts[2].strip()
        
        office.timezone = request.form.get('timezone')
        office.email = request.form.get('contact_email')
        office.phone = request.form.get('contact_phone')
        office.is_active = request.form.get('status') == 'active'
        
        try:
            db.session.commit()
            flash('Office updated successfully', 'success')
            return redirect(url_for('admin.offices'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating office: {str(e)}', 'danger')
    
    return render_template('admin/office_form.html', office=office)

@admin_bp.route('/offices/<int:office_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_office(office_id):
    """Delete an office."""
    office = Office.query.get_or_404(office_id)
    try:
        db.session.delete(office)
        db.session.commit()
        flash('Office deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting office: {str(e)}', 'danger')
    
    return redirect(url_for('admin.offices'))

@admin_bp.route('/offices/<int:office_id>/users', methods=['GET'])
@login_required
@admin_required
def office_users(office_id):
    """Render the office users page."""
    office = Office.query.get_or_404(office_id)
    users = User.query.all()
    
    # Query the users that belong to this office through their office_id field
    office_users = User.query.filter_by(office_id=office_id).all()
    
    user_roles = {}
    for user in office_users:
        user_roles[user.id] = user.role
    
    return render_template(
        'admin/office_users.html', 
        office=office, 
        users=users, 
        office_users=office_users,
        user_roles=user_roles
    )

@admin_bp.route('/offices/<int:office_id>/users/<int:user_id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_office_user(office_id, user_id):
    """Assign a user to an office."""
    role = request.form.get('role')
    if not role:
        flash('Role is required', 'danger')
        return redirect(url_for('admin.office_users', office_id=office_id))
    
    user = User.query.get_or_404(user_id)
    
    # Set the user's office_id directly
    user.office_id = office_id
    user.role = role
    
    try:
        db.session.commit()
        flash('User assigned to office with role: ' + role, 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error assigning user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.office_users', office_id=office_id))

@admin_bp.route('/offices/<int:office_id>/users/<int:user_id>/remove', methods=['POST'])
@login_required
@admin_required
def remove_office_user(office_id, user_id):
    """Remove a user from an office."""
    user = User.query.filter_by(id=user_id, office_id=office_id).first_or_404()
    
    try:
        user.office_id = None
        db.session.commit()
        flash('User removed from office', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.office_users', office_id=office_id))

@admin_bp.route('/offices/<int:office_id>/users/<int:user_id>/update', methods=['POST'])
@login_required
@admin_required
def update_office_user(office_id, user_id):
    """Update a user's role in an office."""
    role = request.form.get('role')
    if not role:
        flash('Role is required', 'danger')
        return redirect(url_for('admin.office_users', office_id=office_id))
    
    # If user_id is 0, this is a new user assignment
    if user_id == 0:
        email = request.form.get('email')
        if not email:
            flash('Email is required', 'danger')
            return redirect(url_for('admin.office_users', office_id=office_id))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash(f'No user found with email: {email}', 'danger')
            return redirect(url_for('admin.office_users', office_id=office_id))
        
        # Set the user's office_id
        user.office_id = office_id
    else:
        # Get existing user
        user = User.query.get_or_404(user_id)
    
    # Update the user's role
    user.role = role
    
    try:
        db.session.commit()
        flash('User role updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user role: {str(e)}', 'danger')
    
    return redirect(url_for('admin.office_users', office_id=office_id))

@admin_bp.route('/offices/<int:office_id>/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def office_settings(office_id):
    """Manage office-specific settings."""
    office = Office.query.get_or_404(office_id)
    
    if request.method == 'POST':
        # Parse settings from form
        settings = {
            'contact_categories': request.form.getlist('contact_categories'),
            'pipeline_stages': request.form.getlist('pipeline_stages'),
            'task_priorities': request.form.getlist('task_priorities'),
            'default_reminder_time': request.form.get('default_reminder_time')
        }
        
        office.settings = settings
        
        try:
            db.session.commit()
            flash('Office settings updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'danger')
    
    return render_template('admin/office_settings.html', office=office)

@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    if current_user.role not in ['admin', 'office_admin', 'super_admin']:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Filter users based on role permissions
    if current_user.role == 'super_admin':
        # Super admins can see all users
        users = User.query.all()
        offices = Office.query.all()
    elif current_user.role == 'office_admin':
        # Office admins can only see users from their office
        users = User.query.filter_by(office_id=current_user.office_id).all()
        offices = Office.query.filter_by(id=current_user.office_id).all()
    else:
        # Safety fallback
        users = []
        offices = []
    
    # Handle add user form submission
    if request.method == 'POST' and request.args.get('action') == 'add':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        office_id = request.form.get('office_id')
        
        # Validation for office admins
        if current_user.role == 'office_admin':
            # Ensure office_id is their own office
            office_id = current_user.office_id
            
            # Restrict role assignment - office admins can't create super_admins
            if role == 'super_admin':
                flash('You do not have permission to create super admin users.', 'danger')
                return redirect(url_for('admin.users'))
        
        # Validate required fields
        if not all([first_name, last_name, email, password, role]):
            flash('All fields are required', 'danger')
            return redirect(url_for('admin.users'))
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('A user with this email already exists', 'danger')
            return redirect(url_for('admin.users'))
        
        # Create new user
        username = email.split('@')[0]  # Use part of email before @ as username
        
        # Check if username already exists and modify if needed
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            username = f"{username}{random.randint(1, 9999)}"
            
        new_user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role
        )
        new_user.set_password(password)
        
        # Associate with office if provided
        if office_id:
            office = Office.query.get(office_id)
            if office:
                new_user.office_id = office.id
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding user: {str(e)}', 'danger')
        
        return redirect(url_for('admin.users'))
    
    return render_template('admin/users.html', users=users, offices=offices)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    # Find user
    user = User.query.get_or_404(user_id)
    
    # Permission checks
    if current_user.role == 'office_admin':
        # Office admins can only delete users from their own office
        if user.office_id != current_user.office_id:
            flash('You do not have permission to delete users from other offices.', 'danger')
            return redirect(url_for('admin.users'))
        # Office admins cannot delete super_admin users
        if user.role == 'super_admin':
            flash('You do not have permission to delete super admin users.', 'danger')
            return redirect(url_for('admin.users'))
    elif current_user.role != 'super_admin':
        flash('You do not have permission to delete users.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Prevent deletion of own account
    if current_user.id == user_id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.email} has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit an existing user."""
    if current_user.role not in ['admin', 'office_admin', 'super_admin']:
        flash('You do not have permission to edit users.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Get the user to edit
    user = User.query.get_or_404(user_id)
    
    # Additional permission checks for office_admin
    if current_user.role == 'office_admin':
        # Office admins can only edit users from their own office
        if user.office_id != current_user.office_id:
            flash('You do not have permission to edit users from other offices.', 'danger')
            return redirect(url_for('admin.users'))
        # Office admins cannot edit super_admin users
        if user.role == 'super_admin':
            flash('You do not have permission to edit super admin users.', 'danger')
            return redirect(url_for('admin.users'))
    
    # Get form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    role = request.form.get('role')
    office_id = request.form.get('office_id')
    is_active = 'is_active' in request.form
    
    # Additional validation for office_admin
    if current_user.role == 'office_admin':
        # Force office_id to be the admin's office
        office_id = current_user.office_id
        # Prevent promotion to super_admin
        if role == 'super_admin':
            flash('You do not have permission to assign super admin role.', 'danger')
            return redirect(url_for('admin.users'))
    
    # Validate required fields
    if not all([first_name, last_name, email, role]):
        flash('All required fields must be filled', 'danger')
        return redirect(url_for('admin.users'))
    
    # Check if email is being changed and already exists
    if email != user.email:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('A user with this email already exists', 'danger')
            return redirect(url_for('admin.users'))
    
    # Update user data
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.role = role
    user.is_active = is_active
    
    # Update office if changed
    if office_id:
        user.office_id = int(office_id)
    else:
        user.office_id = None
    
    try:
        db.session.commit()
        flash('User updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users')) 