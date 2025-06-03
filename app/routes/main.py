from flask import Blueprint, redirect, url_for, render_template, current_app
from flask_login import login_required, current_user

# Create Blueprint
main_bp = Blueprint('main', __name__)

# Basic routes
@main_bp.route('/')
def index():
    try:
        # Check if Flask-Login is properly initialized
        if hasattr(current_app, 'login_manager'):
            if current_user.is_authenticated:
                return redirect(url_for('dashboard.dashboard'))
            return redirect(url_for('auth.login'))
        else:
            # Fallback if login_manager is not available
            current_app.logger.error("Flask-Login not properly initialized")
            return render_template('error.html', 
                                  error_title="Configuration Error",
                                  error_message="The authentication system is not properly configured.")
    except Exception as e:
        current_app.logger.error(f"Error in main index route: {str(e)}")
        # Simple fallback that doesn't depend on other routes
        return """
        <html>
            <head><title>Mobilize CRM</title></head>
            <body>
                <h1>Mobilize CRM</h1>
                <p>The application is currently experiencing technical difficulties.</p>
                <p>Please try again later or contact support.</p>
                <a href="/auth/login">Try logging in</a>
            </body>
        </html>
        """

@main_bp.route('/home')
@login_required
def home():
    return redirect(url_for('dashboard.dashboard'))
