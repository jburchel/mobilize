from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.user import User
from app.models.person import Person
from app.models.contact import Contact
from app.models.sync_history import SyncHistory
from app.services.google.people import GooglePeopleService
from app.extensions import db
import logging
import re
from flask import current_app
from app.services.google_api import GoogleAPIService

logger = logging.getLogger(__name__)

class ContactSyncService:
    """Service for synchronizing contacts between CRM and Google Contacts."""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.google_service = GooglePeopleService(user_id)
        
    def _create_sync_history(self, action: str, status: str, details: Dict[str, Any]) -> SyncHistory:
        """Create a sync history record."""
        history = SyncHistory(
            user_id=self.user_id,
            sync_type='contacts',
            action=action,
            status=status,
            details=details
        )
        db.session.add(history)
        db.session.commit()
        return history
        
    def _map_google_to_person(self, google_contact: Dict[str, Any]) -> Dict[str, Any]:
        """Map Google contact data to Person model fields."""
        names = google_contact.get('names', [{}])[0]
        emails = google_contact.get('emailAddresses', [{}])[0]
        phones = google_contact.get('phoneNumbers', [{}])[0]
        addresses = google_contact.get('addresses', [{}])[0]
        
        return {
            'first_name': names.get('givenName', ''),
            'last_name': names.get('familyName', ''),
            'email': emails.get('value', ''),
            'phone': phones.get('value', ''),
            'address': addresses.get('streetAddress', ''),
            'city': addresses.get('city', ''),
            'state': addresses.get('region', ''),
            'zip_code': addresses.get('postalCode', ''),
            'country': addresses.get('country', ''),
            'google_contact_id': google_contact.get('resourceName', '')
        }
        
    def _find_duplicate_person(self, contact_data: Dict[str, Any]) -> Optional[Person]:
        """Find potential duplicate person based on email or name."""
        if contact_data.get('email'):
            person = Person.query.filter_by(email=contact_data['email']).first()
            if person:
                return person
                
        return Person.query.filter_by(
            first_name=contact_data['first_name'],
            last_name=contact_data['last_name']
        ).first()
        
    def list_google_contacts(self) -> Dict[str, Any]:
        """List Google contacts for preview before sync."""
        try:
            result = self.google_service.list_contacts(page_size=100)
            contacts = result.get('connections', [])
            
            mapped_contacts = []
            for contact in contacts:
                contact_data = self._map_google_to_person(contact)
                # Check for potential duplicates
                duplicate = self._find_duplicate_person(contact_data)
                
                mapped_contacts.append({
                    'google_data': contact_data,
                    'resource_name': contact.get('resourceName'),
                    'has_duplicate': bool(duplicate),
                    'duplicate_info': duplicate.to_dict() if duplicate else None
                })
            
            return {
                'contacts': mapped_contacts,
                'total': len(mapped_contacts)
            }
            
        except Exception as e:
            logger.error(f"Failed to list Google contacts for preview: {str(e)}")
            raise

    def sync_from_google(self, selected_ids: List[str] = None, sync_token: str = None) -> Dict[str, Any]:
        """Sync contacts from Google to CRM."""
        try:
            result = self.google_service.list_contacts(sync_token=sync_token)
            contacts = result.get('connections', [])
            
            # Filter contacts if selection provided
            if selected_ids:
                contacts = [c for c in contacts if c.get('resourceName') in selected_ids]
            
            stats = {
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'errors': 0
            }
            
            for contact in contacts:
                try:
                    contact_data = self._map_google_to_person(contact)
                    
                    # Check for existing person by Google ID
                    person = Person.query.filter_by(
                        google_contact_id=contact_data['google_contact_id']
                    ).first()
                    
                    if not person:
                        # Check for potential duplicates
                        duplicate = self._find_duplicate_person(contact_data)
                        
                        if duplicate:
                            # Update existing person with Google ID
                            for key, value in contact_data.items():
                                setattr(duplicate, key, value)
                            stats['updated'] += 1
                        else:
                            # Create new person
                            user = User.query.get(self.user_id)
                            person = Person(
                                user_id=self.user_id,
                                office_id=user.office_id if user else 1,  # Default to office 1 if not found
                                **contact_data
                            )
                            db.session.add(person)
                            stats['created'] += 1
                    else:
                        # Update existing person
                        for key, value in contact_data.items():
                            setattr(person, key, value)
                        stats['updated'] += 1
                        
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing contact {contact.get('resourceName')}: {str(e)}")
                    stats['errors'] += 1
                    db.session.rollback()
            
            # Create sync history
            self._create_sync_history(
                action='import',
                status='completed',
                details={
                    'stats': stats,
                    'next_sync_token': result.get('nextSyncToken')
                }
            )
            
            return {
                'success': True,
                'stats': stats,
                'next_sync_token': result.get('nextSyncToken')
            }
            
        except Exception as e:
            logger.error(f"Failed to sync contacts from Google: {str(e)}")
            self._create_sync_history(
                action='import',
                status='failed',
                details={'error': str(e)}
            )
            raise
            
    def sync_to_google(self, person_ids: List[int] = None) -> Dict[str, Any]:
        """Sync contacts from CRM to Google."""
        try:
            query = Person.query.filter_by(user_id=self.user_id)
            if person_ids:
                query = query.filter(Person.id.in_(person_ids))
                
            people = query.all()
            stats = {
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'errors': 0
            }
            
            for person in people:
                try:
                    if person.google_contact_id:
                        # Update existing Google contact
                        self.google_service.update_contact(person)
                        stats['updated'] += 1
                    else:
                        # Create new Google contact
                        self.google_service.create_contact(person)
                        stats['created'] += 1
                        
                except Exception as e:
                    logger.error(f"Error syncing person {person.id} to Google: {str(e)}")
                    stats['errors'] += 1
                    
            # Create sync history
            self._create_sync_history(
                action='export',
                status='completed',
                details={'stats': stats}
            )
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Failed to sync contacts to Google: {str(e)}")
            self._create_sync_history(
                action='export',
                status='failed',
                details={'error': str(e)}
            )
            raise

    def preview_merge(self, source_id: str, target_id: str) -> Dict[str, Any]:
        """Preview the result of merging two contacts."""
        try:
            # Get source contact (Google contact)
            source = self.google_service.get_contact(source_id)
            source_data = self._map_google_to_person(source)
            
            # Get target contact (CRM person)
            target = Person.query.get(target_id)
            if not target:
                raise ValueError("Target contact not found")
                
            # Compare fields and identify differences
            fields_comparison = {
                'first_name': {
                    'source': source_data['first_name'],
                    'target': target.first_name,
                    'different': source_data['first_name'] != target.first_name
                },
                'last_name': {
                    'source': source_data['last_name'],
                    'target': target.last_name,
                    'different': source_data['last_name'] != target.last_name
                },
                'email': {
                    'source': source_data['email'],
                    'target': target.email,
                    'different': source_data['email'] != target.email
                },
                'phone': {
                    'source': source_data['phone'],
                    'target': target.phone,
                    'different': source_data['phone'] != target.phone
                },
                'address': {
                    'source': source_data['address'],
                    'target': target.address,
                    'different': source_data['address'] != target.address
                },
                'city': {
                    'source': source_data['city'],
                    'target': target.city,
                    'different': source_data['city'] != target.city
                },
                'state': {
                    'source': source_data['state'],
                    'target': target.state,
                    'different': source_data['state'] != target.state
                },
                'zip_code': {
                    'source': source_data['zip_code'],
                    'target': target.zip_code,
                    'different': source_data['zip_code'] != target.zip_code
                }
            }
            
            return {
                'source': source_data,
                'target': target.to_dict(),
                'fields': fields_comparison
            }
            
        except Exception as e:
            logger.error(f"Failed to preview merge: {str(e)}")
            raise

    def merge_contacts(self, source_id: str, target_id: str, field_selections: Dict[str, str]) -> Dict[str, Any]:
        """Merge two contacts based on field selections."""
        try:
            # Get source contact (Google contact)
            source = self.google_service.get_contact(source_id)
            source_data = self._map_google_to_person(source)
            
            # Get target contact (CRM person)
            target = Person.query.get(target_id)
            if not target:
                raise ValueError("Target contact not found")
                
            # Update fields based on selections
            for field, selection in field_selections.items():
                if selection == 'source':
                    setattr(target, field, source_data[field])
                # If selection is 'target', keep existing value
                
            # Set the Google contact ID to establish the link
            target.google_contact_id = source_id
            
            # Create merge history
            self._create_sync_history(
                action='merge',
                status='completed',
                details={
                    'source_id': source_id,
                    'target_id': target_id,
                    'selections': field_selections
                }
            )
            
            db.session.commit()
            
            # Update the Google contact with merged data
            self.google_service.update_contact(target)
            
            return target.to_dict()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to merge contacts: {str(e)}")
            self._create_sync_history(
                action='merge',
                status='failed',
                details={
                    'source_id': source_id,
                    'target_id': target_id,
                    'error': str(e)
                }
            )
            raise

    @classmethod
    def import_contacts(cls, user_id, token_info, selected_contacts, field_mapping=None):
        """
        Import contacts from Google to the application.
        
        Args:
            user_id: User ID
            token_info: Google token information
            selected_contacts: List of Google contact IDs to import
            field_mapping: Dictionary mapping Google fields to local fields
            
        Returns:
            tuple: (success, import_stats, error_message)
        """
        if not token_info or not selected_contacts:
            return False, None, "No contacts selected for import"
        
        # Import Person model
        from app.models.person import Person
        
        # Initialize sync history record
        sync_history = SyncHistory(
            user_id=user_id,
            sync_type="contacts_import",
            status="in_progress",
            created_at=datetime.now()
        )
        db.session.add(sync_history)
        db.session.commit()
        
        try:
            # Fetch all Google contacts
            all_contacts = []
            page_token = None
            
            while True:
                contacts, page_token = GoogleAPIService.fetch_contacts(token_info, page_token)
                all_contacts.extend(contacts)
                if not page_token:
                    break
            
            # Filter to selected contacts
            filtered_contacts = [c for c in all_contacts if c.get('resourceName', '').split('/')[-1] in selected_contacts]
            
            # Process contacts
            created_count = 0
            updated_count = 0
            skipped_count = 0
            failed_count = 0
            
            for google_contact in filtered_contacts:
                formatted_contact = GoogleAPIService.format_google_contact(google_contact)
                google_id = formatted_contact.get('google_id')
                
                # Check if person already exists with this Google ID
                existing_person = Person.query.filter_by(
                    user_id=user_id,
                    google_contact_id=google_id
                ).first()
                
                if existing_person:
                    # Update existing person based on field mapping
                    try:
                        updated = cls._update_contact_with_mapping(existing_person, formatted_contact, field_mapping)
                        if updated:
                            updated_count += 1
                        else:
                            skipped_count += 1
                    except Exception as e:
                        current_app.logger.error(f"Error updating person {google_id}: {str(e)}")
                        failed_count += 1
                else:
                    # Create new person based on field mapping
                    try:
                        created = cls._create_contact_with_mapping(user_id, formatted_contact, field_mapping)
                        if created:
                            created_count += 1
                        else:
                            skipped_count += 1
                    except Exception as e:
                        current_app.logger.error(f"Error creating person {google_id}: {str(e)}")
                        failed_count += 1
            
            # Update sync history
            sync_history.completed_at = datetime.now()
            sync_history.status = "completed"
            sync_history.items_processed = len(filtered_contacts)
            sync_history.items_created = created_count
            sync_history.items_updated = updated_count
            sync_history.items_skipped = skipped_count
            sync_history.items_failed = failed_count
            
            db.session.commit()
            
            import_stats = {
                "processed": len(filtered_contacts),
                "created": created_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "failed": failed_count
            }
            
            return True, import_stats, None
            
        except Exception as e:
            current_app.logger.error(f"Error importing contacts: {str(e)}")
            
            # Update sync history with error
            sync_history.completed_at = datetime.now()
            sync_history.status = "failed"
            sync_history.error_message = str(e)
            db.session.commit()
            
            return False, None, str(e)
    
    @classmethod
    def _create_contact_with_mapping(cls, user_id, google_contact, field_mapping=None):
        """
        Create a new contact based on Google contact data and field mapping.
        
        Args:
            user_id: User ID
            google_contact: Formatted Google contact data
            field_mapping: Dictionary mapping Google fields to local fields
            
        Returns:
            bool: True if created, False if skipped
        """
        # Get the user's office_id
        from app.models.user import User
        from app.models.person import Person
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"User {user_id} not found when creating contact")
            return False
            
        # Use default mapping if none provided
        mapping = field_mapping or {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email',
            'phone': 'phone',
            'street': 'address',
            'city': 'city',
            'state': 'state',
            'zip_code': 'zip_code',
            'country': 'country'
        }
        
        # Create a Person object instead of a generic Contact
        # This ensures the contact will appear in the People list
        person = Person(user_id=user_id, office_id=user.office_id)
        person.google_contact_id = google_contact.get('google_id')
        person.source = 'google_import'
        
        # Apply mapping
        contact_updated = False
        for google_field, local_field in mapping.items():
            if google_field in google_contact and google_contact.get(google_field):
                setattr(person, local_field, google_contact.get(google_field))
                contact_updated = True
        
        if contact_updated:
            try:
                db.session.add(person)
                db.session.commit()
                current_app.logger.info(f"Created new person from Google: {person.google_contact_id}")
                return True
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error creating person {person.google_contact_id}: {str(e)}")
                raise
        
        return False
    
    @classmethod
    def _update_contact_with_mapping(cls, contact, google_contact, field_mapping=None):
        """
        Update an existing contact based on Google contact data and field mapping.
        Works with both Contact and Person objects.
        
        Args:
            contact: Existing Contact or Person object
            google_contact: Formatted Google contact data
            field_mapping: Dictionary mapping Google fields to local fields
            
        Returns:
            bool: True if updated, False if skipped
        """
        # Use default mapping if none provided
        mapping = field_mapping or {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email',
            'phone': 'phone',
            'street': 'address',
            'city': 'city',
            'state': 'state',
            'zip_code': 'zip_code',
            'country': 'country'
        }
        
        # Apply mapping
        contact_updated = False
        for google_field, local_field in mapping.items():
            if google_field in google_contact and google_contact.get(google_field):
                # Check if the field value is different
                if getattr(contact, local_field) != google_contact.get(google_field):
                    setattr(contact, local_field, google_contact.get(google_field))
                    contact_updated = True
        
        if contact_updated:
            db.session.commit()
            current_app.logger.info(f"Updated {'person' if hasattr(contact, 'type') and contact.type == 'person' else 'contact'} with Google ID: {contact.google_contact_id}")
            return True
        
        return False
    
    @classmethod
    def sync_contacts(cls, user_id, token_info):
        """
        Synchronize contacts between Google and the application.
        
        Args:
            user_id: User ID
            token_info: Google token information
            
        Returns:
            tuple: (success, sync_stats, error_message)
        """
        if not token_info:
            return False, None, "Invalid token information"
        
        # Initialize sync history record
        sync_history = SyncHistory(
            user_id=user_id,
            sync_type="contacts_sync",
            status="in_progress",
            created_at=datetime.now()
        )
        db.session.add(sync_history)
        db.session.commit()
        
        try:
            # Fetch all Google contacts
            all_google_contacts = []
            page_token = None
            
            while True:
                contacts, page_token = GoogleAPIService.fetch_contacts(token_info, page_token)
                all_google_contacts.extend(contacts)
                if not page_token:
                    break
            
            # Format Google contacts
            formatted_google_contacts = [
                GoogleAPIService.format_google_contact(contact)
                for contact in all_google_contacts
            ]
            
            # Process contacts
            created_count = 0
            updated_count = 0
            conflict_count = 0
            skipped_count = 0
            
            # Get existing contacts with Google IDs
            google_contact_ids = [contact.get('google_id') for contact in formatted_google_contacts]
            existing_contacts = Contact.query.filter_by(user_id=user_id).filter(
                Contact.google_contact_id.in_(google_contact_ids)
            ).all()
            
            # Map existing contacts by Google ID
            existing_contacts_map = {
                contact.google_contact_id: contact
                for contact in existing_contacts
            }
            
            # Process each Google contact
            for formatted_contact in formatted_google_contacts:
                google_id = formatted_contact.get('google_id')
                
                if google_id in existing_contacts_map:
                    # Contact exists - check for conflicts
                    existing_contact = existing_contacts_map[google_id]
                    
                    if cls._check_for_conflicts(existing_contact, formatted_contact):
                        # Mark as having a conflict
                        existing_contact.has_conflict = True
                        existing_contact.google_data = formatted_contact
                        db.session.commit()
                        conflict_count += 1
                    else:
                        # Update without conflicts
                        updated = cls._update_contact_with_mapping(existing_contact, formatted_contact)
                        if updated:
                            updated_count += 1
                        else:
                            skipped_count += 1
                else:
                    # Create new contact
                    created = cls._create_contact_with_mapping(user_id, formatted_contact)
                    if created:
                        created_count += 1
                    else:
                        skipped_count += 1
            
            # Update sync history
            sync_history.completed_at = datetime.now()
            sync_history.status = "completed"
            sync_history.items_processed = len(formatted_google_contacts)
            sync_history.items_created = created_count
            sync_history.items_updated = updated_count
            sync_history.items_skipped = skipped_count
            sync_history.items_failed = conflict_count  # Conflicts are counted as failed items
            
            db.session.commit()
            
            # Use the field names expected by the manual_sync route
            sync_stats = {
                "items_processed": len(formatted_google_contacts),
                "items_created": created_count,
                "items_updated": updated_count,
                "items_skipped": skipped_count,
                "items_failed": conflict_count
            }
            
            return True, sync_stats, None
            
        except Exception as e:
            current_app.logger.error(f"Error syncing contacts: {str(e)}")
            
            # Update sync history with error
            sync_history.completed_at = datetime.now()
            sync_history.status = "failed"
            sync_history.error_message = str(e)
            db.session.commit()
            
            return False, None, str(e)
    
    @classmethod
    def _check_for_conflicts(cls, local_contact, google_contact):
        """
        Check if there are conflicts between local and Google contacts.
        
        Args:
            local_contact: Local Contact object
            google_contact: Formatted Google contact data
            
        Returns:
            bool: True if conflicts exist, False otherwise
        """
        # Fields to check for conflicts
        fields_to_check = [
            ('first_name', 'first_name'),
            ('last_name', 'last_name'),
            ('email', 'email'),
            ('phone', 'phone'),
            ('address', 'street'),
            ('city', 'city'),
            ('state', 'state'),
            ('zip_code', 'zip_code'),
            ('country', 'country')
        ]
        
        # Check each field
        has_conflict = False
        for local_field, google_field in fields_to_check:
            # Handle the special case for 'street' -> 'address' mapping
            if local_field == 'street':
                local_value = getattr(local_contact, 'address', None)
            else:
                local_value = getattr(local_contact, local_field, None)
                
            google_value = google_contact.get(google_field)
            
            if local_value and google_value and local_value != google_value:
                has_conflict = True
                break
        
        return has_conflict
    
    @classmethod
    def resolve_conflicts(cls, user_id, resolution_data):
        """
        Resolve conflicts based on user selections.
        
        Args:
            user_id (int): The ID of the user.
            resolution_data (dict): Dictionary containing conflict resolution data
                                    in format {contact_id: {action: 'action_type', fields: {...}}}
        
        Returns:
            dict: Result statistics.
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {"status": "error", "message": "User not found"}
                
            # Create a sync history record
            sync_history = SyncHistory(
                user_id=user_id,
                sync_type='conflicts_resolution',
                status='in_progress',
                created_at=datetime.now()
            )
            db.session.add(sync_history)
            db.session.commit()
            
            # Counters for statistics
            resolved_count = 0
            skipped_count = 0
            error_count = 0
            
            # Process each conflict resolution
            for contact_id, resolution in resolution_data.items():
                try:
                    action = resolution.get('action')
                    contact_id = int(contact_id)
                    local_contact = Contact.query.get(contact_id)
                    
                    if not local_contact:
                        skipped_count += 1
                        continue
                        
                    google_id = local_contact.google_contact_id
                    if not google_id:
                        skipped_count += 1
                        continue
                        
                    if action == 'keep_local':
                        # Mark as resolved, no changes needed
                        local_contact.has_conflict = False
                        local_contact.google_data = None
                        resolved_count += 1
                        
                    elif action == 'keep_google':
                        # Update local contact with Google data
                        google_api = GoogleAPIService()
                        google_contact = google_api.get_contact(google_id, token_info=cls._get_user_token(user_id))
                        
                        if google_contact:
                            contact_data = google_api.format_google_contact(google_contact)
                            
                            local_contact.first_name = contact_data.get('first_name', '')
                            local_contact.last_name = contact_data.get('last_name', '')
                            local_contact.email = contact_data.get('email', '')
                            local_contact.phone = contact_data.get('phone', '')
                            local_contact.address = contact_data.get('street', '')
                            local_contact.city = contact_data.get('city', '')
                            local_contact.state = contact_data.get('state', '')
                            local_contact.zip_code = contact_data.get('zip_code', '')
                            local_contact.country = contact_data.get('country', '')
                            local_contact.has_conflict = False
                            local_contact.google_data = None
                            
                            resolved_count += 1
                        else:
                            skipped_count += 1
                            
                    elif action == 'merge':
                        # Merge fields based on selection
                        google_api = GoogleAPIService()
                        google_contact = google_api.get_contact(google_id, token_info=cls._get_user_token(user_id))
                        
                        if google_contact and 'fields' in resolution:
                            contact_data = google_api.format_google_contact(google_contact)
                            fields = resolution.get('fields', {})
                            
                            # Update fields based on user selection
                            for field, source in fields.items():
                                if source == 'google' and field in contact_data:
                                    setattr(local_contact, field, contact_data.get(field, ''))
                                    
                            local_contact.has_conflict = False
                            local_contact.google_data = None
                            resolved_count += 1
                        else:
                            skipped_count += 1
                    else:
                        # Unknown action
                        skipped_count += 1
                        
                except Exception as e:
                    print(f"Error resolving conflict for contact {contact_id}: {str(e)}")
                    error_count += 1
                    
            # Commit all changes
            db.session.commit()
            
            # Update sync history
            sync_history.status = 'completed'
            sync_history.completed_at = datetime.now()
            sync_history.items_processed = resolved_count + skipped_count + error_count
            sync_history.items_created = 0
            sync_history.items_updated = resolved_count
            sync_history.items_skipped = skipped_count
            sync_history.items_failed = error_count
            db.session.commit()
            
            return {
                "status": "success", 
                "message": f"Successfully resolved {resolved_count} conflicts",
                "items_processed": resolved_count + skipped_count + error_count,
                "items_updated": resolved_count,
                "items_skipped": skipped_count,
                "items_failed": error_count
            }
                
        except Exception as e:
            # Update sync history with error
            if 'sync_history' in locals():
                sync_history.status = 'failed'
                sync_history.completed_at = datetime.now()
                sync_history.error_message = str(e)
                db.session.commit()
                
            return {"status": "error", "message": f"Error resolving conflicts: {str(e)}"}
            
    @classmethod
    def _get_user_token(cls, user_id):
        """Get the user's Google token information"""
        from app.models.google_token import GoogleToken
        import json
        import os
        
        google_token = GoogleToken.query.filter_by(user_id=user_id).first()
        if not google_token:
            return None
            
        return {
            'token': google_token.access_token,
            'refresh_token': google_token.refresh_token,
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'scopes': json.loads(google_token.scopes) if google_token.scopes else [],
            'expiry': google_token.expires_at.isoformat() if google_token.expires_at else None
        } 