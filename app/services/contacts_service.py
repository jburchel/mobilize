from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.models.person import Person
from app.models.google_token import GoogleToken
from app.extensions import db
from datetime import datetime, timedelta

class ContactsService:
    """Service class for Google People (Contacts) API operations."""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize the People API service with user credentials."""
        token = GoogleToken.query.filter_by(user_id=self.user_id).first()
        if not token:
            raise ValueError("No Google token found for user")

        credentials = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,  # Will be loaded from environment
            client_secret=None,  # Will be loaded from environment
            scopes=['https://www.googleapis.com/auth/contacts']
        )

        if credentials.expired:
            credentials.refresh(Request())
            # Update token in database
            token.access_token = credentials.token
            token.expires_at = datetime.utcnow() + timedelta(seconds=credentials.expiry.second)
            db.session.commit()

        self.service = build('people', 'v1', credentials=credentials)

    def create_contact(self, person):
        """Create a Google contact from a person."""
        try:
            contact_body = {
                'names': [
                    {
                        'givenName': person.first_name,
                        'familyName': person.last_name
                    }
                ],
                'emailAddresses': [
                    {
                        'value': person.email,
                        'type': 'work'
                    }
                ] if person.email else [],
                'phoneNumbers': [
                    {
                        'value': person.phone,
                        'type': 'work'
                    }
                ] if person.phone else [],
                'addresses': [
                    {
                        'streetAddress': person.address,
                        'city': person.city,
                        'region': person.state,
                        'postalCode': person.zip_code,
                        'country': 'US',
                        'type': 'work'
                    }
                ] if person.address else []
            }

            contact = self.service.people().createContact(
                body=contact_body
            ).execute()

            # Update person with Google contact ID
            person.google_contact_id = contact['resourceName']
            db.session.commit()

            return contact

        except Exception as e:
            raise Exception(f"Failed to create Google contact: {str(e)}")

    def update_contact(self, person):
        """Update a Google contact for a person."""
        try:
            if not person.google_contact_id:
                return self.create_contact(person)

            contact_body = {
                'etag': self.get_contact(person.google_contact_id)['etag'],
                'names': [
                    {
                        'givenName': person.first_name,
                        'familyName': person.last_name
                    }
                ],
                'emailAddresses': [
                    {
                        'value': person.email,
                        'type': 'work'
                    }
                ] if person.email else [],
                'phoneNumbers': [
                    {
                        'value': person.phone,
                        'type': 'work'
                    }
                ] if person.phone else [],
                'addresses': [
                    {
                        'streetAddress': person.address,
                        'city': person.city,
                        'region': person.state,
                        'postalCode': person.zip_code,
                        'country': 'US',
                        'type': 'work'
                    }
                ] if person.address else []
            }

            contact = self.service.people().updateContact(
                resourceName=person.google_contact_id,
                updatePersonFields='names,emailAddresses,phoneNumbers,addresses',
                body=contact_body
            ).execute()

            return contact

        except Exception as e:
            raise Exception(f"Failed to update Google contact: {str(e)}")

    def delete_contact(self, google_contact_id):
        """Delete a Google contact."""
        try:
            self.service.people().deleteContact(
                resourceName=google_contact_id
            ).execute()
            return True
        except Exception as e:
            raise Exception(f"Failed to delete Google contact: {str(e)}")

    def get_contact(self, resource_name):
        """Get a specific Google contact."""
        try:
            return self.service.people().get(
                resourceName=resource_name,
                personFields='names,emailAddresses,phoneNumbers,addresses'
            ).execute()
        except Exception as e:
            raise Exception(f"Failed to get Google contact: {str(e)}")

    def sync_contacts(self):
        """Sync Google contacts with local database."""
        try:
            # Get all Google contacts
            results = self.service.people().connections().list(
                resourceName='people/me',
                pageSize=1000,
                personFields='names,emailAddresses,phoneNumbers,addresses'
            ).execute()

            connections = results.get('connections', [])

            for contact in connections:
                # Check if contact already exists in database
                google_contact_id = contact['resourceName']
                person = Person.query.filter_by(
                    google_contact_id=google_contact_id
                ).first()

                if not person and 'names' in contact:
                    # Create new person from contact
                    name = contact['names'][0]
                    email = contact.get('emailAddresses', [{}])[0].get('value', '')
                    phone = contact.get('phoneNumbers', [{}])[0].get('value', '')
                    address = contact.get('addresses', [{}])[0]

                    person = Person(
                        first_name=name.get('givenName', ''),
                        last_name=name.get('familyName', ''),
                        email=email,
                        phone=phone,
                        address=address.get('streetAddress', ''),
                        city=address.get('city', ''),
                        state=address.get('region', ''),
                        zip_code=address.get('postalCode', ''),
                        google_contact_id=google_contact_id
                    )
                    db.session.add(person)

            db.session.commit()
            return len(connections)

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to sync Google contacts: {str(e)}") 