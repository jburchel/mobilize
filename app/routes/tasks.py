import os
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
from app.supabase_client import supabase
from app.forms.task import TaskForm
from app.forms.task_batch_reminder import TaskBatchReminderForm
from sqlalchemy import or_

tasks_bp = Blueprint('tasks', __name__, template_folder='../templates/tasks')

@tasks_bp.route('/')
@tasks_bp.route('/list')
@login_required
def index():
    """Display list of tasks."""
    # Start with detailed logging
    current_app.logger.info("==== TASKS INDEX ROUTE STARTED ====")
    current_app.logger.info(f"User ID: {current_user.id if current_user else 'Not logged in'}")
    current_app.logger.info(f"Request args: {request.args}")
    
    # Add more detailed logging for troubleshooting
    import traceback
    import sys
    
    try:
        # Log configuration
        current_app.logger.info(f"SQLALCHEMY_DATABASE_URI set: {'Yes' if current_app.config.get('SQLALCHEMY_DATABASE_URI') else 'No'}")
        current_app.logger.info(f"USE_SUPABASE_CLIENT set: {'Yes' if current_app.config.get('USE_SUPABASE_CLIENT') else 'No'}")
        current_app.logger.info(f"Supabase client available: {'Yes' if supabase else 'No'}")
        
        # Log detailed information about the supabase client
        if supabase:
            current_app.logger.info(f"Supabase type: {type(supabase)}")
            current_app.logger.info(f"Supabase has client attribute: {hasattr(supabase, 'client')}")
            if hasattr(supabase, 'client'):
                current_app.logger.info(f"Supabase client type: {type(supabase.client)}")
                current_app.logger.info(f"Supabase client initialized: {bool(supabase.client)}")
        
        # Test database connection first
        try:
            current_app.logger.info("Testing database connection...")
            from sqlalchemy import text
            db.session.execute(text('SELECT 1')).scalar()
            current_app.logger.info("Database connection test successful")
            use_supabase = False
        except Exception as db_error:
            current_app.logger.error(f"Database connection test failed: {str(db_error)}")
            # Get database connection info
            db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
            masked_uri = db_uri
            if '://' in db_uri:
                parts = db_uri.split('://', 1)
                if '@' in parts[1]:
                    auth, rest = parts[1].split('@', 1)
                    if ':' in auth:
                        user, _ = auth.split(':', 1)
                        masked_uri = f"{parts[0]}://{user}:****@{rest}"
            current_app.logger.error(f"Database URI: {masked_uri}")
            
            # Check if Supabase client is available as a fallback
            if current_app.config.get('USE_SUPABASE_CLIENT') and supabase:
                current_app.logger.info("Using Supabase client as a fallback")
                use_supabase = True
            else:
                current_app.logger.error("No fallback available - Supabase client not configured")
                return render_template('error.html', 
                                    error_title="Database Connection Error",
                                    error_message="Unable to connect to the database. Please try again later or contact support.",
                                    error_details=str(db_error))
            
        # Get filters from query params
        status_filter = request.args.get('status')
        priority_filter = request.args.get('priority')
        search_text = request.args.get('search', '').lower().strip()
        
        # Get tasks based on connection method
        if 'use_supabase' in locals() and use_supabase:
            # Use Supabase client to get tasks
            current_app.logger.info("Getting tasks from Supabase client")
            try:
                # Check if supabase is available
                current_app.logger.info(f"Supabase object type: {type(supabase)}")
                current_app.logger.info(f"Supabase has client: {'Yes' if hasattr(supabase, 'client') else 'No'}")
                
                # Get tasks from Supabase
                if not supabase or not hasattr(supabase, 'client') or not supabase.client:
                    current_app.logger.error("Supabase client is not initialized")
                    return render_template('error.html', 
                                    error_title="Database Connection Error",
                                    error_message="Unable to connect to the database. Please try again later or contact support.",
                                    error_details="Supabase client is not initialized")
                
                # Log Supabase client details
                current_app.logger.info(f"Supabase URL: {supabase.supabase_url if hasattr(supabase, 'supabase_url') else 'Not available'}")
                
                # Try to test the connection first
                try:
                    connection_test = supabase.test_connection()
                    current_app.logger.info(f"Supabase connection test result: {connection_test}")
                except Exception as test_err:
                    current_app.logger.error(f"Supabase connection test failed: {str(test_err)}")
                
                # Get tasks from Supabase
                current_app.logger.info(f"Attempting to get tasks for user ID: {current_user.id}")
                tasks = supabase.get_tasks(user_id=current_user.id)
                current_app.logger.info(f"Retrieved {len(tasks) if tasks else 0} tasks from Supabase")
                
                # Convert to list of Task objects for compatibility
                all_tasks = []
                for task_data in tasks:
                    task = Task()
                    for key, value in task_data.items():
                        if hasattr(task, key):
                            setattr(task, key, value)
                    all_tasks.append(task)
                
                current_app.logger.info(f"Converted {len(all_tasks)} tasks to Task objects")
                
                # We'll filter these tasks in Python since we can't use SQLAlchemy
                query = all_tasks
                
                if not tasks:
                    current_app.logger.error("No data returned from Supabase tasks query")
                    query = []
            except Exception as supabase_err:
                error_traceback = traceback.format_exc()
                exc_type, exc_value, exc_tb = sys.exc_info()
                current_app.logger.error(f"Error getting tasks from Supabase: {str(supabase_err)}")
                current_app.logger.error(f"Exception type: {exc_type.__name__}")
                current_app.logger.error(f"Exception traceback: {error_traceback}")
                
                # Log detailed information about the Supabase client
                if supabase:
                    current_app.logger.error(f"Supabase type: {type(supabase)}")
                    if hasattr(supabase, 'client'):
                        current_app.logger.error(f"Supabase client type: {type(supabase.client)}")
                    if hasattr(supabase, 'supabase_url'):
                        current_app.logger.error(f"Supabase URL: {supabase.supabase_url}")
                    if hasattr(supabase, 'supabase_key'):
                        current_app.logger.error(f"Supabase key set: {'Yes' if supabase.supabase_key else 'No'}")
                
                return render_template('error.html',
                                    error_title="Error Loading Tasks",
                                    error_message="An error occurred while loading your tasks from Supabase.",
                                    error_details=f"{str(supabase_err)}\n\nTraceback: {error_traceback}")
        else:
            # Use SQLAlchemy to get tasks
            query = Task.query.filter(
                (Task.assigned_to == str(current_user.id)) | 
                (Task.created_by == current_user.id) |
                (Task.owner_id == current_user.id)
            )
    except Exception as e:
        error_traceback = traceback.format_exc()
        exc_type, exc_value, exc_tb = sys.exc_info()
        current_app.logger.error(f"Error in tasks index route: {str(e)}")
        current_app.logger.error(f"Exception type: {exc_type.__name__}")
        current_app.logger.error(f"Exception traceback: {error_traceback}")
        
        # Log detailed information about the current state
        current_app.logger.error(f"Current user: {current_user.id if current_user else 'Not logged in'}")
        current_app.logger.error(f"Database URI: {current_app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')}")
        current_app.logger.error(f"Supabase URL: {os.environ.get('SUPABASE_URL', 'Not set')}")
        
        return render_template('error.html', 
                            error_title="Error Loading Tasks",
                            error_message="An error occurred while loading your tasks.",
                            error_details=f"{str(e)}\n\nTraceback: {error_traceback}")
    
    # Check if we're using Supabase or SQLAlchemy
    using_supabase = isinstance(query, list)
    current_date = datetime.now().date()
    
    if using_supabase:
        # We already have all tasks from Supabase, filter in Python
        all_tasks = query.copy()  # Make a copy of the original list
        filtered_tasks = query  # Start with all tasks
        
        # Apply status filter
        if status_filter and status_filter != 'all':
            if status_filter == 'overdue':
                # Special handling for overdue tasks
                filtered_tasks = [task for task in filtered_tasks 
                                if task.status != TaskStatus.COMPLETED.value and 
                                task.due_date and 
                                datetime.strptime(task.due_date, '%Y-%m-%d').date() < current_date]
            else:
                filtered_tasks = [task for task in filtered_tasks if task.status == status_filter]
        
        # Apply priority filter
        if priority_filter and priority_filter != 'all':
            filtered_tasks = [task for task in filtered_tasks if task.priority == priority_filter]
        
        # Apply search filter
        if search_text:
            filtered_tasks = [task for task in filtered_tasks 
                            if (task.title and search_text in task.title.lower()) or 
                               (task.description and search_text in task.description.lower())]
        
        # Calculate overdue count
        overdue_count = sum(1 for task in all_tasks 
                          if task.status != TaskStatus.COMPLETED.value and 
                          task.due_date and 
                          datetime.strptime(task.due_date, '%Y-%m-%d').date() < current_date)
                          
        # Sort tasks by due date
        filtered_tasks.sort(key=lambda task: task.due_date if task.due_date else '9999-12-31')
        
        # Log success using Supabase
        current_app.logger.info(f"Successfully loaded {len(filtered_tasks)} tasks from Supabase")
    else:
        # Using SQLAlchemy query
        # Apply status filter
        if status_filter and status_filter != 'all':
            if status_filter == 'overdue':
                # Special handling for overdue tasks
                query = query.filter(
                    Task.status != TaskStatus.COMPLETED,
                    Task.due_date < current_date
                )
            else:
                query = query.filter(Task.status == status_filter)
        
        # Apply priority filter
        if priority_filter and priority_filter != 'all':
            query = query.filter(Task.priority == priority_filter)
        
        # Apply search filter if provided
        if search_text:
            search_query = f"%{search_text}%"
            query = query.filter(
                or_(
                    Task.title.ilike(search_query),
                    Task.description.ilike(search_query),
                    Person.first_name.ilike(search_query),
                    Person.last_name.ilike(search_query),
                    Church.name.ilike(search_query)
                )
            ).outerjoin(Person, Task.person_id == Person.id).outerjoin(Church, Task.church_id == Church.id)
        
        # Get all tasks for statistics
        all_tasks_query = Task.query.filter(
            (Task.assigned_to == str(current_user.id)) | 
            (Task.created_by == current_user.id) |
            (Task.owner_id == current_user.id)
        )
        all_tasks = all_tasks_query.all()
        
        # Calculate overdue count
        overdue_count = sum(1 for task in all_tasks if task.status != TaskStatus.COMPLETED and task.due_date and task.due_date < current_date)
        
        # Get filtered tasks with ordering
        filtered_tasks = query.order_by(Task.due_date.asc()).all()
        
        # Log success using SQLAlchemy
        current_app.logger.info(f"Successfully loaded {len(filtered_tasks)} tasks from database")
    
    # Log the results
    current_app.logger.info(f"Loaded {len(filtered_tasks)} tasks with {overdue_count} overdue")
            
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
    task = Task.query.get_or_404(id)
    
    # Update the task
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now()
    
    # Add completion notes if provided
    completion_notes = request.form.get('completion_notes')
    if completion_notes:
        task.completion_notes = completion_notes
        
    task.updated_at = datetime.now()
    db.session.commit()
    
    flash('Task marked as completed!', 'success')
    return redirect(url_for('tasks.index'))

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

