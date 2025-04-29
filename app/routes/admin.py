from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response, send_file, current_app
from flask_login import login_required, current_user
from app.models import Office, User, Church, Contact, Person
from app.models.office import user_offices
from app.models.communication import Communication
from app.models.task import Task
from app.models.email_signature import EmailSignature
from app.utils.decorators import admin_required
from app.services.gmail_service import GmailService
from app.services.email_service import send_email
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError
import datetime
from werkzeug.security import generate_password_hash
import json
import random
from app.utils.user_utils import create_person_for_user
from datetime import datetime, timedelta
import uuid
import io
import csv
import time
from io import BytesIO
import os

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
    """Admin dashboard."""
    # Get counts of various entities
    user_count = 5  # Replace with actual query
    contact_count = 120  # Replace with actual query
    church_count = 35  # Replace with actual query
    message_count = 450  # Replace with actual query
    
    # Get counts of active and inactive users
    active_users = 4  # Replace with actual query
    inactive_users = 1  # Replace with actual query
    
    # Recent activity
    recent_activity = [
        {'user': 'admin@example.com', 'action': 'Added new user', 'time': '5 minutes ago'},
        {'user': 'john@example.com', 'action': 'Updated profile', 'time': '2 hours ago'},
        {'user': 'system', 'action': 'Backup completed', 'time': '1 day ago'}
    ]
    
    return render_template('admin/dashboard.html', 
                          user_count=user_count,
                          contact_count=contact_count,
                          church_count=church_count,
                          message_count=message_count,
                          active_users=active_users,
                          inactive_users=inactive_users,
                          recent_activity=recent_activity)

@admin_bp.route('/system')
@login_required
@admin_required
def system_dashboard():
    """System dashboard."""
    # Get system statistics
    system_stats = {
        'cpu_usage': random.randint(10, 90),
        'memory_usage': random.randint(20, 80),
        'disk_usage': random.randint(30, 70),
        'app_uptime': '5d 12h 34m',
        'server_uptime': '15d 7h 22m',
        'last_backup': datetime.now() - timedelta(days=1),
        'database_size': '287.5 MB',
        'python_version': '3.11.5',
        'flask_version': '2.3.2'
    }
    
    # Recent system events
    recent_events = [
        {'type': 'backup', 'status': 'success', 'details': 'Database backup completed successfully', 'time': '1 day ago'},
        {'type': 'update', 'status': 'success', 'details': 'System updated to version 1.2.3', 'time': '3 days ago'},
        {'type': 'maintenance', 'status': 'info', 'details': 'Scheduled maintenance completed', 'time': '1 week ago'},
        {'type': 'error', 'status': 'danger', 'details': 'Database connection error (resolved)', 'time': '2 weeks ago'}
    ]
    
    return render_template('admin/system/dashboard.html', 
                          system_stats=system_stats,
                          recent_events=recent_events)

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
            role=role,
            first_login=True  # Explicitly mark as first login
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
            
            # Create a Person record for the new user
            try:
                person = create_person_for_user(new_user)
                flash('User added successfully and person record created', 'success')
            except ValueError as e:
                flash(f'User added but could not create person record: {str(e)}', 'warning')
            except Exception as e:
                current_app.logger.error(f"Error creating person for user: {str(e)}")
                flash(f'User added but error creating person record: {str(e)}', 'warning')
                
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
        # Check if user has owned resources
        owned_churches_count = db.session.query(Church).filter_by(owner_id=user_id).count()
        associated_contacts_count = db.session.query(Contact).filter_by(user_id=user_id).count()
        owned_communications_count = db.session.query(Communication).filter_by(owner_id=user_id).count()
        sender_communications_count = db.session.query(Communication).filter_by(user_id=user_id).count()
        owned_tasks_count = db.session.query(Task).filter_by(owner_id=user_id).count()
        assigned_tasks_count = db.session.query(Task).filter_by(assigned_to=user_id).count()
        
        # If user has resources, handle reassignment
        has_resources = (owned_churches_count > 0 or associated_contacts_count > 0 or 
                         owned_communications_count > 0 or sender_communications_count > 0 or
                         owned_tasks_count > 0 or assigned_tasks_count > 0)
        
        if has_resources:
            reassign_to_id = request.form.get('reassign_to_id')
            
            # If no reassign user specified, try to find office admin
            if not reassign_to_id and user.office_id:
                office_admin = User.query.filter_by(office_id=user.office_id, role='office_admin').first()
                if office_admin:
                    reassign_to_id = office_admin.id
            
            # If we have someone to reassign to, perform reassignment
            if reassign_to_id:
                reassign_to = User.query.get(reassign_to_id)
                if reassign_to:
                    # Reassign churches
                    if owned_churches_count > 0:
                        Church.query.filter_by(owner_id=user_id).update({'owner_id': reassign_to_id})
                    
                    # Reassign contacts
                    if associated_contacts_count > 0:
                        Contact.query.filter_by(user_id=user_id).update({'user_id': reassign_to_id})
                    
                    # Reassign communications
                    if owned_communications_count > 0:
                        Communication.query.filter_by(owner_id=user_id).update({'owner_id': reassign_to_id})
                    
                    if sender_communications_count > 0:
                        Communication.query.filter_by(user_id=user_id).update({'user_id': reassign_to_id})
                    
                    # Reassign tasks
                    if owned_tasks_count > 0:
                        Task.query.filter_by(owner_id=user_id).update({'owner_id': reassign_to_id})
                    
                    if assigned_tasks_count > 0:
                        Task.query.filter_by(assigned_to=user_id).update({'assigned_to': reassign_to_id})
                    
                    # Delete email signatures (they are personal, so not reassigned)
                    EmailSignature.query.filter_by(user_id=user_id).delete()
                    
                    db.session.flush()
                    
                    # Now delete the user
                    db.session.delete(user)
                    db.session.commit()
                    flash(f'User {user.email} has been deleted successfully. Resources were reassigned to {reassign_to.email}.', 'success')
                    return redirect(url_for('admin.users'))
                else:
                    flash(f'The user you selected for reassignment does not exist.', 'danger')
                    return redirect(url_for('admin.users'))
            
            # If no reassignment target, show selection form
            users_in_office = User.query.filter(User.office_id == user.office_id, 
                                               User.id != user_id,
                                               User.is_active == True).all()
            
            resource_message = []
            if owned_churches_count > 0:
                resource_message.append(f"{owned_churches_count} churches")
            if associated_contacts_count > 0:
                resource_message.append(f"{associated_contacts_count} contacts")
            if owned_communications_count > 0 or sender_communications_count > 0:
                comm_count = owned_communications_count + sender_communications_count
                resource_message.append(f"{comm_count} communications")
            if owned_tasks_count > 0 or assigned_tasks_count > 0:
                task_count = owned_tasks_count + assigned_tasks_count
                resource_message.append(f"{task_count} tasks")
            
            resources_str = ", ".join(resource_message)
            
            flash(f'This user owns {resources_str}. Please select a user to reassign them to before deleting.', 'warning')
            return render_template('admin/users.html', 
                                  users=User.query.all(),
                                  offices=Office.query.all(),
                                  show_reassign=True, 
                                  user_to_delete=user,
                                  reassign_options=users_in_office)
        
        # If no resources, delete directly
        # Delete email signatures (they are personal, so not reassigned)
        EmailSignature.query.filter_by(user_id=user_id).delete()
        
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

# System Logs and Monitoring Routes
@admin_bp.route('/logs/system')
@admin_required
def system_logs():
    # Sample data for system logs
    logs = []
    
    # Generate some sample log entries
    log_levels = ['INFO', 'WARNING', 'ERROR']
    log_messages = [
        'User login successful',
        'Failed login attempt',
        'Database connection established',
        'High memory usage detected',
        'API request completed',
        'Email sending failed',
        'Background task completed',
        'File upload successful',
        'Permission denied for user',
        'Configuration update applied'
    ]
    
    # Create 20 sample log entries
    for i in range(20):
        # Randomize timestamp within the last 24 hours
        hours_ago = random.randint(0, 24)
        minutes_ago = random.randint(0, 59)
        timestamp = datetime.now() - timedelta(hours=hours_ago, minutes=minutes_ago)
        
        # Weighted random level (more INFO than WARNING, more WARNING than ERROR)
        level_weights = [0.7, 0.2, 0.1]  # 70% INFO, 20% WARNING, 10% ERROR
        level = random.choices(log_levels, weights=level_weights, k=1)[0]
        
        # Random message
        message = random.choice(log_messages)
        if level == 'ERROR':
            message = f"ERROR: {message}"
        elif level == 'WARNING':
            message = f"WARNING: {message}"
        
        logs.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
    
    # Sort logs by timestamp, newest first
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('admin/logs/system_logs.html', logs=logs)

