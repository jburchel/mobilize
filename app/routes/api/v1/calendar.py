from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.calendar_service import CalendarService
from app.models.user import User
from app.models.google_token import GoogleToken
from app.extensions import db
from datetime import datetime

calendar_bp = Blueprint('calendar', __name__)

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

@calendar_bp.route('/events', methods=['POST'])
@jwt_required()
def create_event():
    """Create a calendar event."""
    try:
        credentials = get_google_credentials()
        if not credentials:
            return jsonify({'error': 'Google authentication required'}), 401
        
        data = request.get_json()
        if not data or not all(k in data for k in ('summary', 'start', 'end')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            # Validate datetime format
            datetime.fromisoformat(data['start'])
            datetime.fromisoformat(data['end'])
        except ValueError:
            return jsonify({'error': 'Invalid datetime format'}), 400
        
        # Initialize Calendar service with credentials
        calendar_service = CalendarService(credentials)
        
        # TODO: Implement event creation
        return jsonify({'message': 'Event created successfully'}), 201
    except Exception as e:
        current_app.logger.error(f"Error creating event: {str(e)}")
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/events', methods=['GET'])
@jwt_required()
def get_events():
    """Get calendar events."""
    try:
        credentials = get_google_credentials()
        if not credentials:
            return jsonify({'error': 'Google authentication required'}), 401
        
        # Initialize Calendar service with credentials
        calendar_service = CalendarService(credentials)
        
        # TODO: Implement getting events
        return jsonify({'events': []}), 200
    except Exception as e:
        current_app.logger.error(f"Error getting events: {str(e)}")
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_calendar():
    """Synchronize calendar."""
    try:
        credentials = get_google_credentials()
        if not credentials:
            return jsonify({'error': 'Google authentication required'}), 401
        
        # Initialize Calendar service with credentials
        calendar_service = CalendarService(credentials)
        
        # TODO: Implement calendar sync
        return jsonify({'message': 'Calendar sync initiated'}), 200
    except Exception as e:
        current_app.logger.error(f"Error syncing calendar: {str(e)}")
        return jsonify({'error': str(e)}), 500 