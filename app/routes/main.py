"""Main routes for the Mobilize-CRM application."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Redirect to dashboard or login based on user authentication status."""
    if current_user.is_authenticated:
        logger.info(f"User {current_user.email} accessed the main page, redirecting to dashboard.")
        return redirect(url_for('dashboard.dashboard'))
    else:
        logger.info("Anonymous user accessed the main page, redirecting to login.")
        return redirect(url_for('auth.login'))

@main_bp.route('/home')
@login_required
def home():
    """Display the home page for logged-in users."""
    logger.info(f"User {current_user.email} accessed the home page.")
    return render_template('home.html', title='Home')
