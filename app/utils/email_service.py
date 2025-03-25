import os
import uuid
import re
from datetime import datetime
from urllib.parse import urljoin
from flask import current_app, render_template, url_for
from flask_mail import Message
from functools import wraps
from app.extensions import db, mail
from app.models.email_template import EmailTemplate
from app.models.email_tracking import EmailTracking
from app.models.email_campaign import EmailCampaign
from app.models.person import Person


def ensure_mail_configured(f):
    """Decorator to ensure mail is configured before sending."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.config.get('MAIL_SERVER'):
            current_app.logger.error("Mail server not configured")
            # Return three values (success, message, count/tracking_id) based on the function signature
            if f.__name__ == 'send_bulk_email':
                return False, "Mail server not configured", 0
            else:
                return False, "Mail server not configured", None
        return f(*args, **kwargs)
    return decorated_function


def generate_tracking_id():
    """Generate a unique tracking ID for email tracking."""
    return str(uuid.uuid4())


def replace_template_variables(content, recipient):
    """Replace template variables in content with recipient data."""
    variables = {
        '[Name]': f"{recipient.first_name} {recipient.last_name}",
        '[FirstName]': recipient.first_name,
        '[LastName]': recipient.last_name,
        '[Email]': recipient.email
    }
    
    # Add additional properties if available
    if hasattr(recipient, 'phone') and recipient.phone:
        variables['[Phone]'] = recipient.phone
    
    if hasattr(recipient, 'address') and recipient.address:
        variables['[Address]'] = recipient.address
    
    # Replace all variables in content
    for var, value in variables.items():
        if value:  # Only replace if value exists
            content = content.replace(var, value)
    
    # Check for any remaining unresolved variables and remove them
    pattern = r'\[\w+\]'
    content = re.sub(pattern, '', content)
    
    return content


def insert_tracking_pixel(content, tracking_id):
    """Insert a tracking pixel into the email content."""
    if not tracking_id:
        return content
        
    tracking_url = url_for('api.v1.email_tracking.track_open', 
                          tracking_id=tracking_id, 
                          _external=True)
    
    tracking_pixel = f'<img src="{tracking_url}" width="1" height="1" alt="" />'
    
    # Insert before the closing body tag or at the end if no body tag
    if '</body>' in content:
        content = content.replace('</body>', f'{tracking_pixel}</body>')
    else:
        content += tracking_pixel
        
    return content


def add_tracking_to_links(content, tracking_id):
    """Add tracking to all links in the email content."""
    if not tracking_id:
        return content
        
    def replace_link(match):
        original_url = match.group(1)
        tracking_url = url_for('api.v1.email_tracking.track_click', 
                              tracking_id=tracking_id,
                              redirect_url=original_url,
                              _external=True)
        return f'href="{tracking_url}"'
        
    # Replace href attributes in anchor tags
    pattern = r'href="([^"]+)"'
    return re.sub(pattern, replace_link, content)


@ensure_mail_configured
def send_email(subject, content, to_email, sender_id, office_id, template_id=None, person_id=None, bulk_send_id=None, use_tracking=True):
    """
    Send an email and track it.
    
    Args:
        subject: Email subject
        content: HTML content for the email
        to_email: Recipient email address
        sender_id: ID of the sending user
        office_id: ID of the sending office
        template_id: ID of the email template used (optional)
        person_id: ID of the recipient person (optional)
        bulk_send_id: ID for bulk send tracking (optional)
        use_tracking: Whether to use email tracking
        
    Returns:
        tuple: (success, message, tracking_id)
    """
    try:
        # Generate tracking ID if tracking is enabled
        tracking_id = generate_tracking_id() if use_tracking else None
        
        # Add tracking pixel and link tracking if enabled
        if use_tracking:
            content = insert_tracking_pixel(content, tracking_id)
            content = add_tracking_to_links(content, tracking_id)
        
        # Create the tracking record
        tracking = EmailTracking(
            email_subject=subject,
            recipient_email=to_email,
            status='sending',
            message_id=f"<{tracking_id}@{current_app.config.get('MAIL_SERVER', 'localhost')}>",
            tracking_pixel=tracking_id if use_tracking else None,
            template_id=template_id,
            sender_id=sender_id,
            person_id=person_id,
            office_id=office_id,
            bulk_send_id=bulk_send_id
        )
        db.session.add(tracking)
        db.session.commit()
        
        # Create and send the email through Flask-Mail
        msg = Message(
            subject=subject,
            recipients=[to_email],
            html=content,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        msg.extra_headers = {"Message-ID": tracking.message_id} if tracking.message_id else {}
        
        mail.send(msg)
        
        # Update the tracking record to sent status
        tracking.status = 'sent'
        db.session.commit()
        
        return True, "Email sent successfully", tracking_id
        
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        # If tracking was created, update status to failed
        if tracking_id and 'tracking' in locals():
            tracking.status = 'failed'
            db.session.commit()
        return False, f"Failed to send email: {str(e)}", None


def send_email_with_template(subject, recipients, template, context, sender_id=None, office_id=None, person_id=None, use_tracking=False):
    """
    Render an email template and send it to recipients.
    This is a simplified version for system emails like reminders.
    
    Args:
        subject: Email subject
        recipients: List of email addresses or single email address
        template: Template path to render (e.g. 'emails/task_reminder.html')
        context: Dictionary of variables to pass to the template
        sender_id: ID of the sending user (optional)
        office_id: ID of the sending office (optional)
        person_id: ID of the recipient person (optional)
        use_tracking: Whether to use email tracking
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Convert single recipient to list
        if isinstance(recipients, str):
            recipients = [recipients]
            
        # Render the template
        rendered_content = render_template(template, **context)
        
        # Send to each recipient
        successes = 0
        for recipient in recipients:
            success, message, _ = send_email(
                subject=subject,
                content=rendered_content,
                to_email=recipient,
                sender_id=sender_id,
                office_id=office_id,
                person_id=person_id,
                use_tracking=use_tracking
            )
            if success:
                successes += 1
                
        if successes == len(recipients):
            return True, f"Email sent successfully to {successes} recipients"
        elif successes > 0:
            return True, f"Email sent to {successes} of {len(recipients)} recipients"
        else:
            return False, "Failed to send email to any recipients"
            
    except Exception as e:
        current_app.logger.error(f"Error sending email with template: {str(e)}")
        return False, f"Failed to send email: {str(e)}"