@admin_bp.route('/logs/user-activity')
@admin_required
def user_activity():
    # Sample data for user activity logs
    activities = []
    
    # Sample users
    users = [
        {'email': 'admin@example.com', 'name': 'Admin User'},
        {'email': 'john@example.com', 'name': 'John Smith'},
        {'email': 'sarah@example.com', 'name': 'Sarah Johnson'},
        {'email': 'mike@example.com', 'name': 'Mike Wilson'},
        {'email': 'lisa@example.com', 'name': 'Lisa Brown'}
    ]
    
    # Sample action types
    actions = ['LOGIN', 'LOGOUT', 'CREATE', 'UPDATE', 'DELETE', 'VIEW', 'EXPORT']
    
    # Sample details for each action
    details_templates = {
        'LOGIN': 'User logged in from IP {ip}',
        'LOGOUT': 'User logged out',
        'CREATE': 'Created {resource_type} with ID {resource_id}',
        'UPDATE': 'Updated {resource_type} with ID {resource_id}',
        'DELETE': 'Deleted {resource_type} with ID {resource_id}',
        'VIEW': 'Viewed {resource_type} with ID {resource_id}',
        'EXPORT': 'Exported {resource_type} data'
    }
    
    # Resource types
    resource_types = ['CONTACT', 'CHURCH', 'USER', 'PIPELINE', 'TASK', 'EVENT']
    
    # Generate 30 random activities
    for i in range(30):
        # Random user
        user = random.choice(users)
        
        # Random timestamp in the last 7 days
        hours_ago = random.randint(0, 168)  # Up to 7 days (168 hours)
        minutes_ago = random.randint(0, 59)
        timestamp = datetime.now() - timedelta(hours=hours_ago, minutes=minutes_ago)
        
        # Random action
        action = random.choice(actions)
        
        # Generate appropriate details
        if action in ['CREATE', 'UPDATE', 'DELETE', 'VIEW']:
            resource_type = random.choice(resource_types)
            resource_id = random.randint(1000, 9999)
            details = details_templates[action].format(
                resource_type=resource_type,
                resource_id=resource_id
            )
        elif action == 'LOGIN':
            ip_parts = [str(random.randint(1, 255)) for _ in range(4)]
            ip = '.'.join(ip_parts)
            details = details_templates[action].format(ip=ip)
        else:
            if action == 'EXPORT':
                resource_type = random.choice(resource_types)
                details = details_templates[action].format(resource_type=resource_type)
            else:
                details = details_templates[action]
        
        # Create activity entry
        activities.append({
            'timestamp': timestamp,
            'user_email': user['email'],
            'action': action,
            'details': details
        })
    
    # Sort activities by timestamp, newest first
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('admin/logs/user_activity.html', activities=activities)

@admin_bp.route('/logs/system-performance')
@admin_required
def system_performance():
    # Sample data for the system performance page
    cpu_usage = 45
    memory_usage = 62
    disk_usage = 38
    response_time = 120

    # Sample worker processes
    workers = [
        {"name": "Web Server", "status": "Running", "cpu_usage": 12, "memory_usage": 345},
        {"name": "Background Worker", "status": "Running", "cpu_usage": 8, "memory_usage": 210},
        {"name": "Scheduler", "status": "Running", "cpu_usage": 5, "memory_usage": 125},
        {"name": "Email Service", "status": "Running", "cpu_usage": 3, "memory_usage": 98}
    ]

    # Sample API stats
    api_stats = [
        {"path": "/api/contacts", "avg_response": 85, "requests_per_min": 42, "error_rate": 0.2},
        {"path": "/api/churches", "avg_response": 92, "requests_per_min": 35, "error_rate": 0.5},
        {"path": "/api/pipelines", "avg_response": 110, "requests_per_min": 28, "error_rate": 0.8},
        {"path": "/api/tasks", "avg_response": 78, "requests_per_min": 22, "error_rate": 0.3},
        {"path": "/api/events", "avg_response": 150, "requests_per_min": 18, "error_rate": 1.2},
        {"path": "/api/auth", "avg_response": 65, "requests_per_min": 15, "error_rate": 2.5}
    ]

    # Sample DB stats
    db_stats = {
        "connection_pool": "20/50",
        "active_connections": 8,
        "cache_hit_rate": 92.5
    }

    # Sample system events
    system_events = [
        {"timestamp": datetime.now() - timedelta(minutes=5), "level": "INFO", "message": "Background task runner completed successfully"},
        {"timestamp": datetime.now() - timedelta(minutes=30), "level": "WARNING", "message": "High memory usage detected (80%)"},
        {"timestamp": datetime.now() - timedelta(hours=2), "level": "INFO", "message": "Database backup completed successfully"},
        {"timestamp": datetime.now() - timedelta(hours=5), "level": "ERROR", "message": "Failed to connect to email service"},
        {"timestamp": datetime.now() - timedelta(hours=8), "level": "INFO", "message": "System update applied successfully"}
    ]

    return render_template('admin/logs/system_performance.html',
                          cpu_usage=cpu_usage,
                          memory_usage=memory_usage,
                          disk_usage=disk_usage,
                          response_time=response_time,
                          workers=workers,
                          api_stats=api_stats,
                          db_stats=db_stats,
                          system_events=system_events)

