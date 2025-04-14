from app.tasks.sync import sync_all_users
from app.tasks.task_automation import process_task_reminders
from app.extensions import db, scheduler
from app.models.user import User
from datetime import datetime

def init_scheduler(app):
    """Initialize the scheduler with the Flask app."""
    scheduler.init_app(app)
    scheduler.start()

    # Add jobs with app context wrappers
    def sync_all_users_with_context():
        with app.app_context():
            sync_all_users()
    
    scheduler.add_job(
        id='sync_all_users',
        func=sync_all_users_with_context,  # Use the wrapper function
        trigger='interval',
        minutes=30,
        replace_existing=True
    )
    
    # Add task reminder job with app context wrapper
    def process_task_reminders_with_context():
        with app.app_context():
            process_task_reminders()
    
    scheduler.add_job(
        id='process_task_reminders',
        func=process_task_reminders_with_context,  # Use the wrapper function
        trigger='interval',
        minutes=60,  # Check hourly
        next_run_time=datetime.now(),  # Run immediately when app starts
        replace_existing=True
    )

    # Add more scheduled jobs here as needed
    return scheduler 