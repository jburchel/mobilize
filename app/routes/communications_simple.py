from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Communication, Person, Church, User, Office
import logging

communications_simple_bp = Blueprint('communications_simple', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@communications_simple_bp.route('/communications')
@login_required
def index():
    try:
        logger.info(f"User {current_user.id} accessed communications index")
        communications = Communication.query.order_by(Communication.date.desc()).all()
        return render_template('communications/index.html', communications=communications, title='Communications')
    except Exception as e:
        logger.error(f"Error in communications index: {str(e)}")
        flash('An error occurred while loading communications. Please try again later.', 'error')
        return render_template('error.html', error_message="An error occurred", page_title="Error")

@communications_simple_bp.route('/communications/new', methods=['GET'])
@login_required
def new():
    try:
        people = Person.query.all()
        churches = Church.query.all()
        users = User.query.all()
        offices = Office.query.all()
        return render_template('communications/new.html', people=people, churches=churches, users=users, offices=offices, title='New Communication')
    except Exception as e:
        logger.error(f"Error in new communication form: {str(e)}")
        flash('An error occurred while loading the form. Please try again later.', 'error')
        return render_template('error.html', error_message="An error occurred", page_title="Error")
