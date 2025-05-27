from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.extensions import db
import os

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def index():
    """Render the settings index page."""
    return render_template('settings/index.html')

@settings_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Manage user profile settings."""
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        job_title = request.form.get('job_title')
        department = request.form.get('department')
        
        # Validate required fields
        if not all([first_name, last_name, email]):
            flash('Name and email are required', 'danger')
            return redirect(url_for('settings.profile'))
        
        # Handle profile image upload
        profile_image = request.files.get('profile_image')
        if profile_image and profile_image.filename:
            try:
                # Create upload directory if it doesn't exist
                upload_dir = os.path.join('app', 'static', 'uploads', 'profiles')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generate unique filename
                import uuid
                filename = f"{uuid.uuid4()}.{profile_image.filename.split('.')[-1]}"
                filepath = os.path.join(upload_dir, filename)
                
                # Remove old profile image if it exists
                if current_user.profile_image:
                    old_filepath = os.path.join('app', current_user.profile_image.lstrip('/'))
                    if os.path.exists(old_filepath):
                        try:
                            os.remove(old_filepath)
                        except Exception as e:
                            current_app.logger.warning(f"Could not remove old profile image: {str(e)}")
                
                # Save the new profile image
                profile_image.save(filepath)
                current_user.profile_image = f"/static/uploads/profiles/{filename}"
                current_app.logger.info(f"Updated profile image for user {current_user.id} to {current_user.profile_image}")
            except Exception as e:
                current_app.logger.error(f"Error saving profile image: {str(e)}")
                flash(f'Error saving profile image: {str(e)}', 'warning')
        
        # Update user profile
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        current_user.phone = phone
        if job_title:
            current_user.job_title = job_title
        if department:
            current_user.department = department
        
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
        
        return redirect(url_for('settings.profile'))
    
    return render_template('settings/profile.html')

@settings_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    """Manage notification settings."""
    
    # Default notification settings if not set
    if not current_user.notification_settings:
        current_user.notification_settings = {
            'email_notifications': True,
            'task_reminders': True,
            'task_assignments': True,
            'system_announcements': True
        }
    
    if request.method == 'POST':
        # Update notification settings
        current_user.notification_settings = {
            'email_notifications': request.form.get('email_notifications') == 'on',
            'task_reminders': request.form.get('task_reminders') == 'on',
            'task_assignments': request.form.get('task_assignments') == 'on',
            'system_announcements': request.form.get('system_announcements') == 'on'
        }
        
        # Update legacy notification fields for backward compatibility
        current_user.notify_tasks = current_user.notification_settings['task_reminders'] or current_user.notification_settings['task_assignments']
        current_user.notify_system = current_user.notification_settings['system_announcements']
        
        try:
            db.session.commit()
            flash('Notification settings updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating notification settings: {str(e)}', 'danger')
        
        return redirect(url_for('settings.notifications'))
    
    return render_template('settings/notifications.html', user=current_user)

@settings_bp.route('/security', methods=['GET', 'POST'])
@login_required
def security():
    """Manage security settings like password change."""
    if request.method == 'POST':
        # Get form data
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate passwords
        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('settings.security'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('settings.security'))
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('settings.security'))
        
        # Update password
        current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Password updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating password: {str(e)}', 'danger')
        
        return redirect(url_for('settings.security'))
    
    return render_template('settings/security.html')

@settings_bp.route('/email', methods=['GET', 'POST'])
@login_required
def email():
    """Manage email settings like sync preferences."""
    if request.method == 'POST':
        # Get form data
        email_sync_type = request.form.get('email_sync_type')
        
        try:
            # Update user's email sync preference
            current_user.email_sync_contacts_only = (email_sync_type == 'contacts_only')
            
            db.session.commit()
            flash('Email settings updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating email settings: {str(e)}")
            
            # If the column doesn't exist yet, attempt to create it
            if "no such column" in str(e):
                try:
                    from sqlalchemy import text
                    with db.engine.connect() as conn:
                        # Add the column if it doesn't exist
                        conn.execute(text(
                            "ALTER TABLE users ADD COLUMN email_sync_contacts_only BOOLEAN DEFAULT 0"
                        ))
                        conn.commit()
                        
                        # Try to update the user's preference again
                        current_user.email_sync_contacts_only = (email_sync_type == 'contacts_only')
                        db.session.commit()
                        
                        flash('Email settings updated successfully', 'success')
                        current_app.logger.info("Created email_sync_contacts_only column and updated user preference")
                    
                except Exception as inner_e:
                    db.session.rollback()
                    current_app.logger.error(f"Error creating email_sync_contacts_only column: {str(inner_e)}")
                    flash(f'Error updating email settings: Database schema needs to be updated', 'danger')
            else:
                flash(f'Error updating email settings: {str(e)}', 'danger')
        
        return redirect(url_for('settings.email'))
    
    return render_template('settings/email.html') 