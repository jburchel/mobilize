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

            logger.error("INIT DEBUG - Building Gmail service with credentials")
            self.service = build('gmail', 'v1', credentials=credentials)
            logger.error("INIT DEBUG - Gmail service built successfully")
            
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
            
            sender_email = None
            if token:
                logger.error(f"TOKEN DEBUG - access_token exists: {bool(token.access_token)}")
                logger.error(f"TOKEN DEBUG - refresh_token exists: {bool(token.refresh_token)}")
                logger.error(f"TOKEN DEBUG - email field: {token.email}")
                if token.email:
                    sender_email = token.email
                    message['from'] = sender_email
                else:
                    logger.error("TOKEN DEBUG - Email field is empty, using default")
                    message['from'] = 'noreply@mobilize-app.org'
                    sender_email = 'noreply@mobilize-app.org'
            else:
                logger.error("TOKEN DEBUG - No token found, using default sender")
                message['from'] = 'noreply@mobilize-app.org'
                sender_email = 'noreply@mobilize-app.org'

            # Add body parts
            message.attach(MIMEText(body, 'plain'))
            
            # Add HTML version if provided
            if html:
                message.attach(MIMEText(html, 'html'))
            else:
                # Convert plain text to simple HTML
                # Manually create HTML content without using f-string with backslash
                body_html = body.replace('\n', '<br>')
                html_content = '<html><body><p>' + body_html + '</p></body></html>'
                message.attach(MIMEText(html_content, 'html'))
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send the message
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            # Log the email event
            from app.utils.log_utils import log_email_event
            
            # Create a unique ID for this email
            email_id = result.get('id', str(random.randint(10000, 99999)))
            
            # Log the email event
            log_email_event(
                email_id=email_id,
                sender=sender_email,
                recipient=to,
                subject=subject,
                status='sent',
                user_id=self.user_id
            )
            
            # Create a Communication record for this email
            communication = Communication(
                user_id=self.user_id,
                contact_email=to,
                subject=subject,
                content=body,
                direction='outbound',
                date_sent=datetime.now(),
                email_status='sent',
                gmail_message_id=result.get('id'),
                gmail_thread_id=result.get('threadId')
            )
            db.session.add(communication)
            db.session.commit()
            
            return result
            
        except Exception as e:
            # Log the error
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending email: {str(e)}")
            
            # Log the email event as failed
            from app.utils.log_utils import log_email_event
            
            # Create a unique ID for this email
            email_id = str(random.randint(10000, 99999))
            
            # Log the email event
            log_email_event(
                email_id=email_id,
                sender=sender_email if 'sender_email' in locals() else 'unknown',
                recipient=to,
                subject=subject,
                status='failed',
                user_id=self.user_id,
                error=str(e)
            )
            
            # Create a Communication record for this failed email
            communication = Communication(
                user_id=self.user_id,
                contact_email=to,
                subject=subject,
                content=body,
                direction='outbound',
                date_sent=datetime.now(),
                email_status='failed',
                error_message=str(e)
            )
            db.session.add(communication)
            db.session.commit()
            
            # Re-raise the exception
            raise

    def sync_emails(self, days_back=7):
        """Sync emails from Gmail to local database."""
        try:
            logger = logging.getLogger(__name__)
            logger.info(f"Starting email sync for user {self.user_id}")
            
            # Calculate date range for query
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for Gmail API query
            start_date_str = start_date.strftime('%Y/%m/%d')
            end_date_str = end_date.strftime('%Y/%m/%d')
            
            # Query for emails in the date range
            query = f"after:{start_date_str} before:{end_date_str}"
            
            # Get messages matching the query
            response = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100  # Limit to 100 messages for performance
            ).execute()
            
            messages = response.get('messages', [])
            synced_count = 0
            
            # Define a function to check if a message already exists in the database
            def check_message_exists_with_retry(message_id, max_retries=3):
                for attempt in range(max_retries):
                    try:
                        existing = Communication.query.filter_by(
                            gmail_message_id=message_id
                        ).first()
                        return existing is not None
                    except Exception as e:
                        logger.error(f"Error checking message existence (attempt {attempt+1}): {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(0.5)  # Wait before retrying
                        else:
                            raise
                return False
            
            # Process each message
            for message_data in messages:
                message_id = message_data['id']
                
                # Skip if message already exists in database
                if check_message_exists_with_retry(message_id):
                    logger.info(f"Skipping already synced message {message_id}")
                    continue
                
                try:
                    # Get full message details
                    message = self.service.users().messages().get(
                        userId='me',
                        id=message_id,
                        format='full'
                    ).execute()
                    
                    # Extract message details
                    headers = message['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                    from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                    to_header = next((h['value'] for h in headers if h['name'].lower() == 'to'), 'Unknown')
                    date_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), None)
                    
                    # Extract sender email
                    sender_email = self._extract_email_address(from_header)
                    recipient_email = self._extract_email_address(to_header)
                    
                    # Determine direction (inbound/outbound)
                    token = GoogleToken.query.filter_by(user_id=self.user_id).first()
                    user_email = token.email if token else None
                    
                    direction = 'inbound'
                    if user_email and recipient_email and user_email != recipient_email:
                        direction = 'outbound'
                    
                    # Extract message body
                    body = 'No content'
                    if 'parts' in message['payload']:
                        parts = message['payload']['parts']
                        for part in parts:
                            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                                body = base64.urlsafe_b64decode(part['body']['data']).decode()
                                break
                    elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                        body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode()
                    
                    # Parse date
                    date_sent = datetime.now()
                    if 'internalDate' in message:
                        date_sent = datetime.fromtimestamp(int(message['internalDate'])/1000)
                    elif date_header:
                        try:
                            from email.utils import parsedate_to_datetime
                            date_sent = parsedate_to_datetime(date_header)
                        except Exception:
                            pass
                    
                    # Create Communication record
                    communication = Communication(
                        user_id=self.user_id,
                        contact_email=sender_email if direction == 'inbound' else recipient_email,
                        subject=subject,
                        content=body,
                        direction=direction,
                        date_sent=date_sent,
                        email_status='received' if direction == 'inbound' else 'sent',
                        gmail_message_id=message_id,
                        gmail_thread_id=message.get('threadId')
                    )
                    
                    db.session.add(communication)
                    db.session.commit()
                    synced_count += 1
                    
                    # Log success
                    logger.info(f"Synced message {message_id} from {sender_email}")
                    
                except Exception as message_error:
                    logger.error(f"Error processing message {message_id}: {str(message_error)}")
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
                            if p['mimeType'] == 'text/plain' and 'data' in p['body']
                        ),
                        'No content'
                    )
                elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                    body = base64.urlsafe_b64decode(
                        message['payload']['body']['data']
                    ).decode()
                else:
                    body = 'No content'

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
