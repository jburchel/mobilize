"""
Test version of communications routes for testing purposes.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models.models_legacy import Communication, Person, Church
from datetime import datetime

communications_test_bp = Blueprint('communications_test', __name__, url_prefix='/communications_test')

@communications_test_bp.route('/')
@login_required
def index():
    """Display a list of communications for testing."""
    try:
        current_app.logger.info(f"User {current_user.email} accessed communications test index")
        communications = Communication.query.order_by(Communication.date_sent.desc()).limit(50).all()
        return render_template('communications_test/index.html', communications=communications, page_title="Test Communications")
    except Exception as e:
        current_app.logger.error(f"Error in communications test index: {str(e)}")
        flash('An error occurred while loading communications. Please try again later.', 'error')
        return render_template('error.html', error_message="An error occurred", page_title="Error")

@communications_test_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new communication for testing."""
    if request.method == 'POST':
        try:
            date_sent = datetime.strptime(request.form['date_sent'], '%Y-%m-%d')
            method = request.form['method']
            content = request.form.get('content', '')
            person_id = request.form.get('person_id')
            church_id = request.form.get('church_id')
            direction = request.form.get('direction', 'outbound')
            office_id = int(current_user.office_id) if current_user.office_id else None

            communication = Communication(
                date_sent=date_sent,
                method=method,
                content=content,
                person_id=person_id if person_id else None,
                church_id=church_id if church_id else None,
                user_id=current_user.id,
                direction=direction,
                office_id=office_id
            )
            db.session.add(communication)
            db.session.commit()
            flash('Communication added successfully!', 'success')
            return redirect(url_for('communications_test.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding communication: {str(e)}")
            flash(f"Error adding communication: {str(e)}", 'error')
            return render_template('communications_test/add.html', page_title="Add Test Communication")
    else:
        people = Person.query.all()
        churches = Church.query.all()
        return render_template('communications_test/add.html', people=people, churches=churches, page_title="Add Test Communication")
