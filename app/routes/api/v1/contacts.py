from flask import Blueprint, jsonify, request
from app.models.contact import ContactModel
from app.models.person import Person
from app.models.church import Church
from app.extensions import db
from app.auth.firebase import auth_required, admin_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from app.tasks.sync import sync_user_contacts
from app.models.user import User
from app.services.contact_sync import ContactSyncService
from flask_login import current_user, login_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import current_app

contacts_bp = Blueprint('contacts_api', __name__)

@contacts_bp.route('/', methods=['GET'])
@auth_required
def get_contacts():
    """Get all contacts with optional filtering."""
    try:
        contact_type = request.args.get('type')
        office_id = request.args.get('office_id')
        
        query = ContactModel.query
        
        if contact_type:
            query = query.filter(ContactModel.type == contact_type)
        if office_id:
            query = query.filter(ContactModel.office_id == office_id)
            
        contacts = query.all()
        return jsonify([contact.to_dict() for contact in contacts]), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@contacts_bp.route('/<int:contact_id>', methods=['GET'])
@auth_required
def get_contact(contact_id):
    """Get a specific contact by ID."""
    try:
        contact = ContactModel.query.get_or_404(contact_id)
        return jsonify(contact.to_dict()), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@contacts_bp.route('/', methods=['POST'])
@auth_required
def create_contact():
    """Create a new contact."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
            
        # Validate email format
        email = data.get('email')
        if email and '@' not in email:
            return jsonify({
                'error': 'Invalid email format'
            }), 400
            
        contact = ContactModel(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            notes=data.get('notes'),
            office_id=data.get('office_id'),
            type=data.get('type', 'contact_model')
        )
        db.session.add(contact)
        db.session.commit()
        return jsonify(contact.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@contacts_bp.route('/person', methods=['POST'])
@auth_required
def create_person():
    """Create a new person contact."""
    try:
        data = request.get_json()
        person = Person(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            notes=data.get('notes'),
            office_id=data.get('office_id')
        )
        db.session.add(person)
        db.session.commit()
        return jsonify(person.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@contacts_bp.route('/church', methods=['POST'])
@auth_required
def create_church():
    """Create a new church contact."""
    try:
        data = request.get_json()
        church = Church(
            name=data.get('name'),
            location=data.get('location'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            notes=data.get('notes'),
            office_id=data.get('office_id'),
            senior_pastor_name=data.get('senior_pastor_name'),
            denomination=data.get('denomination')
        )
        db.session.add(church)
        db.session.commit()
        return jsonify(church.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@contacts_bp.route('/<int:contact_id>', methods=['PUT'])
@auth_required
def update_contact(contact_id):
    """Update a specific contact."""
    try:
        contact = ContactModel.query.get_or_404(contact_id)
        data = request.get_json()
        
        # Update contact fields if provided in the request
        if 'first_name' in data:
            contact.first_name = data['first_name']
        if 'last_name' in data:
            contact.last_name = data['last_name']
        if 'email' in data:
            contact.email = data['email']
        if 'phone' in data:
            contact.phone = data['phone']
        if 'address' in data:
            contact.address = data['address']
        if 'city' in data:
            contact.city = data['city']
        if 'state' in data:
            contact.state = data['state']
        if 'zip_code' in data:
            contact.zip_code = data['zip_code']
        if 'notes' in data:
            contact.notes = data['notes']
        if 'office_id' in data:
            contact.office_id = data['office_id']
        if 'type' in data:
            contact.type = data['type']
            
        db.session.commit()
        return jsonify(contact.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@contacts_bp.route('/<int:contact_id>', methods=['DELETE'])
@auth_required
def delete_contact(contact_id):
    """Delete a specific contact."""
    try:
        contact = ContactModel.query.get_or_404(contact_id)
        db.session.delete(contact)
        db.session.commit()
        return '', 204
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@contacts_bp.route('/search', methods=['GET'])
@auth_required
def search_contacts():
    """Search contacts based on query string."""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Search query is required'}), 400

        contacts = ContactModel.query.filter(
            or_(
                ContactModel.first_name.ilike(f'%{query}%'),
                ContactModel.last_name.ilike(f'%{query}%'),
                ContactModel.email.ilike(f'%{query}%')
            )
        ).all()

        return jsonify([contact.to_dict() for contact in contacts]), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@contacts_bp.route('/sync', methods=['POST'])
@auth_required
def sync_contacts():
    """Synchronize contacts from Google."""
    try:
        # Get the current user from Firebase authentication
        user_id = request.firebase_uid
        user = User.query.filter_by(firebase_uid=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if not user.google_token:
            return jsonify({'error': 'Google authentication required'}), 401
            
        # Queue the sync task
        sync_user_contacts.delay(user.id)
        
        return jsonify({'message': 'Contact synchronization started'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@contacts_bp.route('/google/preview', methods=['GET'])
@auth_required
def preview_google_contacts():
    """Preview contacts from Google before import."""
    try:
        sync_service = ContactSyncService(current_user)
        result = sync_service.list_google_contacts()
        
        return jsonify({
            'success': True,
            'contacts': result['contacts'],
            'total': result['total']
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contacts_bp.route('/google/sync', methods=['POST'])
@auth_required
def sync_selected_contacts():
    """Sync selected contacts from Google."""
    try:
        data = request.get_json()
        contact_ids = data.get('contact_ids', [])
        sync_direction = data.get('direction', 'from_google')  # or 'to_google'
        
        sync_service = ContactSyncService(current_user)
        
        if sync_direction == 'from_google':
            result = sync_service.sync_from_google(selected_ids=contact_ids)
        else:
            result = sync_service.sync_to_google(person_ids=contact_ids)
            
        return jsonify({
            'success': True,
            'stats': result['stats']
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contacts_bp.route('/merge', methods=['POST'])
@auth_required
def merge_contacts():
    """Merge two contacts together."""
    try:
        data = request.get_json()
        source_id = data.get('source_id')
        target_id = data.get('target_id')
        field_selections = data.get('field_selections', {})
        
        if not source_id or not target_id:
            return jsonify({
                'success': False,
                'error': 'Both source and target contact IDs are required'
            }), 400
            
        sync_service = ContactSyncService(current_user)
        result = sync_service.merge_contacts(source_id, target_id, field_selections)
        
        return jsonify({
            'success': True,
            'merged_contact': result
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contacts_bp.route('/merge/preview', methods=['POST'])
@auth_required
def preview_merge():
    """Preview the result of merging two contacts."""
    try:
        data = request.get_json()
        source_id = data.get('source_id')
        target_id = data.get('target_id')
        
        if not source_id or not target_id:
            return jsonify({
                'success': False,
                'error': 'Both source and target contact IDs are required'
            }), 400
            
        sync_service = ContactSyncService(current_user)
        result = sync_service.preview_merge(source_id, target_id)
        
        return jsonify({
            'success': True,
            'merge_preview': result
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contacts_bp.route('/conflicts/count', methods=['GET'])
@login_required
def get_conflicts_count():
    """Return count of contact conflicts for the current user"""
    # For testing, just return a placeholder value
    return jsonify({
        'count': 0  # No conflicts for now
    }) 