@tasks_bp.route('/debug')
def debug_tasks():
    """Debug route for tasks page."""
    # Log detailed information about the environment
    current_app.logger.info("==== TASKS DEBUG ROUTE STARTED ====")
    
    # Check database connection
    db_status = "Unknown"
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1')).scalar()
        db_status = "Connected"
    except Exception as e:
        db_status = f"Error: {str(e)}"
    
    # Check Supabase connection
    supabase_status = "Unknown"
    try:
        if supabase and hasattr(supabase, 'client') and supabase.client:
            test_result = supabase.test_connection()
            supabase_status = f"Available, Test Result: {test_result}"
        else:
            supabase_status = "Not initialized"
    except Exception as e:
        supabase_status = f"Error: {str(e)}"
    
    # Get environment variables
    env_vars = {
        'SQLALCHEMY_DATABASE_URI': current_app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set'),
        'USE_SUPABASE_CLIENT': current_app.config.get('USE_SUPABASE_CLIENT', 'Not set'),
        'SUPABASE_URL': os.environ.get('SUPABASE_URL', 'Not set'),
        'DATABASE_URL': os.environ.get('DATABASE_URL', 'Not set')
    }
    
    # Mask sensitive information
    for key in ['SQLALCHEMY_DATABASE_URI', 'DATABASE_URL']:
        if env_vars[key] and '://' in env_vars[key]:
            parts = env_vars[key].split('://', 1)
            if '@' in parts[1]:
                auth, rest = parts[1].split('@', 1)
                if ':' in auth:
                    user, _ = auth.split(':', 1)
                    env_vars[key] = f"{parts[0]}://{user}:****@{rest}"
    
    # Now try to simulate the tasks index route functionality
    tasks_simulation_result = {}
    try:
        current_app.logger.info("Simulating tasks index route functionality")
        import traceback
        import sys
        
        # Test database connection first
        try:
            current_app.logger.info("Testing database connection...")
            from sqlalchemy import text
            db.session.execute(text('SELECT 1')).scalar()
            current_app.logger.info("Database connection test successful")
            use_supabase = False
            tasks_simulation_result['database_test'] = 'Success'
        except Exception as db_error:
            error_traceback = traceback.format_exc()
            current_app.logger.error(f"Database connection test failed: {str(db_error)}")
            current_app.logger.error(f"Exception traceback: {error_traceback}")
            tasks_simulation_result['database_test'] = f'Failed: {str(db_error)}'
            tasks_simulation_result['database_error_traceback'] = error_traceback
            
            # Check if Supabase client is available as a fallback
            if current_app.config.get('USE_SUPABASE_CLIENT') and supabase:
                current_app.logger.info("Using Supabase client as a fallback")
                use_supabase = True
                tasks_simulation_result['using_supabase_fallback'] = True
            else:
                current_app.logger.error("No fallback available - Supabase client not configured")
                tasks_simulation_result['using_supabase_fallback'] = False
        
        # Get tasks based on connection method
        if 'use_supabase' in locals() and use_supabase:
            # Use Supabase client to get tasks
            current_app.logger.info("Getting tasks from Supabase client")
            try:
                # Check if supabase is available
                current_app.logger.info(f"Supabase object type: {type(supabase)}")
                current_app.logger.info(f"Supabase has client: {'Yes' if hasattr(supabase, 'client') else 'No'}")
                
                # Get tasks from Supabase - simulate with a dummy user ID
                if not supabase or not hasattr(supabase, 'client') or not supabase.client:
                    current_app.logger.error("Supabase client is not initialized")
                    tasks_simulation_result['supabase_client_initialized'] = False
                else:
                    tasks_simulation_result['supabase_client_initialized'] = True
                    
                    # Log Supabase client details
                    current_app.logger.info(f"Supabase URL: {supabase.supabase_url if hasattr(supabase, 'supabase_url') else 'Not available'}")
                    
                    # Try to test the connection first
                    try:
                        connection_test = supabase.test_connection()
                        current_app.logger.info(f"Supabase connection test result: {connection_test}")
                        tasks_simulation_result['supabase_connection_test'] = f'Success: {connection_test}'
                    except Exception as test_err:
                        error_traceback = traceback.format_exc()
                        current_app.logger.error(f"Supabase connection test failed: {str(test_err)}")
                        current_app.logger.error(f"Exception traceback: {error_traceback}")
                        tasks_simulation_result['supabase_connection_test'] = f'Failed: {str(test_err)}'
                        tasks_simulation_result['supabase_connection_error_traceback'] = error_traceback
                    
                    # Try to get tasks with a dummy user ID
                    try:
                        dummy_user_id = 1  # Use a dummy user ID for testing
                        current_app.logger.info(f"Attempting to get tasks for dummy user ID: {dummy_user_id}")
                        tasks = supabase.get_tasks(user_id=dummy_user_id)
                        current_app.logger.info(f"Retrieved {len(tasks) if tasks else 0} tasks from Supabase")
                        tasks_simulation_result['supabase_get_tasks'] = f'Success: Retrieved {len(tasks) if tasks else 0} tasks'
                    except Exception as tasks_err:
                        error_traceback = traceback.format_exc()
                        current_app.logger.error(f"Error getting tasks from Supabase: {str(tasks_err)}")
                        current_app.logger.error(f"Exception traceback: {error_traceback}")
                        tasks_simulation_result['supabase_get_tasks'] = f'Failed: {str(tasks_err)}'
                        tasks_simulation_result['supabase_get_tasks_error_traceback'] = error_traceback
            except Exception as supabase_err:
                error_traceback = traceback.format_exc()
                current_app.logger.error(f"Error in Supabase client section: {str(supabase_err)}")
                current_app.logger.error(f"Exception traceback: {error_traceback}")
                tasks_simulation_result['supabase_section_error'] = f'Failed: {str(supabase_err)}'
                tasks_simulation_result['supabase_section_error_traceback'] = error_traceback
        else:
            # Use SQLAlchemy to get tasks - simulate with a dummy query
            try:
                current_app.logger.info("Simulating SQLAlchemy query")
                from sqlalchemy import or_
                dummy_user_id = 1  # Use a dummy user ID for testing
                query = Task.query.filter(
                    (Task.assigned_to == str(dummy_user_id)) | 
                    (Task.created_by == dummy_user_id) |
                    (Task.owner_id == dummy_user_id)
                )
                # Just build the query, don't execute it
                tasks_simulation_result['sqlalchemy_query_build'] = 'Success'
            except Exception as query_err:
                error_traceback = traceback.format_exc()
                current_app.logger.error(f"Error building SQLAlchemy query: {str(query_err)}")
                current_app.logger.error(f"Exception traceback: {error_traceback}")
                tasks_simulation_result['sqlalchemy_query_build'] = f'Failed: {str(query_err)}'
                tasks_simulation_result['sqlalchemy_query_error_traceback'] = error_traceback
    except Exception as sim_err:
        error_traceback = traceback.format_exc()
        current_app.logger.error(f"Error in tasks simulation: {str(sim_err)}")
        current_app.logger.error(f"Exception traceback: {error_traceback}")
        tasks_simulation_result['overall_simulation'] = f'Failed: {str(sim_err)}'
        tasks_simulation_result['overall_simulation_error_traceback'] = error_traceback
    
    # Return debug information
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'database_status': db_status,
        'supabase_status': supabase_status,
        'environment_variables': env_vars,
        'supabase_info': {
            'type': str(type(supabase)),
            'has_client': hasattr(supabase, 'client'),
            'client_initialized': bool(supabase and hasattr(supabase, 'client') and supabase.client)
        },
        'tasks_simulation': tasks_simulation_result
    })

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