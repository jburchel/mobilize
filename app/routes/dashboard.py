from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import Person, Church, Task, Communication
from app.utils.decorators import office_required
from datetime import datetime, timedelta
from flask import current_app

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
@office_required
def index():
    """Render the dashboard view with relevant statistics."""
    office_id = current_user.office_id
    
    # Get dashboard statistics
    stats = get_dashboard_stats()
    
    # Get pending tasks for the current user
    pending_tasks = Task.query.filter_by(
        assigned_to=current_user.id, 
        status='pending'
    ).order_by(Task.due_date.asc()).limit(5).all()
    
    # Get recent communications
    recent_communications = Communication.query.filter_by(
        office_id=office_id
    ).order_by(
        Communication.created_at.desc()
    ).limit(5).all()
    
    # Prepare recent activities list
    recent_activities = []
    
    # Add communications to activities
    for comm in recent_communications:
        contact_name = "Unknown"
        
        # Try to get the person's name
        if comm.person_id:
            person = Person.query.get(comm.person_id)
            if person:
                contact_name = f"{person.first_name} {person.last_name}"
        
        # Try to get the church's name
        elif comm.church_id:
            church = Church.query.get(comm.church_id)
            if church:
                contact_name = church.name
                
        comm_type = comm.type.capitalize() if comm.type else "Communication"
        activity = {
            'type': 'communication',
            'description': f"{comm_type} with {contact_name}",
            'timestamp': comm.created_at,
            'id': comm.id
        }
        recent_activities.append(activity)
    
    # Add completed tasks to activities (optional)
    recent_completed_tasks = Task.query.filter(
        Task.office_id == office_id,
        Task.status == 'completed',
        Task.completed_date.isnot(None)
    ).order_by(Task.completed_date.desc()).limit(5).all()
    
    for task in recent_completed_tasks:
        activity = {
            'type': 'task',
            'description': f'Task completed: {task.title}',
            'timestamp': task.completed_date,
            'id': task.id
        }
        recent_activities.append(activity)
    
    # Sort all activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]  # Limit to 10 most recent
    
    return render_template(
        'dashboard/index.html',
        stats=stats,
        pending_tasks=pending_tasks,
        recent_activities=recent_activities
    )

@dashboard_bp.route('/api/stats')
@login_required
@office_required
def dashboard_stats_api():
    """API endpoint to get updated dashboard statistics."""
    stats = get_dashboard_stats()
    return jsonify(stats)

def get_dashboard_stats():
    """Helper function to generate dashboard statistics."""
    office_id = current_user.office_id
    
    # Count people and churches
    try:
        people_count = Person.query.filter_by(office_id=office_id).count()
    except Exception as e:
        current_app.logger.error(f"Error counting people: {str(e)}")
        people_count = 0
        
    try:
        church_count = Church.query.filter_by(office_id=office_id).count()
    except Exception as e:
        current_app.logger.error(f"Error counting churches: {str(e)}")
        church_count = 0
        
    # Count tasks
    try:
        pending_tasks = Task.query.filter_by(
            assigned_to=current_user.id,
            status='pending',
            office_id=office_id
        ).count()
        overdue_tasks = Task.query.filter(
            Task.assigned_to == current_user.id,
            Task.status == 'pending',
            Task.due_date < datetime.now().date(),
            Task.office_id == office_id
        ).count()
    except Exception as e:
        current_app.logger.error(f"Error counting tasks: {str(e)}")
        pending_tasks = 0
        overdue_tasks = 0
        
    # Count communications
    try:
        recent_communications = Communication.query.filter_by(
            office_id=office_id
        ).filter(
            Communication.created_at >= (datetime.now() - timedelta(days=30))
        ).count()
    except Exception as e:
        current_app.logger.error(f"Error counting communications: {str(e)}")
        recent_communications = 0
    
    return {
        'people_count': people_count,
        'church_count': church_count,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_communications': recent_communications
    } 