@admin_bp.route('/logs/activity')
@login_required
def activity_logs():
    """Display activity logs."""
    # Generate sample activity data
    activities = []
    
    # Define sample timestamps spread over the last 30 days
    now = datetime.now()
    
    # Define sample subsystems
    subsystems = ['Authentication', 'Database', 'API', 'File System', 'Background Jobs', 
                 'Email Service', 'Payment Processing', 'User Management', 'Church Management']
    
    # Define sample operations
    operations = ['CREATE', 'READ', 'UPDATE', 'DELETE', 'IMPORT', 'EXPORT', 'SCHEDULE', 
                 'CANCEL', 'PROCESS', 'SYNC', 'BACKUP', 'RESTORE']
    
    # Define sample status values
    statuses = ['SUCCESS', 'FAILURE', 'WARNING', 'PENDING', 'TIMEOUT', 'ABORTED']
    
    # Define sample impacts
    impacts = ['HIGH', 'MEDIUM', 'LOW', 'NONE']
    
    # Define sample users
    users = [
        {'email': 'admin@example.com', 'name': 'System Admin'},
        {'email': 'john.doe@example.com', 'name': 'John Doe'},
        {'email': 'jane.smith@example.com', 'name': 'Jane Smith'},
        {'email': 'pastor@church.org', 'name': 'Pastor Williams'},
        {'email': 'coordinator@ministry.com', 'name': 'Sarah Johnson'},
        None  # For system activities with no user
    ]
    
    # Generate 40 random activity logs
    for _ in range(40):
        # Random timestamp in the last 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        mins_ago = random.randint(0, 59)
        timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)
        
        # Random subsystem and operation
        subsystem = random.choice(subsystems)
        operation = random.choice(operations)
        
        # Status with weighted probability (success more likely)
        status_weights = [0.7, 0.1, 0.1, 0.05, 0.025, 0.025]  # Probabilities for each status
        status = random.choices(statuses, weights=status_weights, k=1)[0]
        
        # Random impact level based on status
        if status == 'SUCCESS':
            impact = random.choices(impacts, weights=[0.05, 0.15, 0.3, 0.5], k=1)[0]
        elif status == 'FAILURE':
            impact = random.choices(impacts, weights=[0.6, 0.3, 0.1, 0], k=1)[0]
        else:
            impact = random.choices(impacts, weights=[0.2, 0.4, 0.3, 0.1], k=1)[0]
        
        # Random user (sometimes None for system activities)
        user = random.choice(users)
        
        # Generate a description based on subsystem and operation
        if subsystem == 'Authentication':
            resource = random.choice(['user session', 'password', 'account', 'token'])
            if operation == 'CREATE':
                description = f"New {resource} created"
            elif operation in ['UPDATE', 'PROCESS']:
                description = f"{resource.capitalize()} updated"
            elif operation == 'DELETE':
                description = f"{resource.capitalize()} removed"
            else:
                description = f"{operation.capitalize()} operation on {resource}"
        
        elif subsystem == 'Database':
            resource = random.choice(['record', 'table', 'query', 'connection', 'index'])
            description = f"Database {operation.lower()} on {resource}"
            
        elif subsystem == 'API':
            resource = random.choice(['endpoint', 'request', 'response', 'integration'])
            description = f"API {operation.lower()} - {resource}"
            
        elif subsystem in ['User Management', 'Church Management']:
            resource = random.choice(['profile', 'role', 'permission', 'group', 'membership'])
            description = f"{subsystem} {operation.lower()} - {resource}"
            
        else:
            description = f"{subsystem} {operation.lower()} operation"
        
        # Add more details for failed operations
        if status == 'FAILURE':
            description += " - " + random.choice([
                "Resource not found", 
                "Permission denied",
                "Validation error",
                "Timeout exceeded",
                "Conflict detected",
                "Rate limit reached",
                "Invalid input"
            ])
        
        # Generate a random IP address
        ip_address = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        
        # Create the activity log entry
        activities.append({
            'timestamp': timestamp,
            'subsystem': subsystem,
            'operation': operation,
            'description': description,
            'status': status,
            'impact': impact,
            'user': user['name'] if user else 'System',
            'email': user['email'] if user else None,
            'ip_address': ip_address if user else None,
            'duration': random.randint(1, 5000) if operation not in ['CREATE', 'DELETE'] else None,
            'resource_id': f"{random.randint(1000, 9999)}" if random.random() > 0.3 else None
        })
    
    # Sort activities by timestamp in descending order
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Generate summary statistics
    total_activities = len(activities)
    success_count = len([a for a in activities if a['status'] == 'SUCCESS'])
    failure_count = len([a for a in activities if a['status'] == 'FAILURE'])
    warning_count = len([a for a in activities if a['status'] == 'WARNING'])
    
    subsystem_counts = {}
    for activity in activities:
        subsystem = activity['subsystem']
        if subsystem in subsystem_counts:
            subsystem_counts[subsystem] += 1
        else:
            subsystem_counts[subsystem] = 1
    
    # Get top 5 subsystems by activity count
    top_subsystems = sorted(subsystem_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Create summary data
    summary = {
        'total': total_activities,
        'success_rate': (success_count / total_activities) * 100 if total_activities > 0 else 0,
        'failure_rate': (failure_count / total_activities) * 100 if total_activities > 0 else 0,
        'warning_rate': (warning_count / total_activities) * 100 if total_activities > 0 else 0,
        'top_subsystems': top_subsystems
    }
    
    return render_template('admin/logs/activity_logs.html', activities=activities, summary=summary)

@admin_bp.route('/logs/security')
@login_required
def security_logs():
    """Display security logs."""
    # Generate sample security log data
    security_logs = []
    
    # Define sample timestamps spread over the last 30 days
    now = datetime.now()
    
    # Define sample security event types
    event_types = [
        'LOGIN_FAILURE', 'PERMISSION_DENIED', 'DATA_ACCESS', 'ACCOUNT_LOCKED', 
        'CONFIG_CHANGE', 'PASSWORD_CHANGE', 'PRIVILEGE_ESCALATION', 'SUSPICIOUS_ACTIVITY',
        'BRUTE_FORCE_ATTEMPT', 'SESSION_HIJACKING', 'UNUSUAL_LOGIN_TIME', 'UNUSUAL_LOGIN_LOCATION'
    ]
    
    # Define security levels
    levels = ['CRITICAL', 'WARNING', 'INFO']
    level_weights = [0.2, 0.3, 0.5]  # Probabilities for each level
    
    # Define sample users
    users = [
        {'email': 'admin@example.com', 'name': 'System Admin'},
        {'email': 'john.doe@example.com', 'name': 'John Doe'},
        {'email': 'jane.smith@example.com', 'name': 'Jane Smith'},
        {'email': 'pastor@church.org', 'name': 'Pastor Williams'},
        {'email': 'coordinator@ministry.com', 'name': 'Sarah Johnson'},
        None  # For anonymous activities
    ]
    
    # Generate sample security logs
    for i in range(50):
        # Random timestamp in the last 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        mins_ago = random.randint(0, 59)
        timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)
        
        # Random event type
        event_type = random.choice(event_types)
        
        # Security level with weighted probability
        level = random.choices(levels, weights=level_weights, k=1)[0]
        
        # Adjust level based on event type for more realism
        if event_type in ['BRUTE_FORCE_ATTEMPT', 'SESSION_HIJACKING', 'PRIVILEGE_ESCALATION']:
            level = 'CRITICAL'
        elif event_type in ['LOGIN_FAILURE', 'UNUSUAL_LOGIN_LOCATION', 'PERMISSION_DENIED']:
            level = random.choices(['CRITICAL', 'WARNING'], weights=[0.3, 0.7], k=1)[0]
        
        # Random user (sometimes None for anonymous activities)
        user = random.choice(users)
        
        # Generate IP address and location info
        ip_address = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        
        # Generate a description based on event type
        if event_type == 'LOGIN_FAILURE':
            description = f"Failed login attempt for {user['email'] if user else 'unknown user'}"
            if random.random() > 0.7:
                description += " - Invalid password"
            elif random.random() > 0.5:
                description += " - Account not found"
            else:
                description += " - Account locked"
        
        elif event_type == 'PERMISSION_DENIED':
            resources = ['user data', 'admin settings', 'financial records', 'member database', 'settings page']
            description = f"Attempted unauthorized access to {random.choice(resources)}"
        
        elif event_type == 'DATA_ACCESS':
            description = f"Unusual data access pattern detected for user {user['name'] if user else 'Unknown'}"
        
        elif event_type == 'ACCOUNT_LOCKED':
            description = f"Account locked after multiple failed login attempts"
        
        elif event_type == 'CONFIG_CHANGE':
            configs = ['security settings', 'user permissions', 'system configuration', 'email templates', 'payment gateway']
            description = f"Configuration change in {random.choice(configs)}"
        
        elif event_type == 'BRUTE_FORCE_ATTEMPT':
            description = f"Possible brute force attack detected from IP {ip_address}"
        
        elif event_type == 'UNUSUAL_LOGIN_LOCATION':
            countries = ['United States', 'China', 'Russia', 'Brazil', 'India', 'Nigeria', 'Netherlands']
            description = f"Login from unusual location: {random.choice(countries)}"
        
        else:
            description = f"{event_type.replace('_', ' ').title()} detected"
        
        # Create the security log entry
        security_logs.append({
            'id': str(uuid.uuid4())[:8],  # Generate a short UUID as ID
            'timestamp': timestamp,
            'level': level,
            'event_type': event_type,
            'ip_address': ip_address,
            'user': user['name'] if user else 'Anonymous',
            'description': description,
        })
    
    # Sort logs by timestamp in descending order
    security_logs.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Generate summary statistics
    critical_alerts = len([log for log in security_logs if log['level'] == 'CRITICAL'])
    warning_alerts = len([log for log in security_logs if log['level'] == 'WARNING'])
    failed_logins = len([log for log in security_logs if log['event_type'] == 'LOGIN_FAILURE' and 
                        (now - log['timestamp']).total_seconds() < 86400])  # Last 24 hours
    locked_accounts = len([log for log in security_logs if log['event_type'] == 'ACCOUNT_LOCKED'])
    
    # Calculate historical data for charts (last 14 days)
    dates = [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(13, -1, -1)]
    
    # Initialize counters for each type of event
    critical_history = [0] * 14
    warning_history = [0] * 14
    login_failure_history = [0] * 14
    
    # Count events for each day
    for log in security_logs:
        day_index = (now - log['timestamp']).days
        if 0 <= day_index < 14:
            if log['level'] == 'CRITICAL':
                critical_history[13 - day_index] += 1
            elif log['level'] == 'WARNING':
                warning_history[13 - day_index] += 1
            if log['event_type'] == 'LOGIN_FAILURE':
                login_failure_history[13 - day_index] += 1
    
    # Generate top security issues
    event_counts = {}
    for log in security_logs:
        key = f"{log['level']}:{log['event_type']}"
        if key in event_counts:
            event_counts[key]['count'] += 1
            if log['timestamp'] > event_counts[key]['last_occurrence']:
                event_counts[key]['last_occurrence'] = log['timestamp']
        else:
            event_counts[key] = {
                'level': log['level'],
                'event_type': log['event_type'],
                'count': 1,
                'last_occurrence': log['timestamp'],
                'description': log['description']
            }
    
    # Get top 5 security issues
    top_security_issues = sorted(event_counts.values(), key=lambda x: (x['level'] == 'CRITICAL', x['level'] == 'WARNING', x['count']), reverse=True)[:5]
    
    # Format for display
    for issue in top_security_issues:
        issue['title'] = f"{issue['level']}: {issue['event_type'].replace('_', ' ').title()}"
        issue['last_occurrence'] = issue['last_occurrence'].strftime('%Y-%m-%d %H:%M:%S')
    
    # Generate access locations for map
    locations = {}
    # Mock geo locations
    cities = ['New York', 'Los Angeles', 'Chicago', 'London', 'Paris', 'Tokyo', 'Sydney', 'Moscow', 'Berlin', 'Beijing']
    countries = ['USA', 'USA', 'USA', 'UK', 'France', 'Japan', 'Australia', 'Russia', 'Germany', 'China']
    latitudes = [40.7128, 34.0522, 41.8781, 51.5074, 48.8566, 35.6762, -33.8688, 55.7558, 52.5200, 39.9042]
    longitudes = [-74.0060, -118.2437, -87.6298, -0.1278, 2.3522, 139.6503, 151.2093, 37.6176, 13.4050, 116.4074]
    
    for i, log in enumerate(security_logs):
        if log['ip_address'] not in locations:
            # Create a mock location
            idx = i % 10  # Cycle through the 10 predefined cities
            locations[log['ip_address']] = {
                'ip_address': log['ip_address'],
                'city': cities[idx],
                'country': countries[idx],
                'latitude': latitudes[idx] + random.uniform(-0.1, 0.1),  # Add small random offset
                'longitude': longitudes[idx] + random.uniform(-0.1, 0.1),
                'event_count': 1
            }
        else:
            locations[log['ip_address']]['event_count'] += 1
    
    access_locations = list(locations.values())
    
    # Sample admin users for alert settings
    admins = [
        {'id': 1, 'name': 'Admin User', 'email': 'admin@example.com', 'receives_alerts': True},
        {'id': 2, 'name': 'Security Officer', 'email': 'security@example.com', 'receives_alerts': True},
        {'id': 3, 'name': 'System Manager', 'email': 'manager@example.com', 'receives_alerts': False}
    ]
    
    return render_template('admin/logs/security_logs.html',
                          security_logs=security_logs,
                          critical_alerts=critical_alerts,
                          warning_alerts=warning_alerts,
                          failed_logins=failed_logins,
                          locked_accounts=locked_accounts,
                          security_dates=json.dumps(dates),
                          critical_history=json.dumps(critical_history),
                          warning_history=json.dumps(warning_history),
                          login_failure_history=json.dumps(login_failure_history),
                          top_security_issues=top_security_issues,
                          access_locations=access_locations,
                          admins=admins)

