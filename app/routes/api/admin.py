from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import User, Office
from app.utils.decorators import admin_required

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/api')

@admin_api_bp.route('/offices/<int:office_id>/users', methods=['GET'])
@login_required
@admin_required
def get_office_users(office_id):
    """Return all users in a specific office."""
    # Check if current user has permission to view this office's data
    if not current_user.is_super_admin() and current_user.office_id != office_id:
        return jsonify({'error': 'Not authorized to access this office'}), 403

    try:
        # Get all users from the specified office
        users = User.query.filter_by(office_id=office_id, is_active=True).all()
        
        # Convert users to dictionaries
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role
            })
        
        return jsonify(users_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 