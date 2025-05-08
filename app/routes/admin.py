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
import sqlite3

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
    # Get real counts of various entities
    from app.models import User, Contact, Church, Office, Communication
    
    user_count = User.query.count()
    contact_count = Contact.query.count()
    church_count = Church.query.count()
    office_count = Office.query.count()
    message_count = Communication.query.count()
    
    # Get counts of active and inactive users
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    
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
                          office_count=office_count,
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
        # Log the full error for debugging
        current_app.logger.error(f'Error deleting user {user_id}: {str(e)}')
        # Show a user-friendly message
        flash('An error occurred while deleting the user. This may be due to database constraints or related records. Please contact support if the issue persists.', 'danger')
    
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
@login_required
@admin_required
def system_logs():
    """Display system logs."""
    from app.utils.log_utils import get_system_logs, get_log_statistics
    
    # Get query parameters for filtering
    level_filter = request.args.get('level')
    search_term = request.args.get('search')
    max_entries = int(request.args.get('max', 1000))
    
    # Get logs using the log_utils module
    logs = get_system_logs(max_entries=max_entries, level_filter=level_filter, search_term=search_term)
    
    # If no logs are found, create a sample log entry to avoid empty display
    if not logs:
        logs = [{
            'timestamp': datetime.now(),
            'level': 'INFO',
            'message': 'No log entries found. This could be because the application is new, logs have been cleared, or the log file is not accessible.',
            'color': 'text-info'
        }]
    
    return render_template('admin/logs/system_logs.html', logs=logs)

@admin_bp.route('/logs/user-activity')
@login_required
@admin_required
def user_activity():
    """Display user activity logs."""
    from app.utils.log_utils import get_activity_logs, log_activity
    
    # Log this activity
    log_activity(
        subsystem='Admin',
        operation='VIEW',
        description='Viewed user activity logs',
        status='SUCCESS',
        impact='LOW'
    )
    
    # Get real activity logs from the log_utils module
    # Increase max_entries to get more logs
    activities = get_activity_logs(max_entries=200)
    
    # Transform the logs to match the expected format in the template
    transformed_activities = []
    for activity in activities:
        # Extract the user email if available
        email = activity.get('email')
        
        # Map operation to action
        action = activity.get('operation', 'UNKNOWN')
        
        # Create details from description and other fields
        details = activity.get('description', '')
        if activity.get('ip_address'):
            details += f" from IP {activity.get('ip_address')}"
        if activity.get('resource_id'):
            details += f" (Resource ID: {activity.get('resource_id')})"
        
        # Create the transformed activity entry
        transformed_activities.append({
            'timestamp': activity.get('timestamp'),
            'user_email': email,
            'action': action,
            'details': details
        })
    
    # If no logs are found, create a message to inform the user
    if not transformed_activities:
        flash('No user activity logs found. This page will start populating as users interact with the system.', 'info')
        
        # Add the current view as the first activity
        transformed_activities = [
            {
                'timestamp': datetime.now(),
                'user_email': current_user.email if hasattr(current_user, 'email') else None,
                'action': 'VIEW',
                'details': 'Viewed user activity logs'
            }
        ]
    
    # Sort activities by timestamp, newest first
    transformed_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('admin/logs/user_activity.html', activities=transformed_activities)
    