def send_pipeline_reminder_email(user, contacts, stage, pipeline_name, days_in_stage):
    """Send a reminder email about contacts that have been in a pipeline stage too long."""
    subject = f"Pipeline Alert: {len(contacts)} contacts in {stage.name} for {days_in_stage} days"
    
    context = {
        'user': user,
        'contacts': contacts,
        'stage': stage,
        'pipeline_name': pipeline_name,
        'days_in_stage': days_in_stage,
        'app_url': current_app.config.get('APP_URL', 'http://localhost:5000')
    }
    
    return send_email_with_template(
        subject=subject,
        recipients=user.email,
        template='emails/pipeline_reminder.html',
        context=context,
        sender_id=None,  # System email
        office_id=user.office_id
    )


@ensure_mail_configured
def send_bulk_email(campaign_id):
    """
    Send emails for a bulk campaign.
    
    Args:
        campaign_id: ID of the campaign to send
        
    Returns:
        tuple: (success, message, sent_count)
    """
    try:
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            return False, "Campaign not found", 0
        
        # Check if campaign is in a sendable state
        if campaign.status not in ['draft', 'scheduled']:
            return False, f"Campaign is in {campaign.status} status and cannot be sent", 0
        
        # Mark campaign as sending
        campaign.status = 'sending'
        db.session.commit()
        
        # Get recipients based on filter criteria
        recipient_filter = campaign.get_recipient_filter()
        recipients_query = Person.query.filter_by(office_id=campaign.office_id)
        
        # Apply filters
        if 'status' in recipient_filter and recipient_filter['status']:
            recipients_query = recipients_query.filter(Person.status.in_(recipient_filter['status']))
        
        # Apply other filter criteria
        if 'has_email' in recipient_filter and recipient_filter['has_email']:
            recipients_query = recipients_query.filter(Person.email.isnot(None), Person.email != '')
            
        if 'tags' in recipient_filter and recipient_filter['tags']:
            for tag in recipient_filter['tags']:
                recipients_query = recipients_query.filter(Person.tags.contains(tag))
        
        if 'exclude_previous_recipients' in recipient_filter and recipient_filter['exclude_previous_recipients']:
            previous_recipients = db.session.query(EmailTracking.person_id).distinct()
            recipients_query = recipients_query.filter(~Person.id.in_(previous_recipients))
        
        recipients = recipients_query.all()
        
        # Update recipient count
        campaign.recipient_count = len(recipients)
        db.session.commit()
        
        # Send to each recipient
        sent_count = 0
        for recipient in recipients:
            if not recipient.email:
                continue  # Skip recipients without email
            
            # Personalize content for this recipient
            personalized_subject = replace_template_variables(campaign.subject, recipient)
            personalized_content = replace_template_variables(campaign.content, recipient)
            
            # Send the email
            success, message, tracking_id = send_email(
                subject=personalized_subject,
                content=personalized_content,
                to_email=recipient.email,
                sender_id=campaign.created_by,
                office_id=campaign.office_id,
                template_id=campaign.template_id,
                person_id=recipient.id,
                bulk_send_id=str(campaign.id),
                use_tracking=True
            )
            
            if success:
                sent_count += 1
        
        # Update campaign status and tracking stats
        campaign.status = 'completed'
        campaign.sent_at = datetime.utcnow()
        campaign.update_stats()
        db.session.commit()
        
        return True, f"Campaign sent successfully to {sent_count} recipients", sent_count
        
    except Exception as e:
        current_app.logger.error(f"Error sending bulk email: {str(e)}")
        if 'campaign' in locals():
            campaign.status = 'failed'
            db.session.commit()
        return False, f"Failed to send bulk email: {str(e)}", 0 