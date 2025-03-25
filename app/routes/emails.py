from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models.email_template import EmailTemplate
from app.models.email_campaign import EmailCampaign
from app.models.email_tracking import EmailTracking
from app.models.person import Person
from app.utils.email_service import send_bulk_email
from app.extensions import db
import datetime
import json

emails_bp = Blueprint('emails', __name__, template_folder='../templates/emails')

@emails_bp.route('/', methods=['GET'])
@login_required
def index():
    """Email management dashboard."""
    return render_template('emails/index.html', page_title="Email Management")

@emails_bp.route('/templates', methods=['GET', 'POST'])
@login_required
def templates():
    """Manage email templates."""
    if request.method == 'POST':
        # Handle template creation/edit form submission
        template_id = request.form.get('template_id')
        name = request.form.get('name')
        category = request.form.get('category')
        subject = request.form.get('subject')
        content = request.form.get('content')
        
        # Validate form inputs
        if not all([name, subject, content, category]):
            flash('All fields are required', 'danger')
            return redirect(url_for('emails.templates'))
        
        # Extract variables from the content
        variables = []
        import re
        var_pattern = r'\[(.*?)\]'
        matches = re.findall(var_pattern, content)
        if matches:
            variables = list(set(matches))  # Remove duplicates
        
        if template_id:
            # Update existing template
            template = EmailTemplate.query.get(template_id)
            if template and template.office_id == current_user.office_id:
                template.name = name
                template.subject = subject
                template.content = content
                template.category = category
                template.set_variables(variables)
                db.session.commit()
                flash('Template updated successfully', 'success')
            else:
                flash('Template not found or you don\'t have permission', 'danger')
        else:
            # Create new template
            template = EmailTemplate(
                name=name,
                subject=subject,
                content=content,
                category=category,
                created_by=current_user.id,
                office_id=current_user.office_id
            )
            template.set_variables(variables)
            db.session.add(template)
            db.session.commit()
            flash('Template created successfully', 'success')
        
        return redirect(url_for('emails.templates'))
    
    # GET request - show templates list
    templates = EmailTemplate.query.filter_by(
        office_id=current_user.office_id,
        is_active=True
    ).order_by(EmailTemplate.created_at.desc()).all()
    
    return render_template('emails/templates.html', 
                           templates=templates,
                           page_title="Email Templates")

@emails_bp.route('/templates/<int:template_id>', methods=['GET'])
@login_required
def template_detail(template_id):
    """Get template details in JSON format."""
    template = EmailTemplate.query.get(template_id)
    
    if not template or template.office_id != current_user.office_id:
        return jsonify({'error': 'Template not found'}), 404
    
    return jsonify(template.to_dict())