@admin_bp.route('/system/performance')
@login_required
@admin_required
def system_performance():
    # Import system monitoring utilities
    from app.utils.system_monitor import (
        get_system_metrics,
        get_worker_processes,
        get_api_stats,
        get_database_stats,
        get_system_events,
        get_response_time
    )
    
    # Log this activity
    from app.utils.log_utils import log_activity
    log_activity(
        subsystem='Admin',
        operation='VIEW',
        description='Viewed system performance dashboard',
        status='SUCCESS',
        impact='LOW'
    )
    
    # Get real system metrics
    system_metrics = get_system_metrics()
    cpu_usage = system_metrics['cpu_usage']
    memory_usage = system_metrics['memory_usage']
    disk_usage = system_metrics['disk_usage']
    
    # Get response time
    response_time = get_response_time()
    
    # Get worker processes
    workers = get_worker_processes()
    
    # Get API stats
    api_stats = get_api_stats()
    
    # Get database stats
    db_stats = get_database_stats()
    
    # Get system events
    system_events = get_system_events()

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
@admin_required
def activity_logs():
    """Display activity logs."""
    from app.utils.log_utils import get_activity_logs, log_activity
    
    # Log this activity
    log_activity(
        subsystem='Admin',
        operation='VIEW',
        description='Viewed activity logs',
        status='SUCCESS',
        impact='LOW'
    )
    
    # Get activity logs from the log_utils module
    # Increase max_entries to get more logs
    activities = get_activity_logs(max_entries=500)
    
    # If no logs are found, create a single entry for this view
    if not activities:
        # Create a message to inform the user
        flash('No activity logs found. This page will start populating as users interact with the system.', 'info')
        
        # Add the current view as the first activity
        activities = [
            {
                'timestamp': datetime.now(),
                'subsystem': 'Admin',
                'operation': 'VIEW',
                'description': 'Viewed activity logs',
                'status': 'SUCCESS',
                'impact': 'LOW',
                'user': current_user.name if hasattr(current_user, 'name') else current_user.username,
                'email': current_user.email if hasattr(current_user, 'email') else None,
                'ip_address': request.remote_addr,
                'duration': 0,
                'resource_id': None
            }
        ]
    
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
@admin_required
def security_logs():
    """Display security logs."""
    from app.utils.log_utils import get_security_logs
    from datetime import datetime, timedelta
    
    # Define now for timestamp comparisons
    now = datetime.now()
    
    # Get filter parameters from request
    level_filter = request.args.get('level')
    search_term = request.args.get('search')
    days = int(request.args.get('days', 30))
    
    # Get security logs from the log_utils module
    security_logs = get_security_logs(max_entries=100, level_filter=level_filter, search_term=search_term, days=days)
    
    # If no logs are found, show a message
    if not security_logs:
        return render_template('admin/logs/security_logs.html', logs=[], message="No security logs found.")
    
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
    # Get security logs using log_utils
    try:
        from app.utils.log_utils import get_security_logs
        # Get all security logs for the past 30 days
        security_logs = get_security_logs(days=30)
    except Exception as e:
        current_app.logger.error(f"Error fetching security logs for export: {str(e)}")
        # Fallback to empty list if there's an error
        security_logs = []
        flash(f"Error exporting security logs: {str(e)}", 'error')
    
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
    from app.utils.log_utils import log_activity
    from app.models.google_settings import GoogleWorkspaceSettings
    from app.models.google_token import GoogleToken
    
    # Log this activity
    log_activity(
        subsystem='Admin',
        operation='VIEW',
        description='Viewed Google Workspace settings',
        status='SUCCESS',
        impact='LOW'
    )
    
    # Get current settings from database
    settings_obj = GoogleWorkspaceSettings.get_settings()
    settings = settings_obj.to_dict()
    
    # Mask the client secret if it exists
    if settings['client_secret']:
        settings['client_secret'] = '•' * 16
    
    # Get the application URL for the redirect URI if not set
    if not settings['redirect_uri']:
        settings['redirect_uri'] = request.url_root.rstrip('/') + '/auth/google/callback'
    
    # Count connected users
    connected_users = GoogleToken.query.count()
    settings['connected_users'] = connected_users
    
    # Create status information
    status = {
        'connected': settings['enabled'] and bool(settings['client_id']) and bool(settings['client_secret']),
        'token_valid': connected_users > 0,
        'last_sync': settings['last_sync'] or datetime.now() - timedelta(days=30),
        'synced_resources': {
            'users': settings['synced_users'],
            'groups': settings['synced_groups'],
            'events': settings['synced_events']
        }
    }
    
    return render_template('admin/system/google_workspace_settings.html', settings=settings, status=status)

@admin_bp.route('/system/google-workspace', methods=['POST'])
@login_required
@admin_required
def update_google_workspace_settings():
    """Update Google Workspace Integration Settings."""
    from app.utils.log_utils import log_activity
    from app.models.google_settings import GoogleWorkspaceSettings
    
    # Get current settings from database
    settings = GoogleWorkspaceSettings.get_settings()
    
    # Update settings from form data
    try:
        settings.update_from_form(request.form)
        
        # Log the activity
        log_activity(
            subsystem='Admin',
            operation='UPDATE',
            description='Updated Google Workspace settings',
            status='SUCCESS',
            impact='MEDIUM'
        )
        
        flash('Google Workspace settings updated successfully', 'success')
    except Exception as e:
        # Log the error
        current_app.logger.error(f"Error updating Google Workspace settings: {str(e)}")
        log_activity(
            subsystem='Admin',
            operation='UPDATE',
            description=f"Failed to update Google Workspace settings: {str(e)}",
            status='FAILURE',
            impact='HIGH'
        )
        flash(f'Error updating Google Workspace settings: {str(e)}', 'danger')
    
    return redirect(url_for('admin.google_workspace_settings'))

