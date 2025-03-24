from app.tasks.sync import sync_all_users
from app.extensions import db, scheduler
from app.models.user import User

def init_scheduler(app):
    """Initialize the scheduler with the Flask app."""
    scheduler.init_app(app)
    scheduler.start()

    # Add jobs
    scheduler.add_job(
        id='sync_all_users',
        func=sync_all_users,
        trigger='interval',
        minutes=30,
        replace_existing=True
    )

    # Add more scheduled jobs here as needed
    return scheduler 