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

class GmailService:
    """Service class for Gmail API operations."""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize the Gmail API service with user credentials."""
        token = GoogleToken.query.filter_by(user_id=self.user_id).first()
        if not token:
            raise ValueError("No Google token found for user")

        credentials = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,  # Will be loaded from environment
            client_secret=None,  # Will be loaded from environment
            scopes=['https://www.googleapis.com/auth/gmail.modify']
        )

        if credentials.expired:
            credentials.refresh(Request())
            # Update token in database
            token.access_token = credentials.token
            token.expires_at = datetime.utcnow() + timedelta(seconds=credentials.expiry.second)
            db.session.commit()

        self.service = build('gmail', 'v1', credentials=credentials)

    def send_email(self, to, subject, body, html=None):
        """Send an email using Gmail API."""
        try:
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject

            # Add plain text version
            message.attach(MIMEText(body, 'plain'))

            # Add HTML version if provided
            if html:
                message.attach(MIMEText(html, 'html'))

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            # Create communication record
            communication = Communication(
                type='email',
                subject=subject,
                content=body,
                sender_id=self.user_id,
                status='sent',
                gmail_message_id=sent_message['id'],
                gmail_thread_id=sent_message.get('threadId')
            )
            db.session.add(communication)
            db.session.commit()

            return sent_message

        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")

    def sync_emails(self, days_back=7):
        """Sync emails from Gmail to local database."""
        try:
            # Calculate time range for sync
            after_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            
            # Get list of messages
            results = self.service.users().messages().list(
                userId='me',
                q=f'after:{after_date}'
            ).execute()

            messages = results.get('messages', [])
            
            for message in messages:
                # Check if message already synced
                existing = Communication.query.filter_by(
                    gmail_message_id=message['id']
                ).first()
                
                if not existing:
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
                        ).decode()

                    # Create communication record
                    communication = Communication(
                        type='email',
                        subject=subject,
                        content=body,
                        sender_id=self.user_id,
                        status='received',
                        gmail_message_id=message['id'],
                        gmail_thread_id=msg['threadId'],
                        sent_at=datetime.fromtimestamp(int(msg['internalDate'])/1000)
                    )
                    db.session.add(communication)

            db.session.commit()
            return len(messages)

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to sync emails: {str(e)}")

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