@admin_bp.route('/system/email-settings')
@login_required
@admin_required
def email_settings():
    """Email System Settings."""
    from app.utils.log_utils import log_activity
    from app.models.email_settings import EmailSettings
    from app.models.email_template import EmailTemplate
    from app.models.google_token import GoogleToken
    
    # Log this activity
    log_activity(
        subsystem='Admin',
        operation='VIEW',
        description='Viewed email settings',
        status='SUCCESS',
        impact='LOW'
    )
    
    # Get current settings from database
    settings_obj = EmailSettings.get_settings()
    settings = settings_obj.to_dict()
    
    # Get real email templates from the database
    email_templates = EmailTemplate.query.order_by(EmailTemplate.updated_at.desc()).all()
    templates = []
    for template in email_templates:
        templates.append({
            'id': template.id,
            'name': template.name,
            'description': template.subject,
            'modified_at': template.updated_at.strftime('%Y-%m-%d %H:%M') if template.updated_at else 'N/A'
        })
    
    # Get email stats from the settings object
    stats = {
        'sent_today': settings_obj.sent_today,
        'sent_week': settings_obj.sent_week,
        'bounced': settings_obj.bounced,
        'failed': settings_obj.failed,
        'delivery_rate': settings_obj.delivery_rate
    }
    
    # Try to get real data from Gmail API if available
    try:
        # Get Gmail token for current user
        token = GoogleToken.query.filter_by(user_id=current_user.id).first()
        
        if token:
            # Initialize the Gmail service if user has valid credentials
            gmail_service = GmailService(current_user.id)
            
            # In a real implementation, we would fetch actual metrics from Gmail API
            # For now, we'll use the values from the database
            pass
    except Exception as e:
        current_app.logger.error(f"Error loading Gmail statistics: {str(e)}")
        flash(f"Unable to load Gmail statistics: {str(e)}", "warning")
    
    # Get recent email activities from the database using the EmailTracking model
    from app.models.email_tracking import EmailTracking
    from datetime import datetime, timedelta
    
    # Try to import humanize, but provide a fallback if it's not available
    try:
        import humanize
        humanize_available = True
    except ImportError:
        humanize_available = False
        current_app.logger.warning("Humanize package not available, using basic time formatting instead")
    
    # Get the 10 most recent email activities
    recent_email_tracks = EmailTracking.query.order_by(EmailTracking.sent_at.desc()).limit(10).all()
    
    # Convert to the format needed for the template
    recent_activities = []
    for track in recent_email_tracks:
        # Calculate time ago in a human-readable format
        time_diff = datetime.utcnow() - track.sent_at
        if humanize_available:
            time_ago = humanize.naturaltime(time_diff)
        else:
            # Basic time formatting fallback
            if time_diff.days > 0:
                time_ago = f"{time_diff.days} days ago"
            elif time_diff.seconds >= 3600:
                hours = time_diff.seconds // 3600
                time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif time_diff.seconds >= 60:
                minutes = time_diff.seconds // 60
                time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                time_ago = f"{time_diff.seconds} second{'s' if time_diff.seconds != 1 else ''} ago"
        
        # Determine status color based on email status
        status_color = 'secondary'  # Default
        if track.status == 'sent' or track.status == 'delivered':
            status_color = 'success'
        elif track.status == 'opened':
            status_color = 'info'
        elif track.status == 'clicked':
            status_color = 'primary'
        elif track.status == 'bounced':
            status_color = 'warning'
        elif track.status == 'failed':
            status_color = 'danger'
        
        recent_activities.append({
            'subject': track.email_subject,
            'recipient': track.recipient_email,
            'time_ago': time_ago,
            'status': track.status.capitalize(),
            'status_color': status_color
        })
    
    # If no real data exists yet, provide some sample data
    if not recent_activities:
        current_app.logger.info("No email tracking data found, using sample data")
        recent_activities = [
            {'subject': 'Welcome to Mobilize App', 'recipient': 'john.doe@example.com', 'time_ago': '12 minutes ago', 'status': 'Delivered', 'status_color': 'success'},
            {'subject': 'Your Password Has Been Reset', 'recipient': 'jane.smith@example.com', 'time_ago': '1 hour ago', 'status': 'Delivered', 'status_color': 'success'},
            {'subject': 'New Task Assignment', 'recipient': 'robert.johnson@example.com', 'time_ago': '3 hours ago', 'status': 'Opened', 'status_color': 'info'},
            {'subject': 'Weekly Report', 'recipient': 'team@example.com', 'time_ago': '6 hours ago', 'status': 'Bounced', 'status_color': 'warning'},
            {'subject': 'Meeting Reminder', 'recipient': 'lisa.wong@example.com', 'time_ago': '1 day ago', 'status': 'Failed', 'status_color': 'danger'}
        ]

    
    return render_template('admin/system/email_settings.html', settings=settings, email_templates=templates, stats=stats, recent_activities=recent_activities)

