from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.models.contact import Contact
from app.models.person import Person
from app.models.google_token import GoogleToken
from app.models.sync_history import SyncHistory
from app.services.google.people import GooglePeopleService
from app.services.contact_sync import ContactSyncService
from app.services.google_api import GoogleAPIService
from app.extensions import db
import logging
import os
import json
import re
from datetime import datetime
import time

google_sync_bp = Blueprint('google_sync', __name__)
logger = logging.getLogger(__name__)

@google_sync_bp.route('/')
@login_required
def index():
    """Google Sync dashboard showing sync status and options."""
    # Get sync history for the current user
    sync_history = SyncHistory.query.filter_by(user_id=current_user.id).order_by(SyncHistory.created_at.desc()).limit(10).all()
    
    # Check if user has valid Google tokens
    google_token = GoogleToken.query.filter_by(user_id=current_user.id).first()
    has_valid_token = google_token is not None
    
    return render_template('google_sync/index.html', 
                          sync_history=sync_history,
                          has_valid_token=has_valid_token)

@google_sync_bp.route('/contacts/import')
@login_required
def import_contacts():
    """Contact import wizard."""
    # Check if user has valid Google tokens
    google_token = GoogleToken.query.filter_by(user_id=current_user.id).first()
    if not google_token:
        flash('You need to connect your Google account first.', 'warning')
        return redirect(url_for('auth.google_auth'))
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    page_token = request.args.get('page_token', None)
    
    # Get the token info dictionary for the API service
    token_info = {
        'token': google_token.access_token,
        'refresh_token': google_token.refresh_token,
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'scopes': json.loads(google_token.scopes) if google_token.scopes else [],
        'expiry': google_token.expires_at.isoformat() if google_token.expires_at else None
    }
    
    try:
        # Fetch Google contacts with pagination
        contacts, next_page_token = GoogleAPIService.fetch_contacts(token_info, page_token=page_token, limit=per_page)
        
        # Format the contacts for display
        formatted_contacts = []
        
        # Get list of already imported Google contact IDs
        imported_contact_ids = [c.google_contact_id for c in Contact.query.filter(
            Contact.user_id == current_user.id,
            Contact.google_contact_id.isnot(None)
        ).all()]
        
        # Process each contact
        for contact in contacts:
            resource_name = contact.get('resourceName', '')
            contact_id = resource_name.split('/')[-1] if resource_name else ''
            
            # Extract names
            names = contact.get('names', [])
            first_name = names[0].get('givenName', '') if names else ''
            last_name = names[0].get('familyName', '') if names else ''
            display_name = names[0].get('displayName', '') if names else ''
            
            # If no first/last name but display name exists, try to parse it
            if (not first_name or not last_name) and display_name:
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
                        if not first_name:
                            first_name = first_spouse
                        if not last_name:
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
                        elif not first_name and not last_name:
                            # Standard approach: Try to split by the last space (common Western name pattern)
                            parts = display_name.strip().split()
                            if len(parts) >= 2:
                                first_name = ' '.join(parts[:-1])
                                last_name = parts[-1]
                            else:
                                # Single word name
                                first_name = display_name
                                last_name = ''
            
            # Name to display in the UI
            name_to_display = display_name if display_name else f"{first_name} {last_name}".strip()
            if not name_to_display:
                name_to_display = '[No Name]'
            
            # Extract emails
            emails = []
            for email_obj in contact.get('emailAddresses', []):
                emails.append(email_obj.get('value', ''))
            
            # Extract phones
            phones = []
            for phone_obj in contact.get('phoneNumbers', []):
                phones.append(phone_obj.get('value', ''))
            
            formatted_contacts.append({
                'id': contact_id,
                'resource_name': resource_name,
                'name': name_to_display,
                'display_name': display_name,
                'first_name': first_name,
                'last_name': last_name,
                'emails': emails,
                'phones': phones,
                'already_imported': contact_id in imported_contact_ids
            })
        
        # Get total count (approximate)
        try:
            total_count = request.args.get('total_count', 0, type=int)
            if page == 1:
                # Only make this call on the first page to avoid extra API calls
                all_contacts, _ = GoogleAPIService.fetch_contacts(token_info, limit=1)
                total_count = int(all_contacts[0].get('totalItems', len(formatted_contacts))) if all_contacts else len(formatted_contacts)
        except Exception as e:
            logger.warning(f"Error getting total contact count: {str(e)}")
            total_count = 0
        
        return render_template('google_sync/import_contacts.html', 
                              google_contacts=formatted_contacts,
                              current_page=page,
                              next_page_token=next_page_token,
                              has_next=bool(next_page_token),
                              has_prev=page > 1,
                              prev_page=page-1 if page > 1 else None,
                              next_page=page+1 if next_page_token else None,
                              per_page=per_page,
                              total_count=total_count)
    except Exception as e:
        logger.error(f"Error fetching Google contacts: {str(e)}")
        flash(f"Error fetching Google contacts: {str(e)}", 'error')
        return redirect(url_for('google_sync.index'))