@emails_bp.route('/templates/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id):
    """Delete an email template."""
    template = EmailTemplate.query.get(template_id)
    
    if not template or template.office_id != current_user.office_id:
        flash('Template not found or you don\'t have permission', 'danger')
        return redirect(url_for('emails.templates'))
    
    # Soft delete by marking as inactive
    template.is_active = False
    db.session.commit()
    flash('Template deleted successfully', 'success')
    return redirect(url_for('emails.templates'))

@emails_bp.route('/campaigns', methods=['GET'])
@login_required
def campaigns():
    """Manage email campaigns."""
    # Get all campaigns for this office
    campaigns = EmailCampaign.query.filter_by(
        office_id=current_user.office_id,
    ).order_by(EmailCampaign.created_at.desc()).all()
    
    # Get templates for dropdown
    templates = EmailTemplate.query.filter_by(
        office_id=current_user.office_id,
        is_active=True
    ).order_by(EmailTemplate.name).all()
    
    return render_template('emails/campaigns.html', 
                           campaigns=campaigns,
                           templates=templates,
                           page_title="Email Campaigns")

@emails_bp.route('/campaigns/new', methods=['GET', 'POST'])
@login_required
def new_campaign():
    """Create a new email campaign."""
    if request.method == 'POST':
        # Handle campaign creation form submission
        name = request.form.get('name')
        description = request.form.get('description')
        subject = request.form.get('subject')
        content = request.form.get('content')
        template_id = request.form.get('template_id')
        
        # Recipient filters
        filter_data = {
            'status': request.form.getlist('status'),
            'tags': request.form.getlist('tags'),
            'has_email': request.form.get('has_email') == 'true',
            'exclude_previous_recipients': request.form.get('exclude_previous_recipients') == 'true'
        }
        
        # Validate form inputs
        if not all([name, subject, content]):
            flash('Name, subject, and content are required', 'danger')
            return redirect(url_for('emails.new_campaign'))
        
        # Create new campaign
        campaign = EmailCampaign(
            name=name,
            description=description,
            subject=subject,
            content=content,
            template_id=template_id if template_id else None,
            created_by=current_user.id,
            office_id=current_user.office_id,
            status='draft'
        )
        
        # Set recipient filter
        campaign.set_recipient_filter(filter_data)
        
        # Calculate recipient count based on filters
        recipients_query = Person.query.filter_by(office_id=current_user.office_id)
        
        # Apply status filters
        if filter_data.get('status'):
            recipients_query = recipients_query.filter(Person.status.in_(filter_data['status']))
        
        # Apply tag filters
        if filter_data.get('tags'):
            for tag in filter_data['tags']:
                recipients_query = recipients_query.filter(Person.tags.contains(tag))
        
        # Apply email filter
        if filter_data.get('has_email'):
            recipients_query = recipients_query.filter(Person.email.isnot(None), Person.email != '')
        
        # Exclude previous recipients if requested
        if filter_data.get('exclude_previous_recipients'):
            previous_recipients = db.session.query(EmailTracking.person_id).distinct()
            recipients_query = recipients_query.filter(~Person.id.in_(previous_recipients))
        
        # Count recipients
        campaign.recipient_count = recipients_query.count()
        
        db.session.add(campaign)
        db.session.commit()
        
        flash('Campaign created successfully', 'success')
        return redirect(url_for('emails.edit_campaign', campaign_id=campaign.id))
    
    # GET request - show new campaign form
    templates = EmailTemplate.query.filter_by(
        office_id=current_user.office_id,
        is_active=True
    ).order_by(EmailTemplate.name).all()
    
    # Get available person statuses
    statuses = db.session.query(Person.status).filter_by(
        office_id=current_user.office_id
    ).distinct().all()
    statuses = [s[0] for s in statuses if s[0]]
    
    # Get available tags
    tags = []
    try:
        # This assumes tags are stored in a column or can be extracted from the people table
        # You may need to adjust this based on your actual data model
        tags_query = db.session.query(db.func.unnest(Person.tags)).filter(
            Person.office_id == current_user.office_id
        ).distinct().all()
        tags = [t[0] for t in tags_query if t[0]]
    except:
        # If the above query fails (e.g., no tags column), provide an empty list
        pass
    
    return render_template('emails/campaign_form.html',
                          campaign=None,
                          templates=templates,
                          statuses=statuses,
                          tags=tags,
                          has_email=False,
                          exclude_previous_recipients=False,
                          page_title="New Email Campaign")

@emails_bp.route('/campaigns/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_campaign(campaign_id):
    """Edit an existing email campaign."""
    campaign = EmailCampaign.query.get(campaign_id)
    
    if not campaign or campaign.office_id != current_user.office_id:
        flash('Campaign not found or you don\'t have permission', 'danger')
        return redirect(url_for('emails.campaigns'))
    
    if campaign.status not in ['draft', 'scheduled']:
        flash('Only draft or scheduled campaigns can be edited', 'warning')
        return redirect(url_for('emails.campaigns'))
    
    if request.method == 'POST':
        # Handle campaign update form submission
        campaign.name = request.form.get('name')
        campaign.description = request.form.get('description')
        campaign.subject = request.form.get('subject')
        campaign.content = request.form.get('content')
        campaign.template_id = request.form.get('template_id') or None
        
        # Recipient filters
        filter_data = {
            'status': request.form.getlist('status'),
            'tags': request.form.getlist('tags'),
            'has_email': request.form.get('has_email') == 'true',
            'exclude_previous_recipients': request.form.get('exclude_previous_recipients') == 'true'
        }
        
        # Validate form inputs
        if not all([campaign.name, campaign.subject, campaign.content]):
            flash('Name, subject, and content are required', 'danger')
            return redirect(url_for('emails.edit_campaign', campaign_id=campaign.id))
        
        # Set recipient filter
        campaign.set_recipient_filter(filter_data)
        
        # Calculate recipient count based on filters
        recipients_query = Person.query.filter_by(office_id=current_user.office_id)
        
        # Apply status filters
        if filter_data.get('status'):
            recipients_query = recipients_query.filter(Person.status.in_(filter_data['status']))
        
        # Apply tag filters
        if filter_data.get('tags'):
            for tag in filter_data['tags']:
                recipients_query = recipients_query.filter(Person.tags.contains(tag))
        
        # Apply email filter
        if filter_data.get('has_email'):
            recipients_query = recipients_query.filter(Person.email.isnot(None), Person.email != '')
        
        # Exclude previous recipients if requested
        if filter_data.get('exclude_previous_recipients'):
            previous_recipients = db.session.query(EmailTracking.person_id).distinct()
            recipients_query = recipients_query.filter(~Person.id.in_(previous_recipients))
        
        # Count recipients
        campaign.recipient_count = recipients_query.count()
        
        db.session.commit()
        flash('Campaign updated successfully', 'success')
        return redirect(url_for('emails.campaigns'))
    
    # GET request - show edit form
    templates = EmailTemplate.query.filter_by(
        office_id=current_user.office_id,
        is_active=True
    ).order_by(EmailTemplate.name).all()
    
    # Get available person statuses
    statuses = db.session.query(Person.status).filter_by(
        office_id=current_user.office_id
    ).distinct().all()
    statuses = [s[0] for s in statuses if s[0]]
    
    # Get currently selected filters
    filter_data = campaign.get_recipient_filter()
    selected_statuses = filter_data.get('status', [])
    selected_tags = filter_data.get('tags', [])
    has_email = filter_data.get('has_email', False)
    exclude_previous_recipients = filter_data.get('exclude_previous_recipients', False)
    
    # Get available tags
    tags = []
    try:
        # This assumes tags are stored in a column or can be extracted from the people table
        tags_query = db.session.query(db.func.unnest(Person.tags)).filter(
            Person.office_id == current_user.office_id
        ).distinct().all()
        tags = [t[0] for t in tags_query if t[0]]
    except:
        # If the above query fails (e.g., no tags column), provide an empty list
        pass
    
    return render_template('emails/campaign_form.html',
                          campaign=campaign,
                          templates=templates,
                          statuses=statuses,
                          selected_statuses=selected_statuses,
                          tags=tags,
                          selected_tags=selected_tags,
                          has_email=has_email,
                          exclude_previous_recipients=exclude_previous_recipients,
                          page_title="Edit Email Campaign")

@emails_bp.route('/campaigns/<int:campaign_id>/preview', methods=['GET'])
@login_required
def preview_campaign(campaign_id):
    """Preview an email campaign."""
    campaign = EmailCampaign.query.get(campaign_id)
    
    if not campaign or campaign.office_id != current_user.office_id:
        flash('Campaign not found or you don\'t have permission', 'danger')
        return redirect(url_for('emails.campaigns'))
    
    # Get recipient count
    filter_data = campaign.get_recipient_filter()
    recipients_query = Person.query.filter_by(office_id=current_user.office_id)
    if filter_data.get('status'):
        recipients_query = recipients_query.filter(Person.status.in_(filter_data['status']))
    
    # Get the first few recipients for preview
    preview_recipients = recipients_query.limit(5).all()
    
    return render_template('emails/campaign_preview.html',
                          campaign=campaign,
                          recipients=preview_recipients,
                          recipient_count=recipients_query.count(),
                          page_title="Preview Campaign")

@emails_bp.route('/campaigns/<int:campaign_id>/send', methods=['POST'])
@login_required
def send_campaign(campaign_id):
    """Send an email campaign."""
    campaign = EmailCampaign.query.get(campaign_id)
    
    if not campaign or campaign.office_id != current_user.office_id:
        flash('Campaign not found or you don\'t have permission', 'danger')
        return redirect(url_for('emails.campaigns'))
    
    if campaign.status not in ['draft', 'scheduled']:
        flash('This campaign has already been sent or cancelled', 'warning')
        return redirect(url_for('emails.campaigns'))
    
    # Call the send_bulk_email function
    success, message, sent_count = send_bulk_email(campaign.id)
    
    if success:
        flash(f'Campaign is being sent to {sent_count} recipients', 'success')
    else:
        flash(f'Error sending campaign: {message}', 'danger')
    
    return redirect(url_for('emails.campaigns'))

@emails_bp.route('/campaigns/<int:campaign_id>/cancel', methods=['POST'])
@login_required
def cancel_campaign(campaign_id):
    """Cancel a scheduled email campaign."""
    campaign = EmailCampaign.query.get(campaign_id)
    
    if not campaign or campaign.office_id != current_user.office_id:
        flash('Campaign not found or you don\'t have permission', 'danger')
        return redirect(url_for('emails.campaigns'))
    
    if campaign.status not in ['draft', 'scheduled']:
        flash('This campaign cannot be cancelled', 'warning')
        return redirect(url_for('emails.campaigns'))
    
    campaign.status = 'cancelled'
    db.session.commit()
    flash('Campaign has been cancelled', 'success')
    
    return redirect(url_for('emails.campaigns'))

@emails_bp.route('/campaigns/<int:campaign_id>/analytics', methods=['GET'])
@login_required
def campaign_analytics(campaign_id):
    """View analytics for an email campaign."""
    campaign = EmailCampaign.query.get(campaign_id)
    
    if not campaign or campaign.office_id != current_user.office_id:
        flash('Campaign not found or you don\'t have permission', 'danger')
        return redirect(url_for('emails.campaigns'))
    
    # Get tracking data
    tracking_data = EmailTracking.query.filter_by(
        bulk_send_id=str(campaign.id)
    ).all()
    
    # Prepare analytics
    analytics = {
        'sent': len(tracking_data),
        'opened': sum(1 for t in tracking_data if t.open_count > 0),
        'clicked': sum(1 for t in tracking_data if t.click_count > 0),
        'bounced': sum(1 for t in tracking_data if t.status == 'bounced'),
        'open_rate': 0,
        'click_rate': 0
    }
    
    if analytics['sent'] > 0:
        analytics['open_rate'] = round((analytics['opened'] / analytics['sent']) * 100, 1)
        analytics['click_rate'] = round((analytics['clicked'] / analytics['sent']) * 100, 1)
    
    return render_template('emails/campaign_analytics.html',
                          campaign=campaign,
                          analytics=analytics,
                          tracking_data=tracking_data,
                          page_title="Campaign Analytics")

@emails_bp.route('/track/open/<tracking_id>', methods=['GET'])
def track_open(tracking_id):
    """Track email opens via a tracking pixel."""
    tracking = EmailTracking.query.filter_by(tracking_pixel=tracking_id).first()
    
    if tracking:
        tracking.mark_opened()
        db.session.commit()
        
        # If this is part of a campaign, update campaign stats
        if tracking.bulk_send_id:
            campaign = EmailCampaign.query.get(int(tracking.bulk_send_id))
            if campaign:
                campaign.update_stats()
                db.session.commit()
    
    # Return a 1x1 transparent pixel
    return current_app.send_static_file('images/pixel.gif')

@emails_bp.route('/track/click/<tracking_id>', methods=['GET'])
def track_click(tracking_id):
    """Track email link clicks and redirect to the original URL."""
    tracking = EmailTracking.query.filter_by(tracking_pixel=tracking_id).first()
    redirect_url = request.args.get('redirect_url', '/')
    
    if tracking:
        tracking.mark_clicked()
        db.session.commit()
        
        # If this is part of a campaign, update campaign stats
        if tracking.bulk_send_id:
            campaign = EmailCampaign.query.get(int(tracking.bulk_send_id))
            if campaign:
                campaign.update_stats()
                db.session.commit()
    
    return redirect(redirect_url)

@emails_bp.route('/campaigns/count-recipients', methods=['GET'])
@login_required
def count_recipients():
    """Count recipients based on filter criteria."""
    # Get filter parameters
    status_filters = request.args.getlist('status')
    tag_filters = request.args.getlist('tags')
    has_email = request.args.get('has_email') == 'true'
    exclude_previous = request.args.get('exclude_previous') == 'true'
    
    # Build recipient query
    query = Person.query.filter_by(office_id=current_user.office_id)
    
    # Apply status filters
    if status_filters:
        query = query.filter(Person.status.in_(status_filters))
    
    # Apply tag filters if available
    if tag_filters:
        # This assumes you have a tags relationship or column
        for tag in tag_filters:
            query = query.filter(Person.tags.contains(tag))
    
    # Apply email filter
    if has_email:
        query = query.filter(Person.email.isnot(None), Person.email != '')
    
    # Exclude previous recipients if requested
    if exclude_previous:
        # Get list of people who have received campaigns before
        previous_recipients = db.session.query(EmailTracking.person_id).distinct()
        query = query.filter(~Person.id.in_(previous_recipients))
    
    # Count distinct recipients
    count = query.count()
    
    return jsonify({'count': count}) 