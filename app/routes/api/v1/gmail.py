from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.gmail_service import GmailService
from app.models.user import User
from app.models.google_token import GoogleToken
from app.extensions import db
from app.models.communication import Communication
from datetime import datetime, timezone

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
        user_id = get_jwt_identity()
        token = GoogleToken.query.filter_by(user_id=user_id).first()
        
        if not token:
            return jsonify({'error': 'Google authentication required'}), 401
        
        data = request.get_json()
        if not data or not all(k in data for k in ('to', 'subject', 'body')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Initialize Gmail service with user_id
        gmail_service = GmailService(user_id)
        
        # Send the email
        html_body = data.get('html_body', data['body'])  # Use HTML body if provided, or fall back to plain text
        result = gmail_service.send_email(
            to=data['to'],
            subject=data['subject'],
            body=data['body'],
            html=html_body
        )
        
        # Get user object to get office_id
        user = User.query.get(user_id)
        office_id = user.office_id if user and hasattr(user, 'office_id') else None
        
        # Save communication record
        communication = Communication(
            type='email',
            subject=data['subject'],
            message=data['body'],
            person_id=data.get('person_id'),
            church_id=data.get('church_id'),
            user_id=user_id,
            owner_id=user_id,
            office_id=office_id,
            direction='outbound',
            date_sent=datetime.now(timezone.utc),
            email_status='sent',
            gmail_message_id=result.get('id'),
            gmail_thread_id=result.get('threadId')
        )
        db.session.add(communication)
        db.session.commit()
        
        return jsonify({
            'message': 'Email sent successfully', 
            'email_id': result.get('id'),
            'thread_id': result.get('threadId')
        }), 200
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

@gmail_bp.route('/reauth', methods=['GET'])
@jwt_required()
def reauthorize():
    """Force re-authorization by removing the current token."""
    try:
        user_id = get_jwt_identity()
        token = GoogleToken.query.filter_by(user_id=user_id).first()
        
        if token:
            # Just delete the token to force re-auth
            db.session.delete(token)
            db.session.commit()
            return jsonify({'message': 'Token removed, please re-authorize with Google'}), 200
        else:
            return jsonify({'message': 'No token found, nothing to remove'}), 200
    except Exception as e:
        current_app.logger.error(f"Error removing token: {str(e)}")
        return jsonify({'error': str(e)}), 500 