from flask import Blueprint, render_template, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import text
from app.extensions import db

communications_robust_bp = Blueprint('communications_robust', __name__, template_folder='../templates/communications')

@communications_robust_bp.route('/')
@login_required
def index():
    """Robust communications route that handles type mismatches explicitly."""
    try:
        current_app.logger.info("Starting robust communications route")
        current_app.logger.info(f"User ID: {current_user.id} (type: {type(current_user.id).__name__})")
        
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
            'page_title': "Communications Hub (Robust)"
        }
        
        # Explicitly handle email signatures with proper type conversion
        try:
            # First try direct query using text() to avoid SQLAlchemy type casting
            current_app.logger.info(f"Querying email signatures for user_id: {current_user.id}")
            
            # Use raw SQL with explicit type casting to handle both integer and string user_ids
            result = db.session.execute(
                text("""
                SELECT id, name, signature, is_default, user_id 
                FROM email_signatures 
                WHERE user_id::TEXT = :user_id_str
                """),
                {"user_id_str": str(current_user.id)}
            ).fetchall()
            
            # Process the results
            if result:
                from app.models.email_signature import EmailSignature
                
                # Convert raw results to EmailSignature objects
                signatures = []
                for row in result:
                    signature = EmailSignature(
                        id=row.id,
                        name=row.name,
                        content=row.content,
                        is_default=row.is_default,
                        user_id=row.user_id
                    )
                    signatures.append(signature)
                
                current_app.logger.info(f"Found {len(signatures)} email signatures")
                current_user.email_signatures = signatures
            else:
                current_app.logger.warning(f"No email signatures found for user_id: {current_user.id}")
                current_user.email_signatures = []
        
        except Exception as e:
            current_app.logger.error(f"Error loading email signatures: {str(e)}")
            current_app.logger.exception("Full traceback for email signature error:")
            current_user.email_signatures = []
        
        # Return a simple template with debugging information
        return render_template('communications/simple.html', **context)
    
    except Exception as e:
        current_app.logger.error(f"Error in robust communications route: {str(e)}")
        current_app.logger.exception("Full traceback:")
        
        # Return error as JSON to avoid template rendering issues
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'user_id': str(current_user.id) if hasattr(current_user, 'id') else 'Unknown',
            'user_id_type': type(current_user.id).__name__ if hasattr(current_user, 'id') else 'Unknown'
        }), 500