@admin_bp.route('/export-security-logs')
@login_required
def export_security_logs():
    """Export security logs as CSV."""
    # In a real application, this would query the database
    # For the demo, we'll reuse the sample data generation
    security_logs = []
    
    # Define sample timestamps spread over the last 30 days
    now = datetime.now()
    
    # Define sample security event types
    event_types = [
        'LOGIN_FAILURE', 'PERMISSION_DENIED', 'DATA_ACCESS', 'ACCOUNT_LOCKED', 
        'CONFIG_CHANGE', 'PASSWORD_CHANGE', 'PRIVILEGE_ESCALATION', 'SUSPICIOUS_ACTIVITY',
        'BRUTE_FORCE_ATTEMPT', 'SESSION_HIJACKING', 'UNUSUAL_LOGIN_TIME', 'UNUSUAL_LOGIN_LOCATION'
    ]
    
    # Define security levels
    levels = ['CRITICAL', 'WARNING', 'INFO']
    level_weights = [0.2, 0.3, 0.5]  # Probabilities for each level
    
    # Define sample users
    users = [
        {'email': 'admin@example.com', 'name': 'System Admin'},
        {'email': 'john.doe@example.com', 'name': 'John Doe'},
        {'email': 'jane.smith@example.com', 'name': 'Jane Smith'},
        {'email': 'pastor@church.org', 'name': 'Pastor Williams'},
        {'email': 'coordinator@ministry.com', 'name': 'Sarah Johnson'},
        None  # For anonymous activities
    ]
    
    # Generate sample security logs
    for i in range(50):
        # Random timestamp in the last 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        mins_ago = random.randint(0, 59)
        timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)
        
        # Random event type
        event_type = random.choice(event_types)
        
        # Security level with weighted probability
        level = random.choices(levels, weights=level_weights, k=1)[0]
        
        # Adjust level based on event type for more realism
        if event_type in ['BRUTE_FORCE_ATTEMPT', 'SESSION_HIJACKING', 'PRIVILEGE_ESCALATION']:
            level = 'CRITICAL'
        elif event_type in ['LOGIN_FAILURE', 'UNUSUAL_LOGIN_LOCATION', 'PERMISSION_DENIED']:
            level = random.choices(['CRITICAL', 'WARNING'], weights=[0.3, 0.7], k=1)[0]
        
        # Random user (sometimes None for anonymous activities)
        user = random.choice(users)
        
        # Generate IP address
        ip_address = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        
        # Generate a description based on event type
        if event_type == 'LOGIN_FAILURE':
            description = f"Failed login attempt for {user['email'] if user else 'unknown user'}"
        elif event_type == 'PERMISSION_DENIED':
            resources = ['user data', 'admin settings', 'financial records', 'member database', 'settings page']
            description = f"Attempted unauthorized access to {random.choice(resources)}"
        elif event_type == 'DATA_ACCESS':
            description = f"Unusual data access pattern detected for user {user['name'] if user else 'Unknown'}"
        elif event_type == 'ACCOUNT_LOCKED':
            description = f"Account locked after multiple failed login attempts"
        elif event_type == 'CONFIG_CHANGE':
            configs = ['security settings', 'user permissions', 'system configuration', 'email templates', 'payment gateway']
            description = f"Configuration change in {random.choice(configs)}"
        else:
            description = f"{event_type.replace('_', ' ').title()} detected"
        
        # Create the security log entry
        security_logs.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'level': level,
            'event_type': event_type,
            'ip_address': ip_address,
            'user': user['name'] if user else 'Anonymous',
            'description': description,
        })
    
    # Sort logs by timestamp in descending order
    security_logs.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Create a CSV response
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Timestamp', 'Level', 'Event Type', 'IP Address', 'User', 'Description'])
    
    # Write data
    for log in security_logs:
        writer.writerow([
            log['timestamp'],
            log['level'],
            log['event_type'],
            log['ip_address'],
            log['user'],
            log['description']
        ])
    
    # Create the response
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment;filename=security_logs.csv',
            'Cache-Control': 'no-cache'
        }
    )
    
    return response

# System Settings Routes

@admin_bp.route('/system/google-workspace')
@login_required
@admin_required
def google_workspace_settings():
    """Google Workspace Integration Settings."""
    # Get current settings from database (using mock data for now)
    settings = {
        'enabled': True,
        'domain': 'example.org',
        'client_id': 'your-client-id.apps.googleusercontent.com',
        'client_secret': '••••••••••••••••••',  # Masked for security
        'scopes': ['calendar', 'contacts', 'drive', 'gmail'],
        'sync_frequency': 'hourly',
        'last_sync': datetime.now() - timedelta(hours=2),
        'connected_users': 8
    }
    
    # Add status information
    status = {
        'connected': True,
        'token_valid': True,
        'last_sync': datetime.now() - timedelta(hours=2),
        'synced_resources': {
            'users': 42,
            'groups': 8,
            'events': 156
        }
    }
    
    return render_template('admin/system/google_workspace_settings.html', settings=settings, status=status)

