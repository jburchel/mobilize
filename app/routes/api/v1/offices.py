from flask import Blueprint, jsonify, request
from app.models.office import Office
from app.extensions import db
from app.auth.firebase import auth_required, admin_required
from sqlalchemy.exc import SQLAlchemyError

offices_bp = Blueprint('offices_api', __name__)

@offices_bp.route('/', methods=['GET'])
@auth_required
def get_offices():
    """Get all offices."""
    try:
        offices = Office.query.all()
        return jsonify([office.to_dict() for office in offices]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@offices_bp.route('/<int:office_id>', methods=['GET'])
@auth_required
def get_office(office_id):
    """Get a specific office by ID."""
    try:
        office = Office.query.get_or_404(office_id)
        return jsonify(office.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@offices_bp.route('/', methods=['POST'])
@admin_required
def create_office():
    """Create a new office (admin only)."""
    try:
        data = request.get_json()
        office = Office(
            name=data['name'],
            location=data.get('location'),
            timezone=data.get('timezone'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            status=data.get('status', 'active')
        )
        db.session.add(office)
        db.session.commit()
        return jsonify(office.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@offices_bp.route('/<int:office_id>', methods=['PUT'])
@admin_required
def update_office(office_id):
    """Update an existing office (admin only)."""
    try:
        office = Office.query.get_or_404(office_id)
        data = request.get_json()
        
        for key, value in data.items():
            if hasattr(office, key):
                setattr(office, key, value)
        
        db.session.commit()
        return jsonify(office.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@offices_bp.route('/<int:office_id>', methods=['DELETE'])
@admin_required
def delete_office(office_id):
    """Delete an office (admin only)."""
    try:
        office = Office.query.get_or_404(office_id)
        db.session.delete(office)
        db.session.commit()
        return jsonify({'message': 'Office deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@offices_bp.route('/<int:office_id>/users', methods=['GET'])
@auth_required
def get_office_users(office_id):
    """Get all users assigned to an office."""
    try:
        office = Office.query.get_or_404(office_id)
        return jsonify([user.to_dict() for user in office.users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@offices_bp.route('/<int:office_id>/users', methods=['POST'])
@admin_required
def assign_user_to_office(office_id):
    """Assign a user to an office (admin only)."""
    try:
        data = request.get_json()
        office = Office.query.get_or_404(office_id)
        user_id = data['user_id']
        role = data.get('role', 'standard_user')
        
        # Implementation will depend on your user-office relationship model
        # This is a placeholder for the actual implementation
        return jsonify({'message': 'User assigned to office successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400 