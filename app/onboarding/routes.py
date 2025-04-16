from flask import Blueprint, redirect, url_for, render_template, request, flash, current_app
from flask_login import login_required, current_user
from app.extensions import db
import json

onboarding_bp = Blueprint('onboarding', __name__)

@onboarding_bp.route('/welcome')
@login_required
def welcome():
    """Show welcome page for first-time users."""
    # If user has already completed onboarding, redirect to dashboard
    if not current_user.first_login:
        return redirect(url_for('dashboard.index'))
    
    return render_template('onboarding/welcome.html')

@onboarding_bp.route('/complete', methods=['POST'])
@login_required
def complete():
    """Complete the onboarding process."""
    # Get form data
    email_sync_type = request.form.get('email_sync_type', 'all')
    email_notifications = 'email_notifications' in request.form
    task_reminders = 'task_reminders' in request.form
    task_assignments = 'task_assignments' in request.form
    system_announcements = 'system_announcements' in request.form
    
    try:
        # Update email sync preference
        current_user.email_sync_contacts_only = (email_sync_type == 'contacts_only')
        
        # Update notification settings
        notification_settings = {
            'email_notifications': email_notifications,
            'task_reminders': task_reminders,
            'task_assignments': task_assignments,
            'system_announcements': system_announcements
        }
        current_user.notification_settings = notification_settings
        
        # Mark onboarding as complete
        current_user.first_login = False
        
        # Save changes
        db.session.commit()
        
        # Show success message
        flash('Your preferences have been saved successfully. Welcome to Mobilize CRM!', 'success')
        
        # Redirect to dashboard
        return redirect(url_for('dashboard.index'))
    
    except Exception as e:
        current_app.logger.error(f"Error saving onboarding preferences: {str(e)}")
        db.session.rollback()
        flash(f'An error occurred while saving your preferences: {str(e)}', 'danger')
        return redirect(url_for('onboarding.welcome')) 