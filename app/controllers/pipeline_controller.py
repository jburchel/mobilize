from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app
from flask_login import login_required, current_user
from app.models import Pipeline, PipelineStage, PipelineContact, PipelineStageHistory, Contact, Office
from app.extensions import db
from datetime import datetime
import json

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/pipeline')

@pipeline_bp.route('/')
@login_required
def index():
    """Show all pipelines."""
    # Get all custom (non-main) pipelines
    custom_pipelines = Pipeline.query.filter_by(is_main_pipeline=False).all()
    
    # Get main pipelines
    people_main_pipeline = Pipeline.get_main_pipeline('people')
    church_main_pipeline = Pipeline.get_main_pipeline('church')
    
    return render_template('pipeline/index.html', 
                          custom_pipelines=custom_pipelines,
                          people_main_pipeline=people_main_pipeline,
                          church_main_pipeline=church_main_pipeline)

@pipeline_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new pipeline."""
    from app.models import Office
    
    # Get all offices for the dropdown
    offices = Office.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        pipeline_type = request.form.get('pipeline_type', 'people')
        office_id = request.form.get('office_id')
        parent_pipeline_stage = request.form.get('parent_pipeline_stage')
        
        # Validate form data
        if not name or not office_id:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('pipeline.create'))
        
        pipeline = Pipeline(
            name=name,
            description=description,
            pipeline_type=pipeline_type,
            office_id=office_id,
            parent_pipeline_stage=parent_pipeline_stage,
            is_main_pipeline=False  # User-created pipelines are never main pipelines
        )
        
        db.session.add(pipeline)
        db.session.commit()
        
        flash('Pipeline created successfully', 'success')
        return redirect(url_for('pipeline.manage_stages', pipeline_id=pipeline.id))
    
    # For GET requests
    pipeline_type = request.args.get('type', 'people')
    
    # Get the parent pipeline stages for this type
    temp_pipeline = Pipeline(pipeline_type=pipeline_type)
    parent_stages = temp_pipeline.get_available_parent_stages()
    
    return render_template('pipeline/create.html', 
                          offices=offices,
                          pipeline_type=pipeline_type,
                          parent_stages=parent_stages)

@pipeline_bp.route('/<int:pipeline_id>')
@login_required
def view(pipeline_id):
    """View pipeline and its stages with contacts."""
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    stages = pipeline.stages.filter_by(is_active=True).order_by(PipelineStage.order).all()
    
    # For each stage, get contacts currently in that stage
    stage_contacts = {}
    for stage in stages:
        pipeline_contacts = PipelineContact.query.filter_by(
            pipeline_id=pipeline_id, current_stage_id=stage.id
        ).all()
        
        contacts_data = []
        for pc in pipeline_contacts:
            contact = Contact.query.get(pc.contact_id)
            if contact:
                # Get last history item for this contact in this pipeline
                last_movement = PipelineStageHistory.query.filter_by(
                    pipeline_contact_id=pc.id
                ).order_by(PipelineStageHistory.moved_at.desc()).first()
                
                contacts_data.append({
                    'contact': contact,
                    'pipeline_contact': pc,
                    'days_in_stage': (datetime.utcnow() - pc.last_updated).days,
                    'last_movement': last_movement
                })
        
        stage_contacts[stage.id] = contacts_data
    
    return render_template('pipeline/view.html', 
                          pipeline=pipeline, 
                          stages=stages, 
                          contacts_by_stage=stage_contacts,
                          pipeline_type=pipeline.pipeline_type)

@pipeline_bp.route('/<int:pipeline_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(pipeline_id):
    """Edit an existing pipeline."""
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    
    # Don't allow editing of main pipelines
    if pipeline.is_main_pipeline:
        flash('System pipelines cannot be edited', 'warning')
        return redirect(url_for('pipeline.index'))
    
    from app.models import Office
    offices = Office.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        office_id = request.form.get('office_id')
        is_active = request.form.get('is_active') == 'on'
        parent_pipeline_stage = request.form.get('parent_pipeline_stage')
        
        # Validate form data
        if not name or not office_id:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('pipeline.edit', pipeline_id=pipeline_id))
        
        # Update pipeline
        pipeline.name = name
        pipeline.description = description
        pipeline.office_id = office_id
        pipeline.is_active = is_active
        pipeline.parent_pipeline_stage = parent_pipeline_stage
        pipeline.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Pipeline updated successfully', 'success')
        return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
    
    # For GET requests
    parent_stages = pipeline.get_available_parent_stages()
    
    return render_template('pipeline/edit.html', 
                          pipeline=pipeline,
                          offices=offices,
                          parent_stages=parent_stages)

@pipeline_bp.route('/<int:pipeline_id>/stages', methods=['GET', 'POST'])
@login_required
def manage_stages(pipeline_id):
    """Manage stages for a pipeline."""
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    
    # If this is a main pipeline, only super admins can edit it
    if pipeline.is_main_pipeline and not current_user.is_super_admin():
        flash('Only super administrators can edit system pipeline stages', 'warning')
        return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
    
    if request.method == 'POST':
        try:
            # Get the stages data from the form
            stages_data_str = request.form.get('stages_data', '[]')
            
            # Log the received data for debugging
            current_app.logger.debug(f"Received stages_data: {stages_data_str}")
            
            # Parse the JSON data - handle empty strings safely
            if not stages_data_str or stages_data_str.isspace() or stages_data_str == '':
                stages_data = []
            else:
                try:
                    stages_data = json.loads(stages_data_str)
                except json.JSONDecodeError:
                    current_app.logger.error(f"Invalid JSON data: {stages_data_str}")
                    flash('Invalid stage data format. Please try again.', 'danger')
                    stages = pipeline.get_active_stages()
                    return render_template('pipeline/edit_stages.html', 
                                          pipeline=pipeline,
                                          stages=stages,
                                          page_title=f"Manage Stages - {pipeline.name}")
            
            # Process the submitted stage data
            for stage_data in stages_data:
                stage_id = stage_data.get('id')
                
                # Check if this is a new stage (id starts with 'new_')
                if stage_id and str(stage_id).startswith('new_'):
                    # Create a new stage
                    new_stage = PipelineStage(
                        pipeline_id=pipeline_id,
                        name=stage_data.get('name', 'New Stage'),
                        order=stage_data.get('order', 1),
                        color=stage_data.get('color', '#3498db'),
                        description=stage_data.get('description', ''),
                        is_active=True
                    )
                    db.session.add(new_stage)
                elif stage_id:  # Existing stage
                    stage = PipelineStage.query.get(stage_id)
                    if stage and stage.pipeline_id == pipeline_id:
                        stage.name = stage_data.get('name', stage.name)
                        stage.order = stage_data.get('order', stage.order)
                        stage.color = stage_data.get('color', stage.color)
                        stage.description = stage_data.get('description', stage.description)
                        
                        # Update automation fields if present
                        if 'auto_move_days' in stage_data:
                            stage.auto_move_days = stage_data.get('auto_move_days')
                        if 'auto_reminder' in stage_data:
                            stage.auto_reminder = stage_data.get('auto_reminder')
                        if 'auto_task_template' in stage_data:
                            stage.auto_task_template = stage_data.get('auto_task_template')
                else:  # New stage without ID
                    new_stage = PipelineStage(
                        pipeline_id=pipeline_id,
                        name=stage_data.get('name', 'New Stage'),
                        order=stage_data.get('order', 1),
                        color=stage_data.get('color', '#3498db'),
                        description=stage_data.get('description', ''),
                        is_active=True
                    )
                    db.session.add(new_stage)
            
            db.session.commit()
            flash('Pipeline stages updated successfully', 'success')
            return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating pipeline stages: {str(e)}")
            flash(f'There was an error processing the stage data: {str(e)}', 'danger')
            # Continue to render the template with existing data
    
    # Get active stages for this pipeline
    stages = pipeline.get_active_stages()
    
    return render_template('pipeline/edit_stages.html', 
                          pipeline=pipeline,
                          stages=stages,
                          page_title=f"Manage Stages - {pipeline.name}")

@pipeline_bp.route('/<int:pipeline_id>/add_contact', methods=['GET', 'POST'])
@login_required
def add_contact(pipeline_id):
    """Add a contact to a pipeline."""
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    stages = pipeline.get_active_stages()  # Get all active stages for this pipeline
    
    if request.method == 'POST':
        contact_ids = request.form.getlist('contact_ids')
        stage_id = request.form.get('stage_id')
        
        if not contact_ids:
            flash('Please select at least one contact', 'warning')
            return redirect(url_for('pipeline.add_contact', pipeline_id=pipeline_id))
            
        if not stage_id:
            flash('Please select a stage', 'warning')
            return redirect(url_for('pipeline.add_contact', pipeline_id=pipeline_id))
        
        for contact_id in contact_ids:
            # Check if contact is already in pipeline
            existing = PipelineContact.query.filter_by(
                pipeline_id=pipeline_id, 
                contact_id=contact_id
            ).first()
            
            if not existing:
                # Add contact to pipeline
                pipeline_contact = PipelineContact(
                    pipeline_id=pipeline_id,
                    contact_id=contact_id,
                    current_stage_id=stage_id,
                    entered_at=datetime.utcnow()
                )
                db.session.add(pipeline_contact)
                
                # Create initial stage history
                history = PipelineStageHistory(
                    pipeline_contact=pipeline_contact,
                    to_stage_id=stage_id,
                    moved_by_user_id=current_user.id if current_user.is_authenticated else None,
                    notes="Initial stage"
                )
                db.session.add(history)
        
        db.session.commit()
        flash(f'{len(contact_ids)} contacts added to the pipeline', 'success')
            
        return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
    
    # Get search parameters
    search_query = request.args.get('search', '')
    contact_type = request.args.get('type', 'all')
    
    # Get contacts not already in this pipeline
    subquery = db.session.query(PipelineContact.contact_id).filter_by(pipeline_id=pipeline_id).subquery()
    
    # Base query for contacts not in the pipeline
    from app.models import Contact, Person, Church
    base_query = Contact.query.filter(Contact.id.notin_(subquery))
    
    # Apply search if provided
    if search_query:
        search_term = f"%{search_query}%"
        base_query = base_query.filter(
            db.or_(
                Contact.first_name.ilike(search_term),
                Contact.last_name.ilike(search_term),
                Contact.email.ilike(search_term),
                Contact.phone.ilike(search_term)
            )
        )
    
    # Filter by type based on pipeline_type and request parameter
    if pipeline.pipeline_type == 'people' or contact_type == 'person':
        people = Person.query.filter(Person.id.in_([c.id for c in base_query.filter_by(type='person')]))
        churches = []
    elif pipeline.pipeline_type == 'church' or contact_type == 'church':
        people = []
        churches = Church.query.filter(Church.id.in_([c.id for c in base_query.filter_by(type='church')]))
    else:
        people = Person.query.filter(Person.id.in_([c.id for c in base_query.filter_by(type='person')]))
        churches = Church.query.filter(Church.id.in_([c.id for c in base_query.filter_by(type='church')]))
    
    return render_template('pipeline/add_contact.html', 
                          pipeline=pipeline,
                          stages=stages,
                          people=people,
                          churches=churches,
                          search_query=search_query,
                          contact_type=contact_type,
                          page_title=f"Add Contacts to {pipeline.name}")

@pipeline_bp.route('/contact/<int:pipeline_contact_id>/move', methods=['POST'])
@login_required
def move_contact(pipeline_contact_id):
    """Move a contact to a different stage."""
    pipeline_contact = PipelineContact.query.get_or_404(pipeline_contact_id)
    
    stage_id = request.form.get('stage_id')
    notes = request.form.get('notes', '')
    
    if not stage_id:
        return jsonify({'success': False, 'message': 'Stage ID is required'}), 400
    
    try:
        history = pipeline_contact.move_to_stage(
            stage_id=int(stage_id),
            user_id=current_user.id,
            notes=notes
        )
        
        return jsonify({
            'success': True, 
            'message': 'Contact moved successfully',
            'history_id': history.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@pipeline_bp.route('/contact/<int:pipeline_contact_id>/remove', methods=['POST'])
@login_required
def remove_contact(pipeline_contact_id):
    """Remove a contact from a pipeline."""
    pipeline_contact = PipelineContact.query.get_or_404(pipeline_contact_id)
    pipeline_id = pipeline_contact.pipeline_id
    
    try:
        # Delete associated history records
        PipelineStageHistory.query.filter_by(pipeline_contact_id=pipeline_contact_id).delete()
        
        # Delete the pipeline contact
        db.session.delete(pipeline_contact)
        db.session.commit()
        
        flash('Contact removed from pipeline successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing contact: {str(e)}', 'danger')
    
    return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))

@pipeline_bp.route('/<int:pipeline_id>/history')
@login_required
def history(pipeline_id):
    """View pipeline history for all contacts or a specific contact."""
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    pipeline_contact_id = request.args.get('pipeline_contact_id', type=int)
    
    if pipeline_contact_id:
        # Get history for specific contact
        pipeline_contact = PipelineContact.query.get_or_404(pipeline_contact_id)
        if pipeline_contact.pipeline_id != pipeline_id:
            flash('Invalid contact for this pipeline', 'danger')
            return redirect(url_for('pipeline.history', pipeline_id=pipeline_id))
        
        contact = Contact.query.get(pipeline_contact.contact_id)
        history_items = PipelineStageHistory.query.filter_by(
            pipeline_contact_id=pipeline_contact_id
        ).order_by(PipelineStageHistory.moved_at.desc()).all()
        
        return render_template('pipeline/contact_history.html',
                              pipeline=pipeline,
                              contact=contact,
                              pipeline_contact=pipeline_contact,
                              history_items=history_items,
                              page_title=f"Contact History - {contact.get_name()}")
    else:
        # Get history for all contacts in pipeline
        history_items = PipelineStageHistory.query.join(
            PipelineContact, PipelineStageHistory.pipeline_contact_id == PipelineContact.id
        ).filter(
            PipelineContact.pipeline_id == pipeline_id
        ).order_by(PipelineStageHistory.moved_at.desc()).limit(100).all()
        
        return render_template('pipeline/history.html',
                              pipeline=pipeline,
                              history_items=history_items,
                              page_title=f"Pipeline History - {pipeline.name}")

@pipeline_bp.route('/api/pipeline/<int:pipeline_id>/contacts')
@login_required
def api_pipeline_contacts(pipeline_id):
    """API endpoint to get all contacts in a pipeline with their stages."""
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    
    pipeline_contacts = PipelineContact.query.filter_by(pipeline_id=pipeline_id).all()
    
    result = []
    for pc in pipeline_contacts:
        contact = Contact.query.get(pc.contact_id)
        if contact:
            stage = PipelineStage.query.get(pc.current_stage_id)
            result.append({
                'pipeline_contact_id': pc.id,
                'contact_id': contact.id,
                'contact_name': f"{contact.first_name} {contact.last_name}",
                'stage_id': pc.current_stage_id,
                'stage_name': stage.name if stage else 'Unknown',
                'stage_color': stage.color if stage else '#cccccc',
                'days_in_stage': (datetime.utcnow() - pc.last_updated).days,
                'entered_at': pc.entered_at.isoformat() if pc.entered_at else None,
                'last_updated': pc.last_updated.isoformat() if pc.last_updated else None
            })
    
    return jsonify(result)

@pipeline_bp.route('/<int:pipeline_id>/delete', methods=['POST'])
@login_required
def delete(pipeline_id):
    """Delete a pipeline and all its stages."""
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    
    # Cannot delete main pipelines
    if pipeline.is_main_pipeline:
        flash('System pipelines cannot be deleted', 'danger')
        return redirect(url_for('pipeline.index'))
    
    # Check if user has permission to delete the pipeline
    # Only office admins or super admins can delete pipelines
    if not (current_user.is_super_admin() or 
            (pipeline.office and current_user.is_office_admin(pipeline.office_id))):
        flash('You do not have permission to delete this pipeline', 'danger')
        return redirect(url_for('pipeline.index'))
    
    try:
        # First, delete any pipeline contacts
        PipelineContact.query.filter_by(pipeline_id=pipeline_id).delete()
        
        # Then delete all stages
        PipelineStage.query.filter_by(pipeline_id=pipeline_id).delete()
        
        # Finally delete the pipeline itself
        db.session.delete(pipeline)
        db.session.commit()
        
        flash(f'Pipeline "{pipeline.name}" has been deleted', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting pipeline: {str(e)}")
        flash('An error occurred while deleting the pipeline', 'danger')
    
    return redirect(url_for('pipeline.index'))

@pipeline_bp.route('/update', methods=['POST'])
@login_required
def update_pipeline():
    """Update a pipeline's details from the modal form."""
    try:
        pipeline_id = request.form.get('pipeline_id')
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not pipeline_id or not name:
            flash('Pipeline ID and name are required.', 'danger')
            return redirect(url_for('pipeline.index'))
        
        pipeline = Pipeline.query.get(pipeline_id)
        if not pipeline:
            flash('Pipeline not found.', 'danger')
            return redirect(url_for('pipeline.index'))
        
        # Check permissions - only owner, office admin, or super admin can edit
        if not (current_user.is_super_admin() or 
                (pipeline.office and current_user.is_office_admin(pipeline.office_id)) or
                pipeline.created_by_id == current_user.id):
            flash('You do not have permission to edit this pipeline.', 'danger')
            return redirect(url_for('pipeline.index'))
        
        # Update pipeline details
        pipeline.name = name
        pipeline.description = description
        
        db.session.commit()
        flash('Pipeline updated successfully.', 'success')
        
        return redirect(url_for('pipeline.index'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error editing pipeline: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('pipeline.index')) 