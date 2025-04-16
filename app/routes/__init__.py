from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, current_app, request
from app.config import config
from flask_login import login_required, current_user
from functools import wraps
from app.models.user import User
from app.models.office import Office

# Import blueprints
from app.routes.dashboard import dashboard_bp
from app.routes.people import people_bp
from app.routes.churches import churches_bp
from app.routes.tasks import tasks_bp
from app.routes.communications import communications_bp
from .google_sync import google_sync_bp
from app.routes.admin import admin_bp
from app.routes.settings import settings_bp
from app.routes.pipeline import pipeline_bp
from app.routes.reports import reports_bp
from app.routes.emails import emails_bp
from app.onboarding.routes import onboarding_bp

test_bp = Blueprint('test', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['super_admin', 'office_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

@test_bp.route('/test')
def test():
    return jsonify({'message': 'Test route working'})

# List of blueprints to register with the app
blueprints = [
    test_bp,
    admin_bp,
    dashboard_bp,
    people_bp,
    churches_bp,
    tasks_bp,
    communications_bp,
    google_sync_bp,
    settings_bp,
    pipeline_bp,
    reports_bp,
    emails_bp,
    onboarding_bp
]

# This function is no longer used since blueprints are registered directly in app/__init__.py
def register_routes(app):
    pass

__all__ = ['blueprints'] 