@admin_bp.route('/system/google-workspace', methods=['POST'])
@login_required
@admin_required
def update_google_workspace_settings():
    """Update Google Workspace Integration Settings."""
    # In a real app, we would validate and save the form data to the database
    flash('Google Workspace settings updated successfully', 'success')
    return redirect(url_for('admin.google_workspace_settings'))

@admin_bp.route('/system/email-settings')
@login_required
@admin_required
def email_settings():
    """Email System Settings."""
    # Get current settings from database (using mock data for now)
    settings = {
        'mail_default_sender': 'Mobilize App <info@mobilize-app.org>',
        'email_signature': '<p>Blessings,<br>The Team at Mobilize App</p>'
    }
    
    # Get sample email templates
    templates = [
        {'id': 1, 'name': 'Welcome Email', 'subject': 'Welcome to Mobilize App', 'last_modified': datetime.now() - timedelta(days=3)},
        {'id': 2, 'name': 'Password Reset', 'subject': 'Reset Your Password', 'last_modified': datetime.now() - timedelta(weeks=2)},
        {'id': 3, 'name': 'Account Verification', 'subject': 'Verify Your Account', 'last_modified': datetime.now() - timedelta(days=3)},
        {'id': 4, 'name': 'New Message Notification', 'subject': 'You Have a New Message', 'last_modified': datetime.now() - timedelta(days=5)},
        {'id': 5, 'name': 'Task Assignment', 'subject': 'New Task Assigned to You', 'last_modified': datetime.now() - timedelta(days=1)}
    ]
    
    # Get email stats (load from Gmail API if the user is authenticated)
    stats = {
        'sent_today': 0,
        'sent_week': 0,
        'bounced': 0,
        'failed': 0,
        'delivery_rate': 100
    }
    
    # Try to get real data from Gmail API
    try:
        # Get Gmail token for current user
        from app.models.google_token import GoogleToken
        token = GoogleToken.query.filter_by(user_id=current_user.id).first()
        
        if token:
            # Initialize the Gmail service if user has valid credentials
            gmail_service = GmailService(current_user.id)
            
            # Get last 7 days of emails - normally we'd use the Gmail API to get these counts
            # For demo, we'll use mock data until we implement more Gmail API metrics
            stats = {
                'sent_today': 47,
                'sent_week': 342,
                'bounced': 3,
                'failed': 5,
                'delivery_rate': 98
            }
    except Exception as e:
        flash(f"Unable to load Gmail statistics: {str(e)}", "warning")
    
    # Mock recent email activities - these would come from real Gmail API data in production
    recent_activities = [
        {'subject': 'Welcome to Mobilize App', 'recipient': 'john.doe@example.com', 'time_ago': '12 minutes ago', 'status': 'Delivered', 'status_color': 'success'},
        {'subject': 'Your Password Has Been Reset', 'recipient': 'jane.smith@example.com', 'time_ago': '1 hour ago', 'status': 'Delivered', 'status_color': 'success'},
        {'subject': 'New Task Assignment', 'recipient': 'robert.johnson@example.com', 'time_ago': '3 hours ago', 'status': 'Opened', 'status_color': 'info'},
        {'subject': 'Weekly Report', 'recipient': 'team@example.com', 'time_ago': '6 hours ago', 'status': 'Bounced', 'status_color': 'warning'},
        {'subject': 'Meeting Reminder', 'recipient': 'lisa.wong@example.com', 'time_ago': '1 day ago', 'status': 'Failed', 'status_color': 'danger'}
    ]
    
    return render_template('admin/system/email_settings.html', settings=settings, templates=templates, stats=stats, recent_activities=recent_activities)

@admin_bp.route('/system/email-settings', methods=['POST'])
@login_required
@admin_required
def update_email_settings():
    """Update Email Settings."""
    # Get form data
    mail_default_sender = request.form.get('mail_default_sender')
    email_signature = request.form.get('email_signature')
    
    # In a real app, we would save these settings to the database
    # For now, just simulate success
    
    flash('Email settings updated successfully', 'success')
    return redirect(url_for('admin.email_settings'))

@admin_bp.route('/system/email-settings/test', methods=['POST'])
@login_required
@admin_required
def test_email_connection():
    """Send a test email using Gmail API."""
    # Get the recipient email from the form
    recipient = request.form.get('recipient', current_user.email)
    subject = request.form.get('subject', 'Test Email from Mobilize App')
    message = request.form.get('message', 'This is a test email from the Mobilize App to verify email settings are working correctly.')
    
    try:
        # Use GmailService to send the test email
        gmail_service = GmailService(current_user.id)
        gmail_service.send_email(
            to=recipient,
            subject=subject,
            body=message,
            html=f"<p>{message}</p>"
        )
        
        if request.is_xhr or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': f'Test email sent to {recipient}'})
        else:
            flash(f'Test email sent successfully to {recipient}', 'success')
            return redirect(url_for('admin.email_settings'))
    except Exception as e:
        if request.is_xhr or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)})
        else:
            flash(f'Error sending test email: {str(e)}', 'error')
            return redirect(url_for('admin.email_settings'))

@admin_bp.route('/system/email-settings/preview/<int:template_id>')
@login_required
@admin_required
def preview_email_template(template_id):
    """Preview an email template."""
    # In a real app, we would fetch the template from the database
    # For now, just return a sample template
    template_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Template Preview #{template_id}</h2>
            </div>
            <div class="content">
                <p>Hello {{{{ recipient_name }}}},</p>
                <p>This is a preview of email template #{template_id}. In a real application, this would be the actual content of the email template.</p>
                <p>The email would contain personalized information and relevant details based on the template's purpose.</p>
                <p>Click <a href="#">here</a> to learn more.</p>
                <p>Thank you,<br>The Mobilize App Team</p>
            </div>
            <div class="footer">
                <p>This email was sent from the Mobilize App. Please do not reply to this email.</p>
                <p>&copy; {datetime.now().year} Mobilize App. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return template_html

@admin_bp.route('/system/database')
@login_required
@admin_required
def database_management():
    """Database Management."""
    # Get mock database stats
    db_stats = {
        'size': '287.5 MB',
        'tables': 24,
        'records': 14572,
        'avg_query_time': 83,
        'last_optimization': datetime.now() - timedelta(days=2),
        'health_score': 85,
        'fragmentation': 25,
        'slow_queries': 8
    }
    
    # Get mock table stats
    table_stats = [
        {'name': 'users', 'records': 531, 'size': '12.5 MB', 'last_updated': datetime.now() - timedelta(hours=4), 'status': 'Healthy'},
        {'name': 'contacts', 'records': 2815, 'size': '64.2 MB', 'last_updated': datetime.now() - timedelta(hours=2), 'status': 'Healthy'},
        {'name': 'churches', 'records': 472, 'size': '18.9 MB', 'last_updated': datetime.now() - timedelta(days=1), 'status': 'Needs Optimization'},
        {'name': 'people', 'records': 2343, 'size': '45.3 MB', 'last_updated': datetime.now() - timedelta(hours=6), 'status': 'Healthy'},
        {'name': 'messages', 'records': 8324, 'size': '112.7 MB', 'last_updated': datetime.now() - timedelta(hours=1), 'status': 'Needs Optimization'},
        {'name': 'tasks', 'records': 2087, 'size': '33.9 MB', 'last_updated': datetime.now() - timedelta(hours=3), 'status': 'Healthy'}
    ]
    
    # Get mock recent backups
    backups = [
        {'id': 1, 'created_at': datetime.now() - timedelta(days=1), 'size': '281.2 MB', 'created_by': 'System', 'type': 'Automated', 'status': 'Complete'},
        {'id': 2, 'created_at': datetime.now() - timedelta(days=2), 'size': '280.7 MB', 'created_by': 'System', 'type': 'Automated', 'status': 'Complete'},
        {'id': 3, 'created_at': datetime.now() - timedelta(days=3), 'size': '279.8 MB', 'created_by': 'admin@example.com', 'type': 'Manual', 'status': 'Complete'},
        {'id': 4, 'created_at': datetime.now() - timedelta(days=4), 'size': '278.5 MB', 'created_by': 'System', 'type': 'Automated', 'status': 'Complete'},
        {'id': 5, 'created_at': datetime.now() - timedelta(days=8), 'size': '276.1 MB', 'created_by': 'System', 'type': 'Automated', 'status': 'Complete'}
    ]
    
    return render_template('admin/system/database.html', db_stats=db_stats, table_stats=table_stats, backups=backups)

