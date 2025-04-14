from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.calendar_service import CalendarService
from app.models.user import User
from app.models.google_token import GoogleToken
from app.extensions import db
from datetime import datetime
from app.models.task import Task

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

@calendar_bp.route("/sync-reminder-settings", methods=["POST"])
@jwt_required()
def sync_reminder_settings():
    """
    Sync reminder settings for one or multiple tasks with Google Calendar.
    Requires:
    - task_ids: List of task IDs in the request JSON
    - reminder_option (optional): New reminder option to set (e.g., "15_min", "1_hour")
    """
    from flask import current_app, request, jsonify
    from app.models.task import Task
    from app.services.calendar_service import CalendarService

    user = User.query.get(get_jwt_identity())
    data = request.get_json()
    
    if not data or 'task_ids' not in data:
        return jsonify({"error": "Missing task_ids parameter"}), 400
    
    task_ids = data.get('task_ids', [])
    if not isinstance(task_ids, list) or not task_ids:
        return jsonify({"error": "task_ids must be a non-empty list"}), 400

    # Check if we need to update the reminder option
    new_reminder_option = data.get('reminder_option')
    update_reminder = new_reminder_option is not None

    # Get Google Calendar credentials
    credentials = get_google_credentials()
    if not credentials:
        return jsonify({"error": "Google Calendar credentials not found"}), 401

    try:
        calendar_service = CalendarService(credentials)
        results = {}
        
        for task_id in task_ids:
            task = Task.query.get(task_id)
            
            if not task:
                results[task_id] = {
                    "success": False,
                    "message": "Task not found"
                }
                continue
                
            # Check task ownership/permissions
            if task.user_id != user.id:
                results[task_id] = {
                    "success": False,
                    "message": "Unauthorized access to task"
                }
                continue
                
            if not task.google_calendar_sync_enabled or not task.google_calendar_event_id:
                results[task_id] = {
                    "success": False,
                    "message": "Task not synced with Google Calendar"
                }
                continue
            
            # Update reminder option if requested
            if update_reminder:
                task.reminder_option = new_reminder_option
                db.session.commit()
                
            # Attempt to sync reminder settings
            updated_event = calendar_service.sync_reminder_settings(task)
            
            if updated_event:
                # Update last synced timestamp
                task.last_synced_at = datetime.utcnow()
                db.session.commit()
                
                results[task_id] = {
                    "success": True,
                    "message": "Reminder settings updated successfully"
                }
            else:
                results[task_id] = {
                    "success": False,
                    "message": "Failed to update reminder settings"
                }
        
        return jsonify({
            "success": True,
            "results": results
        })
    
    except Exception as e:
        import traceback
        error = f"Error syncing reminder settings: {str(e)}\n{traceback.format_exc()}"
        current_app.logger.error(error)
        return jsonify({"error": str(e)}), 500 