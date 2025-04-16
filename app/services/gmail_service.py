from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.models.communication import Communication
from app.models.google_token import GoogleToken
from app.extensions import db
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import logging
import os
import time
import random

class GmailService:
    """Service class for Gmail API operations."""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize the Gmail API service with user credentials."""
        logger = logging.getLogger(__name__)
        
        token = GoogleToken.query.filter_by(user_id=self.user_id).first()
        if not token:
            logger.error(f"No Google token found for user {self.user_id}")
            raise ValueError("No Google token found for user")
            
        logger.error(f"INIT DEBUG - Creating credentials for user {self.user_id}")
        logger.error(f"INIT DEBUG - Token info: access_token exists={bool(token.access_token)}, refresh_token exists={bool(token.refresh_token)}")
        
        # Get client ID and secret from environment
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            logger.error("INIT DEBUG - Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET env variables")
        
        try:
            credentials = Credentials(
                token=token.access_token,
                refresh_token=token.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=['https://www.googleapis.com/auth/gmail.modify']
            )
            
            logger.error(f"INIT DEBUG - Created credentials object, expired={credentials.expired}")

            if credentials.expired:
                logger.error("INIT DEBUG - Credentials expired, attempting refresh")
                credentials.refresh(Request())
                # Update token in database
                token.access_token = credentials.token
                token.expires_at = datetime.utcnow() + timedelta(seconds=credentials.expiry.second)
                db.session.commit()
                logger.error("INIT DEBUG - Credentials refreshed successfully")

            logger.error(f"INIT DEBUG - Building Gmail service with credentials")
            self.service = build('gmail', 'v1', credentials=credentials)
            logger.error(f"INIT DEBUG - Gmail service built successfully")
            
        except Exception as e:
            import traceback
            logger.error(f"INIT DEBUG - Error initializing Gmail service: {str(e)}")
            logger.error(f"INIT DEBUG - Traceback: {traceback.format_exc()}")
            raise

    def send_email(self, to, subject, body, html=None):
        """Send an email using Gmail API."""
        try:
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject
            
            # Get the user's email and use it as the From address
            token = GoogleToken.query.filter_by(user_id=self.user_id).first()
            
            # IMPORTANT: Log token details for debugging
            logger = logging.getLogger(__name__)
            logger.error(f"TOKEN DEBUG - user_id: {self.user_id}, token found: {token is not None}")
            if token:
                logger.error(f"TOKEN DEBUG - access_token exists: {bool(token.access_token)}")
                logger.error(f"TOKEN DEBUG - refresh_token exists: {bool(token.refresh_token)}")
                logger.error(f"TOKEN DEBUG - email field: {token.email}")
                # If token.email is empty, get it from the authenticated user's profile
                if not token.email:
                    logger.error("TOKEN DEBUG - Email is empty, attempting to get from user profile")
                    try:
                        from google.oauth2.credentials import Credentials
                        from googleapiclient.discovery import build
                        import os
                        
                        # Create temp credentials
                        credentials = Credentials(
                            token=token.access_token,
                            refresh_token=token.refresh_token,
                            token_uri="https://oauth2.googleapis.com/token",
                            client_id=os.getenv('GOOGLE_CLIENT_ID'),
                            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
                            scopes=['https://www.googleapis.com/auth/userinfo.email']
                        )
                        
                        # Get user info to get email
                        service = build('oauth2', 'v2', credentials=credentials)
                        user_info = service.userinfo().get().execute()
                        if 'email' in user_info:
                            token.email = user_info['email']
                            from app.extensions import db
                            db.session.commit()
                            logger.error(f"TOKEN DEBUG - Retrieved and saved email: {token.email}")
                    except Exception as e:
                        logger.error(f"TOKEN DEBUG - Failed to get email from profile: {str(e)}")
            
            from_email = token.email if token and hasattr(token, 'email') and token.email else 'me'
            message['from'] = from_email
            logger.error(f"TOKEN DEBUG - Using from_email: {from_email}")

            # Add plain text version
            message.attach(MIMEText(body, 'plain'))

            # Add HTML version if provided
            if html:
                message.attach(MIMEText(html, 'html'))

            # Debug the message before sending
            logger.debug(f"Sending email to: {to}, subject: {subject}, from: {from_email}")
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Debug the raw message size
            logger.debug(f"Raw message size: {len(raw_message)} bytes")
            
            logger.error(f"TOKEN DEBUG - About to call Gmail API with userId='me', checking service: {self.service is not None}")
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Email sent successfully, Gmail message ID: {sent_message.get('id')}")

            # Create communication record - do not create a duplicate record
            # since the communications controller already creates one
            return sent_message

        except Exception as e:
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send email: {str(e)}")
            logger.error(f"ERROR TRACEBACK: {traceback.format_exc()}")
            raise Exception(f"Failed to send email: {str(e)}")

    def sync_emails(self, days_back=7):
        """Sync emails from Gmail to local database."""
        try:
            # Calculate time range for sync
            after_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            
            # Get the user's sync preference
            from app.models.user import User
            user = User.query.get(self.user_id)
            
            # Check if the user has the email_sync_contacts_only attribute
            # This helps with backward compatibility during the migration
            sync_contacts_only = False
            try:
                if hasattr(user, 'email_sync_contacts_only'):
                    sync_contacts_only = user.email_sync_contacts_only
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error checking email_sync_contacts_only preference: {str(e)}")
                logger.info("Defaulting to sync all emails mode")
            
            # Get list of messages
            results = self.service.users().messages().list(
                userId='me',
                q=f'after:{after_date}'
            ).execute()

            messages = results.get('messages', [])
            synced_count = 0
            logger = logging.getLogger(__name__)
            
            # If we're only syncing contacts, get all email addresses from the database
            contact_emails = set()
            if sync_contacts_only:
                from app.models.person import Person
                from app.models.church import Church
                
                # Get all person emails
                people = Person.query.filter(Person.email != None, Person.email != '').all()
                for person in people:
                    if person.email:
                        contact_emails.add(person.email.lower())
                
                # Get all church emails and related contacts
                churches = Church.query.all()
                for church in churches:
                    # Add main church email
                    if church.email:
                        contact_emails.add(church.email.lower())
                    
                    # Add pastor emails
                    if church.senior_pastor_email:
                        contact_emails.add(church.senior_pastor_email.lower())
                    if church.mission_pastor_email:
                        contact_emails.add(church.mission_pastor_email.lower())
                
                logger.info(f"Found {len(contact_emails)} contact emails for filtering")
            
            # Use session.no_autoflush to prevent premature flush operations
            with db.session.no_autoflush:
                for message in messages:
                    # Function to check if message exists with retry logic
                    def check_message_exists_with_retry(message_id, max_retries=3):
                        for attempt in range(max_retries):
                            try:
                                return Communication.query.filter_by(
                                    gmail_message_id=message_id
                                ).first()
                            except Exception as e:
                                if "database is locked" in str(e) and attempt < max_retries - 1:
                                    # Exponential backoff with jitter
                                    sleep_time = (2 ** attempt) + random.random()
                                    logger.warning(f"Database locked, retrying in {sleep_time:.2f} seconds...")
                                    time.sleep(sleep_time)
                                else:
                                    raise
                    
                    # Check if message already synced with retry logic
                    try:
                        existing = check_message_exists_with_retry(message['id'])
                        
                        if existing:
                            continue
                            
                        # Get full message details
                        msg = self.service.users().messages().get(
                            userId='me',
                            id=message['id']
                        ).execute()

                        headers = msg['payload']['headers']
                        subject = next(
                            (h['value'] for h in headers if h['name'].lower() == 'subject'),
                            'No Subject'
                        )
                        
                        # Get sender and recipient
                        from_email = next(
                            (h['value'] for h in headers if h['name'].lower() == 'from'),
                            'Unknown'
                        )
                        
                        to_email = next(
                            (h['value'] for h in headers if h['name'].lower() == 'to'),
                            'Unknown'
                        )
                        
                        # Extract email addresses from the from/to fields
                        from_email_address = self._extract_email_address(from_email)
                        to_email_address = self._extract_email_address(to_email)
                        
                        # If we're only syncing contacts, check if this email is to/from a contact
                        if sync_contacts_only:
                            is_from_contact = from_email_address and from_email_address.lower() in contact_emails
                            is_to_contact = to_email_address and to_email_address.lower() in contact_emails
                            
                            # Skip this email if it's not to or from a contact
                            if not is_from_contact and not is_to_contact:
                                continue
                        
                        # Determine direction (inbound or outbound)
                        # Look up the user's email from GoogleToken
                        token = GoogleToken.query.filter_by(user_id=self.user_id).first()
                        user_email = token.email if token and token.email else None
                        
                        # If the user's email is in the 'to' field, it's inbound
                        direction = 'inbound'
                        if user_email and user_email in from_email:
                            direction = 'outbound'
                        
                        # Get message body
                        if 'parts' in msg['payload']:
                            parts = msg['payload']['parts']
                            body = next(
                                (
                                    base64.urlsafe_b64decode(p['body']['data']).decode()
                                    for p in parts
                                    if p['mimeType'] == 'text/plain'
                                ),
                                'No content'
                            )
                        else:
                            body = base64.urlsafe_b64decode(
                                msg['payload']['body']['data']
                            ).decode() if 'data' in msg['payload']['body'] else 'No content'

                        # Create communication record
                        communication = Communication(
                            type='email',
                            message=body,
                            subject=subject,
                            direction=direction,
                            date_sent=datetime.fromtimestamp(int(msg['internalDate'])/1000),
                            date=datetime.fromtimestamp(int(msg['internalDate'])/1000),
                            gmail_message_id=message['id'],
                            gmail_thread_id=msg['threadId'],
                            email_status='synced',
                            user_id=self.user_id,
                            owner_id=self.user_id,
                            office_id=1,  # Default office ID - you may need to get this dynamically
                            last_synced_at=datetime.now()
                        )
                        
                        # Retry logic for adding and committing
                        max_commit_retries = 3
                        for commit_attempt in range(max_commit_retries):
                            try:
                                db.session.add(communication)
                                db.session.commit()
                                synced_count += 1
                                break
                            except Exception as commit_error:
                                if "database is locked" in str(commit_error) and commit_attempt < max_commit_retries - 1:
                                    # Exponential backoff with jitter
                                    sleep_time = (2 ** commit_attempt) + random.random()
                                    logger.warning(f"Database locked during commit, retrying in {sleep_time:.2f} seconds...")
                                    time.sleep(sleep_time)
                                    db.session.rollback()
                                else:
                                    logger.error(f"Error committing message {message['id']}: {str(commit_error)}")
                                    db.session.rollback()
                                    # If this specific message failed after all retries, continue with the next one
                                    break
                    except Exception as message_error:
                        logger.error(f"Error processing message {message['id']}: {str(message_error)}")
                        # Continue with next message

            logger.info(f"Successfully synced {synced_count} emails from Gmail")
            return synced_count

        except Exception as e:
            db.session.rollback()
            logger = logging.getLogger(__name__)
            logger.error(f"Error syncing emails: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to sync emails: {str(e)}")
            
    def _extract_email_address(self, email_string):
        """Extract email address from a string like 'Name <email@example.com>' or just 'email@example.com'"""
        if not email_string:
            return None
            
        # Try to match pattern "Name <email@example.com>"
        import re
        email_pattern = r'<([^<>]+)>'
        match = re.search(email_pattern, email_string)
        
        if match:
            return match.group(1)
        
        # If no match, try to find any email pattern
        email_pattern = r'[\w\.-]+@[\w\.-]+'
        match = re.search(email_pattern, email_string)
        
        if match:
            return match.group(0)
            
        return None

    def get_email_thread(self, thread_id):
        """Get all messages in an email thread."""
        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id
            ).execute()

            messages = []
            for message in thread['messages']:
                headers = message['payload']['headers']
                subject = next(
                    (h['value'] for h in headers if h['name'].lower() == 'subject'),
                    'No Subject'
                )
                from_header = next(
                    (h['value'] for h in headers if h['name'].lower() == 'from'),
                    'Unknown'
                )
                
                if 'parts' in message['payload']:
                    parts = message['payload']['parts']
                    body = next(
                        (
                            base64.urlsafe_b64decode(p['body']['data']).decode()
                            for p in parts
                            if p['mimeType'] == 'text/plain'
                        ),
                        'No content'
                    )
                else:
                    body = base64.urlsafe_b64decode(
                        message['payload']['body']['data']
                    ).decode()

                messages.append({
                    'id': message['id'],
                    'subject': subject,
                    'from': from_header,
                    'body': body,
                    'date': datetime.fromtimestamp(int(message['internalDate'])/1000)
                })

            return messages

        except Exception as e:
            raise Exception(f"Failed to get email thread: {str(e)}")

    def mark_as_read(self, message_id):
        """Mark an email as read."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            raise Exception(f"Failed to mark message as read: {str(e)}")

    def archive_email(self, message_id):
        """Archive an email (remove from inbox)."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return True
        except Exception as e:
            raise Exception(f"Failed to archive message: {str(e)}") 