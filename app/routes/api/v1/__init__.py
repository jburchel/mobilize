from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from .contacts import contacts_bp
from .tasks import tasks_bp
from .communications import communications_bp
from .offices import offices_bp
from .users import users_bp
from .gmail import gmail_bp
from .calendar import calendar_bp
from .google_sync import google_api_sync_blueprint
from .dashboard import dashboard_api_bp

# Create API blueprint
api_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Register all API blueprints
api_bp.register_blueprint(contacts_bp, url_prefix='/contacts')
api_bp.register_blueprint(tasks_bp, url_prefix='/tasks')
api_bp.register_blueprint(communications_bp, url_prefix='/communications')
api_bp.register_blueprint(offices_bp, url_prefix='/offices')
api_bp.register_blueprint(users_bp, url_prefix='/users')
api_bp.register_blueprint(gmail_bp, url_prefix='/gmail')
api_bp.register_blueprint(calendar_bp, url_prefix='/calendar')
api_bp.register_blueprint(google_api_sync_blueprint, url_prefix='/google-sync')
api_bp.register_blueprint(dashboard_api_bp, url_prefix='/dashboard')

def register_api_routes(app):
    """Register API blueprint with app"""
    app.register_blueprint(api_bp) 