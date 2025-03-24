"""
API endpoints for Google Sync operations
"""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.models.sync_history import SyncHistory
from app.services.google_api import GoogleAPIService
from app.services.contact_sync import ContactSyncService

google_api_sync_blueprint = Blueprint('google_api_sync', __name__)

@google_api_sync_blueprint.route('/sync-status', methods=['GET'])
@jwt_required()
def api_get_sync_status():
    """
    Get the status of Google sync for the current user.
    Returns connection status and last sync information.
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check if user has Google tokens
        has_tokens = user.google_token_info is not None and len(user.google_token_info) > 0
        
        # Check if token is valid
        is_connected = False
        if has_tokens:
            is_connected = GoogleAPIService.is_token_valid(user.google_token_info)
        
        # Get last sync information
        last_sync = SyncHistory.query.filter_by(
            user_id=current_user_id
        ).order_by(SyncHistory.start_time.desc()).first()
        
        last_sync_data = None
        if last_sync:
            last_sync_data = {
                "id": last_sync.id,
                "type": last_sync.sync_type,
                "status": last_sync.status,
                "start_time": last_sync.start_time.isoformat() if last_sync.start_time else None,
                "end_time": last_sync.end_time.isoformat() if last_sync.end_time else None,
                "processed": last_sync.processed,
                "created": last_sync.created,
                "updated": last_sync.updated,
                "skipped": last_sync.skipped,
                "failed": last_sync.failed,
                "conflicts": last_sync.conflicts
            }
        
        return jsonify({
            "is_connected": is_connected,
            "last_sync": last_sync_data
        })
    except Exception as e:
        current_app.logger.error(f"Error getting sync status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@google_api_sync_blueprint.route('/conflicts/count', methods=['GET'])
@jwt_required()
def api_get_conflicts_count():
    """
    Get the count of conflicts for the current user.
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Count contacts with conflicts
        from app.models.base import Contact
        conflict_count = Contact.query.filter_by(
            user_id=current_user_id,
            has_conflict=True
        ).count()
        
        return jsonify({"count": conflict_count})
    except Exception as e:
        current_app.logger.error(f"Error getting conflicts count: {str(e)}")
        return jsonify({"error": str(e)}), 500

@google_api_sync_blueprint.route('/sync', methods=['POST'])
@jwt_required()
def api_start_sync():
    """
    Start a synchronization operation.
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check for Google token
        if not user.google_token_info:
            return jsonify({"error": "Google account not connected"}), 400
        
        # Start the sync
        success, stats, error = ContactSyncService.sync_contacts(current_user_id, user.google_token_info)
        
        if success:
            return jsonify({"success": True, "stats": stats})
        else:
            return jsonify({"success": False, "error": error}), 500
    except Exception as e:
        current_app.logger.error(f"Error starting sync: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@google_api_sync_blueprint.route('/import', methods=['POST'])
@jwt_required()
def api_import_contacts():
    """
    Import selected contacts from Google.
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check for Google token
        if not user.google_token_info:
            return jsonify({"error": "Google account not connected"}), 400
        
        # Get contacts to import from request
        data = request.get_json()
        if not data or 'contacts' not in data:
            return jsonify({"error": "No contacts specified for import"}), 400
        
        selected_contacts = data['contacts']
        field_mapping = data.get('field_mapping')
        
        # Start the import
        success, stats, error = ContactSyncService.import_contacts(
            current_user_id, 
            user.google_token_info, 
            selected_contacts,
            field_mapping
        )
        
        if success:
            return jsonify({"success": True, "stats": stats})
        else:
            return jsonify({"success": False, "error": error}), 500
    except Exception as e:
        current_app.logger.error(f"Error importing contacts: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@google_api_sync_blueprint.route('/resolve-conflicts', methods=['POST'])
@jwt_required()
def api_resolve_conflicts():
    """
    Resolve conflicts between local and Google contacts.
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get resolution data from request
        data = request.get_json()
        if not data or 'resolutions' not in data:
            return jsonify({"error": "No resolution data provided"}), 400
        
        resolution_data = data['resolutions']
        
        # Resolve conflicts
        success, stats, error = ContactSyncService.resolve_conflicts(
            current_user_id, 
            resolution_data
        )
        
        if success:
            return jsonify({"success": True, "stats": stats})
        else:
            return jsonify({"success": False, "error": error}), 500
    except Exception as e:
        current_app.logger.error(f"Error resolving conflicts: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@google_api_sync_blueprint.route('/history', methods=['GET'])
@jwt_required()
def api_get_sync_history():
    """
    Get synchronization history for the current user.
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get page and per_page parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sync_type = request.args.get('type')
        
        # Query sync history
        query = SyncHistory.query.filter_by(user_id=current_user_id)
        
        if sync_type:
            query = query.filter_by(sync_type=sync_type)
        
        # Paginate results
        history_pagination = query.order_by(SyncHistory.start_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format results
        history_items = []
        for item in history_pagination.items:
            history_items.append({
                "id": item.id,
                "type": item.sync_type,
                "status": item.status,
                "start_time": item.start_time.isoformat() if item.start_time else None,
                "end_time": item.end_time.isoformat() if item.end_time else None,
                "duration": (item.end_time - item.start_time).total_seconds() if item.end_time and item.start_time else None,
                "processed": item.processed,
                "created": item.created,
                "updated": item.updated,
                "skipped": item.skipped,
                "failed": item.failed,
                "conflicts": item.conflicts,
                "error_message": item.error_message
            })
        
        return jsonify({
            "items": history_items,
            "total": history_pagination.total,
            "pages": history_pagination.pages,
            "page": page,
            "per_page": per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error getting sync history: {str(e)}")
        return jsonify({"error": str(e)}), 500 