@google_sync_bp.route('/contacts/map', methods=['POST'])
@login_required
def map_contacts():
    """Contact mapping interface."""
    selected_contacts = request.form.getlist('selected_contacts')
    if not selected_contacts:
        flash('No contacts selected.', 'warning')
        return redirect(url_for('google_sync.import_contacts'))
    
    # Get Google token
    google_token = GoogleToken.query.filter_by(user_id=current_user.id).first()
    if not google_token:
        flash('Google token not found.', 'error')
        return redirect(url_for('google_sync.index'))
    
    # Get the token info dictionary for the API service
    token_info = {
        'token': google_token.access_token,
        'refresh_token': google_token.refresh_token,
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'scopes': json.loads(google_token.scopes) if google_token.scopes else [],
        'expiry': google_token.expires_at.isoformat() if google_token.expires_at else None
    }
    
    try:
        # Fetch selected contacts (may need to make multiple API calls)
        selected_contact_details = []
        
        # Process in batches to avoid hitting API limits
        batch_size = 25
        for i in range(0, len(selected_contacts), batch_size):
            batch = selected_contacts[i:i+batch_size]
            
            # For each batch, we might need to fetch multiple pages of contacts to find all selected ones
            page_token = None
            found_contacts_count = 0
            
            while found_contacts_count < len(batch):
                # Fetch a page of contacts
                contacts, next_page_token = GoogleAPIService.fetch_contacts(token_info, page_token=page_token, limit=100)
                
                # Filter and process the selected contacts from this page
                for contact in contacts:
                    resource_name = contact.get('resourceName', '')
                    contact_id = resource_name.split('/')[-1] if resource_name else ''
                    
                    if contact_id in batch:
                        # Format the contact for the mapping template
                        formatted_contact = GoogleAPIService.format_google_contact(contact)
                        selected_contact_details.append(formatted_contact)
                        found_contacts_count += 1
                
                if not next_page_token or found_contacts_count >= len(batch):
                    break
                    
                page_token = next_page_token
        
        # Define field mapping options for the template
        field_mappings = [
            {'google_field': 'first_name', 'label': 'First Name', 'required': True},
            {'google_field': 'last_name', 'label': 'Last Name', 'required': True},
            {'google_field': 'email', 'label': 'Email', 'required': False},
            {'google_field': 'phone', 'label': 'Phone', 'required': False},
            {'google_field': 'street', 'label': 'Street Address', 'required': False},
            {'google_field': 'city', 'label': 'City', 'required': False},
            {'google_field': 'state', 'label': 'State/Province', 'required': False},
            {'google_field': 'zip_code', 'label': 'Zip/Postal Code', 'required': False},
            {'google_field': 'country', 'label': 'Country', 'required': False},
            {'google_field': 'title', 'label': 'Title', 'required': False},
            {'google_field': 'company', 'label': 'Company', 'required': False}
        ]
        
        return render_template('google_sync/map_contacts.html', 
                              contact_details=selected_contact_details,
                              field_mappings=field_mappings)
    except Exception as e:
        logger.error(f"Error fetching Google contact details: {str(e)}")
        flash(f"Error fetching Google contact details: {str(e)}", 'error')
        return redirect(url_for('google_sync.import_contacts'))