@admin_bp.route('/system/database/backup', methods=['POST'])
@login_required
@admin_required
def create_database_backup():
    """Create a database backup."""
    # In a real app, we would create an actual backup
    # For now, just simulate success
    time.sleep(2)  # Simulate backup creation time
    
    flash('Database backup created successfully', 'success')
    return redirect(url_for('admin.database_management'))

@admin_bp.route('/system/database/optimize', methods=['POST'])
@login_required
@admin_required
def optimize_database():
    """Optimize the database."""
    # In a real app, we would optimize the database
    # For now, just simulate success
    time.sleep(3)  # Simulate optimization time
    
    flash('Database optimized successfully', 'success')
    return redirect(url_for('admin.database_management'))

@admin_bp.route('/system/database/restore/<int:backup_id>', methods=['POST'])
@login_required
@admin_required
def restore_database(backup_id):
    """Restore the database from a backup."""
    # In a real app, we would restore from the specified backup
    # For now, just simulate success
    time.sleep(4)  # Simulate restoration time
    
    flash('Database restored successfully from backup', 'success')
    return redirect(url_for('admin.database_management'))

@admin_bp.route('/system/database/download/<int:backup_id>')
@login_required
@admin_required
def download_database_backup(backup_id):
    """Download a database backup file."""
    # In a real app, we would retrieve the actual backup file and send it
    # For now, just generate a dummy SQL file
    
    # Create a simple SQL dump as an example
    sql_content = f"""-- Database backup {backup_id}
-- Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- This is a sample backup file for demonstration purposes

BEGIN TRANSACTION;

-- Table structure for users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample data
INSERT INTO users (email, password_hash, name) VALUES
('admin@example.com', 'hashed_password_here', 'Admin User'),
('user@example.com', 'hashed_password_here', 'Regular User');

-- Additional tables would be included in a real backup

COMMIT;
"""
    
    # Create a BytesIO object
    bytes_io = BytesIO(sql_content.encode('utf-8'))
    
    # Return the file as an attachment
    return send_file(
        bytes_io,
        mimetype='application/sql',
        as_attachment=True,
        download_name=f'database_backup_{backup_id}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.sql'
    )

@admin_bp.route('/system/database/import', methods=['POST'])
@login_required
@admin_required
def import_database_data():
    """Import data into the database."""
    # Check if file was uploaded
    if 'importFile' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('admin.database_management'))
    
    file = request.files['importFile']
    
    # Check if file is empty
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('admin.database_management'))
    
    # Get form parameters
    import_format = request.form.get('importFormat', 'auto')
    target_table = request.form.get('targetTable', '')
    truncate_before_import = 'truncateBeforeImport' in request.form
    ignore_errors = 'ignoreErrors' in request.form
    header_row = 'headerRow' in request.form
    
    # Check file size (10MB limit)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        flash('File too large. Maximum size is 10MB.', 'error')
        return redirect(url_for('admin.database_management'))
    
    # Determine file format if auto-detect
    if import_format == 'auto':
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext == 'sql':
            import_format = 'sql'
        elif file_ext == 'csv':
            import_format = 'csv'
        elif file_ext == 'json':
            import_format = 'json'
        elif file_ext in ['xls', 'xlsx']:
            import_format = 'excel'
        else:
            flash('Could not automatically determine file format. Please specify.', 'error')
            return redirect(url_for('admin.database_management'))
    
    # In a real app, we would process the file based on its format and import into the database
    # For now, just simulate success
    time.sleep(2)  # Simulate processing time
    
    # Generate a success message
    records_imported = random.randint(10, 1000)
    flash(f'Successfully imported {records_imported} records from {file.filename}', 'success')
    
    return redirect(url_for('admin.database_management'))

@admin_bp.route('/logs/email')
@login_required
@admin_required
def email_logs():
    """Display email logs and analytics."""
    # Get mock email stats
    stats = {
        'total_sent': 1287,
        'total_opened': 856,
        'total_clicked': 412,
        'total_bounced': 37,
        'open_rate': 66,
        'click_rate': 32,
        'delivery_rate': 97,
        'bounce_rate': 3
    }
    
    # Create summary for the dashboard cards
    summary = {
        'total': 1287,
        'delivered_rate': 97,
        'failed_rate': 3,
        'open_rate': 66
    }
    
    # Mock chart data
    chart_data = {
        'labels': [(datetime.now() - timedelta(days=i)).strftime('%m/%d') for i in range(7, 0, -1)],
        'sent': [42, 57, 36, 41, 29, 38, 47],
        'opened': [28, 34, 21, 26, 17, 22, 31],
        'clicked': [14, 18, 11, 15, 9, 12, 16]
    }
    
    # Mock email logs
    logs = []
    statuses = ['sent', 'delivered', 'opened', 'bounced', 'failed']
    status_colors = {
        'sent': 'info',
        'delivered': 'primary',
        'opened': 'success',
        'failed': 'danger',
        'bounced': 'warning'
    }
    
    # Generate mock log entries
    for i in range(1, 25):
        sent_time = datetime.now() - timedelta(hours=i*2)
        status = random.choice(statuses)
        opened = status in ['opened']
        opened_at = sent_time + timedelta(hours=1) if opened else None
        click_count = random.randint(0, 3) if opened else 0
        
        logs.append({
            'id': i,
            'sent_at': sent_time.strftime('%m/%d/%Y %H:%M'),
            'subject': f'Sample Email {i}',
            'recipient_email': f'recipient{i}@example.com',
            'sender_name': 'System Admin',
            'status': status,
            'status_color': status_colors[status],
            'opened': opened,
            'opened_at': opened_at.strftime('%m/%d/%Y %H:%M') if opened_at else None,
            'click_count': click_count
        })
    
    return render_template('admin/logs/email_logs.html', stats=stats, chart_data=chart_data, logs=logs, summary=summary)

@admin_bp.route('/api/logs/email/chart-data')
@login_required
@admin_required
def email_logs_chart_data():
    """API endpoint to get email logs chart data based on period."""
    period = request.args.get('period', 'week')
    
    # Generate different data based on the requested period
    if period == 'week':
        labels = [(datetime.now() - timedelta(days=i)).strftime('%m/%d') for i in range(7, 0, -1)]
        sent = [42, 57, 36, 41, 29, 38, 47]
        opened = [28, 34, 21, 26, 17, 22, 31]
        clicked = [14, 18, 11, 15, 9, 12, 16]
    elif period == 'month':
        labels = [(datetime.now() - timedelta(days=i*3)).strftime('%m/%d') for i in range(10, 0, -1)]
        sent = [124, 157, 136, 141, 129, 138, 147, 118, 131, 142]
        opened = [83, 94, 81, 86, 77, 82, 91, 75, 84, 89]
        clicked = [42, 53, 41, 45, 39, 42, 46, 38, 42, 47]
    else:  # year
        labels = [(datetime.now() - timedelta(days=i*30)).strftime('%m/%Y') for i in range(12, 0, -1)]
        sent = [356, 412, 378, 402, 367, 394, 425, 377, 412, 388, 412, 438]
        opened = [218, 253, 231, 246, 225, 241, 261, 231, 254, 237, 255, 269]
        clicked = [112, 131, 119, 128, 116, 125, 135, 119, 131, 123, 133, 139]
    
    return jsonify({
        'labels': labels,
        'sent': sent,
        'opened': opened,
        'clicked': clicked
    })