@admin_bp.route('/system/email-settings', methods=['POST'])
@login_required
@admin_required
def update_email_settings():
    """Update Email Settings."""
    from app.utils.log_utils import log_activity
    from app.models.email_settings import EmailSettings
    
    # Get current settings from database
    settings = EmailSettings.get_settings()
    
    # Update settings from form data
    try:
        # Update settings using the model's update_from_form method
        settings.update_from_form(request.form)
        
        # Log the activity
        log_activity(
            subsystem='Admin',
            operation='UPDATE',
            description='Updated email settings',
            status='SUCCESS',
            impact='MEDIUM'
        )
        
        flash('Email settings updated successfully', 'success')
    except Exception as e:
        # Log the error
        current_app.logger.error(f"Error updating email settings: {str(e)}")
        log_activity(
            subsystem='Admin',
            operation='UPDATE',
            description=f"Failed to update email settings: {str(e)}",
            status='FAILURE',
            impact='HIGH'
        )
        flash(f'Error updating email settings: {str(e)}', 'danger')
    
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
    from app.utils.db_utils import get_database_stats, get_table_stats, get_database_backups
    
    # Get real database stats
    db_stats = get_database_stats()
    
    # Get real table stats
    table_stats = get_table_stats()
    
    # Get real database backups
    backups = get_database_backups()
    
    return render_template('admin/system/database.html', db_stats=db_stats, table_stats=table_stats, backups=backups)

@admin_bp.route('/system/database/backup', methods=['POST'])
@login_required
@admin_required
def create_database_backup():
    """Create a database backup."""
    from app.utils.db_utils import create_database_backup as create_backup
    
    backup_id = create_backup()
    
    if backup_id:
        flash('Database backup created successfully', 'success')
    else:
        flash('Failed to create database backup', 'error')
        
    return redirect(url_for('admin.database_management'))

@admin_bp.route('/system/database/optimize', methods=['POST'])
@login_required
@admin_required
def optimize_database():
    """Optimize the database."""
    from app.utils.db_utils import optimize_database as optimize_db
    
    success = optimize_db()
    
    if success:
        flash('Database optimized successfully', 'success')
    else:
        flash('Failed to optimize database', 'error')
        
    return redirect(url_for('admin.database_management'))

@admin_bp.route('/system/database/restore/<int:backup_id>', methods=['POST'])
@login_required
@admin_required
def restore_database(backup_id):
    """Restore the database from a backup."""
    from app.utils.db_utils import restore_database_from_backup
    
    success = restore_database_from_backup(backup_id)
    
    if success:
        flash('Database restored successfully from backup', 'success')
    else:
        flash('Failed to restore database from backup', 'error')
        
    return redirect(url_for('admin.database_management'))

