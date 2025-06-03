"""
Robust version of communications routes with additional features for testing purposes.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models.models_legacy import Communication, Person, Church
from datetime import datetime

communications_robust_bp = Blueprint('communications_robust', __name__, url_prefix='/communications_robust')

@communications_robust_bp.route('/')
@login_required
def index():
    """Display a list of communications with robust filtering options."""
    try:
        current_app.logger.info(f"User {current_user.email} accessed communications robust index")
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        office_id = int(current_user.office_id) if current_user.office_id else None
        
        query = Communication.query
        if office_id and not current_user.is_super_admin():
            query = query.filter_by(office_id=office_id)
        
        communications = query.order_by(Communication.date_sent.desc()).paginate(page=page, per_page=per_page)
        return render_template('communications_robust/index.html', communications=communications, page_title="Robust Communications")
    except Exception as e:
        current_app.logger.error(f"Error in communications robust index: {str(e)}")
        flash('An error occurred while loading communications. Please try again later.', 'error')
        return render_template('error.html', error_message="An error occurred", page_title="Error")

@communications_robust_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new communication with robust options."""
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
            return redirect(url_for('communications_robust.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding communication: {str(e)}")
            flash(f"Error adding communication: {str(e)}", 'error')
            return render_template('communications_robust/add.html', page_title="Add Robust Communication")
    else:
        people = Person.query.all()
        churches = Church.query.all()
        return render_template('communications_robust/add.html', people=people, churches=churches, page_title="Add Robust Communication")