@admin_bp.route('/api/logs/email/details')
@login_required
@admin_required
def email_details():
    """API endpoint to get detailed information about a specific email."""
    email_id = request.args.get('id')
    
    if not email_id:
        return jsonify({'success': False, 'error': 'Email ID is required'})
    
    # In a real app, we would fetch actual email data
    # Generate mock email details
    sent_time = datetime.now() - timedelta(hours=int(email_id))
    delivered_time = sent_time + timedelta(minutes=2)
    opened_time = sent_time + timedelta(hours=1)
    
    # Determine status randomly but consistently for the same ID
    random.seed(int(email_id))
    status_options = ['delivered', 'opened', 'bounced', 'failed']
    status_weights = [0.5, 0.3, 0.1, 0.1]
    status = random.choices(status_options, status_weights)[0]
    
    status_colors = {
        'delivered': 'primary',
        'opened': 'success',
        'failed': 'danger',
        'bounced': 'warning'
    }
    
    # Only include opened_at if status is 'opened'
    opened_at = opened_time.strftime('%m/%d/%Y %H:%M') if status == 'opened' else None
    
    # Only include bounce_reason if status is 'bounced'
    bounce_reason = 'Invalid recipient address' if status == 'bounced' else None
    
    # Only include click events if status is 'opened'
    click_events = []
    if status == 'opened':
        click_count = random.randint(0, 2)
        for i in range(click_count):
            click_time = opened_time + timedelta(minutes=random.randint(5, 30))
            click_events.append({
                'url': f'https://example.com/link{i+1}',
                'clicked_at': click_time.strftime('%m/%d/%Y %H:%M')
            })
    
    # Sample HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Sample Email {email_id}</h2>
            </div>
            <div class="content">
                <p>Hello recipient{email_id}@example.com,</p>
                <p>This is a sample email content for demonstration purposes. In a real application, this would be the actual content of the email that was sent.</p>
                <p>The email contains information relevant to the recipient, such as account updates, notifications, or other important information.</p>
                <p>Click <a href="https://example.com/link1">here</a> to view more details.</p>
                <p>Or check out our <a href="https://example.com/link2">latest updates</a>.</p>
                <p>Thank you,<br>The System Admin</p>
            </div>
            <div class="footer">
                <p>This email was sent from the Mobilize App. Please do not reply to this email.</p>
                <p>&copy; 2023 Mobilize App. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    email_data = {
        'id': email_id,
        'subject': f'Sample Email {email_id}',
        'sender': 'System Admin <system@example.com>',
        'recipient': f'recipient{email_id}@example.com',
        'sent_at': sent_time.strftime('%m/%d/%Y %H:%M'),
        'delivered_at': delivered_time.strftime('%m/%d/%Y %H:%M') if status != 'failed' else None,
        'opened_at': opened_at,
        'status': status,
        'status_color': status_colors[status],
        'bounce_reason': bounce_reason,
        'click_events': click_events,
        'html_content': html_content.replace('"', '\\"').replace('\n', '')
    }
    
    # Reset the random seed
    random.seed()
    
    return jsonify({
        'success': True,
        'email': email_data
    })

@admin_bp.route('/api/logs/email/resend', methods=['POST'])
@login_required
@admin_required
def resend_email():
    """API endpoint to resend an email."""
    data = request.json
    email_id = data.get('email_id')
    
    if not email_id:
        return jsonify({'success': False, 'error': 'Email ID is required'})
    
    # In a real app, we would actually resend the email
    # For demo purposes, just return success
    time.sleep(1)  # Simulate processing time
    
    return jsonify({
        'success': True,
        'message': f'Email {email_id} resent successfully'
    }) 

@admin_bp.route('/logs/database')
@login_required
@admin_required
def database_logs():
    """Display database logs and analytics."""
    # Get mock database operation stats
    stats = {
        'total_operations': 12487,
        'successful_operations': 12350,
        'failed_operations': 137,
        'avg_response_time': 28
    }
    
    # Summary data for cards
    summary = {
        'total_queries': 12487,
        'avg_query_time': 28,
        'slow_queries': 42,
        'error_rate': 1.1
    }
    
    # Mock chart data for database activity
    chart_data = {
        'labels': [(datetime.now() - timedelta(hours=i)).strftime('%H:%M') for i in range(24, 0, -1)],
        'select': [random.randint(50, 200) for _ in range(24)],
        'insert': [random.randint(10, 50) for _ in range(24)],
        'update': [random.randint(5, 30) for _ in range(24)],
        'delete': [random.randint(1, 10) for _ in range(24)]
    }
    
    # Mock operation types distribution
    operation_types = [65, 15, 12, 3, 5]  # SELECT, INSERT, UPDATE, DELETE, OTHER
    
    # Mock database logs
    logs = []
    operations = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE INDEX', 'ALTER TABLE']
    operation_weights = [0.65, 0.15, 0.12, 0.03, 0.03, 0.02]
    tables = ['users', 'contacts', 'churches', 'people', 'messages', 'tasks', 'notes', 'pipelines']
    statuses = ['SUCCESS', 'FAILED', 'SLOW']
    status_weights = [0.95, 0.03, 0.02]
    status_colors = {
        'SUCCESS': 'success',
        'FAILED': 'danger',
        'SLOW': 'warning'
    }
    
    # Generate mock log entries
    for i in range(1, 50):
        timestamp = datetime.now() - timedelta(minutes=random.randint(1, 1440))  # Last 24 hours
        operation = random.choices(operations, weights=operation_weights, k=1)[0]
        table = random.choice(tables)
        status = random.choices(statuses, weights=status_weights, k=1)[0]
        duration = random.randint(5, 500) if status != 'SLOW' else random.randint(1000, 5000)
        
        logs.append({
            'id': i,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'operation': operation,
            'table': table,
            'user': random.choice(['admin@example.com', 'system', 'scheduler', 'api@example.com']),
            'duration': duration,
            'status': status,
            'status_color': status_colors[status],
            'records_affected': random.randint(1, 100) if operation != 'SELECT' else random.randint(1, 1000)
        })
    
    # Sort logs by timestamp in descending order
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Generate mock active tables
    active_tables = []
    for table in tables[:6]:  # Take the first 6 tables
        active_tables.append({
            'name': table,
            'operations': random.randint(100, 2000),
            'avg_duration': random.randint(10, 100),
            'activity_percentage': random.randint(30, 95)
        })
    
    # Sort active tables by operations count in descending order
    active_tables.sort(key=lambda x: x['operations'], reverse=True)
    
    # Generate mock slow queries
    slow_queries = []
    sql_templates = [
        "SELECT * FROM {table} WHERE id IN (SELECT user_id FROM {related_table} WHERE created_at > '2023-01-01')",
        "SELECT * FROM {table} LEFT JOIN {related_table} ON {table}.id = {related_table}.{table_singular}_id",
        "SELECT COUNT(*) FROM {table} GROUP BY {column} HAVING COUNT(*) > 10",
        "UPDATE {table} SET updated_at = NOW() WHERE {column} = {value}",
        "INSERT INTO {table} ({columns}) VALUES ({values})"
    ]
    
    for i in range(5):
        table = random.choice(tables)
        related_table = random.choice([t for t in tables if t != table])
        table_singular = table[:-1] if table.endswith('s') else table
        column = random.choice(['id', 'name', 'created_at', 'status', 'user_id'])
        columns = ', '.join([column, 'created_at', 'updated_at'])
        values = f"'{random.randint(1, 100)}', NOW(), NOW()"
        
        sql_template = random.choice(sql_templates)
        sql = sql_template.format(
            table=table, 
            related_table=related_table,
            table_singular=table_singular,
            column=column,
            columns=columns,
            value=random.randint(1, 100),
            values=values
        )
        
        slow_queries.append({
            'sql': sql,
            'table': table,
            'duration': random.randint(1000, 5000),
            'timestamp': (datetime.now() - timedelta(minutes=random.randint(1, 1440))).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Sort slow queries by duration in descending order
    slow_queries.sort(key=lambda x: x['duration'], reverse=True)
    
    # List of tables for filter dropdown
    tables = [{'name': table} for table in tables]
    
    # Add databases for filter dropdown
    databases = ['mobilize_app', 'mobilize_analytics', 'mobilize_reporting']
    
    return render_template('admin/logs/database_logs.html', 
                          stats=stats, 
                          chart_data=chart_data, 
                          operation_types=operation_types,
                          logs=logs, 
                          active_tables=active_tables, 
                          slow_queries=slow_queries,
                          tables=tables,
                          databases=databases,
                          summary=summary)

@admin_bp.route('/api/logs/database/chart-data')
@login_required
@admin_required
def database_logs_chart_data():
    """API endpoint to get database logs chart data based on period."""
    period = request.args.get('period', 'day')
    
    # Generate different data based on the requested period
    if period == 'day':
        labels = [(datetime.now() - timedelta(hours=i)).strftime('%H:%M') for i in range(24, 0, -1)]
        select = [random.randint(50, 200) for _ in range(24)]
        insert = [random.randint(10, 50) for _ in range(24)]
        update = [random.randint(5, 30) for _ in range(24)]
        delete = [random.randint(1, 10) for _ in range(24)]
    elif period == 'week':
        labels = [(datetime.now() - timedelta(days=i)).strftime('%a') for i in range(7, 0, -1)]
        select = [random.randint(500, 1500) for _ in range(7)]
        insert = [random.randint(100, 300) for _ in range(7)]
        update = [random.randint(50, 150) for _ in range(7)]
        delete = [random.randint(10, 50) for _ in range(7)]
    else:  # month
        labels = [(datetime.now() - timedelta(days=i)).strftime('%d') for i in range(30, 0, -1)]
        select = [random.randint(1000, 3000) for _ in range(30)]
        insert = [random.randint(200, 600) for _ in range(30)]
        update = [random.randint(100, 300) for _ in range(30)]
        delete = [random.randint(20, 100) for _ in range(30)]
    
    return jsonify({
        'labels': labels,
        'select': select,
        'insert': insert,
        'update': update,
        'delete': delete
    })

@admin_bp.route('/api/logs/database/details')
@login_required
@admin_required
def database_log_details():
    """API endpoint to get detailed information about a specific database operation log."""
    log_id = request.args.get('id')
    
    if not log_id:
        return jsonify({'success': False, 'error': 'Log ID is required'})
    
    # In a real app, we would fetch actual log data from the database
    # Generate mock log details based on the ID
    random.seed(int(log_id))  # Ensure consistent results for the same ID
    
    operations = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE INDEX', 'ALTER TABLE']
    operation_weights = [0.65, 0.15, 0.12, 0.03, 0.03, 0.02]
    tables = ['users', 'contacts', 'churches', 'people', 'messages', 'tasks', 'notes', 'pipelines']
    statuses = ['SUCCESS', 'FAILED', 'SLOW']
    status_weights = [0.95, 0.03, 0.02]
    status_colors = {
        'SUCCESS': 'success',
        'FAILED': 'danger',
        'SLOW': 'warning'
    }
    
    timestamp = datetime.now() - timedelta(minutes=random.randint(1, 1440))
    operation = random.choices(operations, weights=operation_weights, k=1)[0]
    table = random.choice(tables)
    user = random.choice(['admin@example.com', 'system', 'scheduler', 'api@example.com'])
    status = random.choices(statuses, weights=status_weights, k=1)[0]
    duration = random.randint(5, 500) if status != 'SLOW' else random.randint(1000, 5000)
    records_affected = random.randint(1, 100) if operation != 'SELECT' else random.randint(1, 1000)
    
    # Generate SQL query based on operation
    columns = ['id', 'name', 'email', 'created_at', 'updated_at']
    
    if operation == 'SELECT':
        sql = f"SELECT * FROM {table} WHERE id > {random.randint(1, 100)} LIMIT {random.randint(10, 100)}"
    elif operation == 'INSERT':
        values = [f"'{random.randint(1, 1000)}'", "'Test'", "'test@example.com'", "NOW()", "NOW()"]
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)})"
    elif operation == 'UPDATE':
        sql = f"UPDATE {table} SET updated_at = NOW() WHERE id = {random.randint(1, 1000)}"
    elif operation == 'DELETE':
        sql = f"DELETE FROM {table} WHERE id = {random.randint(1, 1000)}"
    elif operation == 'CREATE INDEX':
        sql = f"CREATE INDEX idx_{table}_{columns[random.randint(0, len(columns)-1)]} ON {table} ({columns[random.randint(0, len(columns)-1)]})"
    else:  # ALTER TABLE
        sql = f"ALTER TABLE {table} ADD COLUMN new_column VARCHAR(255)"
    
    # Generate error message if status is FAILED
    error = None
    if status == 'FAILED':
        error_messages = [
            f"Error: column {random.choice(columns)} does not exist",
            "Error: syntax error at or near '='",
            "Error: relation does not exist",
            "Error: duplicate key value violates unique constraint",
            "Error: database is locked"
        ]
        error = random.choice(error_messages)
    
    # Generate execution plan for SELECT queries
    execution_plan = None
    if operation == 'SELECT':
        execution_plan = f"""
Seq Scan on {table}  (cost=0.00..{random.randint(10, 100)}.{random.randint(10, 99)} rows={records_affected} width={random.randint(20, 100)})
  Filter: (id > {random.randint(1, 100)})
"""
    
    # Reset random seed
    random.seed()
    
    log_data = {
        'id': log_id,
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'operation': operation,
        'table': table,
        'user': user,
        'duration': duration,
        'status': status,
        'status_color': status_colors[status],
        'records_affected': records_affected,
        'sql': sql,
        'error': error,
        'execution_plan': execution_plan
    }
    
    return jsonify({
        'success': True,
        'log': log_data
    })

