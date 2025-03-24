from typing import List, Dict, Any
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.models.person import Person
from app.models.contact import Contact
from app.models.user import User
from app.extensions import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GooglePeopleService:
    """Service class for Google People API operations."""
    
    SCOPES = ['https://www.googleapis.com/auth/contacts']
    API_VERSION = 'v1'
    API_SERVICE = 'people'
    
    def __init__(self, user: User):
        """Initialize the service with user credentials."""
        self.user = user
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the Google People API service."""
        try:
            if not self.user.google_refresh_token:
                raise ValueError("User does not have Google credentials")
                
            credentials = Credentials(
                None,  # No access token needed as we'll use refresh token
                refresh_token=self.user.google_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.user.google_client_id,
                client_secret=self.user.google_client_secret,
                scopes=self.SCOPES
            )
            
            self.service = build(self.API_SERVICE, self.API_VERSION, credentials=credentials)
            logger.info(f"Google People API service initialized for user {self.user.id}")
        except Exception as e:
            logger.error(f"Failed to initialize Google People API service: {str(e)}")
            raise
    
    def list_contacts(self, page_size: int = 100, sync_token: str = None) -> Dict[str, Any]:
        """List Google contacts with pagination support."""
        try:
            request = self.service.people().connections().list(
                resourceName='people/me',
                pageSize=page_size,
                personFields='names,emailAddresses,phoneNumbers,addresses,organizations,biographies',
                syncToken=sync_token
            )
            
            return request.execute()
        except Exception as e:
            logger.error(f"Failed to list Google contacts: {str(e)}")
            raise
    
    def get_contact(self, resource_name: str) -> Dict[str, Any]:
        """Get a specific Google contact by resource name."""
        try:
            return self.service.people().get(
                resourceName=resource_name,
                personFields='names,emailAddresses,phoneNumbers,addresses,organizations,biographies'
            ).execute()
        except Exception as e:
            logger.error(f"Failed to get Google contact {resource_name}: {str(e)}")
            raise
    
    def create_contact(self, person: Person) -> Dict[str, Any]:
        """Create a new Google contact from a Person model."""
        try:
            contact_data = {
                'names': [{
                    'givenName': person.first_name,
                    'familyName': person.last_name
                }],
                'emailAddresses': [{'value': person.email}] if person.email else [],
                'phoneNumbers': [{'value': person.phone}] if person.phone else [],
                'addresses': [{
                    'streetAddress': person.address_street,
                    'city': person.address_city,
                    'region': person.address_state,
                    'postalCode': person.address_zip,
                    'country': person.address_country
                }] if person.address_street else []
            }
            
            result = self.service.people().createContact(
                body=contact_data
            ).execute()
            
            # Update person with Google contact ID
            person.google_contact_id = result.get('resourceName')
            db.session.commit()
            
            return result
        except Exception as e:
            logger.error(f"Failed to create Google contact for person {person.id}: {str(e)}")
            raise
    
    def update_contact(self, person: Person) -> Dict[str, Any]:
        """Update an existing Google contact from a Person model."""
        if not person.google_contact_id:
            raise ValueError("Person does not have a Google contact ID")
            
        try:
            contact_data = {
                'etag': self.get_contact(person.google_contact_id).get('etag'),
                'names': [{
                    'givenName': person.first_name,
                    'familyName': person.last_name
                }],
                'emailAddresses': [{'value': person.email}] if person.email else [],
                'phoneNumbers': [{'value': person.phone}] if person.phone else [],
                'addresses': [{
                    'streetAddress': person.address_street,
                    'city': person.address_city,
                    'region': person.address_state,
                    'postalCode': person.address_zip,
                    'country': person.address_country
                }] if person.address_street else []
            }
            
            return self.service.people().updateContact(
                resourceName=person.google_contact_id,
                updatePersonFields='names,emailAddresses,phoneNumbers,addresses',
                body=contact_data
            ).execute()
        except Exception as e:
            logger.error(f"Failed to update Google contact for person {person.id}: {str(e)}")
            raise
    
    def delete_contact(self, resource_name: str) -> None:
        """Delete a Google contact by resource name."""
        try:
            self.service.people().deleteContact(
                resourceName=resource_name
            ).execute()
        except Exception as e:
            logger.error(f"Failed to delete Google contact {resource_name}: {str(e)}")
            raise 