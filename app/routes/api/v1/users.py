from flask import Blueprint, jsonify, request
from app.models.user import User
from app.extensions import db
from app.auth.firebase import auth_required, admin_required
from sqlalchemy.exc import SQLAlchemyError

users_bp = Blueprint('users_api', __name__)

@users_bp.route('/', methods=['GET'])
@admin_required
def get_users():
    """Get all users (admin only)."""
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
@auth_required
def get_user(user_id):
    """Get a specific user by ID."""
    try:
        user = User.query.get_or_404(user_id)
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/me', methods=['GET'])
@auth_required
def get_current_user():
    """Get the current authenticated user."""
    try:
        # Implementation will depend on how you store the current user
        # This is a placeholder
        return jsonify({'message': 'Current user details'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/', methods=['POST'])
@admin_required
def create_user():
    """Create a new user (admin only)."""
    try:
        data = request.get_json()
        user = User(
            email=data['email'],
            firebase_uid=data['firebase_uid'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role=data.get('role', 'standard_user'),
            is_active=data.get('is_active', True)
        )
        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@users_bp.route('/<int:user_id>', methods=['PUT'])
@auth_required
def update_user(user_id):
    """Update an existing user."""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Only admins can update role and active status
        if 'role' in data or 'is_active' in data:
            if not request.user.is_admin:  # You'll need to implement this check
                return jsonify({'error': 'Unauthorized to modify role or status'}), 403
        
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        db.session.commit()
        return jsonify(user.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)."""
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@users_bp.route('/<int:user_id>/preferences', methods=['PUT'])
@auth_required
def update_preferences(user_id):
    """Update user preferences."""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not hasattr(user, 'preferences'):
            user.preferences = {}
        
        user.preferences.update(data)
        db.session.commit()
        return jsonify(user.preferences), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@users_bp.route('/<int:user_id>/signature', methods=['PUT'])
@auth_required
def update_signature(user_id):
    """Update user email signature."""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        user.email_signature = data.get('signature')
        db.session.commit()
        return jsonify({'message': 'Signature updated successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400 