@admin_bp.route('/roles_permissions')
@login_required
@admin_required
def roles_permissions():
    """Manage user roles and permissions."""
    # Get all roles from the database
    from app.models import Role, Permission, RolePermission
    
    # Get all roles
    roles = Role.query.all()
    
    # Get all permissions
    permissions = Permission.query.all()
    
    # Get role-permission mappings
    role_permissions = {}
    for role in roles:
        role_permissions[role.id] = [rp.permission_id for rp in RolePermission.query.filter_by(role_id=role.id).all()]
    
    # Get user counts by role
    from sqlalchemy import func
    from app.models import User
    
    user_counts = {}
    for role in roles:
        count = User.query.filter_by(role_id=role.id).count()
        user_counts[role.id] = count
    
    return render_template('admin/roles_permissions.html', 
                          roles=roles, 
                          permissions=permissions, 
                          role_permissions=role_permissions,
                          user_counts=user_counts)

@admin_bp.route('/roles_permissions/update', methods=['POST'])
@login_required
@admin_required
def update_roles_permissions():
    """Update role permissions."""
    from app.models import Role, Permission, RolePermission, db
    
    # Get form data
    role_id = request.form.get('role_id')
    permission_ids = request.form.getlist('permissions')
    
    if not role_id:
        flash('Role ID is required', 'error')
        return redirect(url_for('admin.roles_permissions'))
    
    # Get the role
    role = Role.query.get(role_id)
    if not role:
        flash('Role not found', 'error')
        return redirect(url_for('admin.roles_permissions'))
    
    try:
        # Delete existing role permissions
        RolePermission.query.filter_by(role_id=role_id).delete()
        
        # Add new role permissions
        for permission_id in permission_ids:
            role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
            db.session.add(role_permission)
        
        db.session.commit()
        flash(f'Permissions for role "{role.name}" updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating permissions: {str(e)}', 'error')
    
    return redirect(url_for('admin.roles_permissions'))

@admin_bp.route('/roles/create', methods=['POST'])
@login_required
@admin_required
def create_role():
    """Create a new role."""
    from app.models import Role, db
    
    # Get form data
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        flash('Role name is required', 'error')
        return redirect(url_for('admin.roles_permissions'))
    
    try:
        # Check if role already exists
        existing_role = Role.query.filter_by(name=name).first()
        if existing_role:
            flash(f'Role "{name}" already exists', 'error')
            return redirect(url_for('admin.roles_permissions'))
        
        # Create new role
        role = Role(name=name, description=description)
        db.session.add(role)
        db.session.commit()
        flash(f'Role "{name}" created successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating role: {str(e)}', 'error')
    
    return redirect(url_for('admin.roles_permissions'))

@admin_bp.route('/permissions/create', methods=['POST'])
@login_required
@admin_required
def create_permission():
    """Create a new permission."""
    from app.models import Permission, db
    
    # Get form data
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        flash('Permission name is required', 'error')
        return redirect(url_for('admin.roles_permissions'))
    
    try:
        # Check if permission already exists
        existing_permission = Permission.query.filter_by(name=name).first()
        if existing_permission:
            flash(f'Permission "{name}" already exists', 'error')
            return redirect(url_for('admin.roles_permissions'))
        
        # Create new permission
        permission = Permission(name=name, description=description)
        db.session.add(permission)
        db.session.commit()
        flash(f'Permission "{name}" created successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating permission: {str(e)}', 'error')
    
    return redirect(url_for('admin.roles_permissions'))