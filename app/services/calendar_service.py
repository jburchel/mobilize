from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.models.task import Task
from app.models.google_token import GoogleToken
from app.extensions import db
from datetime import datetime, timedelta, time
import json
import pytz

class CalendarService:
    """Service class for Google Calendar API operations."""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize the Calendar API service with user credentials."""
        from flask import current_app
        
        try:
            current_app.logger.info(f"Initializing Calendar service for user {self.user_id}")
            
            token = GoogleToken.query.filter_by(user_id=self.user_id).first()
            if not token:
                current_app.logger.error(f"No Google token found for user {self.user_id}")
                raise ValueError("No Google token found for user")

            # Log token information for debugging (without sensitive details)
            current_app.logger.debug(f"Google token found for user {self.user_id}")
            current_app.logger.debug(f"Token expires at: {token.expires_at}")
            current_app.logger.debug(f"Token has refresh_token: {'Yes' if token.refresh_token else 'No'}")
            
            # Check if token scopes include calendar
            has_calendar_scope = False
            if token.scopes:
                try:
                    scopes = json.loads(token.scopes)
                    has_calendar_scope = any('calendar' in scope.lower() for scope in scopes)
                    current_app.logger.debug(f"Token scopes: {scopes}")
                except json.JSONDecodeError:
                    current_app.logger.warning(f"Could not parse token scopes JSON: {token.scopes}")
            
            if not has_calendar_scope:
                current_app.logger.warning(f"Token for user {self.user_id} may not have calendar scopes")

            credentials = token.to_credentials()
            
            if credentials.expired:
                current_app.logger.info(f"Token for user {self.user_id} is expired, attempting to refresh")
                credentials.refresh(Request())
                # Update token in database
                token.access_token = credentials.token
                token.expires_at = datetime.utcnow() + timedelta(seconds=credentials.expiry.second)
                db.session.commit()
                current_app.logger.info(f"Successfully refreshed token for user {self.user_id}")

            current_app.logger.info(f"Building Calendar API service for user {self.user_id}")
            self.service = build('calendar', 'v3', credentials=credentials)
            current_app.logger.info(f"Successfully initialized Calendar service for user {self.user_id}")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            current_app.logger.error(f"Failed to initialize Calendar service: {str(e)}")
            current_app.logger.error(f"Error details: {error_details}")
            raise ValueError(f"Failed to initialize Calendar service: {str(e)}")

    def _get_reminder_settings(self, task):
        """Get reminder settings based on task's reminder_option."""
        from flask import current_app
        
        # Default is to use Google Calendar's default reminders
        reminder_settings = {
            'useDefault': True
        }
        
        # Check if task has a specific reminder option
        if hasattr(task, 'reminder_option') and task.reminder_option and task.reminder_option != 'none':
            # Parse the reminder option and convert to minutes
            try:
                reminder_minutes = 0
                
                if task.reminder_option == '15_min':
                    reminder_minutes = 15
                elif task.reminder_option == '30_min':
                    reminder_minutes = 30
                elif task.reminder_option == '1_hour':
                    reminder_minutes = 60
                elif task.reminder_option == '2_hours':
                    reminder_minutes = 120
                elif task.reminder_option == '1_day':
                    reminder_minutes = 24 * 60
                elif task.reminder_option == '3_days':
                    reminder_minutes = 3 * 24 * 60
                elif task.reminder_option == '1_week':
                    reminder_minutes = 7 * 24 * 60
                
                if reminder_minutes > 0:
                    reminder_settings = {
                        'useDefault': False,
                        'overrides': [
                            {
                                'method': 'popup',
                                'minutes': reminder_minutes
                            }
                        ]
                    }
                    current_app.logger.debug(f"Using custom reminder: {reminder_minutes} minutes before for task {task.id}")
            except Exception as e:
                current_app.logger.warning(f"Error setting reminder option: {str(e)}")
        
        return reminder_settings

    def create_event(self, task):
        """Create a calendar event from a task."""
        from flask import current_app
        
        try:
            if not task.due_date:
                current_app.logger.error(f"Cannot create calendar event: Task {task.id} has no due date")
                raise ValueError("Task has no due date")
                
            current_app.logger.info(f"Creating Google Calendar event for task {task.id}: {task.title}")
            
            # Convert date to datetime with time
            from datetime import datetime, time, timedelta
            
            # Default time is noon if no specific time is set
            default_time = time(12, 0)
            
            # Check if task has due_time attribute and it's not empty
            if hasattr(task, 'due_time') and task.due_time:
                try:
                    # Parse the time string in format HH:MM
                    hour, minute = map(int, task.due_time.split(':'))
                    event_time = time(hour, minute)
                    current_app.logger.debug(f"Using task due_time: {task.due_time} for event")
                except (ValueError, AttributeError) as time_error:
                    # If time parsing fails, use default time
                    current_app.logger.warning(f"Could not parse time string '{task.due_time}': {str(time_error)}. Using default time (noon).")
                    event_time = default_time
            else:
                # No specific time found, use default
                current_app.logger.debug("No due_time found for task, using default time (noon)")
                event_time = default_time
            
            # Combine the date and time into a datetime object
            start_datetime = datetime.combine(task.due_date, event_time)
            end_datetime = start_datetime + timedelta(hours=1)
            
            # Format the datetimes for Google Calendar API (RFC3339 format)
            # Include time zone offset for proper display
            local_timezone = pytz.timezone('America/New_York')  # Adjust to your time zone
            
            start_datetime_local = local_timezone.localize(start_datetime)
            end_datetime_local = local_timezone.localize(end_datetime)
            
            # Format times in ISO 8601 / RFC 3339 format with timezone info
            start_time_str = start_datetime_local.isoformat()
            end_time_str = end_datetime_local.isoformat()
            
            current_app.logger.debug(f"Event start time: {start_time_str}, end time: {end_time_str}")
            
            # Get reminder settings based on task's reminder option
            reminders = self._get_reminder_settings(task)
            
            event = {
                'summary': task.title,
                'description': task.description or '',
                'start': {
                    'dateTime': start_time_str,
                    'timeZone': 'America/New_York',  # Use the same time zone
                },
                'end': {
                    'dateTime': end_time_str,
                    'timeZone': 'America/New_York',  # Use the same time zone
                },
                'reminders': reminders
            }

            current_app.logger.debug(f"Creating event with data: {event}")
            
            # Log the exact request being sent to the API for debugging
            current_app.logger.debug("Calling Google Calendar API to insert event")
            try:
                event_result = self.service.events().insert(
                    calendarId='primary',
                    body=event
                ).execute()
            except Exception as api_error:
                current_app.logger.error(f"Google Calendar API error: {str(api_error)}")
                current_app.logger.error(f"Event data that caused error: {event}")
                import traceback
                current_app.logger.error(f"API error details: {traceback.format_exc()}")
                raise
            
            current_app.logger.info(f"Successfully created Google Calendar event with ID: {event_result['id']}")

            # Update task with calendar event ID and sync time
            task.google_calendar_event_id = event_result['id']
            task.last_synced_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"Updated task {task.id} with event ID {event_result['id']}")

            return event_result

        except Exception as e:
            import traceback
            error_message = f"Failed to create calendar event: {str(e)}\n{traceback.format_exc()}"
            current_app.logger.error(error_message)
            print(error_message)  # Print for immediate debugging
            raise Exception(error_message)

    def update_event(self, task):
        """Update a calendar event from a task."""
        from flask import current_app

        if not task.google_calendar_event_id:
            current_app.logger.error(f"Cannot update calendar event: Task {task.id} has no associated Google Calendar event")
            return self.create_event(task)

        try:
            if not task.due_date:
                current_app.logger.error(f"Cannot update calendar event: Task {task.id} has no due date")
                raise ValueError("Task has no due date")

            current_app.logger.info(f"Updating Google Calendar event {task.google_calendar_event_id} for task {task.id}: {task.title}")

            # Convert date to datetime with time
            from datetime import datetime, time, timedelta

            # Default time is noon if no specific time is set
            default_time = time(12, 0)

            # Check if task has due_time attribute and it's not empty
            if hasattr(task, 'due_time') and task.due_time:
                try:
                    # Parse the time string in format HH:MM
                    hour, minute = map(int, task.due_time.split(':'))
                    event_time = time(hour, minute)
                    current_app.logger.debug(f"Using task due_time: {task.due_time} for event")
                except (ValueError, AttributeError) as time_error:
                    # If time parsing fails, use default time
                    current_app.logger.warning(f"Could not parse time string '{task.due_time}': {str(time_error)}. Using default time (noon).")
                    event_time = default_time
            else:
                # No specific time found, use default
                current_app.logger.debug("No due_time found for task, using default time (noon)")
                event_time = default_time

            # Combine the date and time into a datetime object
            start_datetime = datetime.combine(task.due_date, event_time)
            end_datetime = start_datetime + timedelta(hours=1)

            # Format the datetimes for Google Calendar API (RFC3339 format)
            # Include time zone offset for proper display
            local_timezone = pytz.timezone('America/New_York')  # Adjust to your time zone

            start_datetime_local = local_timezone.localize(start_datetime)
            end_datetime_local = local_timezone.localize(end_datetime)

            # Format times in ISO 8601 / RFC 3339 format with timezone info
            start_time_str = start_datetime_local.isoformat()
            end_time_str = end_datetime_local.isoformat()

            current_app.logger.debug(f"Event start time: {start_time_str}, end time: {end_time_str}")
            
            # Get reminder settings based on task's reminder option
            reminders = self._get_reminder_settings(task)

            event = {
                'summary': task.title,
                'description': task.description or '',
                'start': {
                    'dateTime': start_time_str,
                    'timeZone': 'America/New_York',  # Use the same time zone
                },
                'end': {
                    'dateTime': end_time_str,
                    'timeZone': 'America/New_York',  # Use the same time zone
                },
                'reminders': reminders
            }

            current_app.logger.debug(f"Updating event with data: {event}")

            current_app.logger.debug("Calling Google Calendar API to update event")
            event_result = self.service.events().update(
                calendarId='primary',
                eventId=task.google_calendar_event_id,
                body=event
            ).execute()

            current_app.logger.info(f"Successfully updated Google Calendar event with ID: {event_result['id']}")

            # Update task with sync time
            task.last_synced_at = datetime.utcnow()
            db.session.commit()

            current_app.logger.info(f"Updated sync timestamp for task {task.id}")

            return event_result

        except Exception as e:
            import traceback
            error_message = f"Failed to update calendar event: {str(e)}\n{traceback.format_exc()}"
            current_app.logger.error(error_message)
            print(error_message)  # Print for immediate debugging
            raise Exception(error_message)

    def delete_event(self, event_id):
        """Delete a calendar event by ID."""
        from flask import current_app
        
        try:
            current_app.logger.info(f"Deleting Google Calendar event: {event_id}")
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            current_app.logger.info(f"Successfully deleted Google Calendar event: {event_id}")
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to delete Google Calendar event: {str(e)}")
            raise Exception(f"Failed to delete Google Calendar event: {str(e)}")

    def create_meeting(self, summary, description, start_time, duration_minutes=60, attendees=None):
        """Create a Google Calendar event with Google Meet conferencing.
        
        Args:
            summary: Title of the meeting
            description: Description of the meeting
            start_time: Datetime object for the start time
            duration_minutes: Duration of the meeting in minutes
            attendees: List of email addresses to invite to the meeting
        """
        from flask import current_app
        
        try:
            current_app.logger.info(f"Creating Google Calendar event with Google Meet for: {summary}")
            
            # Calculate end time based on duration
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Format the datetimes for Google Calendar API (RFC3339 format)
            # Include time zone offset for proper display
            local_timezone = pytz.timezone('America/New_York')  # Adjust to your time zone
            
            start_datetime_local = local_timezone.localize(start_time) if start_time.tzinfo is None else start_time
            end_datetime_local = local_timezone.localize(end_time) if end_time.tzinfo is None else end_time
            
            # Format times in ISO 8601 / RFC 3339 format with timezone info
            start_time_str = start_datetime_local.isoformat()
            end_time_str = end_datetime_local.isoformat()
            
            current_app.logger.debug(f"Meeting start time: {start_time_str}, end time: {end_time_str}")
            
            event = {
                'summary': summary,
                'description': description or '',
                'start': {
                    'dateTime': start_time_str,
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_time_str,
                    'timeZone': 'America/New_York',
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"meet-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                },
                'reminders': {
                    'useDefault': True
                }
            }
            
            # Add attendees if provided
            if attendees:
                if isinstance(attendees, str):
                    # If a single email is provided as a string, convert to list
                    attendees = [attendees]
                
                event['attendees'] = [{'email': email} for email in attendees if email]
                current_app.logger.debug(f"Adding {len(event['attendees'])} attendees to meeting")

            current_app.logger.debug(f"Creating event with data: {event}")
            
            current_app.logger.debug("Calling Google Calendar API to insert event with conferencing")
            event_result = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1,
                sendUpdates='all'  # Send email notifications to attendees
            ).execute()
            
            current_app.logger.info(f"Successfully created Google Meet event with ID: {event_result['id']}")
            
            return event_result
        except Exception as e:
            current_app.logger.error(f"Failed to create Google Meet event: {str(e)}")
            raise Exception(f"Failed to create Google Meet event: {str(e)}")

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
            event_count = 0

            # Get user record for office_id
            from app.models.user import User
            user = User.query.get(self.user_id)
            if not user:
                raise Exception(f"User with ID {self.user_id} not found")

            with db.session.no_autoflush:
                for event in events:
                    # Skip events without a summary
                    if 'summary' not in event:
                        continue

                    # Check if event is already linked to a task
                    task = Task.query.filter_by(
                        google_calendar_event_id=event['id']
                    ).first()

                    if not task:
                        # Parse event start time
                        start = event['start'].get('dateTime', event['start'].get('date'))
                        
                        # Convert to datetime object based on format
                        if 'T' in start:
                            # This is a datetime format
                            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                            due_date = start_dt.date()
                            due_time = start_dt.strftime('%H:%M')
                        else:
                            # This is a date-only format
                            due_date = datetime.fromisoformat(start).date()
                            due_time = None

                        # Create new task from event
                        task = Task(
                            title=event['summary'],
                            description=event.get('description', ''),
                            due_date=due_date,
                            due_time=due_time,
                            status='pending',
                            priority='medium',
                            reminder_option='none',
                            google_calendar_event_id=event['id'],
                            google_calendar_sync_enabled=True,
                            created_by=self.user_id,
                            owner_id=self.user_id,  # Set owner_id to the user who is syncing
                            office_id=user.office_id,  # Set office_id if available
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        db.session.add(task)
                        event_count += 1

            db.session.commit()
            return event_count

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            db.session.rollback()
            raise Exception(f"Failed to sync calendar events: {str(e)}\n{error_details}")

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

    def sync_reminder_settings(self, task):
        """Update only the reminder settings for an existing calendar event."""
        from flask import current_app

        if not task.google_calendar_event_id or not task.google_calendar_sync_enabled:
            current_app.logger.debug(f"Cannot sync reminder settings: Task {task.id} has no Google Calendar event or sync is disabled")
            return None

        try:
            current_app.logger.info(f"Syncing reminder settings for Google Calendar event {task.google_calendar_event_id} (Task: {task.id})")
            
            # Get the current event
            event = self.service.events().get(
                calendarId='primary',
                eventId=task.google_calendar_event_id
            ).execute()
            
            # Update only the reminders field
            event['reminders'] = self._get_reminder_settings(task)
            
            # Update the event with new reminders
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=task.google_calendar_event_id,
                body=event
            ).execute()
            
            # Update task sync timestamp
            from datetime import datetime
            task.last_synced_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"Successfully synced reminder settings for task {task.id}")
            return updated_event
            
        except Exception as e:
            import traceback
            error_message = f"Failed to sync reminder settings: {str(e)}\n{traceback.format_exc()}"
            current_app.logger.error(error_message)
            print(error_message)  # Print for immediate debugging
            return None 