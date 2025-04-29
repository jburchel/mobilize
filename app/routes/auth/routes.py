from flask import Blueprint, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.routes.auth import auth_bp
from app.models.google_token import GoogleToken
from app.extensions import db

@auth_bp.route('/reauth/google')
@login_required
def reauth_google():
    """Force re-authorization with Google."""
    try:
        # Remove current token to force re-auth
        token = GoogleToken.query.filter_by(user_id=current_user.id).first()
        if token:
            db.session.delete(token)
            db.session.commit()
            flash('Google token cleared, please re-authorize', 'success')
        
        # Redirect to Google OAuth
        return redirect(url_for('auth.google_login'))
    except Exception as e:
        current_app.logger.error(f"Error during Google reauth: {str(e)}")
        flash(f'Error during Google reauthorization: {str(e)}', 'error')
        return redirect(url_for('dashboard.index')) 