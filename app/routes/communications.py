from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models.communication import Communication
from app.models.person import Person
from app.models.church import Church
from app.extensions import db
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
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
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
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
    
    # Apply date range filter if provided
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            query = query.filter(Communication.date_sent >= start_date_obj)
        except ValueError:
            current_app.logger.error(f"Invalid start_date format: {start_date}")
    
    if end_date:
        try:
            # Set end_date to end of day
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            query = query.filter(Communication.date_sent <= end_date_obj)
        except ValueError:
            current_app.logger.error(f"Invalid end_date format: {end_date}")
    
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
                date_sent=datetime.now(timezone.utc),
                email_status='draft' if comm_type == 'email' else None
            )
            
            # Handle email type - send via Gmail API
            if comm_type == 'email':
                try:
                    # Get the recipient's email address
                    recipient_email = None
                    if person_id:
                        person = Person.query.get(person_id)
                        recipient_email = person.email
                    elif church_id:
                        church = Church.query.get(church_id)
                        # Find the primary contact's email or use the first contact found
                        if church.primary_contact:
                            recipient_email = church.primary_contact.email
                    
                    if not recipient_email:
                        flash('Recipient email address not found', 'error')
                        raise ValueError("Recipient email address not found")
                    
                    # Send the email using Gmail API
                    from app.services.gmail_service import GmailService
                    gmail_service = GmailService(current_user.id)
                    
                    # Log that we're attempting to send an email
                    current_app.logger.info(f"Attempting to send email to {recipient_email} with subject: {subject}")
                    
                    # Actually send the email
                    sent_message = gmail_service.send_email(
                        to=recipient_email,
                        subject=subject,
                        body=message,
                        html=message  # Use the same content for HTML
                    )
                    
                    # Update the communication record with Gmail IDs
                    communication.gmail_message_id = sent_message.get('id')
                    communication.gmail_thread_id = sent_message.get('threadId')
                    communication.email_status = 'sent'
                    
                    current_app.logger.info(f"Email sent successfully. Gmail ID: {communication.gmail_message_id}")
                    flash('Email sent successfully via Gmail!', 'success')
                    
                except Exception as e:
                    current_app.logger.error(f"Error sending email via Gmail API: {str(e)}")
                    communication.email_status = 'failed'
                    flash(f'Error sending email: {str(e)}', 'error')
            
            # Handle video conference type - create Google Meet link
            if comm_type == 'video_conference':
                try:
                    from app.services.calendar_service import CalendarService
                    calendar_service = CalendarService(current_user.id)
                    
                    # Generate a meeting title
                    meeting_title = subject or "Video Conference"
                    if person_id:
                        person = Person.query.get(person_id)
                        meeting_title += f" with {person.first_name} {person.last_name}"
                    elif church_id:
                        church = Church.query.get(church_id)
                        meeting_title += f" with {church.name}"
                    
                    # Create a calendar event with Google Meet
                    event = calendar_service.create_meeting(
                        summary=meeting_title,
                        description=message,
                        start_time=datetime.now(timezone.utc) + timedelta(hours=1),  # Default to 1 hour from now
                        duration_minutes=60  # Default 1 hour meeting
                    )
                    
                    # Store the Google Meet link and event ID
                    if event and 'hangoutLink' in event:
                        communication.google_meet_link = event['hangoutLink']
                        communication.google_calendar_event_id = event['id']
                        communication.message += f"\n\nGoogle Meet Link: {event['hangoutLink']}"
                        
                        # Add the conferencing link to the message
                        flash('Google Meet link created successfully!', 'success')
                    else:
                        flash('Failed to create Google Meet link', 'warning')
                except Exception as e:
                    current_app.logger.error(f"Error creating Google Meet link: {str(e)}")
                    flash(f'Error creating Google Meet link: {str(e)}', 'warning')
            
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
        if not person_id:
            flash('Person ID is required.', 'error')
            return redirect(request.referrer or url_for('communications.index'))
            
        if not comm_type:
            flash('Communication type is required.', 'error')
            return redirect(request.referrer or url_for('communications.index'))
            
        if not notes:
            flash('Notes are required.', 'error')
            return redirect(request.referrer or url_for('communications.index'))
        
        # Verify person exists
        person = Person.query.get(person_id)
        if not person:
            flash('Person not found.', 'error')
            return redirect(request.referrer or url_for('communications.index'))
        
        # Create new communication record
        communication = Communication(
            type=comm_type,
            message=notes,
            subject=f"{comm_type.capitalize()} communication",
            person_id=person_id,
            user_id=current_user.id,
            owner_id=current_user.id,
            office_id=current_user.office_id if hasattr(current_user, 'office_id') else person.office_id,
            direction='outbound',
            date_sent=datetime.now(timezone.utc)
        )
        
        db.session.add(communication)
        db.session.commit()
        
        flash('Communication logged successfully!', 'success')
        
        # Redirect back to the person view page
        return redirect(url_for('people.show', id=person_id))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error logging communication: {str(e)}")
        flash(f'Error logging communication: {str(e)}', 'error')
        return redirect(url_for('people.index') if not request.referrer else request.referrer)

