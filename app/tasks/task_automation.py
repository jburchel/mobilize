from celery.schedules import crontab
from datetime import datetime, timedelta
from app.extensions import celery, db
from app.models.task import Task
from app.models.user import User
from app.utils.email_service import send_email_with_template
from app.services.notification_service import send_notification
import logging

logger = logging.getLogger(__name__)

@celery.task
def process_task_reminders():
    """
    Process all pending task reminders.
    Sends email and in-app notifications for tasks based on their reminder settings.
    """
    try:
        # Get current date and time
        now = datetime.now()
        
        # Get all active, non-completed tasks with reminder options set
        tasks = Task.query.filter(
            Task.status != 'completed',
            Task.reminder_option != 'none',
            Task.reminder_option.isnot(None),
            Task.due_date.isnot(None)
        ).all()
        
        reminders_sent = 0
        logger.info(f"Processing reminders for {len(tasks)} tasks")
        
        for task in tasks:
            # Skip tasks without due date
            if not task.due_date:
                continue
                
            # Calculate when the reminder should be sent based on the reminder_option
            reminder_time = calculate_reminder_time(task)
            
            # If it's time to send the reminder
            if is_time_to_send_reminder(task, reminder_time, now):
                # Send notification to the task owner
                if task.owner_id:
                    owner = User.query.get(task.owner_id)
                    if owner and owner.notification_settings and owner.notification_settings.get('notify_tasks', True):
                        send_task_notification(task, owner)
                
                # Send notification to the assigned user if different from owner
                if task.assigned_to and task.assigned_to != str(task.owner_id):
                    assigned_user = User.query.get(int(task.assigned_to))
                    if assigned_user and assigned_user.notification_settings and assigned_user.notification_settings.get('notify_tasks', True):
                        send_task_notification(task, assigned_user)
                
                # Mark that reminder has been sent by updating the last_synced_at field
                # We use last_synced_at to track when the last reminder was sent
                task.last_synced_at = now
                reminders_sent += 1
                
        db.session.commit()
        logger.info(f"Successfully sent {reminders_sent} task reminders")
        return reminders_sent
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing task reminders: {str(e)}")
        raise

def calculate_reminder_time(task):
    """Calculate when a reminder should be sent based on the task's reminder option."""
    if not task.reminder_option or not task.due_date:
        return None
        
    reminder_delta = {
        '15_min': timedelta(minutes=15),
        '30_min': timedelta(minutes=30),
        '1_hour': timedelta(hours=1),
        '2_hours': timedelta(hours=2),
        '1_day': timedelta(days=1),
        '3_days': timedelta(days=3),
        '1_week': timedelta(days=7)
    }.get(task.reminder_option)
    
    if not reminder_delta:
        return None
        
    # If task has due_time, use it
    if task.due_time:
        try:
            due_time_parts = task.due_time.split(':')
            hour = int(due_time_parts[0])
            minute = int(due_time_parts[1])
            due_datetime = datetime.combine(task.due_date, datetime.min.time().replace(hour=hour, minute=minute))
        except (ValueError, IndexError):
            # If due_time can't be parsed, use start of day
            due_datetime = datetime.combine(task.due_date, datetime.min.time())
    else:
        # Default to start of day if no time specified
        due_datetime = datetime.combine(task.due_date, datetime.min.time())
    
    return due_datetime - reminder_delta

def is_time_to_send_reminder(task, reminder_time, current_time):
    """Determine if it's time to send a reminder."""
    if not reminder_time:
        return False
        
    # Don't send reminder if it's already been sent
    if task.last_synced_at and task.last_synced_at > reminder_time:
        return False
        
    # Check if current time is past the reminder time but within a reasonable window
    # (preventing multiple reminders if the job runs late)
    time_window = current_time - timedelta(hours=2)  # 2-hour window
    return reminder_time <= current_time and reminder_time >= time_window

def send_task_notification(task, user):
    """Send notification for a task to a user."""
    # Send in-app notification
    notification_data = {
        'title': 'Task Reminder',
        'message': f"Reminder: Task '{task.title}' is due soon.",
        'link': f"/tasks/edit/{task.id}",
        'task_id': task.id
    }
    
    try:
        send_notification(
            user_id=user.id,
            notification_type='task_reminder', 
            notification_data=notification_data
        )
    except Exception as e:
        logger.error(f"Failed to send in-app notification: {str(e)}")
    
    # Send email notification
    try:
        context = {
            'user': user,
            'task': task,
            'due_date_formatted': task.due_date.strftime('%m/%d/%Y'),
            'due_time': task.due_time if task.due_time else 'Not specified',
            'app_url': 'http://localhost:8080'  # Should be configured in app config
        }
        
        send_email_with_template(
            subject=f"Task Reminder: {task.title}",
            recipients=[user.email],
            template='emails/task_reminder.html',
            context=context,
            sender_id=None,  # System email
            office_id=user.office_id if hasattr(user, 'office_id') else None
        )
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")

@celery.task
def create_recurring_tasks():
    """Create recurring tasks based on task recurrence settings."""
    # This function would implement the logic for creating recurring tasks
    # Not implemented in this phase yet
    pass

# Schedule periodic tasks
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run task reminders every hour
    sender.add_periodic_task(
        crontab(minute=0),  # Run at the start of every hour
        process_task_reminders.s(),
        name='process-task-reminders-hourly'
    ) 