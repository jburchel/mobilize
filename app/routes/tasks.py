from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models.task import Task
from app.models.contact import Contact
from app.models.person import Person
from app.models.church import Church
from app.models.user import User
from app.extensions import db

tasks_bp = Blueprint('tasks', __name__, template_folder='../templates/tasks')

@tasks_bp.route('/')
@tasks_bp.route('/list')
@login_required
def list():
    """Display list of tasks."""
    # Fetch tasks from database
    tasks = Task.query.order_by(Task.due_date.asc()).all()
    
    # Calculate overdue tasks
    overdue_count = 0
    current_date = datetime.now().date()
    for task in tasks:
        if task.status != 'completed' and task.due_date and task.due_date < current_date:
            overdue_count += 1
            
    return render_template('tasks/list.html', 
                          tasks=tasks, 
                          overdue_count=overdue_count,
                          current_date=current_date,
                          page_title="Task Management")

@tasks_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new task."""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        status = request.form.get('status')
        priority = request.form.get('priority')
        due_date_str = request.form.get('due_date')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        
        assigned_to = request.form.get('assigned_to')
        contact_type = request.form.get('contact_type')
        person_id = request.form.get('person_id') if contact_type == 'person' else None
        church_id = request.form.get('church_id') if contact_type == 'church' else None
        
        # Create new task
        task = Task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_date=due_date,
            assigned_to=assigned_to if assigned_to else None,
            person_id=person_id if person_id else None,
            church_id=church_id if church_id else None,
            created_by=current_user.id,
            owner_id=current_user.id,
            office_id=current_user.office_id,
            reminder_option=request.form.get('reminder_option', 'none'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task added successfully!', 'success')
        return redirect(url_for('tasks.list'))
    
    # For GET request, display the form
    people = Person.query.all()
    churches = Church.query.all()
    users = User.query.all()
    
    return render_template('tasks/add.html', 
                          people=people,
                          churches=churches,
                          users=users,
                          page_title="Add Task")

@tasks_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing task."""
    task = Task.query.get_or_404(id)
    
    if request.method == 'POST':
        # Update task with form data
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.status = request.form.get('status')
        task.priority = request.form.get('priority')
        
        due_date_str = request.form.get('due_date')
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        
        assigned_to = request.form.get('assigned_to')
        task.assigned_to = assigned_to if assigned_to else None
        
        contact_type = request.form.get('contact_type')
        if contact_type == 'person':
            task.person_id = request.form.get('person_id')
            task.church_id = None
        elif contact_type == 'church':
            task.church_id = request.form.get('church_id')
            task.person_id = None
        else:
            task.person_id = None
            task.church_id = None
            
        # Handle reminder option
        task.reminder_option = request.form.get('reminder_option', 'none')
        
        task.updated_at = datetime.now()
        db.session.commit()
        
        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks.list'))
    
    # For GET request, display the form with existing data
    people = Person.query.all()
    churches = Church.query.all()
    users = User.query.all()
    
    # Mock task history for now
    task_history = [
        {
            'action': 'Task Created',
            'description': f'Task "{task.title}" was created',
            'date': task.created_at,
            'user': current_user
        }
    ]
    
    if task.updated_at and task.updated_at > task.created_at:
        task_history.append({
            'action': 'Task Updated',
            'description': 'Task details were updated',
            'date': task.updated_at,
            'user': current_user
        })
    
    return render_template('tasks/edit.html', 
                          task=task,
                          people=people,
                          churches=churches,
                          users=users,
                          task_history=task_history,
                          current_date=datetime.now().date(),
                          page_title=f"Edit Task: {task.title}")

@tasks_bp.route('/complete/<int:id>', methods=['POST'])
@login_required
def complete(id):
    """Mark a task as completed."""
    task = Task.query.get_or_404(id)
    
    # Update the task
    task.status = 'completed'
    task.completed_date = datetime.now()
    
    # Add completion notes if provided
    completion_notes = request.form.get('completion_notes')
    if completion_notes:
        task.completion_notes = completion_notes
        
    task.updated_at = datetime.now()
    db.session.commit()
    
    flash('Task marked as completed!', 'success')
    return redirect(url_for('tasks.list'))

@tasks_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a task."""
    task = Task.query.get_or_404(id)
    
    # Delete the task
    db.session.delete(task)
    db.session.commit()
    
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('tasks.list')) 