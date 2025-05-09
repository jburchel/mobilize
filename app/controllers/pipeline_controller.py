from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Pipeline, PipelineStage, PipelineContact, PipelineStageHistory, Contact
from app.models.person import Person
from app.models.church import Church
from app.models.office import Office
from app.extensions import db
from datetime import datetime
import json
from sqlalchemy import inspect
from flask_wtf.csrf import generate_csrf
from sqlalchemy.orm import selectinload
from sqlalchemy import desc
from sqlalchemy import or_

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/pipeline')

@pipeline_bp.route('/')
@login_required
def index():
    """Show all pipelines."""
    # Get all custom (non-main) pipelines
    custom_pipelines = Pipeline.query.filter_by(is_main_pipeline=False).all()
    
    # Get main pipelines
    # Main people pipeline may use 'person' or 'people' type
    people_main_pipeline = Pipeline.query.filter(
        Pipeline.is_main_pipeline==True,
        Pipeline.pipeline_type.in_(['person','people'])
    ).first()
    
    if not people_main_pipeline:
        people_main_pipeline = Pipeline.query.filter(
            Pipeline.pipeline_type.in_(['person','people'])
        ).first()
        
    church_main_pipeline = Pipeline.query.filter_by(is_main_pipeline=True, pipeline_type='church').first()
    if not church_main_pipeline:
        church_main_pipeline = Pipeline.query.filter_by(pipeline_type='church').first()
    
    # Debug log the pipeline contact counts
    if people_main_pipeline:
        people_count = db.session.execute(
            db.text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
            {"pipeline_id": people_main_pipeline.id}
        ).scalar() or 0
        current_app.logger.info(f"People main pipeline ID: {people_main_pipeline.id}, Contact count (SQL): {people_count}")
        model_count = people_main_pipeline.count_contacts()
        current_app.logger.info(f"People main pipeline contact count (model method): {model_count}")
        
        # Force a refresh of count data
        db.session.refresh(people_main_pipeline)
    
    if church_main_pipeline:
        church_count = db.session.execute(
            db.text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
            {"pipeline_id": church_main_pipeline.id}
        ).scalar() or 0
        current_app.logger.info(f"Church main pipeline ID: {church_main_pipeline.id}, Contact count (SQL): {church_count}")
        model_count = church_main_pipeline.count_contacts()
        current_app.logger.info(f"Church main pipeline contact count (model method): {model_count}")
        
        # Force a refresh of count data
        db.session.refresh(church_main_pipeline)
    
    # Log all pipelines with their counts
    pipelines = Pipeline.query.all()
    for p in pipelines:
        count = db.session.execute(
            db.text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
            {"pipeline_id": p.id}
        ).scalar() or 0
        current_app.logger.info(f"Pipeline ID: {p.id}, Name: {p.name}, Count SQL: {count}, Count Method: {p.count_contacts()}")
    
    return render_template('pipeline/index.html', 
                          custom_pipelines=custom_pipelines,
                          people_main_pipeline=people_main_pipeline,
                          church_main_pipeline=church_main_pipeline)

