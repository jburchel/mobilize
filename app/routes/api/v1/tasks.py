from flask import Blueprint, jsonify, request
from app.models.task import Task
from app.extensions import db
from app.auth.firebase import auth_required, admin_required
from sqlalchemy.exc import SQLAlchemyError

tasks_bp = Blueprint('tasks_api', __name__)

@tasks_bp.route('/', methods=['GET'])
@auth_required
def get_tasks():
    """Get all tasks with optional filtering."""
    try:
        status = request.args.get('status')
        assigned_to = request.args.get('assigned_to')
        contact_id = request.args.get('contact_id')
        
        query = Task.query
        
        if status:
            query = query.filter(Task.status == status)
        if assigned_to:
            query = query.filter(Task.assigned_to == assigned_to)
        if contact_id:
            query = query.filter(Task.contact_id == contact_id)
            
        tasks = query.all()
        return jsonify([task.to_dict() for task in tasks]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@auth_required
def get_task(task_id):
    """Get a specific task by ID."""
    try:
        task = Task.query.get_or_404(task_id)
        return jsonify(task.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/', methods=['POST'])
@auth_required
def create_task():
    """Create a new task."""
    try:
        data = request.get_json()
        task = Task(
            title=data['title'],
            description=data.get('description'),
            due_date=data.get('due_date'),
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'medium'),
            assigned_to=data.get('assigned_to'),
            contact_id=data.get('contact_id'),
            category=data.get('category')
        )
        db.session.add(task)
        db.session.commit()
        return jsonify(task.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@auth_required
def update_task(task_id):
    """Update an existing task."""
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        for key, value in data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        db.session.commit()
        return jsonify(task.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@auth_required
def delete_task(task_id):
    """Delete a task."""
    try:
        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@tasks_bp.route('/<int:task_id>/complete', methods=['POST'])
@auth_required
def complete_task(task_id):
    """Mark a task as complete."""
    try:
        task = Task.query.get_or_404(task_id)
        task.status = 'completed'
        task.completed_at = db.func.now()
        db.session.commit()
        return jsonify(task.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400 