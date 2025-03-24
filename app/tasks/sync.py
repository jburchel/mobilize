from celery.schedules import crontab
from app.extensions import celery
from app.models.user import User
from app.services.gmail_service import GmailService
from app.services.calendar_service import CalendarService
from app.services.contacts_service import ContactsService
from app.extensions import db
import logging

logger = logging.getLogger(__name__)

@celery.task
def sync_user_gmail(user_id):
    """Sync Gmail for a specific user."""
    try:
        gmail_service = GmailService(user_id)
        num_synced = gmail_service.sync_emails()
        logger.info(f"Successfully synced {num_synced} emails for user {user_id}")
        return num_synced
    except Exception as e:
        logger.error(f"Failed to sync Gmail for user {user_id}: {str(e)}")
        raise

@celery.task
def sync_user_calendar(user_id):
    """Sync Calendar for a specific user."""
    try:
        calendar_service = CalendarService(user_id)
        num_synced = calendar_service.sync_events()
        logger.info(f"Successfully synced {num_synced} calendar events for user {user_id}")
        return num_synced
    except Exception as e:
        logger.error(f"Failed to sync Calendar for user {user_id}: {str(e)}")
        raise

@celery.task
def sync_user_contacts(user_id):
    """Sync Contacts for a specific user."""
    try:
        contacts_service = ContactsService(user_id)
        num_synced = contacts_service.sync_contacts()
        logger.info(f"Successfully synced {num_synced} contacts for user {user_id}")
        return num_synced
    except Exception as e:
        logger.error(f"Failed to sync Contacts for user {user_id}: {str(e)}")
        raise

@celery.task
def sync_all_users():
    """Sync Gmail, Calendar, and Contacts for all active users."""
    try:
        users = User.query.filter_by(is_active=True).all()
        for user in users:
            if user.google_token:
                sync_user_gmail.delay(user.id)
                sync_user_calendar.delay(user.id)
                sync_user_contacts.delay(user.id)
        return len(users)
    except Exception as e:
        logger.error(f"Failed to start sync for all users: {str(e)}")
        raise

# Schedule periodic tasks
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Sync all users every hour
    sender.add_periodic_task(
        crontab(minute=0),  # Run at the start of every hour
        sync_all_users.s(),
        name='sync-all-users-hourly'
    ) 