@communications_bp.route('/templates', methods=['GET', 'POST'])
@login_required
def templates():
    """Manage email templates."""
    # Ensure email_templates table exists
    try:
        create_table_sql = text("""
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                created_by INTEGER,
                office_id INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        with db.engine.connect() as conn:
            conn.execute(create_table_sql)
            conn.commit()
        current_app.logger.info("Checked for email_templates table existence")
    except Exception as e:
        current_app.logger.error(f"Error ensuring email_templates table: {str(e)}")
    
    if request.method == 'POST':
        # Handle template save/update
        try:
            data = request.form
            template_id = data.get('template_id')
            
            if template_id and template_id.strip():  # Update existing template
                # Check if template exists
                with db.engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT * FROM email_templates WHERE id = :id"),
                        {"id": template_id}
                    )
                    template_row = result.fetchone()
                    # Convert to dict for easier access
                    template = dict(zip(result.keys(), template_row)) if template_row else None
                
                if not template:
                    flash('Template not found.', 'error')
                    return redirect(url_for('communications.templates'))
                
                # Check permission (only owner or admin can edit)
                if template['created_by'] != current_user.id and current_user.role not in ['admin', 'super_admin']:
                    flash('You do not have permission to edit this template.', 'error')
                    return redirect(url_for('communications.templates'))
                
                # Update template
                update_sql = text("""
                    UPDATE email_templates 
                    SET name = :name, subject = :subject, content = :content, 
                        category = :category, updated_at = :updated_at
                    WHERE id = :id
                """)
                
                with db.engine.connect() as conn:
                    conn.execute(update_sql,
                        {
                            "name": data.get('name'),
                            "subject": data.get('subject'),
                            "content": data.get('content'),
                            "category": data.get('category'),
                            "updated_at": datetime.now(timezone.utc),
                            "id": template_id
                        }
                    )
                    conn.commit()
            else:  # Create new template
                # Insert new template
                insert_sql = text("""
                    INSERT INTO email_templates 
                    (name, subject, content, category, created_by, office_id, created_at, updated_at)
                    VALUES (:name, :subject, :content, :category, :created_by, :office_id, :created_at, :updated_at)
                """)
                
                with db.engine.connect() as conn:
                    conn.execute(insert_sql,
                        {
                            "name": data.get('name'),
                            "subject": data.get('subject'),
                            "content": data.get('content'),
                            "category": data.get('category'),
                            "created_by": current_user.id,
                            "office_id": current_user.office_id,
                            "created_at": datetime.now(timezone.utc),
                            "updated_at": datetime.now(timezone.utc)
                        }
                    )
                    conn.commit()
                
            flash('Template saved successfully!', 'success')
            return redirect(url_for('communications.templates'))
            
        except Exception as e:
            current_app.logger.error(f"Error saving template: {str(e)}")
            flash(f'Error saving template: {str(e)}', 'error')
            return redirect(url_for('communications.templates'))
    
    # For GET requests, fetch templates from the database
    try:
        # Get filter parameters
        category = request.args.get('category')
        search = request.args.get('search')
        
        # Build query
        query = "SELECT * FROM email_templates WHERE 1=1"
        params = {}
        
        # Apply filters
        if category:
            query += " AND category = :category"
            params["category"] = category
        
        if search:
            query += " AND (name LIKE :search OR subject LIKE :search OR content LIKE :search)"
            search_term = f"%{search}%"
            params["search"] = search_term
        
        # Filter by office unless super admin
        if current_user.role != 'super_admin':
            query += " AND office_id = :office_id"
            params["office_id"] = current_user.office_id
        
        # Order by most recently updated first
        query += " ORDER BY updated_at DESC"
        
        # Execute query
        with db.engine.connect() as conn:
            result = conn.execute(text(query), params)
            templates_raw = result.fetchall()
        
        # Convert to list of dicts
        templates = []
        for row in templates_raw:
            # Convert each row to a dict using column names as keys
            keys = result.keys()
            template = dict(zip(keys, row))
            
            # Format dates
            if 'created_at' in template and template['created_at']:
                try:
                    # Convert string to datetime if needed
                    if isinstance(template['created_at'], str):
                        template['created_at'] = datetime.fromisoformat(template['created_at'].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            
            # Store the full content in a data attribute for client-side access
            if 'content' in template and template['content']:
                template['content_preview'] = template['content'][:100] + '...' if len(template['content']) > 100 else template['content']
            
            templates.append(template)
        
        current_app.logger.info(f"Retrieved {len(templates)} email templates")
        
    except Exception as e:
        current_app.logger.error(f"Error fetching templates: {str(e)}")
        templates = []
        flash('Error loading templates. Please try again later.', 'error')
    
    return render_template('communications/templates.html', 
                          templates=templates,
                          page_title="Email Templates")

@communications_bp.route('/templates/delete/<int:id>', methods=['POST'])
@login_required
def delete_template(id):
    """Delete an email template."""
    try:
        # Check if template exists
        select_sql = text("SELECT * FROM email_templates WHERE id = :id")
        
        with db.engine.connect() as conn:
            result = conn.execute(select_sql, {"id": id})
            template_row = result.fetchone()
            # Convert to dict for easier access
            template = dict(zip(result.keys(), template_row)) if template_row else None
        
        if not template:
            flash('Template not found.', 'error')
            return redirect(url_for('communications.templates'))
        
        # Check permission (only owner or admin can delete)
        if template['created_by'] != current_user.id and current_user.role not in ['admin', 'super_admin']:
            flash('You do not have permission to delete this template.', 'error')
            return redirect(url_for('communications.templates'))
        
        # Delete template
        delete_sql = text("DELETE FROM email_templates WHERE id = :id")
        
        with db.engine.connect() as conn:
            conn.execute(delete_sql, {"id": id})
            conn.commit()
        
        flash('Template deleted successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f"Error deleting template: {str(e)}")
        flash(f'Error deleting template: {str(e)}', 'error')
    
    return redirect(url_for('communications.templates'))

@communications_bp.route('/templates/<int:id>', methods=['GET'])
@login_required
def get_template(id):
    """Get a specific email template by ID for editing or viewing."""
    try:
        # Query for the template
        select_sql = text("SELECT * FROM email_templates WHERE id = :id")
        
        with db.engine.connect() as conn:
            result = conn.execute(select_sql, {"id": id})
            template_row = result.fetchone()
            
            if not template_row:
                return jsonify({'success': False, 'message': 'Template not found'}), 404
            
            # Convert to dict
            keys = result.keys()
            template = dict(zip(keys, template_row))
            
            # Check permission
            if template['office_id'] != current_user.office_id and current_user.role not in ['super_admin', 'admin']:
                return jsonify({'success': False, 'message': 'You do not have permission to view this template'}), 403
            
            # Format dates
            if 'created_at' in template and template['created_at']:
                try:
                    if isinstance(template['created_at'], str):
                        template['created_at'] = datetime.fromisoformat(template['created_at'].replace('Z', '+00:00')).isoformat()
                except (ValueError, AttributeError):
                    pass
            
            if 'updated_at' in template and template['updated_at']:
                try:
                    if isinstance(template['updated_at'], str):
                        template['updated_at'] = datetime.fromisoformat(template['updated_at'].replace('Z', '+00:00')).isoformat()
                except (ValueError, AttributeError):
                    pass
            
            return jsonify({'success': True, 'template': template})
    
    except Exception as e:
        current_app.logger.error(f"Error fetching template: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching template: {str(e)}'}), 500 