from flask import Blueprint, render_template, current_app, flash
from flask_login import login_required, current_user

communications_simple_bp = Blueprint('communications_simple', __name__, template_folder='../templates/communications')

@communications_simple_bp.route('/')
@communications_simple_bp.route('/index')
@login_required
def index():
    """Simplified communications hub that avoids complex queries."""
    try:
        current_app.logger.info("Starting simplified communications index route")
        
        # Create a very basic context with minimal data
        context = {
            'communications': [],
            'pagination': {
                'page': 1,
                'per_page': 50,
                'total': 0,
                'pages': 0,
                'has_next': False,
                'has_prev': False
            },
            'page_title': "Communications Hub"
        }
        
        # Skip loading email signatures entirely
        current_user.email_signatures = []
        
        # Log what we're doing
        current_app.logger.info("Rendering simplified communications template")
        
        # Render the simplified template
        return render_template('communications/simple.html', **context)
    except Exception as e:
        current_app.logger.error(f"Error in simplified communications index: {str(e)}")
        current_app.logger.exception("Full traceback:")
        flash('Error loading communications. Please try again later.', 'error')
        return render_template('error.html', error_message=f"Error: {str(e)}", page_title="Error")
