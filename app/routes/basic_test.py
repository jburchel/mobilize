from flask import Blueprint, jsonify, current_app

# Create a blueprint without any dependencies on other parts of the app
basic_test_bp = Blueprint('basic_test', __name__)

@basic_test_bp.route('/')
def index():
    """Most basic test route possible - no login required, no database access."""
    try:
        current_app.logger.info("Basic test route accessed")
        
        # Return the simplest possible response
        return jsonify({
            'status': 'success',
            'message': 'Basic test route working',
            'app_info': {
                'debug': current_app.debug,
                'env': current_app.env
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error in basic test route: {str(e)}")
        current_app.logger.exception("Full traceback:")
        return jsonify({
            'status': 'error',
            'message': f"Error: {str(e)}",
            'error_type': type(e).__name__
        }), 500
