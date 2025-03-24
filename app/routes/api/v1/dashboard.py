from flask import Blueprint, jsonify
from flask_login import current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Person, Church, Task, Communication, User
from app.utils.decorators import office_required
from datetime import datetime, timedelta
from flask import current_app

dashboard_api_bp = Blueprint('dashboard_api', __name__)

@dashboard_api_bp.route('/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    """API endpoint to get updated dashboard statistics."""
    # Get current user from JWT
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    # Get office ID from user
    office_id = user.current_office_id
    
    # Generate stats
    try:
        # Count people and churches
        people_count = Person.query.filter_by(office_id=office_id).count()
        church_count = Church.query.filter_by(office_id=office_id).count()
        
        # Count tasks
        pending_tasks = Task.query.filter_by(
            assigned_to=str(current_user_id),
            status='pending',
            office_id=office_id
        ).count()
        
        overdue_tasks = Task.query.filter(
            Task.assigned_to == str(current_user_id),
            Task.status == 'pending',
            Task.due_date < datetime.now().date(),
            Task.office_id == office_id
        ).count()
        
        # Count communications
        recent_communications = Communication.query.filter_by(
            office_id=office_id
        ).filter(
            Communication.created_at >= (datetime.now() - timedelta(days=30))
        ).count()
        
        stats = {
            'people_count': people_count,
            'church_count': church_count,
            'pending_tasks': pending_tasks,
            'overdue_tasks': overdue_tasks,
            'recent_communications': recent_communications
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        current_app.logger.error(f"Error generating dashboard stats: {str(e)}")
        return jsonify({"error": str(e)}), 500 