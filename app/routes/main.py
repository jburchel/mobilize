from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user

# Create Blueprint
main_bp = Blueprint('main', __name__)

# Basic routes
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/home')
@login_required
def home():
    return redirect(url_for('dashboard.dashboard'))
