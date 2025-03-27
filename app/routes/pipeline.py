from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.controllers.pipeline_controller import (
    index as pipeline_index,
    create as pipeline_create,
    view as pipeline_view,
    edit as pipeline_edit,
    manage_stages as pipeline_manage_stages,
    move_contact_api as pipeline_move_contact_api,
    remove_contact as pipeline_remove_contact,
    add_contact as pipeline_add_contact,
    history as pipeline_history,
    update_pipeline as pipeline_update
)
from app.models import Pipeline, PipelineContact, Contact, Task, Communication, PipelineStageHistory
from datetime import datetime, timedelta
from flask import jsonify
from sqlalchemy import inspect
from app.extensions import db

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/pipeline')

@pipeline_bp.route('/')
@login_required
def index():
    return pipeline_index()

@pipeline_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    return pipeline_create()

@pipeline_bp.route('/<int:pipeline_id>')
@login_required
def view(pipeline_id):
    return pipeline_view(pipeline_id)

@pipeline_bp.route('/<int:pipeline_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(pipeline_id):
    return pipeline_edit(pipeline_id)

@pipeline_bp.route('/<int:pipeline_id>/stages', methods=['GET', 'POST'])
@login_required
def manage_stages(pipeline_id):
    return pipeline_manage_stages(pipeline_id)

@pipeline_bp.route('/move-contact/<int:pipeline_contact_id>', methods=['POST'])
@login_required
def move_contact(pipeline_contact_id):
    return pipeline_move_contact_api(pipeline_contact_id)

@pipeline_bp.route('/remove-contact/<int:pipeline_contact_id>', methods=['POST'])
@login_required
def remove_contact(pipeline_contact_id):
    return pipeline_remove_contact(pipeline_contact_id)

@pipeline_bp.route('/add_contact', methods=['POST'])
@login_required
def add_contact():
    """Add a contact to a pipeline via AJAX."""
    return pipeline_add_contact()

@pipeline_bp.route('/<int:pipeline_id>/history/<int:pipeline_contact_id>')
@login_required
def history(pipeline_id, pipeline_contact_id):
    return pipeline_history(pipeline_id, pipeline_contact_id)

@pipeline_bp.route('/update', methods=['POST'])
@login_required
def update_pipeline():
    return pipeline_update()

@pipeline_bp.route('/<int:pipeline_id>/delete', methods=['POST'])
@login_required
def delete(pipeline_id):
    """Delete a pipeline."""
    try:
        pipeline = Pipeline.query.get_or_404(pipeline_id)
        
        # Check if user has permission (must be in same office)
        if pipeline.office_id != current_user.office_id and not current_user.is_super_admin():
            flash('You do not have permission to delete this pipeline.', 'danger')
            return redirect(url_for('pipeline.index'))
            
        # Don't allow deleting main pipelines
        if pipeline.is_main_pipeline:
            flash('Cannot delete main pipeline.', 'danger')
            return redirect(url_for('pipeline.index'))
            
        # Delete all pipeline contacts
        PipelineContact.query.filter_by(pipeline_id=pipeline_id).delete()
        
        # Delete all pipeline stages and their histories
        for stage in pipeline.stages:
            PipelineStageHistory.query.filter(
                (PipelineStageHistory.from_stage_id == stage.id) | 
                (PipelineStageHistory.to_stage_id == stage.id)
            ).delete()
            
        db.session.delete(pipeline)
        db.session.commit()
        
        flash(f'Pipeline "{pipeline.name}" has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting pipeline: {str(e)}', 'danger')
        
    return redirect(url_for('pipeline.index'))

@pipeline_bp.route('/get-contact-tasks/<int:contact_id>', methods=['GET'])
@login_required
def get_contact_tasks(contact_id):
    """API endpoint to get active tasks for a contact in the pipeline."""
    try:
        contact = Contact.query.get_or_404(contact_id)
        
        # Determine if the Task model has person_id or contact_id
        inspector = inspect(Task)
        task_columns = [column.key for column in inspector.columns]
        
        # Build the filter based on available columns
        filters = []
        if 'person_id' in task_columns and contact.contact_type == 'person':
            filters.append(Task.person_id == contact.id)
        elif 'church_id' in task_columns and contact.contact_type == 'church':
            filters.append(Task.church_id == contact.id)
        elif 'contact_id' in task_columns:
            filters.append(Task.contact_id == contact.id)
        
        # Determine completion field
        completion_attr = 'completed'
        if 'is_completed' in task_columns:
            completion_attr = 'is_completed'
            
        # Get incomplete tasks related to this contact
        tasks = Task.query.filter(
            *filters
        ).filter(
            getattr(Task, completion_attr) == False
        ).all()
        
        task_data = [{
            'id': task.id,
            'title': task.title,
            'url': url_for('tasks.view', task_id=task.id)
        } for task in tasks]
        
        return jsonify({
            'success': True,
            'task_count': len(tasks),
            'tasks': task_data
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching tasks for contact {contact_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching tasks'
        })

@pipeline_bp.route('/get-contact-activity/<int:contact_id>')
@login_required
def get_contact_activity(contact_id):
    """API endpoint to get recent activity for a contact."""
    from flask import jsonify, current_app
    from sqlalchemy import inspect
    
    try:
        contact = Contact.query.get_or_404(contact_id)
        
        # Get the pipeline contact
        pipeline_contact = PipelineContact.query.filter_by(contact_id=contact_id).first()
        
        # Default to last 14 days
        since_date = datetime.utcnow() - timedelta(days=14)
        
        # Inspect models to determine available fields
        comm_inspector = inspect(Communication)
        comm_columns = [column.key for column in comm_inspector.columns]
        
        task_inspector = inspect(Task)
        task_columns = [column.key for column in task_inspector.columns]
        
        # Build filters for communications
        comm_filters = []
        if 'person_id' in comm_columns and contact.contact_type == 'person':
            comm_filters.append(Communication.person_id == contact.id)
        elif 'church_id' in comm_columns and contact.contact_type == 'church':
            comm_filters.append(Communication.church_id == contact.id)
        elif 'contact_id' in comm_columns:
            comm_filters.append(Communication.contact_id == contact.id)
        
        # Get recent communications
        communications = Communication.query.filter(
            *comm_filters
        ).filter(
            Communication.date >= since_date
        ).order_by(Communication.date.desc()).limit(5).all()
        
        # Build filters for tasks
        task_filters = []
        if 'person_id' in task_columns and contact.contact_type == 'person':
            task_filters.append(Task.person_id == contact.id)
        elif 'church_id' in task_columns and contact.contact_type == 'church':
            task_filters.append(Task.church_id == contact.id)
        elif 'contact_id' in task_columns:
            task_filters.append(Task.contact_id == contact.id)
            
        # Determine task completion field
        completion_attr = 'completed'
        if 'is_completed' in task_columns:
            completion_attr = 'is_completed'
        
        # Get recent tasks
        tasks = Task.query.filter(
            *task_filters
        ).filter(
            Task.created_at >= since_date
        ).order_by(Task.created_at.desc()).limit(5).all()
        
        # Get pipeline history if available
        pipeline_history = []
        if pipeline_contact:
            pipeline_history = PipelineStageHistory.query.filter_by(
                pipeline_contact_id=pipeline_contact.id
            ).order_by(PipelineStageHistory.moved_at.desc()).limit(5).all()
        
        # Combine all activities and sort by date
        activities = []
        
        # Add communications
        for comm in communications:
            activities.append({
                'type': 'communication',
                'date': comm.date,
                'description': f"{comm.type}: {comm.subject or 'No subject'}",
                'url': url_for('communications.view', communication_id=comm.id)
            })
        
        # Add tasks
        for task in tasks:
            activities.append({
                'type': 'task',
                'date': task.created_at,
                'description': f"Task created: {task.title}",
                'url': url_for('tasks.view', task_id=task.id)
            })
            
            # Add completion information if task is completed
            if getattr(task, completion_attr) and task.completed_at:
                activities.append({
                    'type': 'task_completed',
                    'date': task.completed_at,
                    'description': f"Task completed: {task.title}",
                    'url': url_for('tasks.view', task_id=task.id)
                })
        
        # Add pipeline movements
        for history in pipeline_history:
            from_stage = history.from_stage.name if history.from_stage else "Start"
            to_stage = history.to_stage.name if history.to_stage else "Unknown"
            
            activities.append({
                'type': 'pipeline_move',
                'date': history.moved_at,
                'description': f"Moved from {from_stage} to {to_stage}",
                'notes': history.notes
            })
        
        # Sort activities by date (newest first)
        activities.sort(key=lambda x: x['date'], reverse=True)
        
        # Convert dates to string format
        for activity in activities:
            activity['date'] = activity['date'].strftime('%Y-%m-%d %H:%M')
        
        return jsonify({
            'success': True,
            'activity_count': len(activities),
            'activities': activities[:10]  # Limit to most recent 10
        })
    except Exception as e:
        current_app.logger.error(f"Error getting activity for contact {contact_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        })

@pipeline_bp.route('/contact-details/<int:contact_id>')
@login_required
def contact_details(contact_id):
    """API endpoint to get details for a contact in the pipeline."""
    try:
        from flask import render_template
        pipeline_contact = PipelineContact.query.get_or_404(contact_id)
        contact = Contact.query.get_or_404(pipeline_contact.contact_id)
        
        # Get history for this contact in the pipeline
        history = PipelineStageHistory.query.filter_by(
            pipeline_contact_id=pipeline_contact.id
        ).order_by(PipelineStageHistory.moved_at.desc()).all()
        
        # Render the contact details template
        html = render_template(
            'pipeline/partials/contact_details.html',
            pipeline_contact=pipeline_contact,
            contact=contact,
            history=history
        )
        
        return jsonify({
            'success': True,
            'html': html
        })
    except Exception as e:
        current_app.logger.error(f"Error getting contact details for {contact_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        })

@pipeline_bp.route('/add_contact/<int:contact_id>', methods=['GET'])
@login_required
def add_contact_page(contact_id):
    """Show page for adding a contact to a pipeline."""
    contact_type = request.args.get('contact_type', 'person')
    contact = Contact.query.get_or_404(contact_id)
    
    # Verify the contact is accessible to the current user
    if not current_user.is_super_admin() and contact.office_id != current_user.office_id:
        flash('You do not have permission to add this contact to a pipeline', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get pipelines that don't already contain this contact
    existing_pipeline_ids = db.session.query(PipelineContact.pipeline_id).filter_by(contact_id=contact_id).all()
    existing_pipeline_ids = [p[0] for p in existing_pipeline_ids]
    
    # Get suitable pipelines based on contact type
    query = Pipeline.query
    
    # Filter by office unless super admin
    if not current_user.is_super_admin():
        query = query.filter_by(office_id=current_user.office_id)
    
    # Filter by pipeline type
    if contact_type == 'person':
        query = query.filter((Pipeline.pipeline_type == 'person') | (Pipeline.pipeline_type == 'both'))
    elif contact_type == 'church':
        query = query.filter((Pipeline.pipeline_type == 'church') | (Pipeline.pipeline_type == 'both'))
    
    # Exclude pipelines that already contain this contact
    if existing_pipeline_ids:
        query = query.filter(~Pipeline.id.in_(existing_pipeline_ids))
    
    # Get the contact's main pipeline stage (if any)
    main_pipeline_stage = None
    if contact_type == 'person':
        main_pipeline = Pipeline.get_main_pipeline('person')
    else:
        main_pipeline = Pipeline.get_main_pipeline('church')
    
    if main_pipeline:
        # Check if contact is in the main pipeline
        pipeline_contact = PipelineContact.query.filter_by(
            contact_id=contact_id,
            pipeline_id=main_pipeline.id
        ).first()
        
        if pipeline_contact and pipeline_contact.current_stage:
            main_pipeline_stage = pipeline_contact.current_stage.name
    
    # If we found a main pipeline stage, filter custom pipelines by that stage
    if main_pipeline_stage:
        # Include pipelines with matching parent_pipeline_stage or None (for backwards compatibility)
        query = query.filter(
            (Pipeline.parent_pipeline_stage == main_pipeline_stage) | 
            (Pipeline.parent_pipeline_stage == None)
        )
    
    # Get all matching pipelines
    pipelines = query.all()
    
    # Pass the contact and available pipelines to the template
    return render_template('pipeline/select_pipeline.html',
                         contact=contact,
                         pipelines=pipelines,
                         contact_type=contact_type)

@pipeline_bp.route('/view')
@login_required
def view_by_query():
    """View a pipeline using query parameters instead of path parameters"""
    pipeline_id = request.args.get('pipeline_id', type=int)
    if not pipeline_id:
        return jsonify({"error": "Pipeline ID is required"}), 400
    return pipeline_view(pipeline_id)

# Import the pipeline_bp from the controller
# All routes are defined in the controller 