@google_sync_bp.route('/contacts/import/execute', methods=['POST'])
@login_required
def execute_import():
    """Execute the contact import with the mapped fields."""
    # Get the form data
    selected_contacts = request.form.getlist('contact_ids')
    
    # Process field mapping
    field_mapping = {}
    for field_name in request.form:
        if field_name.startswith('map_') and not field_name.endswith('_enabled'):
            google_field = field_name.replace('map_', '')
            app_field = request.form.get(field_name)
            if app_field:  # Only add to mapping if a target field is selected
                field_mapping[google_field] = app_field
    
    if not selected_contacts:
        flash('No contacts selected for import.', 'warning')
        return redirect(url_for('google_sync.import_contacts'))
    
    # Get Google token
    google_token = GoogleToken.query.filter_by(user_id=current_user.id).first()
    if not google_token:
        flash('Google token not found.', 'error')
        return redirect(url_for('google_sync.index'))
    
    # Get the token info dictionary for the API service
    token_info = {
        'token': google_token.access_token,
        'refresh_token': google_token.refresh_token,
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'scopes': json.loads(google_token.scopes) if google_token.scopes else [],
        'expiry': google_token.expires_at.isoformat() if google_token.expires_at else None
    }
    
    try:
        # Import the contacts using the ContactSyncService
        success, import_stats, error_message = ContactSyncService.import_contacts(
            current_user.id, 
            token_info, 
            selected_contacts, 
            field_mapping
        )
        
        if success:
            flash(f"Successfully imported {import_stats['created']} contacts and updated {import_stats['updated']} contacts.", 'success')
        else:
            # Format the error message for display
            if 'NOT NULL constraint failed: contacts.office_id' in str(error_message):
                flash("Error importing contacts: Your account is not associated with an office. Please contact your administrator.", 'error')
            else:
                flash(f"Error importing contacts: {error_message}", 'error')
            
            # Log more detailed error information
            logger.error(f"Contact import error: {error_message}")
            
        return redirect(url_for('google_sync.index'))
    except Exception as e:
        db.session.rollback()  # Ensure the session is rolled back properly
        
        # Handle specific errors
        error_msg = str(e)
        if 'office_id' in error_msg and 'NOT NULL' in error_msg:
            flash("Error importing contacts: Your account needs to be associated with an office. Please contact your administrator.", 'error')
        elif 'IntegrityError' in error_msg:
            flash("A database error occurred during import. Some contacts may have duplicate information or missing required fields.", 'error')
        else:
            flash(f"Error importing contacts: {error_msg}", 'error')
        
        logger.error(f"Error importing contacts: {error_msg}")
        return redirect(url_for('google_sync.import_contacts'))

