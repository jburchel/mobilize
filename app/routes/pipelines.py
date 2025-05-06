from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models.pipeline import PipelineStage
from app.models.pipeline_contact import PipelineContact
from app.models.base import Contact
from app.utils.decorators import office_required
from app.controllers.pipeline_controller import PipelineController
from app.controllers.pipeline_guard import PipelineGuard
import json

pipelines_bp = Blueprint('pipelines', __name__)

@pipelines_bp.route('/pipelines')
@login_required
@office_required
def index():
    """List all pipelines for the current user."""
    pipelines = PipelineController.get_pipelines_for_current_user()
    return render_template('pipelines/index.html', pipelines=pipelines)

@pipelines_bp.route('/pipelines/new', methods=['GET', 'POST'])
@login_required
@office_required
def create():
    """Create a new pipeline."""
    if request.method == 'POST':
        name = request.form.get('name')
        pipeline_type = request.form.get('pipeline_type')
        description = request.form.get('description')
        
        if not name or not pipeline_type:
            flash('Name and type are required', 'danger')
            return redirect(url_for('pipelines.create'))
        
        pipeline = PipelineController.create_pipeline(name, pipeline_type, description)
        
        # Create default stages
        default_stages = [
            {'name': 'Initial Contact', 'order': 1},
            {'name': 'Meeting Scheduled', 'order': 2},
            {'name': 'Meeting Completed', 'order': 3},
            {'name': 'Proposal Sent', 'order': 4},
            {'name': 'Closed - Won', 'order': 5},
            {'name': 'Closed - Lost', 'order': 6}
        ]
        
        for stage in default_stages:
            PipelineController.create_pipeline_stage(
                pipeline.id, 
                stage['name'], 
                order=stage['order']
            )
        
        flash('Pipeline created successfully', 'success')
        return redirect(url_for('pipelines.show', id=pipeline.id))
    
    return render_template('pipelines/new.html')

@pipelines_bp.route('/pipelines/<int:id>')
@login_required
@office_required
def show(id):
    """Show details of a specific pipeline."""
    pipeline = PipelineController.get_pipeline_by_id(id)
    
    if not pipeline:
        flash('Pipeline not found or you do not have access', 'danger')
        return redirect(url_for('pipelines.index'))
    
    stages = PipelineController.get_pipeline_stages(id)
    
    # Get contacts for each stage
    for stage in stages:
        stage.contacts = PipelineContact.query.filter_by(
            pipeline_id=id, 
            stage_id=stage.id
        ).all()
        
        # Load contact details for each pipeline contact
        for pipeline_contact in stage.contacts:
            pipeline_contact.contact = Contact.query.get(pipeline_contact.contact_id)
    
    return render_template('pipelines/show.html', pipeline=pipeline, stages=stages)

