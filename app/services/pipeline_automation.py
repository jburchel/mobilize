"""
Pipeline Automation Service for handling automated pipeline actions.
This includes automatic movement of contacts, sending reminders,
and creating tasks based on pipeline stage settings.
"""

from datetime import datetime, timedelta
from app.extensions import db
from app.models import Pipeline, PipelineStage, PipelineContact, PipelineStageHistory, Task, User, Contact, Office
from flask import current_app, render_template
import json
from app.services.notification_service import send_notification
from app.services.email_service import send_email, send_pipeline_reminder_email
import logging

logger = logging.getLogger(__name__)

def run_pipeline_automations():
    """
    Run all pipeline automations in sequence.
    Returns a dictionary with counts of actions taken.
    """
    try:
        # Process automatic movements
        contacts_moved = process_automatic_movements()
        
        # Process automatic tasks (for contacts that have changed stages)
        tasks_created = process_automatic_tasks()
        
        # Send reminders for contacts in stages
        reminders_sent = process_automatic_reminders()
        
        # Commit any pending changes
        db.session.commit()
        
        current_app.logger.info(
            f"Pipeline automations completed: {contacts_moved} contacts moved, "
            f"{reminders_sent} reminders sent, {tasks_created} tasks created"
        )
        
        return {
            "contacts_moved": contacts_moved,
            "reminders_sent": reminders_sent,
            "tasks_created": tasks_created
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error running pipeline automations: {str(e)}")
        raise

def process_automatic_movements():
    """
    Process automatic movement of contacts between pipeline stages.
    Returns the number of contacts moved.
    """
    moved_count = 0
    
    # Find stages with auto-move configured
    auto_move_stages = PipelineStage.query.filter(
        PipelineStage.auto_move_days.isnot(None),
        PipelineStage.auto_move_days > 0,
        PipelineStage.is_active == True
    ).all()
    
    current_app.logger.info(f"Processing automatic movements for {len(auto_move_stages)} stages")
    
    for stage in auto_move_stages:
        # Check if there's a next stage to move to
        next_stage = PipelineStage.query.filter_by(
            pipeline_id=stage.pipeline_id,
            order=stage.order + 1,
            is_active=True
        ).first()
        
        if not next_stage:
            continue  # No next stage to move to
        
        # Find contacts that have been in this stage for too long
        cutoff_date = datetime.utcnow() - timedelta(days=stage.auto_move_days)
        
        pipeline_contacts = PipelineContact.query.filter_by(
            current_stage_id=stage.id
        ).filter(
            PipelineContact.last_updated <= cutoff_date
        ).all()
        
        for pipeline_contact in pipeline_contacts:
            try:
                # Move the contact to the next stage
                pipeline_contact.move_to_stage(
                    next_stage.id,
                    user_id=None,  # Automated move
                    notes=f"Automatically moved after {stage.auto_move_days} days in stage"
                )
                moved_count += 1
                
                current_app.logger.info(
                    f"Auto-moved contact {pipeline_contact.contact_id} from {stage.name} to {next_stage.name}"
                )
            except Exception as e:
                current_app.logger.error(
                    f"Error auto-moving contact {pipeline_contact.contact_id}: {str(e)}"
                )
    
    # Commit all changes
    if moved_count > 0:
        db.session.commit()
    
    return moved_count

def process_automatic_reminders():
    """
    Send reminders for contacts that have been in a stage for too long.
    Returns the number of reminders sent.
    """
    reminders_sent = 0
    
    # Find stages with auto-reminder configured
    reminder_stages = PipelineStage.query.filter_by(
        auto_reminder=True,
        is_active=True
    ).all()
    
    current_app.logger.info(f"Processing automatic reminders for {len(reminder_stages)} stages")
    
    # Process each stage
    for stage in reminder_stages:
        # Get the pipeline for context
        pipeline = Pipeline.query.get(stage.pipeline_id)
        if not pipeline:
            continue
            
        # Define thresholds for reminders (7, 14, 30 days)
        thresholds = [7, 14, 30]
        
        # Get all contacts in this stage
        pipeline_contacts = PipelineContact.query.filter_by(
            current_stage_id=stage.id
        ).all()
        
        # Group contacts by days in stage
        contacts_by_threshold = {}
        for threshold in thresholds:
            contacts_by_threshold[threshold] = []
        
        for pipeline_contact in pipeline_contacts:
            days_in_stage = (datetime.utcnow() - pipeline_contact.last_updated).days
            
            # Check which threshold this contact falls under
            for threshold in thresholds:
                if days_in_stage == threshold:  # Exact match to avoid duplicate reminders
                    contact = Contact.query.get(pipeline_contact.contact_id)
                    if contact:
                        contacts_by_threshold[threshold].append({
                            'contact': contact,
                            'days_in_stage': days_in_stage,
                            'pipeline_contact': pipeline_contact
                        })
        
        # Get office users to notify
        if pipeline.office_id:
            office = Office.query.get(pipeline.office_id)
            if office:
                office_users = User.query.filter_by(office_id=office.id, is_active=True).all()
                office_admins = [u for u in office_users if u.is_office_admin(office.id)]
                
                # Send reminders to office admins
                for threshold, contacts in contacts_by_threshold.items():
                    if contacts:
                        for user in office_admins:
                            try:
                                send_pipeline_reminder_email(
                                    user=user,
                                    stage=stage,
                                    pipeline=pipeline,
                                    contacts=contacts,
                                    days=threshold
                                )
                                reminders_sent += 1
                                
                                current_app.logger.info(
                                    f"Sent {threshold}-day reminder to {user.email} for {len(contacts)} contacts in {stage.name}"
                                )
                            except Exception as e:
                                current_app.logger.error(
                                    f"Error sending reminder email to {user.email}: {str(e)}"
                                )
    
    return reminders_sent

def process_automatic_tasks():
    """
    Create tasks automatically when a contact enters a stage with auto_task_template.
    Returns the number of tasks created.
    """
    tasks_created = 0
    
    # Find all stage histories created within the last day
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    
    # Import here to avoid circular imports
    from app.models import PipelineStageHistory
    
    recent_movements = PipelineStageHistory.query.filter(
        PipelineStageHistory.moved_at >= one_day_ago
    ).all()
    
    current_app.logger.info(f"Processing automatic tasks for {len(recent_movements)} recent stage movements")
    
    for movement in recent_movements:
        # Skip if there's no destination stage
        if not movement.to_stage_id:
            continue
            
        # Get the stage the contact moved to
        stage = PipelineStage.query.get(movement.to_stage_id)
        if not stage or not stage.auto_task_template:
            continue
            
        # Check if we've already created a task for this movement
        # (To prevent duplicate task creation if the function runs multiple times)
        existing_task = Task.query.filter_by(
            pipeline_stage_history_id=movement.id
        ).first()
        
        if existing_task:
            continue
            
        # Get the pipeline contact
        pipeline_contact = movement.pipeline_contact
        if not pipeline_contact:
            continue
            
        # Get the contact
        contact = Contact.query.get(pipeline_contact.contact_id)
        if not contact:
            continue
            
        # Get the pipeline
        pipeline = Pipeline.query.get(stage.pipeline_id)
        if not pipeline:
            continue
        
        try:
            # Parse the task template
            task_template = json.loads(stage.auto_task_template)
            
            # Create the task
            title = task_template.get('title', 'Follow up')
            description = task_template.get('description', '')
            days_to_complete = task_template.get('days_to_complete', 3)
            priority = task_template.get('priority', 'MEDIUM')
            
            # Replace placeholders
            title = title.replace('{contact_name}', contact.get_name())
            description = description.replace('{contact_name}', contact.get_name())
            description = description.replace('{stage_name}', stage.name)
            description = description.replace('{pipeline_name}', pipeline.name)
            
            # Calculate due date
            due_date = datetime.utcnow() + timedelta(days=days_to_complete)
            
            # Create task
            task = Task(
                title=title,
                description=description,
                contact_id=contact.id,
                due_date=due_date,
                priority=priority,
                pipeline_stage_history_id=movement.id,
                office_id=pipeline.office_id
            )
            
            db.session.add(task)
            tasks_created += 1
            
            current_app.logger.info(
                f"Created automatic task '{title}' for contact {contact.id} in stage {stage.name}"
            )
        except Exception as e:
            current_app.logger.error(
                f"Error creating automatic task for contact {contact.id}: {str(e)}"
            )
    
    # Commit all changes
    if tasks_created > 0:
        db.session.commit()
    
    return tasks_created

def url_for(endpoint, **values):
    """Simple utility to generate URLs without Flask request context"""
    from flask import url_for as flask_url_for
    from app import create_app
    from flask import current_app
    
    if current_app:
        # We're in a request context
        return flask_url_for(endpoint, **values)
    else:
        # Create a test request context
        app = create_app()
        with app.test_request_context():
            return flask_url_for(endpoint, **values, _external=True) 