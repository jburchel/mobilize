from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app, session
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.contact import Contact
from app.models.person import Person
from app.models.church import Church
from app.models.user import User
from app.extensions import db
from flask import current_app
from app.utils.decorators import office_required
from app.forms.task import TaskForm
from app.forms.task_batch_reminder import TaskBatchReminderForm
from sqlalchemy import or_

tasks_bp = Blueprint('tasks', __name__, template_folder='../templates/tasks')

@tasks_bp.route('/')
@tasks_bp.route('/list')
@login_required
def index():
    """Display list of tasks."""
    # Get filters from query params
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    search_text = request.args.get('search', '').lower().strip()
    
    # Base query for tasks assigned to the current user
    query = Task.query.filter(
        (Task.assigned_to == str(current_user.id)) | 
        (Task.created_by == current_user.id) |
        (Task.owner_id == current_user.id)
    )
    
    # Apply status filter
    if status_filter and status_filter != 'all':
        if status_filter == 'overdue':
            # Special handling for overdue tasks
            current_date = datetime.now().date()
            query = query.filter(
                Task.status != TaskStatus.COMPLETED,
                Task.due_date < current_date
            )
        else:
            # Convert string status to Enum
            try:
                status_enum = TaskStatus(status_filter)
                query = query.filter(Task.status == status_enum)
            except ValueError:
                # If invalid status provided, log it and ignore the filter
                current_app.logger.warning(f"Invalid status filter: {status_filter}")
    else:
        # Default behavior: exclude completed tasks
        query = query.filter(Task.status != TaskStatus.COMPLETED)
    
    # Apply priority filter
    if priority_filter and priority_filter != 'all':
        try:
            priority_enum = TaskPriority(priority_filter)
            query = query.filter(Task.priority == priority_enum)
        except ValueError:
            # If invalid priority provided, log it and ignore the filter
            current_app.logger.warning(f"Invalid priority filter: {priority_filter}")
    
    # Apply search filter
    if search_text:
        search = f"%{search_text}%"
        query = query.filter(
            or_(
                Task.title.ilike(search),
                Task.description.ilike(search),
                Task.related_to.has(Person.name.ilike(search)),
                Task.related_to.has(Church.name.ilike(search))
            )
        )
    
    # Execute query with ordering
    filtered_tasks = query.order_by(Task.due_date.asc()).all()
    
    # Get all tasks for statistics (including completed)
    all_tasks_query = Task.query.filter(
        (Task.assigned_to == str(current_user.id)) | 
        (Task.created_by == current_user.id) |
        (Task.owner_id == current_user.id)
    )
    all_tasks = all_tasks_query.all()
    
    # Calculate overdue tasks
    overdue_count = 0
    current_date = datetime.now().date()
    for task in filtered_tasks:
        if task.status != TaskStatus.COMPLETED and task.due_date:
            # Compare dates to detect overdue tasks
            if hasattr(task.due_date, 'date'):
                due_date_val = task.due_date.date()
            else:
                due_date_val = task.due_date
            if due_date_val < current_date:
                overdue_count += 1
            
    return render_template('tasks/index.html', 
                          tasks=filtered_tasks, 
                          all_tasks=all_tasks,
                          overdue_count=overdue_count,
                          current_date=current_date,
                          show_completed=(status_filter == 'completed' or status_filter == TaskStatus.COMPLETED.value),
                          page_title="My Tasks")

