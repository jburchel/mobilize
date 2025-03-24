from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models.communication import Communication
from app.models.person import Person
from app.models.church import Church
from app.extensions import db
from datetime import datetime, UTC
import json

communications_bp = Blueprint('communications', __name__, template_folder='../templates/communications')

@communications_bp.route('/')
@communications_bp.route('/index')
@login_required
def index():
    """Display communications hub."""
    # Get filter parameters
    person_id = request.args.get('person_id')
    church_id = request.args.get('church_id')
    comm_type = request.args.get('type')
    direction = request.args.get('direction')
    
    # Build query
    query = Communication.query
    
    # Apply filters
    if person_id:
        query = query.filter(Communication.person_id == person_id)
    if church_id:
        query = query.filter(Communication.church_id == church_id)
    if comm_type:
        query = query.filter(Communication.type == comm_type)
    if direction:
        query = query.filter(Communication.direction == direction)
    
    # Filter by office if not super admin
    if current_user.role != 'super_admin':
        query = query.filter(Communication.office_id == current_user.office_id)
    
    # Fetch communications from database
    try:
        communications = query.order_by(Communication.date_sent.desc()).all()
    except Exception as e:
        current_app.logger.error(f"Error fetching communications: {str(e)}")
        communications = []
        flash('Error loading communications. Please try again later.', 'error')
    
    return render_template('communications/index.html', 
                          communications=communications, 
                          page_title="Communications Hub")

@communications_bp.route('/compose', methods=['GET', 'POST'])
@login_required
def compose():
    """Compose a new communication."""
    if request.method == 'POST':
        try:
            # Extract form data
            recipient_type = request.form.get('recipient_type')
            person_id = request.form.get('person_id') if recipient_type == 'person' else None
            church_id = request.form.get('church_id') if recipient_type == 'church' else None
            comm_type = request.form.get('type', 'email')
            subject = request.form.get('subject')
            message = request.form.get('message')
            
            # Create new communication record
            communication = Communication(
                type=comm_type,
                message=message,
                subject=subject,
                person_id=person_id,
                church_id=church_id,
                user_id=current_user.id,
                owner_id=current_user.id,
                office_id=current_user.office_id,
                direction='outbound',
                date_sent=datetime.now(UTC),
                email_status='sent' if comm_type == 'email' else None
            )
            
            db.session.add(communication)
            db.session.commit()
            
            flash('Message sent successfully!', 'success')
            return redirect(url_for('communications.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error sending communication: {str(e)}")
            flash(f'Error sending message: {str(e)}', 'error')
    
    # For GET request, display the compose form
    reply_to_id = request.args.get('reply_to')
    reply_to = None
    
    if reply_to_id:
        reply_to = Communication.query.get(reply_to_id)
    
    # Get people and churches for recipient selection
    people = Person.query.all()
    churches = Church.query.all()
    
    return render_template('communications/compose.html', 
                          people=people,
                          churches=churches,
                          reply_to=reply_to,
                          page_title="Compose Message")

@communications_bp.route('/view/<int:id>')
@login_required
def view(id):
    """View details of a specific communication."""
    communication = Communication.query.get_or_404(id)
    
    # Check if user has access to this communication
    if current_user.role != 'super_admin' and communication.office_id != current_user.office_id:
        flash('You do not have permission to view this communication.', 'error')
        return redirect(url_for('communications.index'))
    
    return render_template('communications/view.html', 
                          communication=communication,
                          page_title="View Message")

@communications_bp.route('/add', methods=['POST'])
@login_required
def add():
    """Add a new communication log, especially from the person view page."""
    try:
        # Extract form data
        person_id = request.form.get('person_id')
        comm_type = request.form.get('type')
        notes = request.form.get('notes')
        
        # Validate required fields
        if not all([person_id, comm_type, notes]):
            flash('All fields are required.', 'error')
            return redirect(request.referrer or url_for('communications.index'))
        
        # Create new communication record
        communication = Communication(
            type=comm_type,
            message=notes,
            subject=f"{comm_type} communication",
            person_id=person_id,
            user_id=current_user.id,
            owner_id=current_user.id,
            office_id=current_user.office_id,
            direction='outbound',
            date_sent=datetime.now(UTC)
        )
        
        db.session.add(communication)
        db.session.commit()
        
        flash('Communication logged successfully!', 'success')
        
        # Redirect back to the person view page
        return redirect(url_for('people.view', id=person_id))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error logging communication: {str(e)}")
        flash(f'Error logging communication: {str(e)}', 'error')
        return redirect(request.referrer or url_for('communications.index'))

@communications_bp.route('/sync-status')
@login_required
def sync_status():
    """Check the status of the Gmail sync."""
    # Get the latest sync timestamp from database
    last_sync = db.session.query(db.func.max(Communication.last_synced_at)).filter(
        Communication.gmail_message_id.isnot(None)
    ).scalar()
    
    # Count emails imported from Gmail
    gmail_count = Communication.query.filter(
        Communication.gmail_message_id.isnot(None)
    ).count()
    
    status = {
        'status': 'synced' if last_sync else 'not_synced',
        'last_sync': last_sync.isoformat() if last_sync else None,
        'count': gmail_count
    }
    return jsonify(status)

@communications_bp.route('/templates', methods=['GET', 'POST'])
@login_required
def templates():
    """Manage email templates."""
    if request.method == 'POST':
        # Handle template save/update
        try:
            template_data = request.get_json()
            
            # Here you would save the template to database
            # This is a placeholder for future implementation
            
            return jsonify({'success': True, 'message': 'Template saved successfully'})
        except Exception as e:
            current_app.logger.error(f"Error saving template: {str(e)}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
    # Mock templates - these should come from database
    templates = [
        {
            'id': 1,
            'name': 'Welcome Email',
            'subject': 'Welcome to our community!',
            'body': '<p>Dear [Name],</p><p>Welcome to our community! We are thrilled to have you join us.</p><p>Best regards,<br>Your Team</p>'
        },
        {
            'id': 2,
            'name': 'Follow-up Meeting',
            'subject': 'Follow-up from our meeting',
            'body': '<p>Dear [Name],</p><p>Thank you for meeting with us today. Here is a summary of what we discussed...</p><p>Best regards,<br>Your Team</p>'
        },
        {
            'id': 3,
            'name': 'Thank You',
            'subject': 'Thank you for your support',
            'body': '<p>Dear [Name],</p><p>We wanted to express our sincere gratitude for your continued support.</p><p>Best regards,<br>Your Team</p>'
        }
    ]
    
    return render_template('communications/templates.html', 
                          templates=templates,
                          page_title="Email Templates") 