@pipelines_bp.route('/pipelines/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@office_required
def edit(id):
    """Edit a pipeline."""
    # Check if this is a main pipeline (which cannot be modified)
    can_modify, response = PipelineGuard.can_modify_pipeline(id)
    if not can_modify:
        return response
        
    pipeline = PipelineController.get_pipeline_by_id(id)
    
    if not pipeline:
        flash('Pipeline not found or you do not have access', 'danger')
        return redirect(url_for('pipelines.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        pipeline_type = request.form.get('pipeline_type')
        description = request.form.get('description')
        
        if not name or not pipeline_type:
            flash('Name and type are required', 'danger')
            return redirect(url_for('pipelines.edit', id=id))
        
        PipelineController.update_pipeline(id, name, pipeline_type, description)
        flash('Pipeline updated successfully', 'success')
        return redirect(url_for('pipelines.show', id=id))
    
    return render_template('pipelines/edit.html', pipeline=pipeline)

@pipelines_bp.route('/pipelines/<int:id>/delete', methods=['POST'])
@login_required
@office_required
def delete(id):
    """Delete a pipeline."""
    # Check if this is a main pipeline (which cannot be deleted)
    can_delete, response = PipelineGuard.can_delete_pipeline(id)
    if not can_delete:
        return response
        
    if PipelineController.delete_pipeline(id):
        flash('Pipeline deleted successfully', 'success')
    else:
        flash('Failed to delete pipeline', 'danger')
    
    return redirect(url_for('pipelines.index'))

@pipelines_bp.route('/pipelines/<int:id>/stages/new', methods=['GET', 'POST'])
@login_required
@office_required
def create_stage(id):
    """Create a new stage for a pipeline."""
    # Check if this is a main pipeline (which cannot be modified)
    can_modify, response = PipelineGuard.can_modify_pipeline(id)
    if not can_modify:
        return response
        
    pipeline = PipelineController.get_pipeline_by_id(id)
    
    if not pipeline:
        flash('Pipeline not found or you do not have access', 'danger')
        return redirect(url_for('pipelines.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Stage name is required', 'danger')
            return redirect(url_for('pipelines.create_stage', id=id))
        
        stage = PipelineController.create_pipeline_stage(id, name, description)
        if stage:
            flash('Stage created successfully', 'success')
        else:
            flash('Failed to create stage', 'danger')
        
        return redirect(url_for('pipelines.show', id=id))
    
    return render_template('pipelines/new_stage.html', pipeline=pipeline)

@pipelines_bp.route('/pipelines/stages/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@office_required
def edit_stage(id):
    """Edit a pipeline stage."""
    stage = PipelineController.get_pipeline_stage_by_id(id)
    if not stage:
        flash('Stage not found', 'danger')
        return redirect(url_for('pipelines.index'))
    
    # Check if this is a main pipeline (which cannot be modified)
    can_modify, response = PipelineGuard.can_modify_pipeline(stage.pipeline_id)
    if not can_modify:
        return response
    
    pipeline = PipelineController.get_pipeline_by_id(stage.pipeline_id)
    if not pipeline:
        flash('Pipeline not found or you do not have access', 'danger')
        return redirect(url_for('pipelines.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Stage name is required', 'danger')
            return redirect(url_for('pipelines.edit_stage', id=id))
        
        PipelineController.update_pipeline_stage(id, name, description)
        flash('Stage updated successfully', 'success')
        return redirect(url_for('pipelines.show', id=pipeline.id))
    
    return render_template('pipelines/edit_stage.html', pipeline=pipeline, stage=stage)

@pipelines_bp.route('/pipelines/stages/<int:id>/delete', methods=['POST'])
@login_required
@office_required
def delete_stage(id):
    """Delete a pipeline stage."""
    stage = PipelineController.get_pipeline_stage_by_id(id)
    if not stage:
        flash('Stage not found', 'danger')
        return redirect(url_for('pipelines.index'))
    
    pipeline_id = stage.pipeline_id
    
    pipeline = PipelineController.get_pipeline_by_id(pipeline_id)
    if not pipeline:
        flash('Pipeline not found or you do not have access', 'danger')
        return redirect(url_for('pipelines.index'))
    
    if PipelineController.delete_pipeline_stage(id):
        flash('Stage deleted successfully', 'success')
    else:
        flash('Failed to delete stage', 'danger')
    
    return redirect(url_for('pipelines.show', id=pipeline_id))

@pipelines_bp.route('/pipelines/<int:id>/reorder-stages', methods=['POST'])
@login_required
@office_required
def reorder_stages(id):
    """Reorder pipeline stages."""
    pipeline = PipelineController.get_pipeline_by_id(id)
    if not pipeline:
        return jsonify({'success': False, 'message': 'Pipeline not found or you do not have access'})
    
    try:
        stage_order = json.loads(request.form.get('order', '[]'))
        if not stage_order:
            return jsonify({'success': False, 'message': 'No stage order provided'})
        
        if PipelineController.reorder_pipeline_stages(id, stage_order):
            return jsonify({'success': True, 'message': 'Stages reordered successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to reorder stages'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@pipelines_bp.route('/pipelines/<int:id>/contacts')
@login_required
@office_required
def pipeline_contacts(id):
    """List contacts in a pipeline."""
    pipeline = PipelineController.get_pipeline_by_id(id)
    if not pipeline:
        flash('Pipeline not found or you do not have access', 'danger')
        return redirect(url_for('pipelines.index'))
    
    stage_id = request.args.get('stage_id', type=int)
    contacts = PipelineController.get_pipeline_contacts(id, stage_id)
    
    # Load contact details for each pipeline contact
    for pipeline_contact in contacts:
        pipeline_contact.contact = Contact.query.get(pipeline_contact.contact_id)
        pipeline_contact.stage = PipelineStage.query.get(pipeline_contact.stage_id)
    
    stages = PipelineController.get_pipeline_stages(id)
    
    return render_template(
        'pipelines/contacts.html',
        pipeline=pipeline,
        contacts=contacts,
        stages=stages,
        current_stage_id=stage_id
    )

@pipelines_bp.route('/pipelines/<int:id>/contacts/add', methods=['GET', 'POST'])
@login_required
@office_required
def add_contact(id):
    """Add a contact to a pipeline."""
    pipeline = PipelineController.get_pipeline_by_id(id)
    if not pipeline:
        flash('Pipeline not found or you do not have access', 'danger')
        return redirect(url_for('pipelines.index'))
    
    stages = PipelineController.get_pipeline_stages(id)
    if not stages:
        flash('This pipeline has no stages. Please add stages first.', 'warning')
        return redirect(url_for('pipelines.show', id=id))
    
    people, churches = PipelineController.get_available_contacts_for_pipeline(id)
    
    if request.method == 'POST':
        contact_id = request.form.get('contact_id', type=int)
        stage_id = request.form.get('stage_id', type=int)
        notes = request.form.get('notes')
        
        if not contact_id or not stage_id:
            flash('Contact and stage are required', 'danger')
            return redirect(url_for('pipelines.add_contact', id=id))
        
        pipeline_contact = PipelineController.add_contact_to_pipeline(id, contact_id, stage_id, notes)
        if pipeline_contact:
            flash('Contact added to pipeline successfully', 'success')
            return redirect(url_for('pipelines.pipeline_contacts', id=id))
        else:
            flash('Failed to add contact to pipeline', 'danger')
    
    return render_template(
        'pipelines/add_contact.html',
        pipeline=pipeline,
        stages=stages,
        people=people,
        churches=churches
    )

@pipelines_bp.route('/pipelines/contacts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@office_required
def edit_contact(id):
    """Edit a pipeline contact."""
    pipeline_contact = PipelineController.get_pipeline_contact_by_id(id)
    if not pipeline_contact:
        flash('Contact not found in the pipeline', 'danger')
        return redirect(url_for('pipelines.index'))
    
    pipeline = PipelineController.get_pipeline_by_id(pipeline_contact.pipeline_id)
    if not pipeline:
        flash('Pipeline not found or you do not have access', 'danger')
        return redirect(url_for('pipelines.index'))
    
    stages = PipelineController.get_pipeline_stages(pipeline.id)
    contact = Contact.query.get(pipeline_contact.contact_id)
    
    if request.method == 'POST':
        stage_id = request.form.get('stage_id', type=int)
        notes = request.form.get('notes')
        
        if not stage_id:
            flash('Stage is required', 'danger')
            return redirect(url_for('pipelines.edit_contact', id=id))
        
        updated_contact = PipelineController.update_pipeline_contact(id, stage_id, notes)
        if updated_contact:
            flash('Pipeline contact updated successfully', 'success')
            return redirect(url_for('pipelines.pipeline_contacts', id=pipeline.id))
        else:
            flash('Failed to update pipeline contact', 'danger')
    
    return render_template(
        'pipelines/edit_contact.html',
        pipeline=pipeline,
        stages=stages,
        pipeline_contact=pipeline_contact,
        contact=contact
    )

@pipelines_bp.route('/pipelines/contacts/<int:id>/delete', methods=['POST'])
@login_required
@office_required
def delete_contact(id):
    """Remove a contact from a pipeline."""
    pipeline_contact = PipelineController.get_pipeline_contact_by_id(id)
    if not pipeline_contact:
        flash('Contact not found in the pipeline', 'danger')
        return redirect(url_for('pipelines.index'))
    
    pipeline_id = pipeline_contact.pipeline_id
    
    if PipelineController.remove_contact_from_pipeline(id):
        flash('Contact removed from pipeline successfully', 'success')
    else:
        flash('Failed to remove contact from pipeline', 'danger')
    
    return redirect(url_for('pipelines.pipeline_contacts', id=pipeline_id)) 