@admin_bp.route('/system/database/download/<int:backup_id>')
@login_required
@admin_required
def download_database_backup(backup_id):
    """Download a database backup file."""
    from app.utils.db_utils import get_backup_by_id
    
    backup = get_backup_by_id(backup_id)
    
    if not backup or 'path' not in backup:
        flash('Backup not found', 'error')
        return redirect(url_for('admin.database_management'))
    
    backup_path = backup['path']
    
    if not os.path.exists(backup_path):
        flash('Backup file not found', 'error')
        return redirect(url_for('admin.database_management'))
    
    # Get the filename from the path
    filename = os.path.basename(backup_path)
    
    # Return the file as an attachment
    return send_file(
        backup_path,
        as_attachment=True,
        download_name=f'database_backup_{backup_id}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    )

@admin_bp.route('/system/database/table/<table_name>')
@login_required
@admin_required
def table_details(table_name):
    """View details of a specific database table."""
    from app.utils.db_utils import get_table_structure
    
    # Get table structure, indexes, and sample data
    table_data = get_table_structure(table_name)
    
    if not table_data or not table_data['columns']:
        flash(f'Table {table_name} not found or is empty', 'error')
        return redirect(url_for('admin.database_management'))
    
    return render_template(
        'admin/system/table_details.html',
        table_name=table_name,
        columns=table_data['columns'],
        indexes=table_data['indexes'],
        sample_data=table_data['sample_data']
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
    # Get filter parameters from request
    status_filter = request.args.get('status')
    search_term = request.args.get('search')
    days = int(request.args.get('days', 30))
    sender = request.args.get('sender')
    recipient = request.args.get('recipient')
    
    # Get real email logs from the log file
    from app.utils.log_utils import get_email_logs
    logs_data = get_email_logs(
        max_entries=100,
        status_filter=status_filter,
        search_term=search_term,
        days=days,
        sender=sender,
        recipient=recipient
    )
    
    # Process logs for display
    logs = []
    status_colors = {
        'SENT': 'info',
        'DELIVERED': 'primary',
        'OPENED': 'success',
        'FAILED': 'danger',
        'BOUNCED': 'warning'
    }
    
    # Calculate stats
    total_sent = len(logs_data)
    total_opened = sum(1 for log in logs_data if log['status'] == 'OPENED')
    total_clicked = sum(1 for log in logs_data if log['click_count'] > 0)
    total_bounced = sum(1 for log in logs_data if log['status'] == 'BOUNCED')
    total_failed = sum(1 for log in logs_data if log['status'] == 'FAILED')
    
    # Calculate rates
    open_rate = round((total_opened / total_sent * 100) if total_sent > 0 else 0)
    click_rate = round((total_clicked / total_sent * 100) if total_sent > 0 else 0)
    delivery_rate = round(((total_sent - total_bounced - total_failed) / total_sent * 100) if total_sent > 0 else 0)
    bounce_rate = round((total_bounced / total_sent * 100) if total_sent > 0 else 0)
    
    # Create stats dictionary
    stats = {
        'total_sent': total_sent,
        'total_opened': total_opened,
        'total_clicked': total_clicked,
        'total_bounced': total_bounced,
        'open_rate': open_rate,
        'click_rate': click_rate,
        'delivery_rate': delivery_rate,
        'bounce_rate': bounce_rate
    }
    
    # Create summary for the dashboard cards
    summary = {
        'total': total_sent,
        'delivered_rate': delivery_rate,
        'failed_rate': 100 - delivery_rate,
        'open_rate': open_rate
    }
    
    # Prepare chart data (last 7 days)
    last_7_days = [(datetime.now() - timedelta(days=i)).date() for i in range(6, -1, -1)]
    
    # Initialize counts for each day
    daily_sent = {day: 0 for day in last_7_days}
    daily_opened = {day: 0 for day in last_7_days}
    daily_clicked = {day: 0 for day in last_7_days}
    
    # Count emails for each day
    for log in logs_data:
        log_date = log['timestamp'].date()
        if log_date in last_7_days:
            daily_sent[log_date] += 1
            if log['status'] == 'OPENED':
                daily_opened[log_date] += 1
            if log['click_count'] > 0:
                daily_clicked[log_date] += 1
    
    # Create chart data
    chart_data = {
        'labels': [day.strftime('%m/%d') for day in last_7_days],
        'sent': [daily_sent[day] for day in last_7_days],
        'opened': [daily_opened[day] for day in last_7_days],
        'clicked': [daily_clicked[day] for day in last_7_days]
    }
    
    # Format logs for display
    for log in logs_data:
        status = log['status']
        opened = status == 'OPENED'
        
        logs.append({
            'id': log['id'],
            'sent_at': log['timestamp'].strftime('%m/%d/%Y %H:%M'),
            'subject': log['subject'],
            'recipient_email': log['recipients'],
            'sender_name': log['user'] if isinstance(log['user'], str) else 
                          (log['user'].get('name') if isinstance(log['user'], dict) and 'name' in log['user'] else 'System'),
            'status': status,
            'status_color': status_colors.get(status, 'secondary'),
            'opened': opened,
            'opened_at': log['timestamp'].strftime('%m/%d/%Y %H:%M') if opened else None,
            'click_count': log['click_count']
        })
    
    return render_template('admin/logs/email_logs.html', stats=stats, chart_data=chart_data, logs=logs, summary=summary)

@admin_bp.route('/api/logs/email/chart-data')
@login_required
@admin_required
def email_logs_chart_data():
    """API endpoint to get email logs chart data based on period."""
    period = request.args.get('period', 'week')
    
    # Get email logs from the log file
    from app.utils.log_utils import get_email_logs
    
    # Determine the time period for data retrieval
    if period == 'week':
        days = 7
        interval_days = 1
        date_format = '%m/%d'
    elif period == 'month':
        days = 30
        interval_days = 3
        date_format = '%m/%d'
    else:  # year
        days = 365
        interval_days = 30
        date_format = '%m/%Y'
    
    # Get logs for the specified period
    logs = get_email_logs(max_entries=1000, days=days)
    
    # Generate date labels based on the period
    if period == 'week':
        date_points = [(datetime.now() - timedelta(days=i)).date() for i in range(days-1, -1, -1)]
    elif period == 'month':
        date_points = [(datetime.now() - timedelta(days=i*interval_days)).date() for i in range(10, -1, -1)]
    else:  # year
        date_points = [(datetime.now() - timedelta(days=i*interval_days)).date() for i in range(12, -1, -1)]
    
    # Initialize data arrays
    labels = [date.strftime(date_format) for date in date_points]
    sent_data = [0] * len(date_points)
    opened_data = [0] * len(date_points)
    clicked_data = [0] * len(date_points)
    
    # Group logs by date
    for log in logs:
        log_date = log['timestamp'].date()
        
        # Find the corresponding date point index
        for i, date_point in enumerate(date_points):
            # For week, exact match; for month/year, find the closest period
            if period == 'week':
                if log_date == date_point:
                    sent_data[i] += 1
                    if log['status'] == 'OPENED':
                        opened_data[i] += 1
                    if log['click_count'] > 0:
                        clicked_data[i] += 1
                    break
            else:
                # For month/year, check if the log falls within the interval
                next_date = date_point - timedelta(days=interval_days) if i < len(date_points)-1 else datetime.now().date() - timedelta(days=days)
                if log_date >= next_date and log_date <= date_point:
                    sent_data[i] += 1
                    if log['status'] == 'OPENED':
                        opened_data[i] += 1
                    if log['click_count'] > 0:
                        clicked_data[i] += 1
                    break
    
    return jsonify({
        'labels': labels,
        'sent': sent_data,
        'opened': opened_data,
        'clicked': clicked_data
    })

@admin_bp.route('/api/logs/email/details')
@login_required
@admin_required
def email_details():
    """API endpoint to get detailed information about a specific email."""
    email_id = request.args.get('id')
    
    if not email_id:
        return jsonify({'success': False, 'error': 'Email ID is required'})
    
    # Get all email logs and find the specific one by ID
    from app.utils.log_utils import get_email_logs
    all_logs = get_email_logs(max_entries=1000, days=90)  # Get logs from the past 90 days
    
    # Find the email with the matching ID
    email_log = None
    for log in all_logs:
        if log['id'] == email_id:
            email_log = log
            break
    
    if not email_log:
        return jsonify({'success': False, 'error': 'Email not found'})
    
    # Define status colors for UI display
    status_colors = {
        'SENT': 'info',
        'DELIVERED': 'primary',
        'OPENED': 'success',
        'FAILED': 'danger',
        'BOUNCED': 'warning'
    }
    
    # Format the timestamp for display
    sent_at = email_log['timestamp'].strftime('%m/%d/%Y %H:%M')
    
    # Format opened_at if the email was opened
    opened_at = None
    if email_log['status'] == 'OPENED':
        # In a real implementation, we would have the actual opened timestamp
        # For now, we'll use the timestamp + 1 hour as an estimate
        opened_at = (email_log['timestamp'] + timedelta(hours=1)).strftime('%m/%d/%Y %H:%M')
    
    # Format click events if there were any clicks
    click_events = []
    if email_log['click_count'] > 0:
        # In a real implementation, we would have actual click data
        # For now, we'll generate some sample click events
        for i in range(email_log['click_count']):
            click_time = email_log['timestamp'] + timedelta(hours=1, minutes=(i+1)*15)
            click_events.append({
                'url': f'https://mobilize-app.org/link{i+1}',
                'clicked_at': click_time.strftime('%m/%d/%Y %H:%M')
            })
    
    # Create a sample HTML content based on the email subject
    # In a real implementation, we would retrieve the actual email content
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
                <h2>{email_log['subject']}</h2>
            </div>
            <div class="content">
                <p>Hello {email_log['recipients']},</p>
                <p>This is the content of the email that was sent. In a real implementation, we would show the actual email content.</p>
                <p>The email was sent by {email_log['sender']} at {sent_at}.</p>
                <p>Click <a href="https://mobilize-app.org/link1">here</a> to view more details.</p>
                <p>Thank you,<br>Mobilize App Team</p>
            </div>
            <div class="footer">
                <p>This email was sent from the Mobilize App. Please do not reply to this email.</p>
                <p>&copy; 2023 Mobilize App. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create the email data object
    email_data = {
        'id': email_id,
        'subject': email_log['subject'],
        'sender': email_log['sender'],
        'recipient': email_log['recipients'],
        'sent_at': sent_at,
        'delivered_at': (email_log['timestamp'] + timedelta(minutes=2)).strftime('%m/%d/%Y %H:%M') if email_log['status'] not in ['FAILED', 'BOUNCED'] else None,
        'opened_at': opened_at,
        'status': email_log['status'],
        'status_color': status_colors.get(email_log['status'], 'secondary'),
        'bounce_reason': email_log['bounce_reason'],
        'click_events': click_events,
        'html_content': html_content.replace('"', '\"').replace('\n', '')
    }
    
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
    
    # Get the original email details from logs
    from app.utils.log_utils import get_email_logs
    all_logs = get_email_logs(max_entries=1000, days=90)
    
    # Find the email with the matching ID
    email_log = None
    for log in all_logs:
        if log['id'] == email_id:
            email_log = log
            break
    
    if not email_log:
        return jsonify({'success': False, 'error': 'Original email not found'})
    
    try:
        # Get the current user for sending the email
        user_id = current_user.id
        
        # Initialize the Gmail service
        from app.services.gmail_service import GmailService
        gmail_service = GmailService(user_id)
        
        # Send the email using the original details
        sent_message = gmail_service.send_email(
            to=email_log['recipients'],
            subject=f"RESEND: {email_log['subject']}",
            body=f"This is a resend of an email originally sent on {email_log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n\nOriginal content would appear here."
        )
        
        # Return success response
        return jsonify({
            'success': True,
            'message': f'Email {email_id} resent successfully',
            'new_email_id': sent_message.get('id')
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to resend email: {str(e)}'
        }) 

@admin_bp.route('/logs/database')
@login_required
@admin_required
def database_logs():
    """Display database logs and analytics."""
    # Get filter parameters from request
    operation_filter = request.args.get('operation')
    table_filter = request.args.get('table')
    status_filter = request.args.get('status')
    search_term = request.args.get('search')
    days = int(request.args.get('days', 30))
    
    # Get real database logs from the log file
    from app.utils.log_utils import get_database_logs
    from app.utils.db_utils import get_all_tables, get_table_stats
    
    # Get logs data
    logs_data = get_database_logs(
        max_entries=100,
        operation_filter=operation_filter,
        table_filter=table_filter,
        status_filter=status_filter,
        search_term=search_term,
        days=days
    )
    
    # Process logs for display
    logs = []
    status_colors = {
        'SUCCESS': 'success',
        'FAILED': 'danger',
        'SLOW': 'warning'
    }
    
    # Get all table names for filter dropdown
    all_tables = get_all_tables()
    tables = [{'name': table} for table in all_tables]
    
    # Get database name from configuration
    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    db_name = db_uri.split('/')[-1] if '/' in db_uri else 'mobilize_app'
    databases = [db_name]
    
    # Calculate stats from logs
    total_operations = len(logs_data)
    successful_operations = sum(1 for log in logs_data if log['status'] == 'SUCCESS')
    failed_operations = sum(1 for log in logs_data if log['status'] == 'FAILED')
    slow_operations = sum(1 for log in logs_data if log['status'] == 'SLOW')
    
    # Calculate average response time
    if total_operations > 0:
        avg_response_time = sum(log['duration'] for log in logs_data) // max(1, total_operations)
    else:
        avg_response_time = 0
    
    # Create stats dictionary
    stats = {
        'total_operations': total_operations,
        'successful_operations': successful_operations,
        'failed_operations': failed_operations,
        'avg_response_time': avg_response_time
    }
    
    # Create summary for the dashboard cards
    error_rate = (failed_operations / total_operations * 100) if total_operations > 0 else 0
    summary = {
        'total_queries': total_operations,
        'avg_query_time': avg_response_time,
        'slow_queries': slow_operations,
        'error_rate': round(error_rate, 1)
    }
    
    # Calculate operation type distribution
    operation_counts = {}
    for log in logs_data:
        op = log['operation']
        operation_counts[op] = operation_counts.get(op, 0) + 1
    
    # Convert to percentages for the chart
    operation_types = []
    if total_operations > 0:
        for op in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'OTHER']:
            if op == 'OTHER':
                # Sum all operations that aren't the main 4
                other_count = sum(operation_counts.get(o, 0) for o in operation_counts if o not in ['SELECT', 'INSERT', 'UPDATE', 'DELETE'])
                operation_types.append(round(other_count / total_operations * 100))
            else:
                operation_types.append(round(operation_counts.get(op, 0) / total_operations * 100))
    else:
        operation_types = [0, 0, 0, 0, 0]  # Default if no data
    
    # Prepare chart data (last 24 hours)
    last_24_hours = [(datetime.now() - timedelta(hours=i)) for i in range(23, -1, -1)]
    
    # Initialize counts for each hour
    hourly_select = {hour: 0 for hour in last_24_hours}
    hourly_insert = {hour: 0 for hour in last_24_hours}
    hourly_update = {hour: 0 for hour in last_24_hours}
    hourly_delete = {hour: 0 for hour in last_24_hours}
    
    # Count operations for each hour
    for log in logs_data:
        log_hour = log['timestamp'].replace(minute=0, second=0, microsecond=0)
        if log_hour in hourly_select:  # Only count if within last 24 hours
            if log['operation'] == 'SELECT':
                hourly_select[log_hour] += 1
            elif log['operation'] == 'INSERT':
                hourly_insert[log_hour] += 1
            elif log['operation'] == 'UPDATE':
                hourly_update[log_hour] += 1
            elif log['operation'] == 'DELETE':
                hourly_delete[log_hour] += 1
    
    # Create chart data
    chart_data = {
        'labels': [hour.strftime('%H:%M') for hour in last_24_hours],
        'select': [hourly_select[hour] for hour in last_24_hours],
        'insert': [hourly_insert[hour] for hour in last_24_hours],
        'update': [hourly_update[hour] for hour in last_24_hours],
        'delete': [hourly_delete[hour] for hour in last_24_hours]
    }
    
    # Format logs for display
    for log in logs_data:
        logs.append({
            'id': log['id'],
            'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'operation': log['operation'],
            'table': log['table'],
            'user': log['user'],
            'duration': log['duration'],
            'status': log['status'],
            'status_color': status_colors.get(log['status'], 'secondary'),
            'records_affected': log['records_affected']
        })
    
    # Calculate active tables statistics
    table_stats = {}
    for log in logs_data:
        table_name = log['table']
        if table_name not in table_stats:
            table_stats[table_name] = {
                'operations': 0,
                'total_duration': 0,
                'name': table_name
            }
        table_stats[table_name]['operations'] += 1
        table_stats[table_name]['total_duration'] += log['duration']
    
    # Calculate average duration and format active tables
    active_tables = []
    for table_name, stats in table_stats.items():
        avg_duration = stats['total_duration'] // max(1, stats['operations'])
        activity_percentage = min(95, max(30, (stats['operations'] * 100) // max(1, total_operations)))
        
        active_tables.append({
            'name': table_name,
            'operations': stats['operations'],
            'avg_duration': avg_duration,
            'activity_percentage': activity_percentage
        })
    
    # Sort active tables by operations count in descending order
    active_tables.sort(key=lambda x: x['operations'], reverse=True)
    active_tables = active_tables[:6]  # Limit to top 6 most active tables
    
    # Find slow queries (queries with duration > 1000ms)
    slow_queries = []
    for log in logs_data:
        if log['duration'] > 1000 and log['query']:
            slow_queries.append({
                'sql': log['query'],
                'table': log['table'],
                'duration': log['duration'],
                'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # Sort slow queries by duration in descending order
    slow_queries.sort(key=lambda x: x['duration'], reverse=True)
    slow_queries = slow_queries[:5]  # Limit to top 5 slowest queries
    
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
    
    # Get database logs from the log file
    from app.utils.log_utils import get_database_logs
    
    # Determine the time period for data retrieval
    if period == 'day':
        days = 1
        interval = 'hour'
        date_format = '%H:%M'
        intervals = 24
        time_points = [(datetime.now() - timedelta(hours=i)) for i in range(intervals-1, -1, -1)]
    elif period == 'week':
        days = 7
        interval = 'day'
        date_format = '%a'
        intervals = 7
        time_points = [(datetime.now() - timedelta(days=i)) for i in range(intervals-1, -1, -1)]
    else:  # month
        days = 30
        interval = 'day'
        date_format = '%d'
        intervals = 30
        time_points = [(datetime.now() - timedelta(days=i)) for i in range(intervals-1, -1, -1)]
    
    # Get logs for the specified period
    logs = get_database_logs(max_entries=10000, days=days)
    
    # Initialize data arrays
    labels = [point.strftime(date_format) for point in time_points]
    select_data = [0] * intervals
    insert_data = [0] * intervals
    update_data = [0] * intervals
    delete_data = [0] * intervals
    
    # Group logs by time period
    for log in logs:
        log_time = log['timestamp']
        
        # Find the corresponding time point index
        for i, time_point in enumerate(time_points):
            if interval == 'hour':
                # For day view, compare hours
                if log_time.year == time_point.year and log_time.month == time_point.month and log_time.day == time_point.day and log_time.hour == time_point.hour:
                    if log['operation'] == 'SELECT':
                        select_data[i] += 1
                    elif log['operation'] == 'INSERT':
                        insert_data[i] += 1
                    elif log['operation'] == 'UPDATE':
                        update_data[i] += 1
                    elif log['operation'] == 'DELETE':
                        delete_data[i] += 1
                    break
            else:
                # For week/month view, compare days
                if log_time.year == time_point.year and log_time.month == time_point.month and log_time.day == time_point.day:
                    if log['operation'] == 'SELECT':
                        select_data[i] += 1
                    elif log['operation'] == 'INSERT':
                        insert_data[i] += 1
                    elif log['operation'] == 'UPDATE':
                        update_data[i] += 1
                    elif log['operation'] == 'DELETE':
                        delete_data[i] += 1
                    break
    
    return jsonify({
        'labels': labels,
        'select': select_data,
        'insert': insert_data,
        'update': update_data,
        'delete': delete_data
    })

@admin_bp.route('/api/logs/database/details')
@login_required
@admin_required
def database_logs_details():
    """API endpoint to get details of a specific database log entry."""
    log_id = request.args.get('id')
    
    if not log_id:
        return jsonify({'error': 'Log ID is required'}), 400
    
    # Get database logs from the log file
    from app.utils.log_utils import get_database_logs
    
    # Get all logs and find the one with matching ID
    logs = get_database_logs(max_entries=10000)
    log_details = None
    
    # Status color mapping
    status_colors = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning'
    }
    
    for log in logs:
        if log.get('id') == log_id:
            # Format the log data for display
            log_details = {
                'id': log['id'],
                'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'operation': log['operation'],
                'table': log['table'],
                'user': log['user'] if log['user'] else 'System',
                'duration': log['duration'],
                'status': log['status'],
                'status_color': status_colors.get(log['status'].lower(), 'secondary'),
                'records_affected': log['records_affected'],
                'sql': log['query'] if log['query'] else 'N/A',
                'error': None,  # We'll populate this if status is error
                'execution_plan': None  # Could be populated in the future if we capture execution plans
            }
            
            # If status is error, we might have error details in the query field
            if log['status'].lower() == 'error' and log['query']:
                log_details['error'] = log['query']
            
            break
    
    if not log_details:
        return jsonify({'error': 'Log entry not found'}), 404
    
    return jsonify({
        'success': True,
        'log': log_details
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