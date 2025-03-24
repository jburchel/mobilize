from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.gmail_service import GmailService
from app.models.user import User
from app.models.google_token import GoogleToken
from app.extensions import db

gmail_bp = Blueprint('gmail', __name__)

def get_google_credentials():
    """Get Google credentials for the current user."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return None
    
    token = GoogleToken.query.filter_by(user_id=user.id).first()
    if not token:
        return None
    
    return token.to_credentials()

@gmail_bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_emails():
    """Synchronize emails."""
    try:
        credentials = get_google_credentials()
        if not credentials:
            return jsonify({'error': 'Google authentication required'}), 401
        
        # Initialize Gmail service with credentials
        gmail_service = GmailService(credentials)
        
        # TODO: Implement email sync
        return jsonify({'message': 'Email sync initiated'}), 200
    except Exception as e:
        current_app.logger.error(f"Error syncing emails: {str(e)}")
        return jsonify({'error': str(e)}), 500

@gmail_bp.route('/send', methods=['POST'])
@jwt_required()
def send_email():
    """Send an email."""
    try:
        credentials = get_google_credentials()
        if not credentials:
            return jsonify({'error': 'Google authentication required'}), 401
        
        data = request.get_json()
        if not data or not all(k in data for k in ('to', 'subject', 'body')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Initialize Gmail service with credentials
        gmail_service = GmailService(credentials)
        
        # TODO: Implement email sending
        return jsonify({'message': 'Email sent successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        return jsonify({'error': str(e)}), 500

@gmail_bp.route('/threads', methods=['GET'])
@jwt_required()
def get_threads():
    """Get email threads."""
    try:
        credentials = get_google_credentials()
        if not credentials:
            return jsonify({'error': 'Google authentication required'}), 401
        
        # Initialize Gmail service with credentials
        gmail_service = GmailService(credentials)
        
        # TODO: Implement getting email threads
        return jsonify({'threads': []}), 200
    except Exception as e:
        current_app.logger.error(f"Error getting threads: {str(e)}")
        return jsonify({'error': str(e)}), 500 