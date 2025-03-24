from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User
from app.extensions import db

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
        
        # Validate required fields
        if not all([first_name, last_name, email]):
            flash('Name and email are required', 'danger')
            return redirect(url_for('settings.profile'))
        
        # Update user profile
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        current_user.phone = phone
        
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
        
        return redirect(url_for('settings.profile'))
    
    return render_template('settings/profile.html')

@settings_bp.route('/notifications')
@login_required
def notifications():
    """Manage notification settings."""
    return render_template('settings/notifications.html')

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