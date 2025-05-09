from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models.communication import Communication
from app.models.person import Person
from app.models.church import Church
from app.models.email_template import EmailTemplate
from app.models.email_signature import EmailSignature
from app.extensions import db
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import joinedload
from app.utils.decorators import office_required
from app.utils.upload import save_uploaded_file
from app.utils.query_optimization import with_pagination

communications_bp = Blueprint('communications', __name__, template_folder='../templates/communications')

# Helper function to get default signature
def get_default_signature(user_id):
    """Get the default signature for a user"""
    signature = EmailSignature.query.filter_by(
        user_id=user_id,
        is_default=True
    ).first()
    
    return signature

@communications_bp.route('/')
@communications_bp.route('/index')
@login_required
# Temporarily removed caching to fix internal server error
# @cached_query(timeout=60)  # Cache results for 1 minute in production
def index():
    """Display communications hub."""
    start_time = datetime.now()
    
    # Get filter parameters
    person_id = request.args.get('person_id')
    church_id = request.args.get('church_id')
    
    # Convert IDs to integers if they exist to avoid type mismatch
    try:
        person_id = int(person_id) if person_id else None
    except (ValueError, TypeError):
        person_id = None
        current_app.logger.error(f"Invalid person_id format: {person_id}")
    
    try:
        church_id = int(church_id) if church_id else None
    except (ValueError, TypeError):
        church_id = None
        current_app.logger.error(f"Invalid church_id format: {church_id}")
    comm_type = request.args.get('type')
    direction = request.args.get('direction')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)  # Default to 50 items per page
    
    # Build query with eager loading to prevent N+1 query problems
    query = Communication.query.options(
        joinedload(Communication.person),
        joinedload(Communication.church)
    )
    
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
    
    # Order by date sent descending
    query = query.order_by(Communication.date_sent.desc())
    
    # Apply pagination to avoid loading too many records at once
    try:
        communications, pagination = with_pagination(query, page=page, per_page=per_page)
    except Exception as e:
        current_app.logger.error(f"Error in pagination for communications: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'An error occurred while loading communications. Please try again later.'}), 500
    
    # Calculate performance metrics
    query_time = (datetime.now() - start_time).total_seconds() * 1000  # Convert to milliseconds
    
    # Get related data for dropdowns in a single query each
    people = Person.query.filter_by(office_id=current_user.office_id).order_by(Person.first_name).all() if not person_id else []
    churches = Church.query.filter_by(office_id=current_user.office_id).order_by(Church.name).all() if not church_id else []
    
    # Get distinct communication types from the database
    comm_types = db.session.query(Communication.type).distinct().all()
    comm_types = [t[0] for t in comm_types if t[0]]
    
    # Log performance if it exceeds thresholds
    if query_time > 1000:  # Log if query takes longer than 1 second
        current_app.logger.warning(f"Slow communications query: {query_time:.2f}ms for user {current_user.id}")
    
    # Render template with all necessary data
    return render_template('communications/index.html', 
                         communications=communications,
                         pagination=pagination,
                         query_time=query_time,
                         person_id=person_id,
                         church_id=church_id,
                         comm_type=comm_type,
                         direction=direction,
                         start_date=start_date,
                         end_date=end_date,
                         people=people,
                         churches=churches,
                         comm_types=comm_types)

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
            comm_type = request.form.get('type')
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
                    
                    # Get meeting date, time and timezone from form
                    meeting_date = request.form.get('meeting_date')
                    meeting_time = request.form.get('meeting_time')
                    meeting_timezone = request.form.get('meeting_timezone', 'America/New_York')
                    meeting_duration = int(request.form.get('meeting_duration', '60'))
                    
                    # Get recipient email for calendar invitation
                    recipient_email = None
                    if person_id:
                        person = Person.query.get(person_id)
                        recipient_email = person.email
                    elif church_id:
                        church = Church.query.get(church_id)
                        # Find the primary contact's email or use the first contact found
                        if church.primary_contact:
                            recipient_email = church.primary_contact.email
                    
                    # Construct datetime from date and time inputs
                    if meeting_date and meeting_time:
                        # Parse meeting datetime
                        try:
                            meeting_datetime_str = f"{meeting_date} {meeting_time}"
                            meeting_datetime = datetime.strptime(meeting_datetime_str, "%Y-%m-%d %H:%M")
                            
                            # Set the timezone
                            import pytz
                            tz = pytz.timezone(meeting_timezone)
                            meeting_datetime = tz.localize(meeting_datetime)
                            
                            current_app.logger.info(f"Scheduling meeting at {meeting_datetime} for {meeting_duration} minutes")
                        except ValueError as e:
                            current_app.logger.error(f"Error parsing meeting datetime: {str(e)}")
                            meeting_datetime = datetime.now(timezone.utc) + timedelta(hours=1)
                            meeting_duration = 60
                    else:
                        # Default to 1 hour from now
                        meeting_datetime = datetime.now(timezone.utc) + timedelta(hours=1)
                    
                    # Create a calendar event with Google Meet using the specified time
                    # Add recipient as an attendee if email is available
                    attendees = []
                    if recipient_email:
                        attendees.append(recipient_email)
                    
                    event = calendar_service.create_meeting(
                        summary=meeting_title,
                        description=message,
                        start_time=meeting_datetime,
                        duration_minutes=meeting_duration,
                        attendees=attendees if attendees else None
                    )
                    
                    # Store the Google Meet link and event ID
                    if event and 'hangoutLink' in event:
                        communication.google_meet_link = event['hangoutLink']
                        communication.google_calendar_event_id = event['id']
                        
                        # Format the meeting time for the message
                        formatted_time = meeting_datetime.strftime("%A, %B %d, %Y at %I:%M %p %Z")
                        
                        # Add meeting details to the message
                        message_with_details = message  # Start with the original message
                        
                        # Create nicely formatted meeting details
                        meeting_details = f"""
                        <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin: 20px 0;">
                            <h3 style="color: #0d6efd; margin-top: 0;">Video Conference Details</h3>
                            <p><strong>Date:</strong> {formatted_time}</p>
                            <p><strong>Duration:</strong> {meeting_duration} minutes</p>
                            <p><strong>Join with:</strong> <a href="{event['hangoutLink']}" style="color: #0d6efd;">{event['hangoutLink']}</a></p>
                            
                            <div style="margin-top: 20px;">
                                <a href="{event['hangoutLink']}" style="background-color: #0d6efd; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                                    Join Meeting
                                </a>
                            </div>
                        </div>
                        """
                        
                        # Check if there's a signature in the message
                        if '<div class="email-signature">' in message:
                            # Insert meeting details before the signature
                            message_with_details = message.replace(
                                '<div class="email-signature">',
                                f'{meeting_details}<div class="email-signature">'
                            )
                        else:
                            # Otherwise append to the end
                            message_with_details = message + meeting_details
                        
                        # Update the message with the meeting details
                        communication.message = message_with_details
                        
                        # Send an email invitation to the recipient
                        if recipient_email:
                            try:
                                # Create the email invitation
                                from app.services.gmail_service import GmailService
                                gmail_service = GmailService(current_user.id)
                                
                                # Create a complete HTML message for the email
                                html_message = f"""
                                <html>
                                <body>
                                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                                        <h2 style="color: #3b71ca;">{subject}</h2>
                                        <div style="margin-bottom: 20px;">
                                            {message}
                                        </div>
                                        
                                        {meeting_details}
                                        
                                        <p style="color: #6c757d; font-size: 0.9em;">
                                            This invitation was sent via Mobilize CRM. No downloads required to join the meeting.<br>
                                            You should also receive a Google Calendar invitation which will appear in your calendar.
                                        </p>
                                    </div>
                                </body>
                                </html>
                                """
                                
                                # Log that we're attempting to send an email invitation
                                current_app.logger.info(f"Sending meeting invitation to {recipient_email}")
                                
                                # Actually send the email
                                sent_message = gmail_service.send_email(
                                    to=recipient_email,
                                    subject=f"Video Meeting Invitation: {subject}",
                                    body=f"You've been invited to a video meeting: {subject}\n\nDate: {formatted_time}\nDuration: {meeting_duration} minutes\nJoin with: {event['hangoutLink']}",
                                    html=html_message
                                )
                                
                                # Create a separate communication record for the email
                                email_communication = Communication(
                                    type='email',
                                    message=html_message,
                                    subject=f"Video Meeting Invitation: {subject}",
                                    person_id=person_id,
                                    church_id=church_id,
                                    user_id=current_user.id,
                                    owner_id=current_user.id,
                                    office_id=current_user.office_id,
                                    direction='outbound',
                                    date_sent=datetime.now(timezone.utc),
                                    email_status='sent',
                                    gmail_message_id=sent_message.get('id'),
                                    gmail_thread_id=sent_message.get('threadId')
                                )
                                db.session.add(email_communication)
                                
                                flash('Video conference created and invitation email sent!', 'success')
                            except Exception as e:
                                current_app.logger.error(f"Error sending meeting invitation email: {str(e)}")
                                flash(f'Video conference created, but could not send email invitation: {str(e)}', 'warning')
                        else:
                            current_app.logger.warning("Unable to send meeting invitation: Recipient email address not found")
                            flash('Video conference created, but could not send email invitation (no email found).', 'warning')
                        
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
    
    # Get user's default signature
    default_signature = get_default_signature(current_user.id)
    
    # Pass current datetime for the meeting scheduler
    now = datetime.now()
    
    # Get pre-selected person or church if provided
    person_id = request.args.get('person_id')
    church_id = request.args.get('church_id')
    
    # Modal/partial support
    if request.args.get('modal') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('communications/compose_modal.html',
                              people=people,
                              churches=churches,
                              reply_to=reply_to,
                              default_signature=default_signature,
                              now=now,
                              timedelta=timedelta,
                              person_id=person_id,
                              church_id=church_id,
                              email=request.args.get('email'),
                              name=request.args.get('name'))
    return render_template('communications/compose.html',
                          people=people,
                          churches=churches,
                          reply_to=reply_to,
                          default_signature=default_signature,
                          now=now,
                          timedelta=timedelta,
                          page_title="Compose Message",
                          person_id=person_id,
                          church_id=church_id)

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
    # Use the EmailTemplate model instead of raw SQL
    try:
        # Check if the model exists and is properly defined
        current_app.logger.info("Using EmailTemplate model for templates management")
        
        if request.method == 'POST':
            # Handle template save/update
            try:
                data = request.form
                template_id = data.get('template_id')
                
                if template_id and template_id.strip():  # Update existing template
                    # Check if template exists using the model
                    template = EmailTemplate.query.get(template_id)
                    
                    if not template:
                        flash('Template not found.', 'error')
                        return redirect(url_for('communications.templates'))
                    
                    # Check permission (only owner or admin can edit)
                    if template.created_by != current_user.id and current_user.role not in ['admin', 'super_admin']:
                        flash('You do not have permission to edit this template.', 'error')
                        return redirect(url_for('communications.templates'))
                    
                    # Update template using the model
                    template.name = data.get('name')
                    template.subject = data.get('subject')
                    template.content = data.get('content')
                    template.category = data.get('category')
                    template.updated_at = datetime.now(timezone.utc)
                    
                    db.session.commit()
                else:  # Create new template
                    # Create new template using the model
                    new_template = EmailTemplate(
                        name=data.get('name'),
                        subject=data.get('subject'),
                        content=data.get('content'),
                        category=data.get('category'),
                        created_by=current_user.id,
                        office_id=current_user.office_id,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    
                    db.session.add(new_template)
                    db.session.commit()
                
                flash('Template saved successfully!', 'success')
                return redirect(url_for('communications.templates'))
                
            except Exception as e:
                current_app.logger.error(f"Error saving template: {str(e)}")
                flash(f'Error saving template: {str(e)}', 'error')
                return redirect(url_for('communications.templates'))
        
        # For GET requests, fetch templates from the database using the model
        try:
            # Get filter parameters
            category = request.args.get('category')
            search = request.args.get('search')
            
            # Build query using SQLAlchemy
            query = EmailTemplate.query
            
            # Apply filters
            if category:
                query = query.filter(EmailTemplate.category == category)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    db.or_(
                        EmailTemplate.name.ilike(search_term),
                        EmailTemplate.subject.ilike(search_term),
                        EmailTemplate.content.ilike(search_term)
                    )
                )
            
            # Filter by office unless super admin
            if current_user.role != 'super_admin':
                query = query.filter(EmailTemplate.office_id == current_user.office_id)
            
            # Order by most recently updated first
            query = query.order_by(EmailTemplate.updated_at.desc())
            
            # Execute query
            templates_raw = query.all()
            
            # Process templates for display
            templates = []
            for template in templates_raw:
                template_dict = {
                    'id': template.id,
                    'name': template.name,
                    'subject': template.subject,
                    'content': template.content,
                    'category': template.category,
                    'created_by': template.created_by,
                    'office_id': template.office_id,
                    'created_at': template.created_at,
                    'updated_at': template.updated_at,
                    'content_preview': template.content[:100] + '...' if len(template.content) > 100 else template.content
                }
                templates.append(template_dict)
            
            current_app.logger.info(f"Retrieved {len(templates)} email templates")
            
        except Exception as e:
            current_app.logger.error(f"Error fetching templates: {str(e)}")
            templates = []
            flash('Error loading templates. Please try again later.', 'error')
        
        return render_template('communications/templates.html', 
                              templates=templates,
                              page_title="Email Templates")
    
    except Exception as e:
        current_app.logger.error(f"Error in templates route: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
        return render_template('error.html', error=str(e))

@communications_bp.route('/templates/delete/<int:id>', methods=['POST'])
@login_required
def delete_template(id):
    """Delete an email template."""
    try:
        # Check if template exists using the model
        template = EmailTemplate.query.get(id)
        
        if not template:
            flash('Template not found.', 'error')
            return redirect(url_for('communications.templates'))
        
        # Check permission (only owner or admin can delete)
        if template.created_by != current_user.id and current_user.role not in ['admin', 'super_admin']:
            flash('You do not have permission to delete this template.', 'error')
            return redirect(url_for('communications.templates'))
        
        # Delete template using the model
        db.session.delete(template)
        db.session.commit()
        
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
        # Query for the template using the model
        template = EmailTemplate.query.get(id)
        
        if not template:
            return jsonify({'success': False, 'message': 'Template not found'}), 404
        
        # Check permission
        if template.office_id != current_user.office_id and current_user.role not in ['super_admin', 'admin']:
            return jsonify({'success': False, 'message': 'You do not have permission to view this template'}), 403
        
        # Convert to dict for JSON response
        template_dict = {
            'id': template.id,
            'name': template.name,
            'subject': template.subject,
            'content': template.content,
            'category': template.category,
            'created_by': template.created_by,
            'office_id': template.office_id,
            'created_at': template.created_at.isoformat() if template.created_at else None,
            'updated_at': template.updated_at.isoformat() if template.updated_at else None
        }
        
        return jsonify({'success': True, 'template': template_dict})
    
    except Exception as e:
        current_app.logger.error(f"Error fetching template: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching template: {str(e)}'}), 500 

@communications_bp.route('/signatures', methods=['GET', 'POST'])
@login_required
@office_required
def signatures():
    """Manage email signatures."""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create' or action == 'update':
            signature_id = request.form.get('signature_id')
            name = request.form.get('name')
            content = request.form.get('content')
            is_default = True if request.form.get('is_default') else False
            
            if not name or not content:
                flash('Name and content are required', 'error')
                return redirect(url_for('communications.signatures'))
            
            # Handle logo upload if present
            logo_url = None
            if 'logo' in request.files and request.files['logo'].filename:
                try:
                    logo_url = save_uploaded_file(
                        request.files['logo'], 
                        folder='signatures', 
                        allowed_extensions=['jpg', 'jpeg', 'png', 'gif'],
                        max_size=2 * 1024 * 1024  # 2MB
                    )
                except ValueError as e:
                    flash(str(e), 'error')
                    return redirect(url_for('communications.signatures'))
            
            if action == 'create':
                # Create new signature
                signature = EmailSignature(
                    user_id=current_user.id,
                    name=name,
                    content=content.replace('\n', '<br>') if content else '',  # Ensure line breaks are preserved as HTML
                    logo_url=logo_url,
                    is_default=is_default
                )
                db.session.add(signature)
                
                # If this is set as default, unset others
                if is_default:
                    EmailSignature.query.filter(
                        EmailSignature.user_id == current_user.id,
                        EmailSignature.id != signature.id
                    ).update({'is_default': False})
                
                db.session.commit()
                flash('Signature created successfully', 'success')
            
            elif action == 'update':
                # Convert signature_id to integer to avoid type mismatch
                try:
                    signature_id = int(signature_id) if signature_id else None
                except (ValueError, TypeError):
                    flash('Invalid signature ID', 'error')
                    return redirect(url_for('communications.signatures'))
                    
                # Update existing signature
                signature = EmailSignature.query.filter_by(
                    id=signature_id, 
                    user_id=current_user.id
                ).first()
                
                if not signature:
                    flash('Signature not found', 'error')
                    return redirect(url_for('communications.signatures'))
                
                signature.name = name
                signature.content = content.replace('\n', '<br>') if content else ''  # Ensure line breaks are preserved as HTML
                if logo_url:
                    signature.logo_url = logo_url
                signature.is_default = is_default
                
                # If this is set as default, unset others
                if is_default:
                    EmailSignature.query.filter(
                        EmailSignature.user_id == current_user.id,
                        EmailSignature.id != signature.id
                    ).update({'is_default': False})
                
                db.session.commit()
                flash('Signature updated successfully', 'success')
        
        elif action == 'delete':
            signature_id = request.form.get('signature_id')
            # Convert signature_id to integer to avoid type mismatch
            try:
                signature_id = int(signature_id) if signature_id else None
            except (ValueError, TypeError):
                flash('Invalid signature ID', 'error')
                return redirect(url_for('communications.signatures'))
                
            signature = EmailSignature.query.filter_by(
                id=signature_id, 
                user_id=current_user.id
            ).first()
            
            if signature:
                db.session.delete(signature)
                db.session.commit()
                flash('Signature deleted successfully', 'success')
            else:
                flash('Signature not found', 'error')
        
        elif action == 'set_default':
            signature_id = request.form.get('signature_id')
            
            # Convert signature_id to integer to avoid type mismatch
            try:
                signature_id = int(signature_id) if signature_id else None
            except (ValueError, TypeError):
                flash('Invalid signature ID', 'error')
                return redirect(url_for('communications.signatures'))
            
            # Remove default from all signatures for this user
            EmailSignature.query.filter_by(user_id=current_user.id).update({'is_default': False})
            
            # Set the selected one as default
            signature = EmailSignature.query.filter_by(
                id=signature_id, 
                user_id=current_user.id
            ).first()
            
            if signature:
                signature.is_default = True
                db.session.commit()
                flash('Default signature updated', 'success')
            else:
                flash('Signature not found', 'error')
        
        return redirect(url_for('communications.signatures'))
    
    # GET request - show the signatures page
    signatures = EmailSignature.query.filter_by(user_id=current_user.id).order_by(
        EmailSignature.is_default.desc(),
        EmailSignature.name
    ).all()
    
    return render_template('communications/signatures.html', signatures=signatures) 