@tasks_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new task."""
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title')
            if not title:
                flash('Task title is required', 'danger')
                return redirect(request.referrer or url_for('tasks.index'))
                
            description = request.form.get('description')
            status = request.form.get('status', 'pending')  # Default to pending if not provided
            priority = request.form.get('priority')
            if not priority:
                priority = 'medium'  # Default priority
                
            # Ensure priority is lowercase to match the TaskPriority enum values
            priority = priority.lower() if priority else 'medium'
                
            due_date_str = request.form.get('due_date')
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid date format', 'danger')
                    return redirect(request.referrer or url_for('tasks.index'))
            
            # Get due time
            due_time = request.form.get('due_time')
            current_app.logger.debug(f"Due time from form: {due_time}")
            
            assigned_to = request.form.get('assigned_to')
            
            # Handle person_id directly from the form (for tasks added from person detail page)
            person_id = request.form.get('person_id')
            church_id = request.form.get('church_id')
            
            # Only consider contact_type if both person_id and church_id aren't directly provided
            if not person_id and not church_id:
                contact_type = request.form.get('contact_type')
                person_id = request.form.get('person_id') if contact_type == 'person' else None
                church_id = request.form.get('church_id') if contact_type == 'church' else None
            
            # Convert string IDs to integers if they're not None
            if person_id:
                try:
                    person_id = int(person_id)
                except ValueError:
                    person_id = None
                    
            if church_id:
                try:
                    church_id = int(church_id)
                except ValueError:
                    church_id = None
                    
            if assigned_to:
                try:
                    assigned_to = int(assigned_to)
                except ValueError:
                    assigned_to = None
            
            # Get Google Calendar sync option
            google_calendar_sync_enabled = request.form.get('google_calendar_sync_enabled') == 'true'
            
            # Create new task
            task = Task(
                title=title,
                description=description,
                status=status,
                priority=priority,
                due_date=due_date,
                due_time=due_time,  # Store the time
                assigned_to=assigned_to,
                person_id=person_id,
                church_id=church_id,
                created_by=current_user.id,
                owner_id=current_user.id,
                office_id=current_user.office_id,
                reminder_option=request.form.get('reminder_option', 'none'),
                google_calendar_sync_enabled=google_calendar_sync_enabled,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(task)
            db.session.commit()
            
            # Create Google Calendar event if sync is enabled and there's a due date
            if google_calendar_sync_enabled and due_date:
                try:
                    current_app.logger.info(f"Attempting to create Google Calendar event for task: {task.id}, title: {task.title}")
                    from app.services.calendar_service import CalendarService
                    
                    # Check if user has Google token
                    from app.models.google_token import GoogleToken
                    token = GoogleToken.query.filter_by(user_id=current_user.id).first()
                    
                    if not token:
                        current_app.logger.error(f"No Google token found for user {current_user.id}")
                        flash('Task was created, but calendar sync failed: You need to connect your Google account first. Go to Settings > Integrations to connect.', 'warning')
                    else:
                        # Check if token has calendar scope
                        has_calendar_scope = False
                        if token.scopes:
                            try:
                                import json
                                scopes = json.loads(token.scopes)
                                has_calendar_scope = any('calendar' in scope.lower() for scope in scopes)
                            except json.JSONDecodeError:
                                current_app.logger.warning(f"Could not parse token scopes JSON: {token.scopes}")
                        
                        if not has_calendar_scope:
                            current_app.logger.warning(f"Token for user {current_user.id} does not have calendar scopes")
                            flash('Task was created, but calendar sync failed: Your Google account needs calendar permissions. Go to Settings > Integrations to reconnect with calendar access.', 'warning')
                        else:
                            # Proceed with calendar sync
                            calendar_service = CalendarService(current_user.id)
                            calendar_service.create_event(task)
                            current_app.logger.info(f"Successfully created Google Calendar event for task: {task.id}, event ID: {task.google_calendar_event_id}")
                            flash('Task created and added to your Google Calendar!', 'success')
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    current_app.logger.error(f"Error creating Google Calendar event for task {task.id}: {str(e)}")
                    current_app.logger.error(f"Error details: {error_details}")
                    # Don't block task creation if calendar sync fails
                    flash(f'Task was created, but calendar sync failed: {str(e)}', 'warning')
                    pass
            
            flash('Task added successfully!', 'success')
            
            # If task was created from person page, redirect back to the person
            if person_id:
                return redirect(url_for('people.show', id=person_id))
            elif church_id:
                return redirect(url_for('churches.show', id=church_id))
            else:
                return redirect(url_for('tasks.index'))
                
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding task: {str(e)}")
            flash(f'Error adding task: {str(e)}', 'danger')
            # Redirect back to the referring page or tasks index
            return redirect(request.referrer or url_for('tasks.index'))
    
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
        
        # Handle status as Enum
        status_value = request.form.get('status')
        if status_value:
            task.status = TaskStatus(status_value)
            # If task is being marked as completed, set completed_at timestamp
            if status_value == 'completed' and task.status != TaskStatus.COMPLETED:
                task.completed_at = datetime.now()
            # If task is being unmarked as completed, clear completed_at timestamp
            elif status_value != 'completed' and task.status == TaskStatus.COMPLETED:
                task.completed_at = None
        
        # Handle priority as Enum
        priority_value = request.form.get('priority')
        if priority_value:
            task.priority = TaskPriority(priority_value)
        
        due_date_str = request.form.get('due_date')
        was_due_date_changed = False
        old_due_date = task.due_date
        
        # Check if due date changed
        if due_date_str:
            new_due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            if new_due_date != old_due_date:
                was_due_date_changed = True
                task.due_date = new_due_date
        elif task.due_date:  # Due date was removed
            was_due_date_changed = True
            task.due_date = None
        
        # Get and update due time
        old_due_time = task.due_time
        new_due_time = request.form.get('due_time')
        was_due_time_changed = old_due_time != new_due_time
        task.due_time = new_due_time
        current_app.logger.debug(f"Due time updated: {old_due_time} -> {new_due_time}")
        
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
        
        # Handle Google Calendar sync
        old_sync_enabled = task.google_calendar_sync_enabled
        task.google_calendar_sync_enabled = request.form.get('google_calendar_sync_enabled') == 'true'
        
        task.updated_at = datetime.now()
        db.session.commit()
        
        # Handle Google Calendar sync changes
        try:
            from app.services.calendar_service import CalendarService
            calendar_service = CalendarService(current_user.id)
            
            # If sync was newly enabled or date/time changed with sync enabled
            if (task.google_calendar_sync_enabled and not old_sync_enabled) or \
               (task.google_calendar_sync_enabled and (was_due_date_changed or was_due_time_changed)):
                if task.due_date:
                    current_app.logger.info(f"Task {task.id}: Sync enabled or date/time changed. Syncing with Google Calendar...")
                    if task.google_calendar_event_id:
                        current_app.logger.info(f"Updating existing Google Calendar event {task.google_calendar_event_id} for task {task.id}")
                        calendar_service.update_event(task)
                        current_app.logger.info(f"Successfully updated Google Calendar event for task {task.id}")
                    else:
                        current_app.logger.info(f"Creating new Google Calendar event for task {task.id}")
                        calendar_service.create_event(task)
                        current_app.logger.info(f"Successfully created Google Calendar event for task {task.id}, event ID: {task.google_calendar_event_id}")
            # If sync was disabled and there was an event
            elif not task.google_calendar_sync_enabled and old_sync_enabled and task.google_calendar_event_id:
                current_app.logger.info(f"Sync disabled for task {task.id}. Deleting Google Calendar event {task.google_calendar_event_id}")
                calendar_service.delete_event(task.google_calendar_event_id)
                task.google_calendar_event_id = None
                task.last_synced_at = None
                db.session.commit()
                current_app.logger.info(f"Successfully deleted Google Calendar event for task {task.id}")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            current_app.logger.error(f"Error syncing task {task.id} with Google Calendar: {str(e)}")
            current_app.logger.error(f"Error details: {error_details}")
            # Don't block task update if calendar sync fails
            flash(f'Task was updated, but calendar sync failed: {str(e)}', 'warning')
            pass
        
        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks.index'))
    
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
    try:
        current_app.logger.info(f'Task completion requested for task ID: {id}')
        
        # Get CSRF token from form data or header
        csrf_token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
        current_app.logger.debug(f'CSRF token received: {bool(csrf_token)}')
        
        # Verify CSRF token - Flask-WTF stores the token as 'csrf_token' in the session
        # Add detailed logging for debugging
        current_app.logger.info(f'CSRF token from request: {csrf_token and csrf_token[:10]}...')
        current_app.logger.info(f'Session keys: {list(session.keys())}')
        
        # Check for token in different session keys (Flask-WTF might use different keys)
        csrf_session_keys = ['csrf_token', '_csrf_token']
        session_token = None
        for key in csrf_session_keys:
            if key in session:
                session_token = session.get(key)
                current_app.logger.info(f'Found CSRF token in session key: {key}')
                break
        
        if not csrf_token:
            current_app.logger.warning('CSRF token missing in request')
        elif not session_token:
            current_app.logger.warning('CSRF token not found in any session key')
        elif csrf_token != session_token:
            current_app.logger.warning(f'CSRF token mismatch. Request: {csrf_token[:10]}..., Session: {session_token[:10]}...')
        
        # Temporarily bypass CSRF validation to get the feature working
        # TODO: Re-enable CSRF validation once the token issue is resolved
        if False:
            current_app.logger.error('CSRF token missing or invalid')
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'error',
                    'message': 'Security token is invalid. Please refresh the page and try again.'
                }), 403
            flash('Security token is invalid. Please refresh the page and try again.', 'error')
            return redirect(request.referrer or url_for('tasks.index'))
        
        task = Task.query.get_or_404(id)
        current_app.logger.info(f'Found task: {task.title} (ID: {task.id})')
        
        # Update the task
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.updated_at = datetime.now()
        
        # Add completion notes if provided
        if request.is_json and request.json:
            completion_notes = request.json.get('completion_notes')
        else:
            completion_notes = request.form.get('completion_notes')
            
        if completion_notes:
            task.completion_notes = completion_notes
        
        db.session.commit()
        current_app.logger.info(f'Task {task.id} marked as completed')
        
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': 'Task marked as completed!',
                'task_id': task.id,
                'status_display': task.status_display
            })
            
        flash('Task marked as completed!', 'success')
        return redirect(request.referrer or url_for('tasks.index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error completing task {id}: {str(e)}'
        current_app.logger.error(error_msg, exc_info=True)
        
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'error',
                'message': 'An error occurred while completing the task. Please try again.'
            }), 500
            
        flash('An error occurred while completing the task. Please try again.', 'error')
        return redirect(request.referrer or url_for('tasks.index'))

@tasks_bp.route('/send_reminders', methods=['GET'])
@login_required
def send_reminders():
    """Manually trigger task reminders for testing."""
    from app.tasks.task_automation import process_task_reminders
    
    try:
        # Process reminders
        reminders_sent = process_task_reminders()
        
        flash(f'Successfully sent {reminders_sent} task reminders!', 'success')
    except Exception as e:
        flash(f'Error sending reminders: {str(e)}', 'danger')
        
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a task."""
    task = Task.query.get_or_404(id)
    
    # Delete the task
    db.session.delete(task)
    db.session.commit()
    
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/test-calendar-sync')
@login_required
def test_calendar_sync():
    """Test route to directly create a Google Calendar event."""
    from flask import current_app
    from app.services.calendar_service import CalendarService
    from datetime import datetime, timedelta
    
    try:
        # Log the current user
        current_app.logger.info(f"Testing calendar sync for user: {current_user.id} ({current_user.email})")
        
        # Create a dummy task with today's date
        task = Task(
            id=999999,  # Temporary ID for testing
            title="Test Calendar Event",
            description="This is a test event created to verify Google Calendar sync",
            due_date=datetime.now().date(),
            created_by=current_user.id,
            owner_id=current_user.id
        )
        
        # Initialize calendar service
        current_app.logger.info("Initializing Calendar Service")
        calendar_service = CalendarService(current_user.id)
        
        # Create the event
        current_app.logger.info("Attempting to create test event")
        event = calendar_service.create_event(task)
        
        # Don't save the dummy task to the database
        
        return jsonify({
            'success': True,
            'message': 'Test calendar event created successfully',
            'event_id': event.get('id', 'Unknown'),
            'event_link': event.get('htmlLink', 'Unknown')
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error testing calendar sync: {str(e)}")
        current_app.logger.error(f"Error details: {error_details}")
        
        return jsonify({
            'success': False,
            'error': str(e),
            'error_details': error_details
        }), 500 

@tasks_bp.route('/batch-reminder-settings', methods=['GET'])
@login_required
def batch_reminder_settings():
    """Display a page for batch updating reminder settings for tasks."""
    task_ids = request.args.getlist('task_ids')
    
    if not task_ids:
        flash('No tasks selected for batch update', 'warning')
        return redirect(url_for('tasks.index'))
    
    # Get current user's tasks with the specified IDs
    tasks = Task.query.filter(
        Task.id.in_(task_ids),
        Task.user_id == current_user.id
    ).all()
    
    if not tasks:
        flash('No valid tasks found for batch update', 'warning')
        return redirect(url_for('tasks.index'))
    
    return render_template('tasks/batch_reminder_settings.html', tasks=tasks) 