@google_sync_bp.route('/history')
@login_required
def sync_history():
    """View sync history."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    history = SyncHistory.query.filter_by(user_id=current_user.id).order_by(
        SyncHistory.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return render_template('google_sync/history.html', history=history)

@google_sync_bp.route('/conflicts')
@login_required
def conflicts():
    """Conflict resolution interface."""
    # Query for contacts with conflicts
    conflicted_contacts = Contact.query.filter_by(
        has_conflict=True,
        user_id=current_user.id
    ).all()
    
    return render_template('google_sync/conflicts.html', 
                          conflicted_contacts=conflicted_contacts)

@google_sync_bp.route('/conflicts/resolve', methods=['POST'])
@login_required
def resolve_conflicts():
    """Resolve conflicts for contacts."""
    if not request.json:
        return jsonify({"status": "error", "message": "Invalid data format"}), 400
    
    resolution_data = request.json
    
    # Use the class method
    result = ContactSyncService.resolve_conflicts(current_user.id, resolution_data)
    
    if result.get("status") == "success":
        return jsonify(result)
    
    return jsonify(result), 500

@google_sync_bp.route('/manual-sync', methods=['POST'])
@login_required
def manual_sync():
    """Trigger a manual sync for contacts, calendar, or emails."""
    sync_type = request.form.get('sync_type')
    
    if sync_type not in ['contacts', 'calendar', 'emails']:
        flash('Invalid sync type.', 'error')
        return redirect(url_for('google_sync.index'))
    
    # Get Google token
    google_token = GoogleToken.query.filter_by(user_id=current_user.id).first()
    if not google_token:
        flash('You need to connect your Google account first.', 'warning')
        return redirect(url_for('auth.google_auth'))
    
    # Get the token info dictionary for the API service
    token_info = {
        'token': google_token.access_token,
        'refresh_token': google_token.refresh_token,
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'scopes': json.loads(google_token.scopes) if google_token.scopes else [],
        'expiry': google_token.expires_at.isoformat() if google_token.expires_at else None
    }
    
    try:
        if sync_type == 'contacts':
            # Use the ContactSyncService
            success, result, error_message = ContactSyncService.sync_contacts(current_user.id, token_info)
            
            if success:
                # Create sync history record
                sync_record = SyncHistory(
                    user_id=current_user.id,
                    sync_type='contacts_sync',
                    status='completed',
                    items_processed=result.get('items_processed', 0),
                    items_created=result.get('items_created', 0),
                    items_updated=result.get('items_updated', 0),
                    items_skipped=result.get('items_skipped', 0),
                    items_failed=result.get('items_failed', 0),
                    created_at=datetime.now(),
                    completed_at=datetime.now()
                )
                db.session.add(sync_record)
                db.session.commit()
                
                flash(f"Successfully synced contacts. Created: {result.get('items_created', 0)}, Updated: {result.get('items_updated', 0)}, Failed: {result.get('items_failed', 0)}", 'success')
            else:
                flash(f"Error syncing contacts: {error_message}", 'error')
                
        elif sync_type == 'calendar':
            try:
                # Initialize CalendarService
                from app.services.calendar_service import CalendarService
                calendar_service = CalendarService(current_user.id)
                
                # Sync calendar events
                num_synced = calendar_service.sync_events()
                
                # Create sync history record
                sync_record = SyncHistory(
                    user_id=current_user.id,
                    sync_type='calendar_sync',
                    status='completed',
                    items_processed=num_synced,
                    items_created=num_synced,  # Simplified, assuming all are created
                    items_updated=0,
                    items_skipped=0,
                    items_failed=0,
                    created_at=datetime.now(),
                    completed_at=datetime.now()
                )
                db.session.add(sync_record)
                db.session.commit()
                
                flash(f"Successfully synced {num_synced} calendar events.", 'success')
            except Exception as e:
                logger.error(f"Error syncing calendar events: {str(e)}")
                flash(f"Error syncing calendar events: {str(e)}", 'error')
                
        elif sync_type == 'emails':
            try:
                # Initialize GmailService
                from app.services.gmail_service import GmailService
                gmail_service = GmailService(current_user.id)
                
                # Default to 7 days for sync
                days_back = 7
                
                # Maximum retry attempts
                max_retries = 3
                retry_count = 0
                sync_success = False
                last_error = None
                
                # Try to sync with retries
                while retry_count < max_retries and not sync_success:
                    try:
                        # Sync emails
                        num_synced = gmail_service.sync_emails(days_back=days_back)
                        
                        # Create sync history record
                        sync_record = SyncHistory(
                            user_id=current_user.id,
                            sync_type='email_sync',
                            status='completed',
                            items_processed=num_synced,
                            items_created=num_synced,
                            items_updated=0,
                            items_skipped=0,
                            items_failed=0,
                            created_at=datetime.now(),
                            completed_at=datetime.now()
                        )
                        db.session.add(sync_record)
                        db.session.commit()
                        
                        sync_success = True
                        flash(f"Successfully synced {num_synced} emails from the last {days_back} days.", 'success')
                    except Exception as retry_error:
                        retry_count += 1
                        last_error = str(retry_error)
                        logger.warning(f"Email sync attempt {retry_count} failed: {last_error}")
                        
                        # If database lock error, wait before retrying
                        if "database is locked" in last_error:
                            time.sleep(2)  # Wait 2 seconds before retrying
                        
                        # Rollback session to clean state
                        db.session.rollback()
                        
                        # If we've exhausted all retries, raise the last error
                        if retry_count >= max_retries:
                            raise Exception(f"Failed after {max_retries} attempts. Last error: {last_error}")
                
            except Exception as e:
                logger.error(f"Error syncing emails: {str(e)}")
                flash(f"Error syncing emails: {str(e)}", 'error')
        
        return redirect(url_for('google_sync.index'))
    except Exception as e:
        logger.error(f"Error during manual {sync_type} sync: {str(e)}")
        flash(f"Error during manual {sync_type} sync: {str(e)}", 'error')
        return redirect(url_for('google_sync.index'))

@google_sync_bp.route('/status')
@login_required
def sync_status():
    """Return the current sync status"""
    from app.models import SyncHistory
    latest_sync = SyncHistory.query.filter_by(user_id=current_user.id).order_by(SyncHistory.created_at.desc()).first()
    
    status_data = {
        'status': 'idle',
        'type': None,
        'last_sync': None,
    }
    
    if latest_sync:
        status_data['last_sync'] = latest_sync.created_at.isoformat()
        status_data['type'] = latest_sync.sync_type
        status_data['status'] = latest_sync.status
    
    return jsonify(status_data) 