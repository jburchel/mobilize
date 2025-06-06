"""
Google API service for authentication and interaction with Google services
"""
import os
import json
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import current_app, url_for, session
from typing import Dict, Any, Optional
from app.auth.google_oauth import get_google_credentials
import logging
import re

logger = logging.getLogger(__name__)

class GoogleAPIService:
    """
    Service for handling Google API interactions, including authentication,
    fetching contacts, and other Google API operations.
    """
    
    # Google API Scopes
    SCOPES = [
        'https://www.googleapis.com/auth/contacts.readonly',
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    # Constants
    GOOGLE_CLIENT_SECRETS_FILE = 'client_secret.json'
    
    def __init__(self, user_id, api_name, api_version, scopes=None):
        """Initialize the service with user credentials."""
        self.user_id = user_id
        self.api_name = api_name
        self.api_version = api_version
        self.scopes = scopes
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the Google API service."""
        try:
            # Get credentials using the helper function
            credentials = get_google_credentials(self.user_id)
            
            if not credentials:
                raise ValueError(f"User {self.user_id} does not have valid Google credentials")
            
            self.service = build(self.api_name, self.api_version, credentials=credentials)
            logger.info(f"Google {self.api_name} API service initialized for user {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Google {self.api_name} API service: {str(e)}")
            raise
    
    def get_service(self):
        """Get the Google API service object."""
        if not self.service:
            self._initialize_service()
        return self.service
    
    @classmethod
    def get_oauth_flow(cls, redirect_uri=None):
        """Create and return an OAuth flow object for Google authentication."""
        client_secrets_file = os.path.join(
            current_app.config['INSTANCE_PATH'], 
            cls.GOOGLE_CLIENT_SECRETS_FILE
        )
        
        # Check if client secrets file exists
        if not os.path.exists(client_secrets_file):
            current_app.logger.error(f"Client secrets file not found at {client_secrets_file}")
            return None
        
        flow = Flow.from_client_secrets_file(
            client_secrets_file,
            scopes=cls.SCOPES,
            redirect_uri=redirect_uri
        )
        
        return flow
    
    @classmethod
    def get_authorization_url(cls, user_id):
        """
        Generate the authorization URL for Google OAuth flow.
        
        Args:
            user_id: The user ID to store in the state parameter
            
        Returns:
            tuple: (authorization_url, state)
        """
        flow = cls.get_oauth_flow(
            redirect_uri=url_for('google_sync.oauth_callback', _external=True)
        )
        
        if not flow:
            return None, None
        
        # Generate a state value and include the user_id
        state = json.dumps({"user_id": user_id})
        
        # Generate the authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state
        )
        
        return authorization_url, state
    
    @classmethod
    def exchange_code_for_tokens(cls, code, redirect_uri=None):
        """
        Exchange the authorization code for access and refresh tokens.
        
        Args:
            code: The authorization code from the OAuth callback
            redirect_uri: The redirect URI used in the initial authorization request
            
        Returns:
            dict: The token response containing access_token, refresh_token, etc.
        """
        flow = cls.get_oauth_flow(redirect_uri=redirect_uri)
        
        if not flow:
            return None
        
        # Exchange the code for tokens
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Return the token information
            return {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }
        except Exception as e:
            current_app.logger.error(f"Error exchanging code for tokens: {str(e)}")
            return None
    
    @classmethod
    def get_google_credentials(cls, token_info):
        """
        Create Google Credentials object from token information.
        
        Args:
            token_info: Dict containing token information
            
        Returns:
            Credentials: Google Credentials object
        """
        if not token_info:
            return None
        
        # Convert expiry string back to datetime if it exists
        expiry = None
        if token_info.get('expiry'):
            try:
                expiry = datetime.datetime.fromisoformat(token_info['expiry'])
            except ValueError:
                current_app.logger.error(f"Invalid expiry format: {token_info['expiry']}")
        
        # Create credentials object
        try:
            credentials = Credentials(
                token=token_info.get('token'),
                refresh_token=token_info.get('refresh_token'),
                token_uri=token_info.get('token_uri'),
                client_id=token_info.get('client_id'),
                client_secret=token_info.get('client_secret'),
                scopes=token_info.get('scopes'),
                expiry=expiry
            )
            return credentials
        except Exception as e:
            current_app.logger.error(f"Error creating credentials: {str(e)}")
            return None
    
    @classmethod
    def is_token_valid(cls, token_info):
        """
        Check if the token is valid and not expired.
        
        Args:
            token_info: Dict containing token information
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not token_info or not token_info.get('token'):
            return False
        
        # Check if token is expired
        if token_info.get('expiry'):
            try:
                expiry = datetime.datetime.fromisoformat(token_info['expiry'])
                if expiry <= datetime.datetime.now():
                    # Token is expired, try to refresh
                    refreshed_token_info = cls.refresh_token(token_info)
                    return refreshed_token_info is not None
            except ValueError:
                current_app.logger.error(f"Invalid expiry format: {token_info['expiry']}")
                return False
        
        return True
    
    @classmethod
    def refresh_token(cls, token_info):
        """
        Refresh the access token using the refresh token.
        
        Args:
            token_info: Dict containing token information
            
        Returns:
            dict: Updated token information or None if refresh fails
        """
        if not token_info or not token_info.get('refresh_token'):
            return None
        
        credentials = cls.get_google_credentials(token_info)
        
        if not credentials:
            return None
        
        try:
            credentials.refresh(None)  # Use default request
            
            # Update token information
            updated_token_info = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }
            
            return updated_token_info
        except Exception as e:
            current_app.logger.error(f"Error refreshing token: {str(e)}")
            return None
    
    @classmethod
    def get_people_service(cls, token_info):
        """
        Get the Google People API service.
        
        Args:
            token_info: Dict containing token information
            
        Returns:
            Resource: Google People API service resource
        """
        credentials = cls.get_google_credentials(token_info)
        
        if not credentials:
            return None
        
        try:
            return build('people', 'v1', credentials=credentials)
        except HttpError as error:
            current_app.logger.error(f"Error building people service: {str(error)}")
            return None
    
    @classmethod
    def get_calendar_service(cls, token_info):
        """
        Get the Google Calendar API service.
        
        Args:
            token_info: Dict containing token information
            
        Returns:
            Resource: Google Calendar API service resource
        """
        credentials = cls.get_google_credentials(token_info)
        
        if not credentials:
            return None
        
        try:
            return build('calendar', 'v3', credentials=credentials)
        except HttpError as error:
            current_app.logger.error(f"Error building calendar service: {str(error)}")
            return None
    
    @classmethod
    def get_gmail_service(cls, token_info):
        """
        Get the Gmail API service.
        
        Args:
            token_info: Dict containing token information
            
        Returns:
            Resource: Gmail API service resource
        """
        credentials = cls.get_google_credentials(token_info)
        
        if not credentials:
            return None
        
        try:
            return build('gmail', 'v1', credentials=credentials)
        except HttpError as error:
            current_app.logger.error(f"Error building gmail service: {str(error)}")
            return None
    
    @classmethod
    def fetch_contacts(cls, token_info, page_token=None, limit=100):
        """
        Fetch contacts from Google People API.
        
        Args:
            token_info: Dict containing token information
            page_token: Token for pagination
            limit: Maximum number of contacts to fetch per page
            
        Returns:
            tuple: (list of contacts, next page token)
        """
        service = cls.get_people_service(token_info)
        
        if not service:
            return [], None
        
        try:
            # Call the People API to fetch contacts
            results = service.people().connections().list(
                resourceName='people/me',
                pageSize=limit,
                pageToken=page_token,
                personFields='names,emailAddresses,phoneNumbers,addresses,organizations,metadata'
            ).execute()
            
            connections = results.get('connections', [])
            next_page_token = results.get('nextPageToken')
            
            return connections, next_page_token
        except HttpError as error:
            current_app.logger.error(f"Error fetching contacts: {str(error)}")
            return [], None
    
    @classmethod
    def format_google_contact(cls, google_contact):
        """
        Format Google contact data into a dictionary format compatible with our application.
        
        Args:
            google_contact: The Google contact data
            
        Returns:
            dict: Formatted contact data
        """
        resource_name = google_contact.get('resourceName', '')
        google_id = resource_name.split('/')[-1] if resource_name else ''
        
        # Get names
        names = google_contact.get('names', [])
        first_name = names[0].get('givenName', '') if names else ''
        last_name = names[0].get('familyName', '') if names else ''
        display_name = names[0].get('displayName', '') if names else ''
        
        # Enhanced name parsing
        if (not first_name or not last_name) and display_name:
            # If only display name is available, try to extract first and last names
            
            # Special case: Handle names like "Last, First"
            comma_pattern = r'^([^,]+),\s+(.+)$'
            comma_match = re.search(comma_pattern, display_name)
            if comma_match:
                last_name = comma_match.group(1).strip()
                first_name = comma_match.group(2).strip()
            else:
                # Check for common spousal patterns like "John & Jane Doe" or "John and Jane Smith"
                spousal_pattern = r'^(.*?)\s+(?:&|and)\s+(.*?)\s+(\S+)$'
                match = re.search(spousal_pattern, display_name, re.IGNORECASE)
                
                if match:
                    # This is likely a couple
                    first_spouse = match.group(1).strip()
                    second_spouse = match.group(2).strip()
                    shared_last = match.group(3).strip()
                    
                    # Use the first person's name (we can only have one person per contact)
                    first_name = first_spouse
                    last_name = shared_last
                else:
                    # Try additional name patterns
                    
                    # Pattern for names with titles: "Dr. John Smith" or "Mr. John Smith"
                    title_pattern = r'^(?:Dr\.|Mr\.|Mrs\.|Ms\.|Prof\.|Rev\.)\s+(.+?)(?:\s+(\S+))?$'
                    title_match = re.search(title_pattern, display_name)
                    
                    if title_match and title_match.group(2):
                        # We have a title followed by a name with possible last name
                        first_name = title_match.group(1).strip()
                        last_name = title_match.group(2).strip()
                    else:
                        # Standard approach: Try to split by the last space (common Western name pattern)
                        parts = display_name.strip().split()
                        if len(parts) >= 2:
                            first_name = ' '.join(parts[:-1])
                            last_name = parts[-1]
                        else:
                            # Single word name
                            first_name = display_name
                            last_name = ''
        
        # Get email addresses
        email_addresses = google_contact.get('emailAddresses', [])
        primary_email = next((email.get('value', '') for email in email_addresses 
                             if email.get('metadata', {}).get('primary', False)), 
                            email_addresses[0].get('value', '') if email_addresses else '')
        
        # Get phone numbers
        phone_numbers = google_contact.get('phoneNumbers', [])
        primary_phone = next((phone.get('value', '') for phone in phone_numbers 
                             if phone.get('metadata', {}).get('primary', False)), 
                            phone_numbers[0].get('value', '') if phone_numbers else '')
        
        # Get addresses
        addresses = google_contact.get('addresses', [])
        primary_address = next((address for address in addresses 
                               if address.get('metadata', {}).get('primary', False)), 
                              addresses[0] if addresses else {})
        
        street = primary_address.get('streetAddress', '')
        city = primary_address.get('city', '')
        state = primary_address.get('region', '')
        zip_code = primary_address.get('postalCode', '')
        country = primary_address.get('country', '')
        
        # Get organizations
        organizations = google_contact.get('organizations', [])
        organization = organizations[0] if organizations else {}
        title = organization.get('title', '')
        company = organization.get('name', '')
        
        # Get last updated
        metadata = google_contact.get('metadata', {})
        updated = metadata.get('sources', [{}])[0].get('updateTime', '') if metadata.get('sources') else ''
        
        # Format the contact
        formatted_contact = {
            'google_id': google_id,
            'first_name': first_name,
            'last_name': last_name,
            'display_name': display_name,  # Include original display name
            'email': primary_email,
            'phone': primary_phone,
            'street': street,
            'city': city,
            'state': state,
            'zip_code': zip_code,
            'country': country,
            'last_updated': updated
        }
        
        return formatted_contact 