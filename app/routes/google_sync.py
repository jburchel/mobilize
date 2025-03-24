from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.models.contact import Contact
from app.models.person import Person
from app.models.google_token import GoogleToken
from app.models.sync_history import SyncHistory
from app.services.google.people import GooglePeopleService
from app.services.contact_sync import ContactSyncService
from app.extensions import db
import logging

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
    
    # Initialize Google People service
    try:
        people_service = GooglePeopleService(current_user.id)
        # Get contacts from Google (limited to 10 for the wizard UI)
        google_contacts = people_service.list_contacts(max_results=10)
        
        return render_template('google_sync/import_contacts.html', 
                              google_contacts=google_contacts)
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
    
    # Get contacts details from Google
    try:
        people_service = GooglePeopleService(current_user.id)
        contact_details = people_service.get_contacts_by_ids(selected_contacts)
        
        return render_template('google_sync/map_contacts.html', 
                              contact_details=contact_details)
    except Exception as e:
        logger.error(f"Error fetching Google contact details: {str(e)}")
        flash(f"Error fetching Google contact details: {str(e)}", 'error')
        return redirect(url_for('google_sync.import_contacts'))

@google_sync_bp.route('/contacts/import/execute', methods=['POST'])
@login_required
def execute_import():
    """Execute the contact import with the mapped fields."""
    contact_mappings = request.form.to_dict(flat=False)
    
    try:
        # Initialize the contact sync service
        sync_service = ContactSyncService(current_user.id)
        
        # Process the mappings and import contacts
        result = sync_service.import_contacts(contact_mappings)
        
        # Create sync history record
        sync_record = SyncHistory(
            user_id=current_user.id,
            sync_type='contacts_import',
            status='completed',
            items_processed=result.get('processed', 0),
            items_created=result.get('created', 0),
            items_updated=result.get('updated', 0),
            items_skipped=result.get('skipped', 0)
        )
        db.session.add(sync_record)
        db.session.commit()
        
        flash(f"Successfully imported {result.get('created', 0)} contacts and updated {result.get('updated', 0)} contacts.", 'success')
        return redirect(url_for('google_sync.index'))
    except Exception as e:
        logger.error(f"Error importing contacts: {str(e)}")
        flash(f"Error importing contacts: {str(e)}", 'error')
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
    """Resolve conflicts for selected contacts."""
    conflict_resolutions = request.form.to_dict(flat=False)
    
    try:
        # Initialize the contact sync service
        sync_service = ContactSyncService(current_user.id)
        
        # Process conflict resolutions
        result = sync_service.resolve_conflicts(conflict_resolutions)
        
        flash(f"Successfully resolved {result.get('resolved', 0)} conflicts.", 'success')
        return redirect(url_for('google_sync.conflicts'))
    except Exception as e:
        logger.error(f"Error resolving conflicts: {str(e)}")
        flash(f"Error resolving conflicts: {str(e)}", 'error')
        return redirect(url_for('google_sync.conflicts'))

@google_sync_bp.route('/manual-sync', methods=['POST'])
@login_required
def manual_sync():
    """Trigger a manual sync for contacts, calendar, or emails."""
    sync_type = request.form.get('sync_type')
    
    if sync_type not in ['contacts', 'calendar', 'emails']:
        flash('Invalid sync type.', 'error')
        return redirect(url_for('google_sync.index'))
    
    try:
        if sync_type == 'contacts':
            # Initialize the contact sync service
            sync_service = ContactSyncService(current_user.id)
            result = sync_service.sync_contacts()
            
            # Create sync history record
            sync_record = SyncHistory(
                user_id=current_user.id,
                sync_type='contacts_sync',
                status='completed',
                items_processed=result.get('processed', 0),
                items_created=result.get('created', 0),
                items_updated=result.get('updated', 0),
                items_skipped=result.get('skipped', 0)
            )
            db.session.add(sync_record)
            db.session.commit()
            
            flash(f"Successfully synced contacts. Created: {result.get('created', 0)}, Updated: {result.get('updated', 0)}", 'success')
        elif sync_type == 'calendar':
            flash("Calendar sync not implemented yet.", 'info')
        elif sync_type == 'emails':
            flash("Email sync not implemented yet.", 'info')
            
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