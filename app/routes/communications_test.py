from flask import Blueprint, current_app, jsonify
from flask_login import login_required, current_user

communications_test_bp = Blueprint('communications_test', __name__)

@communications_test_bp.route('/')
@login_required
def index():
    """Ultra-simplified test route that returns just JSON data."""
    try:
        current_app.logger.info("Starting ultra-simplified communications test route")
        
        # Create a very basic response with minimal data and no database queries
        data = {
            'status': 'success',
            'message': 'Communications test route working',
            'user': {
                'id': str(current_user.id),
                'id_type': type(current_user.id).__name__,
                'email': current_user.email if hasattr(current_user, 'email') else 'No email attribute'
            }
        }
        
        # Log what we're doing
        current_app.logger.info(f"Returning test data: {data}")
        
        # Return simple JSON response
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error in test route: {str(e)}")
        current_app.logger.exception("Full traceback:")
        return jsonify({
            'status': 'error',
            'message': f"Error: {str(e)}",
            'error_type': type(e).__name__
        }), 500
