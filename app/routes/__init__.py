from flask import Blueprint, jsonify
from app.config import config
from flask_login import login_required, current_user
from functools import wraps

test_bp = Blueprint('test', __name__)
admin_bp = Blueprint('admin', __name__)
dashboard_bp = Blueprint('dashboard', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'super_admin':
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

@test_bp.route('/test')
def test():
    return jsonify({'message': 'Test route working'})

@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return jsonify({'message': 'Welcome to admin dashboard'})

@dashboard_bp.route('/')
@login_required
def index():
    return jsonify({'message': 'Welcome to your dashboard'})

__all__ = ['test_bp', 'admin_bp', 'dashboard_bp'] 