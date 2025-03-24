from flask import Blueprint, jsonify, request
from app.models.communication import Communication
from app.extensions import db
from app.auth.firebase import auth_required, admin_required
from sqlalchemy.exc import SQLAlchemyError

communications_bp = Blueprint('communications_api', __name__)

@communications_bp.route('/', methods=['GET'])
@auth_required
def get_communications():
    """Get all communications with optional filtering."""
    try:
        contact_id = request.args.get('contact_id')
        type = request.args.get('type')
        
        query = Communication.query
        
        if contact_id:
            query = query.filter(Communication.recipient_contact_id == contact_id)
        if type:
            query = query.filter(Communication.type == type)
            
        communications = query.order_by(Communication.date_sent.desc()).all()
        return jsonify([comm.to_dict() for comm in communications]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@communications_bp.route('/<int:communication_id>', methods=['GET'])
@auth_required
def get_communication(communication_id):
    """Get a specific communication by ID."""
    try:
        communication = Communication.query.get_or_404(communication_id)
        return jsonify(communication.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@communications_bp.route('/', methods=['POST'])
@auth_required
def create_communication():
    """Create a new communication record."""
    try:
        data = request.get_json()
        communication = Communication(
            type=data['type'],
            subject=data.get('subject'),
            content=data['content'],
            sender_id=data['sender_id'],
            recipient_contact_id=data['recipient_contact_id'],
            status=data.get('status', 'sent'),
            gmail_thread_id=data.get('gmail_thread_id'),
            gmail_message_id=data.get('gmail_message_id'),
            template_used=data.get('template_used')
        )
        db.session.add(communication)
        db.session.commit()
        return jsonify(communication.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@communications_bp.route('/<int:communication_id>', methods=['PUT'])
@auth_required
def update_communication(communication_id):
    """Update an existing communication."""
    try:
        communication = Communication.query.get_or_404(communication_id)
        data = request.get_json()
        
        for key, value in data.items():
            if hasattr(communication, key):
                setattr(communication, key, value)
        
        db.session.commit()
        return jsonify(communication.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@communications_bp.route('/<int:communication_id>', methods=['DELETE'])
@admin_required
def delete_communication(communication_id):
    """Delete a communication (admin only)."""
    try:
        communication = Communication.query.get_or_404(communication_id)
        db.session.delete(communication)
        db.session.commit()
        return jsonify({'message': 'Communication deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@communications_bp.route('/sync', methods=['POST'])
@auth_required
def sync_communications():
    """Sync communications with Gmail."""
    try:
        # This will be implemented when we integrate with Gmail API
        return jsonify({'message': 'Communication sync initiated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500 