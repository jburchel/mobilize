from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.models.task import Task
from app.models.google_token import GoogleToken
from app.extensions import db
from datetime import datetime, timedelta

class CalendarService:
    """Service class for Google Calendar API operations."""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize the Calendar API service with user credentials."""
        token = GoogleToken.query.filter_by(user_id=self.user_id).first()
        if not token:
            raise ValueError("No Google token found for user")

        credentials = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,  # Will be loaded from environment
            client_secret=None,  # Will be loaded from environment
            scopes=['https://www.googleapis.com/auth/calendar']
        )

        if credentials.expired:
            credentials.refresh(Request())
            # Update token in database
            token.access_token = credentials.token
            token.expires_at = datetime.utcnow() + timedelta(seconds=credentials.expiry.second)
            db.session.commit()

        self.service = build('calendar', 'v3', credentials=credentials)

    def create_event(self, task):
        """Create a calendar event from a task."""
        try:
            event = {
                'summary': task.title,
                'description': task.description,
                'start': {
                    'dateTime': task.due_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': (task.due_date + timedelta(hours=1)).isoformat(),
                    'timeZone': 'UTC',
                },
                'reminders': {
                    'useDefault': True
                }
            }

            event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

            # Update task with calendar event ID
            task.google_calendar_event_id = event['id']
            db.session.commit()

            return event

        except Exception as e:
            raise Exception(f"Failed to create calendar event: {str(e)}")

    def update_event(self, task):
        """Update a calendar event for a task."""
        try:
            if not task.google_calendar_event_id:
                return self.create_event(task)

            event = {
                'summary': task.title,
                'description': task.description,
                'start': {
                    'dateTime': task.due_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': (task.due_date + timedelta(hours=1)).isoformat(),
                    'timeZone': 'UTC',
                }
            }

            event = self.service.events().update(
                calendarId='primary',
                eventId=task.google_calendar_event_id,
                body=event
            ).execute()

            return event

        except Exception as e:
            raise Exception(f"Failed to update calendar event: {str(e)}")

    def delete_event(self, event_id):
        """Delete a calendar event."""
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return True
        except Exception as e:
            raise Exception(f"Failed to delete calendar event: {str(e)}")

    def sync_events(self, days_back=7, days_forward=30):
        """Sync calendar events with tasks."""
        try:
            # Get time range for sync
            now = datetime.utcnow()
            time_min = (now - timedelta(days=days_back)).isoformat() + 'Z'
            time_max = (now + timedelta(days=days_forward)).isoformat() + 'Z'

            # Get all events in range
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])

            for event in events:
                # Check if event is already linked to a task
                task = Task.query.filter_by(
                    google_calendar_event_id=event['id']
                ).first()

                if not task and 'summary' in event:
                    # Create new task from event
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    task = Task(
                        title=event['summary'],
                        description=event.get('description', ''),
                        due_date=datetime.fromisoformat(start.replace('Z', '+00:00')),
                        status='pending',
                        google_calendar_event_id=event['id'],
                        created_by=self.user_id
                    )
                    db.session.add(task)

            db.session.commit()
            return len(events)

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to sync calendar events: {str(e)}")

    def get_upcoming_events(self, days=7):
        """Get upcoming calendar events."""
        try:
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days)).isoformat() + 'Z'

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            return events_result.get('items', [])
        except Exception as e:
            raise Exception(f"Failed to get upcoming events: {str(e)}") 