@pipeline_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new pipeline."""
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
def view(pipeline_id, use_optimized_queries=False):
    """View a pipeline with all its stages and contacts."""
    import time
    start_time = time.time()
    
    try:
        # Use request-level caching for pipeline data
        cache_key = f"pipeline_{pipeline_id}"
        if hasattr(current_app, 'request_cache') and cache_key in current_app.request_cache:
            pipeline = current_app.request_cache[cache_key]
            current_app.logger.info(f"Using cached pipeline data for {pipeline_id}")
        else:
            # Use get_or_404 with eager loading to reduce queries
            from sqlalchemy.orm import joinedload
            pipeline = Pipeline.query.options(
                joinedload(Pipeline.stages)  # Eager load stages
            ).get_or_404(pipeline_id)
            
            # Store in request cache
            if not hasattr(current_app, 'request_cache'):
                current_app.request_cache = {}
            current_app.request_cache[cache_key] = pipeline
        
        # Check if user has permission to view this pipeline
        if not current_user.is_super_admin() and pipeline.office_id != current_user.office_id:
            flash('You do not have permission to view this pipeline', 'danger')
            return redirect(url_for('pipeline.index'))
        
        # Check if we're adding a contact to this pipeline
        contact_id = request.args.get('contact_id', type=int)
        contact_type = request.args.get('contact_type')
        
        if contact_id and contact_type:
            # Get the contact
            contact = Contact.query.get_or_404(contact_id)
            
            # Check contact type compatibility with pipeline
            contact_model_type = getattr(contact, 'type', None) or getattr(contact, 'contact_type', None)
            
            if pipeline.pipeline_type not in ['both', 'person', 'people'] and pipeline.pipeline_type != contact_model_type:
                flash(f'Cannot add {contact_type} to a {pipeline.pipeline_type} pipeline', 'danger')
                return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
            
            # Check if contact is already in pipeline
            existing = PipelineContact.query.filter_by(
                pipeline_id=pipeline_id,
                contact_id=contact_id
            ).first()
            
            if existing:
                flash('Contact is already in this pipeline', 'warning')
                return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
            
            # Get the first stage in the pipeline
            first_stage = PipelineStage.query.filter_by(
                pipeline_id=pipeline_id
            ).order_by(PipelineStage.order).first()
            
            if not first_stage:
                flash('Pipeline has no stages to add contact to', 'danger')
                return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
            
            # Add the contact to the pipeline
            pipeline_contact = PipelineContact(
                pipeline_id=pipeline_id,
                contact_id=contact_id,
                current_stage_id=first_stage.id,
                entered_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            db.session.add(pipeline_contact)
            db.session.commit()  # Commit immediately to get the pipeline_contact.id
            
            # Add history entry
            history = PipelineStageHistory(
                pipeline_contact_id=pipeline_contact.id,
                to_stage_id=first_stage.id,
                created_by_id=current_user.id,
                notes="Initial pipeline stage",
                created_at=datetime.now()
            )
            
            db.session.add(history)
            db.session.commit()
            
            # Success message
            flash(f'Contact added to pipeline in {first_stage.name} stage', 'success')
        
        # Get stages - use the eager loaded stages if available
        if hasattr(pipeline, 'stages') and pipeline.stages:
            stages = sorted(pipeline.stages, key=lambda s: s.order)
        else:
            # Fallback to database query if needed
            stages = PipelineStage.query.filter_by(pipeline_id=pipeline_id).order_by(PipelineStage.order).all()
        
        # Get pipeline contacts with optimized query
        contact_query_time = time.time()
        
        # Use optimized query approach based on flag
        if use_optimized_queries:
            # Use a direct SQL query for maximum performance
            # This is much faster than the ORM for this specific use case
            from sqlalchemy import text
            
            sql_query = """
                SELECT pc.id, pc.contact_id, pc.current_stage_id, pc.entered_at, pc.last_updated,
                       c.type as contact_type, c.name as contact_name,
                       CASE c.type 
                           WHEN 'person' THEN p.first_name || ' ' || p.last_name
                           WHEN 'church' THEN ch.name
                           ELSE c.name
                       END as display_name
                FROM pipeline_contacts pc
                JOIN contacts c ON pc.contact_id = c.id
                LEFT JOIN people p ON c.id = p.id AND c.type = 'person'
                LEFT JOIN churches ch ON c.id = ch.id AND c.type = 'church'
                WHERE pc.pipeline_id = :pipeline_id
            """
            
            # Add user role filters if needed
            if not current_user.is_super_admin():
                if pipeline.pipeline_type in ['person', 'people']:
                    sql_query += " AND p.office_id = :office_id"
                    if current_user.role != 'office_admin':
                        sql_query += " AND p.assigned_to_id = :user_id"
                elif pipeline.pipeline_type == 'church':
                    sql_query += " AND ch.office_id = :office_id"
                    if current_user.role != 'office_admin':
                        sql_query += " AND ch.assigned_to_id = :user_id"
            
            # Prepare parameters
            params = {"pipeline_id": pipeline_id}
            if not current_user.is_super_admin():
                params["office_id"] = current_user.office_id
                if current_user.role != 'office_admin':
                    params["user_id"] = current_user.id
            
            # Execute the query
            result = db.session.execute(text(sql_query), params)
            
            # Get total count for debugging
            sql_count = "SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"
            total_contacts = db.session.execute(text(sql_count), {"pipeline_id": pipeline_id}).scalar() or 0
            
            # Organize contacts by stage
            contacts_by_stage = {stage.id: [] for stage in stages}
            
            # Process the results
            for row in result:
                # Create a lightweight contact object with just the needed attributes
                contact = {
                    'id': row.id,
                    'contact_id': row.contact_id,
                    'current_stage_id': row.current_stage_id,
                    'entered_at': row.entered_at,
                    'last_updated': row.last_updated,
                    'contact_type': row.contact_type,
                    'display_name': row.display_name
                }
                
                # Add to the appropriate stage
                if row.current_stage_id in contacts_by_stage:
                    contacts_by_stage[row.current_stage_id].append(contact)
            
            # Log performance metrics
            current_app.logger.info(f"Optimized SQL query loaded {sum(len(contacts) for contacts in contacts_by_stage.values())} of {total_contacts} contacts in {time.time() - contact_query_time:.2f}s")
        else:
            # Fallback to standard ORM query if optimization is disabled
            # Base query for pipeline contacts
            pipeline_contacts_query = db.session.query(PipelineContact).filter(
                PipelineContact.pipeline_id == pipeline_id
            )
            
            # Apply filters based on user role
            if not current_user.is_super_admin():
                if pipeline.pipeline_type == 'person' or pipeline.pipeline_type == 'people':
                    # For person pipelines, join with Person model
                    pipeline_contacts_query = db.session.query(PipelineContact).join(
                        Person, PipelineContact.contact_id == Person.id
                    ).filter(
                        PipelineContact.pipeline_id == pipeline_id,
                        Person.office_id == current_user.office_id
                    )
                    
                    # If not office admin, filter by assigned_to_id
                    if current_user.role != 'office_admin':
                        pipeline_contacts_query = pipeline_contacts_query.filter(
                            Person.assigned_to_id == current_user.id
                        )
                
                elif pipeline.pipeline_type == 'church':
                    # For church pipelines, join with Church model
                    pipeline_contacts_query = db.session.query(PipelineContact).join(
                        Church, PipelineContact.contact_id == Church.id
                    ).filter(
                        PipelineContact.pipeline_id == pipeline_id,
                        Church.office_id == current_user.office_id
                    )
                    
                    # If not office admin, filter by assigned_to_id
                    if current_user.role != 'office_admin':
                        pipeline_contacts_query = pipeline_contacts_query.filter(
                            Church.assigned_to_id == current_user.id
                        )
            
            # Execute the query with eager loading of related objects
            pipeline_contacts = pipeline_contacts_query.options(
                selectinload(PipelineContact.contact),
                selectinload(PipelineContact.current_stage)
            ).all()
            
            # Organize contacts by stage
            contacts_by_stage = {stage.id: [] for stage in stages}
            for pc in pipeline_contacts:
                if pc.current_stage_id in contacts_by_stage:
                    contacts_by_stage[pc.current_stage_id].append(pc)
            
            # Log performance metrics
            current_app.logger.info(f"Standard ORM query loaded {len(pipeline_contacts)} contacts in {time.time() - contact_query_time:.2f}s")
        
        # Don't load available contacts on initial page load - use AJAX instead
        people = []
        churches = []
        
        # Render the template with optimized data
        render_start = time.time()
        response = render_template('pipeline/view.html',
                             pipeline=pipeline,
                             stages=stages,
                             contacts_by_stage=contacts_by_stage,
                             people=people,
                             churches=churches,
                             use_ajax_loading=True)
        
        # Log total processing time
        current_app.logger.info(f"Rendered pipeline view in {time.time() - render_start:.2f}s")
        current_app.logger.info(f"Total pipeline view processing time: {time.time() - start_time:.2f}s")
        
        return response
    except Exception as e:
        current_app.logger.error(f"Error viewing pipeline: {str(e)}")
        flash(f"Error viewing pipeline: {str(e)}", 'danger')
        return redirect(url_for('pipeline.index'))

@pipeline_bp.route('/<int:pipeline_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(pipeline_id):
    """Edit an existing pipeline."""
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    
    # Don't allow editing of main pipelines
    if pipeline.is_main_pipeline:
        flash('System pipelines cannot be edited', 'warning')
        return redirect(url_for('pipeline.index'))
    
    # Get available offices for dropdown
    offices = Office.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        office_id = request.form.get('office_id')
        is_active = request.form.get('is_active') == 'on'
        parent_pipeline_stage = request.form.get('parent_pipeline_stage')
        pipeline_type = request.form.get('pipeline_type')
        
        # Validate form data
        if not name or not office_id or not pipeline_type:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('pipeline.edit', pipeline_id=pipeline_id))
        
        # Update pipeline
        pipeline.name = name
        pipeline.description = description
        pipeline.office_id = office_id
        pipeline.is_active = is_active
        pipeline.parent_pipeline_stage = parent_pipeline_stage
        pipeline.pipeline_type = pipeline_type
        pipeline.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Pipeline updated successfully', 'success')
        return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
    
    # For GET requests
    parent_stages = pipeline.get_available_parent_stages()
    
    # Debug logging to see why parent stages might be empty
    current_app.logger.info(f"[PIPELINE_EDIT DEBUG] Pipeline type: {pipeline.pipeline_type}")
    current_app.logger.info(f"[PIPELINE_EDIT DEBUG] Parent stages: {parent_stages}")
    
    # Check if there's a type parameter in the URL
    pipeline_type_param = request.args.get('type')
    if pipeline_type_param:
        # Create a temporary pipeline with the requested type for stage options
        temp_pipeline = Pipeline(pipeline_type=pipeline_type_param)
        parent_stages = temp_pipeline.get_available_parent_stages()
        current_app.logger.info(f"[PIPELINE_EDIT DEBUG] Updated pipeline type from URL: {pipeline_type_param}")
        current_app.logger.info(f"[PIPELINE_EDIT DEBUG] Updated parent stages: {parent_stages}")
    
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
            # Check if this is an "add stage" action
            if request.form.get('action') == 'add_stage':
                current_app.logger.info("Processing add stage form submission")
                
                # Get form data
                stage_name = request.form.get('stage_name')
                stage_color = request.form.get('stage_color', '#3498db')
                stage_description = request.form.get('stage_description', '')
                
                # Validate required fields
                if not stage_name:
                    flash('Stage name is required', 'danger')
                    stages = pipeline.get_active_stages()
                    return render_template('pipeline/edit_stages.html', 
                                          pipeline=pipeline,
                                          stages=stages,
                                          page_title=f"Manage Stages - {pipeline.name}")
                
                # Determine order (highest current order + 1)
                max_order = db.session.query(db.func.max(PipelineStage.order))\
                                    .filter(PipelineStage.pipeline_id == pipeline_id).scalar()
                new_order = 1 if max_order is None else max_order + 1
                
                # Create new stage
                new_stage = PipelineStage(
                    pipeline_id=pipeline_id,
                    name=stage_name,
                    order=new_order,
                    color=stage_color,
                    description=stage_description
                )
                
                db.session.add(new_stage)
                db.session.commit()
                
                current_app.logger.info(f"Created new stage: {new_stage.name} with ID {new_stage.id}")
                flash(f'Stage "{stage_name}" added successfully', 'success')
                
                # Stay on the same page to continue editing
                stages = pipeline.get_active_stages()
                return render_template('pipeline/edit_stages.html', 
                                      pipeline=pipeline,
                                      stages=stages,
                                      page_title=f"Manage Stages - {pipeline.name}")
            
            # Otherwise process stages data as before
            stages_data_str = request.form.get('stages_data', '[]')
            
            # Log the received data for debugging
            current_app.logger.debug(f"Received stages_data: {stages_data_str}")
            
            # Parse the JSON data - handle empty strings safely
            if not stages_data_str or stages_data_str.isspace() or stages_data_str == '':
                stages_data = []
                current_app.logger.warning("No stages data received in the request")
            else:
                try:
                    stages_data = json.loads(stages_data_str)
                    current_app.logger.info(f"Successfully parsed stages data: {len(stages_data)} stages")
                except json.JSONDecodeError:
                    current_app.logger.error(f"Invalid JSON data: {stages_data_str}")
                    flash('Invalid stage data format. Please try again.', 'danger')
                    stages = pipeline.get_active_stages()
                    return render_template('pipeline/edit_stages.html', 
                                          pipeline=pipeline,
                                          stages=stages,
                                          page_title=f"Manage Stages - {pipeline.name}")
            
            # Get all existing stage IDs for this pipeline
            existing_stage_ids = [stage.id for stage in PipelineStage.query.filter_by(pipeline_id=pipeline_id).all()]
            submitted_stage_ids = []
            
            # Process the submitted stage data
            new_stages_count = 0
            updated_stages_count = 0
            
            for stage_data in stages_data:
                stage_id = stage_data.get('id')
                current_app.logger.debug(f"Processing stage: {stage_id}, name: {stage_data.get('name')}")
                
                # Check if this is a new stage (id starts with 'new_')
                if stage_id and str(stage_id).startswith('new_'):
                    # Create a new stage
                    new_stage = PipelineStage(
                        pipeline_id=pipeline_id,
                        name=stage_data.get('name', 'New Stage'),
                        order=stage_data.get('order', 1),
                        color=stage_data.get('color', '#3498db'),
                        description=stage_data.get('description', '')
                    )
                    db.session.add(new_stage)
                    new_stages_count += 1
                    current_app.logger.info(f"Created new stage: {new_stage.name}")
                elif stage_id:  # Existing stage
                    # Track this ID as submitted
                    try:
                        numeric_id = int(stage_id)
                        submitted_stage_ids.append(numeric_id)
                    except (ValueError, TypeError):
                        current_app.logger.warning(f"Invalid stage ID: {stage_id}")
                    
                    stage = PipelineStage.query.get(stage_id)
                    if stage and stage.pipeline_id == pipeline_id:
                        stage.name = stage_data.get('name', stage.name)
                        stage.order = stage_data.get('order', stage.order)
                        stage.description = stage_data.get('description', stage.description)
                        stage.color = stage_data.get('color', stage.color)
                        
                        # Update automation fields if present
                        if 'auto_move_days' in stage_data:
                            stage.auto_move_days = stage_data.get('auto_move_days')
                        if 'auto_reminder' in stage_data:
                            stage.auto_reminder = stage_data.get('auto_reminder')
                        if 'auto_task_template' in stage_data:
                            stage.auto_task_template = stage_data.get('auto_task_template')
                        
                        updated_stages_count += 1
                        current_app.logger.info(f"Updated existing stage: {stage.name}")
                else:  # New stage without ID
                    new_stage = PipelineStage(
                        pipeline_id=pipeline_id,
                        name=stage_data.get('name', 'New Stage'),
                        order=stage_data.get('order', 1),
                        color=stage_data.get('color', '#3498db'),
                        description=stage_data.get('description', '')
                    )
                    db.session.add(new_stage)
                    new_stages_count += 1
                    current_app.logger.info(f"Created new stage without ID: {new_stage.name}")
            
            # Handle stage deletions - any stages that existed before but weren't in the submission
            deleted_stages_count = 0
            stages_to_delete = [id for id in existing_stage_ids if id not in submitted_stage_ids]
            
            for stage_id in stages_to_delete:
                stage = PipelineStage.query.get(stage_id)
                if stage and stage.pipeline_id == pipeline_id:
                    # Check if the stage has contacts assigned to it
                    contacts_in_stage = PipelineContact.query.filter_by(current_stage_id=stage_id).count()
                    if contacts_in_stage > 0:
                        current_app.logger.warning(f"Cannot delete stage {stage_id} as it has {contacts_in_stage} contacts assigned")
                        flash(f'Cannot delete stage "{stage.name}" as it has contacts assigned to it. Move contacts to other stages first.', 'warning')
                    else:
                        db.session.delete(stage)
                        deleted_stages_count += 1
                        current_app.logger.info(f"Deleted stage: {stage.name} (ID: {stage_id})")
            
            db.session.commit()
            current_app.logger.info(f"Pipeline stages updated: {new_stages_count} new, {updated_stages_count} updated, {deleted_stages_count} deleted")
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
def add_contact_to_pipeline(pipeline_id):
    """Add contacts to a pipeline."""
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    
    # Check if user has permission to view this pipeline
    if pipeline.office_id != current_user.office_id and not current_user.is_super_admin():
        flash('You do not have permission to add contacts to this pipeline.', 'danger')
        return redirect(url_for('pipeline.index'))
    
    # Handle form submission
    if request.method == 'POST':
        contact_ids = request.form.getlist('contact_ids')
        stage_id = request.form.get('stage_id')
        
        if not contact_ids:
            flash('Please select at least one contact.', 'warning')
            return redirect(url_for('pipeline.add_contact_to_pipeline', pipeline_id=pipeline_id))
            
        if not stage_id:
            flash('Please select a stage.', 'warning')
            return redirect(url_for('pipeline.add_contact_to_pipeline', pipeline_id=pipeline_id))
        
        # Add contacts to pipeline
        stage = PipelineStage.query.get(stage_id)
        if not stage or stage.pipeline_id != pipeline_id:
            flash('Invalid stage selected.', 'danger')
            return redirect(url_for('pipeline.add_contact_to_pipeline', pipeline_id=pipeline_id))
            
        # Add each contact to the pipeline
        added_count = 0
        for contact_id in contact_ids:
            contact = Contact.query.get(contact_id)
            if not contact:
                continue
                
            # Check if contact is already in pipeline
            existing = PipelineContact.query.filter_by(
                pipeline_id=pipeline_id,
                contact_id=contact_id
            ).first()
            
            if existing:
                continue
                
            # Create new pipeline contact
            pipeline_contact = PipelineContact(
                pipeline_id=pipeline_id,
                contact_id=contact_id,
                current_stage_id=stage.id,
                entered_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            db.session.add(pipeline_contact)
            # Commit immediately to get the pipeline_contact.id
            db.session.commit()
            
            try:
                # Create history record with the now available pipeline_contact.id
                history = PipelineStageHistory(
                    pipeline_contact_id=pipeline_contact.id,
                    to_stage_id=stage.id,
                    created_by_id=current_user.id,
                    notes="Initial stage",
                    created_at=datetime.now()
                )
                
                db.session.add(history)
                db.session.commit()
            except Exception as history_error:
                current_app.logger.error(f"Failed to create history record for contact {contact_id} but contact was added: {str(history_error)}")
                # Don't roll back the pipeline_contact creation if history fails
            
            added_count += 1
            
        db.session.commit()
        
        if added_count > 0:
            flash(f'{added_count} contacts added to pipeline.', 'success')
        else:
            flash('No new contacts were added to the pipeline.', 'info')
            
        return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
    
    # Get contacts not already in this pipeline
    # Get contacts in this pipeline
    contact_ids_in_pipeline = db.session.query(PipelineContact.contact_id).filter(
        PipelineContact.pipeline_id == pipeline_id
    ).subquery()
    
    # Filter to get contacts not in pipeline
    pipeline_type = pipeline.pipeline_type
    base_query = Contact.query.filter(Contact.id.notin_(contact_ids_in_pipeline))
    
    # Check the structure of the Contact model to determine which attributes to use
    inspector = inspect(Contact)
    contact_columns = [column.key for column in inspector.columns]
    
    # Determine attribute for filtering by contact type
    type_attribute = 'type'  # Default to 'type'
    if 'contact_type' in contact_columns:
        type_attribute = 'contact_type'
    
    # Filter by contact type based on pipeline type
    if pipeline_type == 'person':
        # Only show people for person pipelines
        people = base_query.filter(getattr(Contact, type_attribute) == 'person').all()
        churches = []
    elif pipeline_type == 'church':
        # Only show churches for church pipelines
        people = []
        churches = base_query.filter(getattr(Contact, type_attribute) == 'church').all()
    else:
        # Show both for mixed pipelines
        people = base_query.filter(getattr(Contact, type_attribute) == 'person').all()
        churches = base_query.filter(getattr(Contact, type_attribute) == 'church').all()
    
    return render_template('pipeline/add_contact.html',
                          pipeline=pipeline,
                          stages=pipeline.stages,
                          people=people,
                          churches=churches)

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
        success = pipeline_contact.move_to_stage(
            stage_id=int(stage_id),
            user_id=current_user.id,
            notes=notes
        )
        
        if success:
            return jsonify({
                'success': True, 
                'message': 'Contact moved successfully'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to move contact'}), 500
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
        ).order_by(PipelineStageHistory.created_at.desc()).all()
        
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
        ).order_by(PipelineStageHistory.created_at.desc()).limit(100).all()
        
        return render_template('pipeline/history.html',
                              pipeline=pipeline,
                              history_items=history_items,
                              page_title=f"Pipeline History - {pipeline.name}")

@pipeline_bp.route('/api/pipeline-contacts/<int:pipeline_id>')
@login_required
def api_pipeline_contacts(pipeline_id):
    """API endpoint to get all contacts in a pipeline with their stages."""
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    
    # Check if user has permission to view this pipeline
    if not current_user.is_super_admin() and pipeline.office_id != current_user.office_id:
        return jsonify({
            'error': 'You do not have permission to view this pipeline'
        }), 403
    
    pipeline_contacts = PipelineContact.query.filter_by(pipeline_id=pipeline_id).all()
    
    # Format the response
    result = []
    for pc in pipeline_contacts:
        contact = pc.contact
        stage = pc.current_stage
        
        result.append({
            'id': pc.id,
            'contact_id': pc.contact_id,
            'contact_name': contact.get_name() if hasattr(contact, 'get_name') else 'Unknown',
            'stage_id': stage.id if stage else None,
            'stage_name': stage.name if stage else 'None'
        })
    
    return jsonify(result)

@pipeline_bp.route('/api/available-contacts/<int:pipeline_id>')
@login_required
def api_available_contacts(pipeline_id):
    """API endpoint to get available contacts for a pipeline.
    This is called via AJAX when the user clicks 'Add Contact' to improve initial page load time."""
    try:
        # Start timing
        start_time = datetime.now()
        
        # Get the pipeline
        pipeline = Pipeline.query.get_or_404(pipeline_id)
        
        # Check if user has permission to view this pipeline
        if not current_user.is_super_admin() and pipeline.office_id != current_user.office_id:
            return jsonify({
                'error': 'You do not have permission to view this pipeline'
            }), 403
        
        # Get IDs of contacts already in this pipeline - use a more efficient query
        existing_contact_ids = db.session.query(PipelineContact.contact_id)\
                                       .filter(PipelineContact.pipeline_id == pipeline_id)\
                                       .all()
        existing_contact_ids = [p[0] for p in existing_contact_ids]
        
        # Only fetch dropdown contacts if we have a reasonable number of existing contacts
        # This prevents performance issues with large exclusion lists
        max_exclusion_list = 1000  # Set a reasonable limit
        
        people = []
        churches = []
        
        # For people pipeline type
        if pipeline.pipeline_type in ['person', 'people', 'both']:
            people_query = Person.query
            
            # Apply exclusion for existing contacts - only if the list is not too large
            if existing_contact_ids and len(existing_contact_ids) < max_exclusion_list:
                people_query = people_query.filter(~Person.id.in_(existing_contact_ids))
            
            # Apply filters based on user role
            if not current_user.is_super_admin():
                # Add office filter for non-super admins
                people_query = people_query.filter(Person.office_id == current_user.office_id)
                
                # Regular users see only their assigned people
                if current_user.role != 'office_admin':
                    people_query = people_query.filter(Person.assigned_to_id == current_user.id)
            
            # Limit the number of results to improve performance
            people = people_query.limit(100).all()
            
            # Format people for JSON response
            people_json = [{
                'id': person.id,
                'name': f"{person.first_name} {person.last_name}",
                'type': 'person'
            } for person in people]

        # For church pipeline type
        if pipeline.pipeline_type in ['church', 'both']:
            church_query = Church.query
            
            # Apply exclusion for existing contacts - only if the list is not too large
            if existing_contact_ids and len(existing_contact_ids) < max_exclusion_list:
                church_query = church_query.filter(~Church.id.in_(existing_contact_ids))
            
            # Apply filters based on user role
            if not current_user.is_super_admin():
                # Add office filter for non-super admins
                church_query = church_query.filter(Church.office_id == current_user.office_id)
                
                # Regular users see only their assigned churches
                if current_user.role != 'office_admin':
                    church_query = church_query.filter(Church.assigned_to_id == current_user.id)
            
            # Limit the number of results to improve performance
            churches = church_query.limit(100).all()
            
            # Format churches for JSON response
            churches_json = [{
                'id': church.id,
                'name': church.name,
                'type': 'church'
            } for church in churches]
        
        # Calculate query time
        query_time = datetime.now() - start_time
        current_app.logger.info(f"Available contacts API query completed in {query_time.total_seconds():.2f} seconds")
        
        # Return the formatted response
        return jsonify({
            'people': people_json if 'people_json' in locals() else [],
            'churches': churches_json if 'churches_json' in locals() else [],
            'pipeline_type': pipeline.pipeline_type
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in available contacts API: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'error': f"Error loading available contacts: {str(e)}"
        }), 500

# This endpoint was replaced by /api/pipeline-contacts/<int:pipeline_id>

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
            (pipeline.office and current_user.role == 'office_admin' and pipeline.office_id == current_user.office_id)):
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
        pipeline_type = request.form.get('pipeline_type', 'people')  # Get pipeline_type with default
        
        if not pipeline_id or not name:
            flash('Pipeline ID and name are required.', 'danger')
            return redirect(url_for('pipeline.index'))
        
        pipeline = Pipeline.query.get(pipeline_id)
        if not pipeline:
            flash('Pipeline not found.', 'danger')
            return redirect(url_for('pipeline.index'))
        
        # Check permissions - only owner, office admin, or super admin can edit
        if not (current_user.is_super_admin() or 
                (pipeline.office and current_user.role == 'office_admin' and pipeline.office_id == current_user.office_id) or
                pipeline.created_by_id == current_user.id):
            flash('You do not have permission to edit this pipeline.', 'danger')
            return redirect(url_for('pipeline.index'))
        
        # Update pipeline details
        pipeline.name = name
        pipeline.description = description
        pipeline.pipeline_type = pipeline_type  # Save the pipeline type
        
        db.session.commit()
        flash('Pipeline updated successfully.', 'success')
        
        return redirect(url_for('pipeline.index'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error editing pipeline: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('pipeline.index'))

@pipeline_bp.route('/move-contact/<int:contact_id>', methods=['POST'])
@login_required
def move_contact_api(contact_id):
    """API endpoint to move a contact to a new stage"""
    current_app.logger.info(f"[PIPELINE_DEBUG] Starting move_contact_api for contact_id={contact_id}")
    try:
        # Get the contact
        pipeline_contact = PipelineContact.query.get_or_404(contact_id)
        current_app.logger.info(f"[PIPELINE_DEBUG] Found pipeline_contact id={pipeline_contact.id}, current_stage_id={pipeline_contact.current_stage_id}")
        
        # Check if user has permission to edit this pipeline
        pipeline = Pipeline.query.get(pipeline_contact.pipeline_id)
        if not pipeline:
            current_app.logger.error(f"[PIPELINE_DEBUG] Pipeline not found for pipeline_id={pipeline_contact.pipeline_id}")
            return jsonify({'success': False, 'message': 'Pipeline not found'})
            
        current_app.logger.info(f"[PIPELINE_DEBUG] Found pipeline id={pipeline.id}, name={pipeline.name}, office_id={pipeline.office_id}")
            
        if not current_user.is_super_admin() and pipeline.office_id != current_user.office_id:
            current_app.logger.error(f"[PIPELINE_DEBUG] Permission denied. User office_id={current_user.office_id}, pipeline office_id={pipeline.office_id}")
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        # Get form data
        data = request.get_json()
        if not data:
            data = request.form
            
        current_app.logger.info(f"[PIPELINE_DEBUG] Move contact data: {data}")
        
        # Get the new stage ID
        new_stage_id = data.get('stage_id')
        if not new_stage_id:
            current_app.logger.error(f"[PIPELINE_DEBUG] No stage ID provided in request data")
            return jsonify({'success': False, 'message': 'No stage ID provided'})
            
        # Convert stage_id to int if needed
        try:
            new_stage_id = int(new_stage_id)
            current_app.logger.info(f"[PIPELINE_DEBUG] Converted stage_id to int: {new_stage_id}")
        except (ValueError, TypeError) as e:
            current_app.logger.error(f"[PIPELINE_DEBUG] Invalid stage ID format: {new_stage_id}, error: {str(e)}")
            return jsonify({'success': False, 'message': 'Invalid stage ID'})
        
        # Get the stage
        new_stage = PipelineStage.query.get(new_stage_id)
        if not new_stage:
            current_app.logger.error(f"[PIPELINE_DEBUG] Stage not found for stage_id={new_stage_id}")
            return jsonify({'success': False, 'message': 'Stage not found'})
            
        current_app.logger.info(f"[PIPELINE_DEBUG] Found new stage id={new_stage.id}, name={new_stage.name}, pipeline_id={new_stage.pipeline_id}")
            
        # Verify stage belongs to this pipeline
        if new_stage.pipeline_id != pipeline_contact.pipeline_id:
            current_app.logger.error(f"[PIPELINE_DEBUG] Stage not in this pipeline. Stage pipeline_id={new_stage.pipeline_id}, contact pipeline_id={pipeline_contact.pipeline_id}")
            return jsonify({'success': False, 'message': 'Stage not in this pipeline'})
        
        # Get notes if provided
        notes = data.get('notes', '')
        current_app.logger.info(f"[PIPELINE_DEBUG] Notes: {notes}")
        
        # Get the old stage
        old_stage = PipelineStage.query.get(pipeline_contact.current_stage_id)
        if old_stage:
            current_app.logger.info(f"[PIPELINE_DEBUG] Found old stage id={old_stage.id}, name={old_stage.name}")
        else:
            current_app.logger.warning(f"[PIPELINE_DEBUG] Old stage not found for stage_id={pipeline_contact.current_stage_id}")
        
        # If no change in stage, just return success
        if old_stage and old_stage.id == new_stage.id:
            current_app.logger.info(f"[PIPELINE_DEBUG] Contact already in this stage. No change needed.")
            return jsonify({'success': True, 'message': 'Contact already in this stage'})
        
        current_app.logger.info(f"[PIPELINE_DEBUG] Moving contact {contact_id} from stage {old_stage.id if old_stage else 'None'} to {new_stage.id}")
        
        # Verify database connection is active
        try:
            db.session.execute(db.text("SELECT 1"))
            current_app.logger.info(f"[PIPELINE_DEBUG] Database connection verified")
        except Exception as db_error:
            current_app.logger.error(f"[PIPELINE_DEBUG] Database connection error: {str(db_error)}")
            return jsonify({
                'success': False,
                'message': f'Database connection error: {str(db_error)}'
            })
        
        # Move the contact to the new stage using the model method
        try:
            current_app.logger.info(f"[PIPELINE_DEBUG] Calling move_to_stage with stage_id={new_stage_id}, user_id={current_user.id}")
            success = pipeline_contact.move_to_stage(
                stage_id=new_stage_id,
                user_id=current_user.id,
                notes=notes
            )
            
            if success:
                # Verify the change was actually made
                db.session.refresh(pipeline_contact)
                current_app.logger.info(f"[PIPELINE_DEBUG] After move: contact stage_id={pipeline_contact.current_stage_id}, expected={new_stage_id}")
                
                if pipeline_contact.current_stage_id == new_stage_id:
                    current_app.logger.info(f"[PIPELINE_DEBUG] Move successful and verified")
                    return jsonify({
                        'success': True,
                        'message': 'Contact moved successfully'
                    })
                else:
                    current_app.logger.error(f"[PIPELINE_DEBUG] Move reported success but verification failed. Current stage={pipeline_contact.current_stage_id}, expected={new_stage_id}")
                    return jsonify({
                        'success': False,
                        'message': 'Move verification failed'
                    })
            else:
                current_app.logger.error(f"[PIPELINE_DEBUG] move_to_stage returned False")
                return jsonify({
                    'success': False,
                    'message': 'Failed to move contact'
                })
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"[PIPELINE_DEBUG] Error in move_to_stage: {str(e)}")
            import traceback
            current_app.logger.error(f"[PIPELINE_DEBUG] Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    except Exception as e:
        current_app.logger.error(f"[PIPELINE_DEBUG] Error moving contact {contact_id}: {str(e)}")
        import traceback
        current_app.logger.error(f"[PIPELINE_DEBUG] Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@pipeline_bp.route('/add_contact', methods=['POST'])
@login_required
def add_contact():
    """Add a contact to a pipeline"""
    try:
        pipeline_id = request.form.get('pipeline_id', type=int)
        contact_id = request.form.get('contact_id', type=int)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not pipeline_id or not contact_id:
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': 'Missing required parameters'
                })
            else:
                flash('Missing required parameters', 'danger')
                return redirect(url_for('pipeline.index'))
            
        # Get the pipeline
        pipeline = Pipeline.query.get_or_404(pipeline_id)
        
        # Check if user has permission to edit this pipeline
        if not current_user.is_super_admin() and pipeline.office_id != current_user.office_id:
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': 'You do not have permission to edit this pipeline'
                })
            else:
                flash('You do not have permission to edit this pipeline', 'danger')
                return redirect(url_for('pipeline.index'))
            
        # Get the first stage in the pipeline
        first_stage = PipelineStage.query.filter_by(
            pipeline_id=pipeline_id
        ).order_by(PipelineStage.order).first()
        
        if not first_stage:
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': 'Pipeline has no stages'
                })
            else:
                flash('Pipeline has no stages. Please add at least one stage first.', 'danger')
                return redirect(url_for('pipeline.manage_stages', pipeline_id=pipeline_id))
            
        # Get the contact
        contact = Contact.query.get_or_404(contact_id)
        
        # Check if this contact type matches the pipeline type
        contact_type = getattr(contact, 'type', None) or getattr(contact, 'contact_type', None)
        if pipeline.pipeline_type == 'person' and contact_type != 'person':
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': 'This pipeline is for people only'
                })
            else:
                flash('This pipeline is for people only', 'danger')
                return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
        elif pipeline.pipeline_type == 'church' and contact_type != 'church':
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': 'This pipeline is for churches only'
                })
            else:
                flash('This pipeline is for churches only', 'danger')
                return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
            
        # Check if contact is already in this pipeline
        existing = PipelineContact.query.filter_by(
            pipeline_id=pipeline_id,
            contact_id=contact_id
        ).first()
        
        if existing:
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': 'Contact is already in this pipeline'
                })
            else:
                flash('Contact is already in this pipeline', 'warning')
                return redirect(url_for('pipeline.view', pipeline_id=pipeline_id))
            
        # Add the contact to the pipeline
        pipeline_contact = PipelineContact(
            pipeline_id=pipeline_id,
            contact_id=contact_id,
            current_stage_id=first_stage.id,
            entered_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        db.session.add(pipeline_contact)
        # Commit immediately to get the pipeline_contact.id
        db.session.commit()
        
        try:
            # Create history record with the now available pipeline_contact.id
            history = PipelineStageHistory(
                pipeline_contact_id=pipeline_contact.id,
                to_stage_id=first_stage.id,
                created_by_id=current_user.id,
                notes="Initial stage",
                created_at=datetime.now()
            )
            
            db.session.add(history)
            db.session.commit()
        except Exception as history_error:
            current_app.logger.error(f"Failed to create history record for contact {contact_id} but contact was added: {str(history_error)}")
            # Don't roll back the pipeline_contact creation if history fails
        
        # Update the contacts list HTML for the first stage
        updated_contacts = PipelineContact.query.filter_by(
            pipeline_id=pipeline_id,
            current_stage_id=first_stage.id
        ).all()
        
        # Redirect URL for both AJAX and regular requests
        redirect_url = url_for('pipeline.view', pipeline_id=pipeline_id)
        
        # For AJAX requests
        if is_ajax:
            return jsonify({
                'success': True,
                'message': 'Contact added to pipeline',
                'contact_id': pipeline_contact.id,
                'stage_id': first_stage.id,
                'updated_contacts': len(updated_contacts),
                'redirect_url': redirect_url
            })
        # For direct form submissions, redirect to the pipeline view
        else:
            flash('Contact added to pipeline successfully', 'success')
            return redirect(redirect_url)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding contact to pipeline: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            })
        else:
            flash(f'Error adding contact: {str(e)}', 'danger')
            return redirect(url_for('pipeline.view', pipeline_id=pipeline_id)) 