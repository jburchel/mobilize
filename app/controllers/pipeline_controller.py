from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app
from flask_login import login_required, current_user
from app.models import Pipeline, PipelineStage, PipelineContact, PipelineStageHistory, Contact, Office, Person, Church
from app.extensions import db
from datetime import datetime
import json
from sqlalchemy import inspect
from flask_wtf.csrf import generate_csrf
from sqlalchemy.orm import selectinload
from sqlalchemy import desc

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/pipeline')

@pipeline_bp.route('/')
@login_required
def index():
    """Show all pipelines."""
    # Get all custom (non-main) pipelines
    custom_pipelines = Pipeline.query.filter_by(is_main_pipeline=False).all()
    
    # Get main pipelines
    people_main_pipeline = Pipeline.query.filter_by(is_main_pipeline=True, pipeline_type='person').first()
    if not people_main_pipeline:
        people_main_pipeline = Pipeline.query.filter_by(pipeline_type='person').first()
        
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
    """View a pipeline with all its stages and contacts."""
    try:
        pipeline = Pipeline.query.get_or_404(pipeline_id)
        
        # Enhanced debug logging to troubleshoot church pipeline issue
        current_app.logger.info(f"[PIPELINE DEBUG] View request for pipeline_id: {pipeline_id}")
        current_app.logger.info(f"[PIPELINE DEBUG] Pipeline details: name={pipeline.name}, type={pipeline.pipeline_type}, id={pipeline.id}")
        
        # Verify database connection
        db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'sqlite' in db_path:
            current_app.logger.info(f"Using database: {db_path}")
        
        # Add debug info
        contact_count = db.session.execute(
            db.text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
            {"pipeline_id": pipeline_id}
        ).scalar() or 0
        current_app.logger.info(f"View pipeline {pipeline_id}, name={pipeline.name}, type={pipeline.pipeline_type}, SQL count: {contact_count}")
        
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
            
        # Get stages with their contacts
        stages = pipeline.get_active_stages()
        
        # Get pipeline contacts based on user role
        if current_user.is_super_admin():
            # Super admins see all contacts
            # Use direct SQL to guarantee we get all contacts
            contact_records = db.session.execute(
                db.text("""
                    SELECT id, contact_id, current_stage_id
                    FROM pipeline_contacts 
                    WHERE pipeline_id = :pipeline_id
                """),
                {"pipeline_id": pipeline_id}
            ).fetchall()
            
            # Create PipelineContact objects from the SQL results
            pipeline_contacts = []
            for record in contact_records:
                pc = PipelineContact.query.get(record[0])
                if pc:
                    pipeline_contacts.append(pc)
                else:
                    current_app.logger.warning(f"Could not find PipelineContact with ID {record[0]}")
            
            # Count church contacts for debugging
            if pipeline.pipeline_type == 'church':
                from app.models.church import Church
                all_churches = Church.query.count()
                church_contacts = db.session.query(PipelineContact.contact_id).filter_by(pipeline_id=pipeline_id).all()
                church_contact_ids = [c[0] for c in church_contacts]
                current_app.logger.info(f"Super admin church pipeline debug: Total churches in DB: {all_churches}")
                current_app.logger.info(f"Church contacts in pipeline: {len(church_contact_ids)}")
                current_app.logger.info(f"Church contact IDs: {church_contact_ids}")
                
                # Additional verification with direct SQL
                direct_sql_count = db.session.execute(
                    db.text("""
                        SELECT COUNT(*) 
                        FROM pipeline_contacts 
                        WHERE pipeline_id = :pipeline_id
                    """),
                    {"pipeline_id": pipeline_id}
                ).scalar() or 0
                current_app.logger.info(f"Direct SQL count for church pipeline: {direct_sql_count}")
            
            current_app.logger.info(f"Super admin view: found {len(pipeline_contacts)} contacts for pipeline {pipeline_id}")
        elif current_user.is_office_admin():
            # Office admins see contacts from their office
            office_id = current_user.office_id
            
            # First get all pipeline contacts for this pipeline
            all_pipeline_contacts = PipelineContact.query.filter_by(pipeline_id=pipeline_id).all()
            current_app.logger.info(f"Office admin view: total contacts in pipeline before filtering: {len(all_pipeline_contacts)}")
            
            # Filter to only include contacts from the user's office
            pipeline_contacts = []
            for pc in all_pipeline_contacts:
                contact = pc.contact
                contact_office_id = getattr(contact, 'office_id', None)
                if contact_office_id == office_id:
                    pipeline_contacts.append(pc)
            
            current_app.logger.info(f"Office admin view: after filtering by office_id {office_id}, found {len(pipeline_contacts)} contacts")
        else:
            # Regular users see only their assigned contacts
            user_id = current_user.id
            office_id = current_user.office_id
            
            # First get all pipeline contacts for this pipeline
            all_pipeline_contacts = PipelineContact.query.filter_by(pipeline_id=pipeline_id).all()
            current_app.logger.info(f"Regular user view: total contacts in pipeline before filtering: {len(all_pipeline_contacts)}")
            
            # Filter to only include contacts assigned to this user
            pipeline_contacts = []
            for pc in all_pipeline_contacts:
                contact = pc.contact
                contact_user_id = getattr(contact, 'assigned_to_id', None)
                contact_office_id = getattr(contact, 'office_id', None)
                
                # Include if assigned to this user and from the same office
                if contact_user_id == user_id and contact_office_id == office_id:
                    pipeline_contacts.append(pc)
            
            current_app.logger.info(f"Regular user view: after filtering by user_id {user_id} and office_id {office_id}, found {len(pipeline_contacts)} contacts")
        
        # Organize contacts by stage
        contacts_by_stage = {stage.id: [] for stage in stages}
        for pc in pipeline_contacts:
            if pc.current_stage_id in contacts_by_stage:
                contacts_by_stage[pc.current_stage_id].append(pc)
        
        # Log contact counts for debugging
        for stage_id, contacts in contacts_by_stage.items():
            stage = next((s for s in stages if s.id == stage_id), None)
            stage_name = stage.name if stage else "Unknown"
            current_app.logger.info(f"Stage {stage_id} ({stage_name}) has {len(contacts)} contacts")
        
        # Debug contact entries
        if contact_count > 0 and len(pipeline_contacts) < contact_count:
            current_app.logger.warning(f"Pipeline {pipeline_id} has {contact_count} contacts in DB but only {len(pipeline_contacts)} were loaded for display")
            
            # Check if some contacts weren't loaded correctly
            missing_contacts = db.session.execute(
                db.text("""
                SELECT pc.id, pc.contact_id, pc.current_stage_id
                FROM pipeline_contacts pc 
                WHERE pc.pipeline_id = :pipeline_id
                """), 
                {"pipeline_id": pipeline_id}
            ).fetchall()
            
            if missing_contacts:
                current_app.logger.info(f"First 5 pipeline contacts DB records: {missing_contacts[:5]}")

        # Get available contacts to populate the Add Contact dropdown based on user role
        people = []
        churches = []
        
        # Get IDs of contacts already in this pipeline
        current_app.logger.info(f"Getting contacts for pipeline {pipeline_id} of type {pipeline.pipeline_type}")
        existing_contact_ids = db.session.query(PipelineContact.contact_id)\
                                       .filter(PipelineContact.pipeline_id == pipeline_id)\
                                       .all()
        existing_contact_ids = [p[0] for p in existing_contact_ids]
        current_app.logger.info(f"Found {len(existing_contact_ids)} existing contacts in this pipeline")
        
        # For people pipeline type
        if pipeline.pipeline_type in ['person', 'both']:
            people_query = Person.query
            
            # Apply exclusion for existing contacts
            if existing_contact_ids:
                people_query = people_query.filter(~Person.id.in_(existing_contact_ids))
            
            # Apply filters based on user role
            if current_user.is_super_admin():
                # Super admins see all people
                pass
            elif current_user.is_office_admin():
                # Office admins see people from their office
                people_query = people_query.filter(Person.office_id == current_user.office_id)
            else:
                # Regular users see only their assigned people
                people_query = people_query.filter(
                    Person.office_id == current_user.office_id,
                    Person.assigned_to_id == current_user.id
                )
                
            people = people_query.all()
            current_app.logger.info(f"Found {len(people)} available people for dropdown")

        # For church pipeline type
        if pipeline.pipeline_type in ['church', 'both']:
            church_query = Church.query
            
            # Apply exclusion for existing contacts
            if existing_contact_ids:
                church_query = church_query.filter(~Church.id.in_(existing_contact_ids))
                
            # Apply filters based on user role
            if current_user.is_super_admin():
                # Super admins see all churches
                pass
            elif current_user.is_office_admin():
                # Office admins see churches from their office
                church_query = church_query.filter(Church.office_id == current_user.office_id)
            else:
                # Regular users see only their assigned churches
                church_query = church_query.filter(
                    Church.office_id == current_user.office_id,
                    Church.assigned_to_id == current_user.id
                )
                
            churches = church_query.all()
            current_app.logger.info(f"Found {len(churches)} available churches for dropdown")
            
        # Render the template with the data
        return render_template('pipeline/view.html',
                            pipeline=pipeline,
                            stages=stages,
                            contacts_by_stage=contacts_by_stage,
                            people=people,
                            churches=churches)
    except Exception as e:
        current_app.logger.error(f"Error viewing pipeline: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f"Error loading pipeline: {str(e)}", "danger")
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
                        description=stage_data.get('description', '')
                    )
                    db.session.add(new_stage)
                elif stage_id:  # Existing stage
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
                else:  # New stage without ID
                    new_stage = PipelineStage(
                        pipeline_id=pipeline_id,
                        name=stage_data.get('name', 'New Stage'),
                        order=stage_data.get('order', 1),
                        color=stage_data.get('color', '#3498db'),
                        description=stage_data.get('description', '')
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
            
            # Create history record
            history = PipelineStageHistory(
                pipeline_contact_id=pipeline_contact.id,
                to_stage_id=stage.id,
                created_by_id=current_user.id,
                notes="Initial stage",
                created_at=datetime.now()
            )
            
            db.session.add(pipeline_contact)
            db.session.add(history)
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

@pipeline_bp.route('/move-contact/<int:contact_id>', methods=['POST'])
@login_required
def move_contact_api(contact_id):
    """API endpoint to move a contact to a new stage"""
    try:
        # Get the contact
        pipeline_contact = PipelineContact.query.get_or_404(contact_id)
        
        # Check if user has permission to edit this pipeline
        pipeline = Pipeline.query.get(pipeline_contact.pipeline_id)
        if not pipeline:
            return jsonify({'success': False, 'message': 'Pipeline not found'})
            
        if not current_user.is_super_admin() and pipeline.office_id != current_user.office_id:
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        # Get form data
        data = request.get_json()
        if not data:
            data = request.form
            
        current_app.logger.debug(f"Move contact data: {data}")
        
        # Get the new stage ID
        new_stage_id = data.get('stage_id')
        if not new_stage_id:
            return jsonify({'success': False, 'message': 'No stage ID provided'})
            
        # Convert stage_id to int if needed
        try:
            new_stage_id = int(new_stage_id)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid stage ID'})
        
        # Get the stage
        new_stage = PipelineStage.query.get(new_stage_id)
        if not new_stage:
            return jsonify({'success': False, 'message': 'Stage not found'})
            
        # Verify stage belongs to this pipeline
        if new_stage.pipeline_id != pipeline_contact.pipeline_id:
            return jsonify({'success': False, 'message': 'Stage not in this pipeline'})
        
        # Get notes if provided
        notes = data.get('notes', '')
        
        # Get the old stage
        old_stage = PipelineStage.query.get(pipeline_contact.current_stage_id)
        
        # If no change in stage, just return success
        if old_stage and old_stage.id == new_stage.id:
            return jsonify({'success': True, 'message': 'Contact already in this stage'})
        
        current_app.logger.debug(f"Moving contact {contact_id} from stage {old_stage.id if old_stage else 'None'} to {new_stage.id}")
        
        # Move the contact to the new stage using the model method
        try:
            success = pipeline_contact.move_to_stage(
                stage_id=new_stage_id,
                user_id=current_user.id,
                notes=notes
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Contact moved successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to move contact'
                })
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in move_to_stage: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    except Exception as e:
        current_app.logger.error(f"Error moving contact {contact_id}: {str(e)}")
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
        
        if not pipeline_id or not contact_id:
            return jsonify({
                'success': False,
                'message': 'Missing required parameters'
            })
            
        # Get the pipeline
        pipeline = Pipeline.query.get_or_404(pipeline_id)
        
        # Check if user has permission to edit this pipeline
        if not current_user.is_super_admin() and pipeline.office_id != current_user.office_id:
            return jsonify({
                'success': False,
                'message': 'You do not have permission to edit this pipeline'
            })
            
        # Get the first stage in the pipeline
        first_stage = PipelineStage.query.filter_by(
            pipeline_id=pipeline_id
        ).order_by(PipelineStage.order).first()
        
        if not first_stage:
            return jsonify({
                'success': False,
                'message': 'Pipeline has no stages'
            })
            
        # Get the contact
        contact = Contact.query.get_or_404(contact_id)
        
        # Check if this contact type matches the pipeline type
        contact_type = getattr(contact, 'type', None) or getattr(contact, 'contact_type', None)
        if pipeline.pipeline_type == 'person' and contact_type != 'person':
            return jsonify({
                'success': False,
                'message': 'This pipeline is for people only'
            })
        elif pipeline.pipeline_type == 'church' and contact_type != 'church':
            return jsonify({
                'success': False,
                'message': 'This pipeline is for churches only'
            })
            
        # Check if contact is already in this pipeline
        existing = PipelineContact.query.filter_by(
            pipeline_id=pipeline_id,
            contact_id=contact_id
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Contact is already in this pipeline'
            })
            
        # Add the contact to the pipeline
        pipeline_contact = PipelineContact(
            pipeline_id=pipeline_id,
            contact_id=contact_id,
            current_stage_id=first_stage.id,
            entered_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        db.session.add(pipeline_contact)
        
        # Create a history entry
        history = PipelineStageHistory(
            pipeline_contact_id=pipeline_contact.id,
            to_stage_id=first_stage.id,
            created_by_id=current_user.id,
            notes="Initial stage",
            created_at=datetime.now()
        )
        
        db.session.add(history)
        db.session.commit()
        
        # Update the contacts list HTML for the first stage
        updated_contacts = PipelineContact.query.filter_by(
            pipeline_id=pipeline_id,
            current_stage_id=first_stage.id
        ).all()
        
        # Return the updated contacts list
        return jsonify({
            'success': True,
            'message': 'Contact added to pipeline',
            'contact_id': pipeline_contact.id,
            'stage_id': first_stage.id,
            'updated_contacts': len(updated_contacts)
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding contact to pipeline: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

class PipelineController:
    @staticmethod
    def get_pipelines_for_current_user():
        """Get all pipelines for the current user's office."""
        if current_user.is_super_admin():
            return Pipeline.query.all()
        else:
            return Pipeline.query.filter_by(office_id=current_user.office_id).all()

    @staticmethod
    def get_pipeline_by_id(pipeline_id):
        """Get a specific pipeline by ID and check access permissions."""
        pipeline = Pipeline.query.get_or_404(pipeline_id)
        
        # Super admins can access any pipeline, others must have matching office_id
        if current_user.is_super_admin() or pipeline.office_id == current_user.office_id:
            return pipeline
        return None

    @staticmethod
    def get_pipeline_stages(pipeline_id):
        """Get all stages for a specific pipeline."""
        return PipelineStage.query.filter_by(pipeline_id=pipeline_id).order_by(PipelineStage.order).all()

    @staticmethod
    def get_pipeline_stage_by_id(stage_id):
        """Get a specific pipeline stage by ID."""
        return PipelineStage.query.get_or_404(stage_id)

    @staticmethod
    def create_pipeline(name, pipeline_type, description=None):
        """Create a new pipeline for the current user's office."""
        pipeline = Pipeline(
            name=name,
            pipeline_type=pipeline_type,
            description=description,
            office_id=current_user.office_id
        )
        db.session.add(pipeline)
        db.session.commit()
        return pipeline

    @staticmethod
    def update_pipeline(pipeline_id, name, pipeline_type, description=None):
        """Update an existing pipeline."""
        pipeline = PipelineController.get_pipeline_by_id(pipeline_id)
        if pipeline:
            pipeline.name = name
            pipeline.pipeline_type = pipeline_type
            pipeline.description = description
            db.session.commit()
            return pipeline
        return None

    @staticmethod
    def delete_pipeline(pipeline_id):
        """Delete a pipeline and its associated stages."""
        pipeline = PipelineController.get_pipeline_by_id(pipeline_id)
        if pipeline:
            # Delete all stages associated with this pipeline
            PipelineStage.query.filter_by(pipeline_id=pipeline_id).delete()
            # Delete the pipeline
            db.session.delete(pipeline)
            db.session.commit()
            return True
        return False

    @staticmethod
    def create_pipeline_stage(pipeline_id, name, description=None, order=None):
        """Create a new stage for a specific pipeline."""
        pipeline = PipelineController.get_pipeline_by_id(pipeline_id)
        if pipeline:
            # If order is not specified, place at the end
            if order is None:
                max_order = db.session.query(db.func.max(PipelineStage.order))\
                                    .filter(PipelineStage.pipeline_id == pipeline_id).scalar()
                order = 1 if max_order is None else max_order + 1

            stage = PipelineStage(
                name=name,
                description=description,
                pipeline_id=pipeline_id,
                order=order
            )
            db.session.add(stage)
            db.session.commit()
            return stage
        return None

    @staticmethod
    def update_pipeline_stage(stage_id, name, description=None, order=None):
        """Update an existing pipeline stage."""
        stage = PipelineController.get_pipeline_stage_by_id(stage_id)
        if stage:
            stage.name = name
            if description is not None:
                stage.description = description
            if order is not None:
                stage.order = order
            db.session.commit()
            return stage
        return None

    @staticmethod
    def delete_pipeline_stage(stage_id):
        """Delete a pipeline stage."""
        stage = PipelineController.get_pipeline_stage_by_id(stage_id)
        if stage:
            # Delete all contacts associated with this stage
            PipelineContact.query.filter_by(current_stage_id=stage_id).delete()
            # Delete the stage
            db.session.delete(stage)
            db.session.commit()
            return True
        return False

    @staticmethod
    def reorder_pipeline_stages(pipeline_id, stage_order):
        """Reorder pipeline stages based on a list of stage IDs."""
        pipeline = PipelineController.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            return False

        # Update the order of each stage
        for index, stage_id in enumerate(stage_order, 1):
            stage = PipelineStage.query.get(stage_id)
            if stage and stage.pipeline_id == pipeline_id:
                stage.order = index

        db.session.commit()
        return True

    @staticmethod
    def get_pipeline_contacts(pipeline_id, stage_id=None):
        """Get contacts in a pipeline, optionally filtered by stage."""
        pipeline = PipelineController.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            return []

        query = PipelineContact.query.filter_by(pipeline_id=pipeline_id)
        if stage_id:
            query = query.filter_by(current_stage_id=stage_id)
        
        return query.order_by(desc(PipelineContact.last_updated)).all()

    @staticmethod
    def get_pipeline_contact_by_id(contact_id):
        """Get a specific pipeline contact by ID."""
        return PipelineContact.query.get_or_404(contact_id)

    @staticmethod
    def add_contact_to_pipeline(pipeline_id, contact_id, stage_id, notes=None):
        """Add a contact to a pipeline at a specific stage."""
        pipeline = PipelineController.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            return None

        # Check if contact exists in the current user's office (or for super admins, any contact)
        contact = Contact.query.get(contact_id)
        if contact and (current_user.is_super_admin() or contact.office_id == current_user.office_id):
            # Check if contact already exists in this pipeline
            existing = PipelineContact.query.filter_by(
                pipeline_id=pipeline_id,
                contact_id=contact_id
            ).first()
            
            if existing:
                # If it exists, update the stage and notes
                existing.current_stage_id = stage_id
                # If notes tracking is implemented, add new note
                # existing.notes = notes
                db.session.commit()
                return existing
            
            # Create new pipeline contact
            pipeline_contact = PipelineContact(
                pipeline_id=pipeline_id,
                contact_id=contact_id,
                current_stage_id=stage_id
                # If notes tracking is implemented, add notes
                # notes=notes
            )
            db.session.add(pipeline_contact)
            db.session.commit()
            return pipeline_contact
        return None

    @staticmethod
    def update_pipeline_contact(contact_id, stage_id=None, notes=None):
        """Update a pipeline contact's stage or notes."""
        pipeline_contact = PipelineController.get_pipeline_contact_by_id(contact_id)
        if pipeline_contact:
            # Get the pipeline to check access
            pipeline = PipelineController.get_pipeline_by_id(pipeline_contact.pipeline_id)
            if not pipeline:
                return None
            
            if stage_id:
                pipeline_contact.current_stage_id = stage_id
            # If notes tracking is implemented:
            # if notes is not None:
            #    pipeline_contact.notes = notes
            db.session.commit()
            return pipeline_contact
        return None

    @staticmethod
    def remove_contact_from_pipeline(contact_id):
        """Remove a contact from a pipeline."""
        pipeline_contact = PipelineController.get_pipeline_contact_by_id(contact_id)
        if pipeline_contact:
            # Get the pipeline to check access
            pipeline = PipelineController.get_pipeline_by_id(pipeline_contact.pipeline_id)
            if not pipeline:
                return False
            
            db.session.delete(pipeline_contact)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_available_contacts_for_pipeline(pipeline_id):
        """Get contacts that can be added to a pipeline."""
        pipeline = PipelineController.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            return [], []

        # Get IDs of contacts already in this pipeline
        existing_contact_ids = db.session.query(PipelineContact.contact_id)\
                                       .filter(PipelineContact.pipeline_id == pipeline_id).all()
        existing_contact_ids = [id[0] for id in existing_contact_ids]
        
        # For people pipeline
        if pipeline.pipeline_type == 'person':
            # For super admins, get all people not already in the pipeline
            if current_user.is_super_admin():
                people = Person.query.filter(~Person.id.in_(existing_contact_ids) if existing_contact_ids else True).all()
            else:
                people = Person.query.filter_by(office_id=current_user.office_id)\
                                    .filter(~Person.id.in_(existing_contact_ids) if existing_contact_ids else True).all()
            return people, []
        
        # For churches pipeline
        elif pipeline.pipeline_type == 'church':
            # For super admins, get all churches not already in the pipeline
            if current_user.is_super_admin():
                churches = Church.query.filter(~Church.id.in_(existing_contact_ids) if existing_contact_ids else True).all()
            else:
                churches = Church.query.filter_by(office_id=current_user.office_id)\
                                      .filter(~Church.id.in_(existing_contact_ids) if existing_contact_ids else True).all()
            return [], churches
        
        # For both types
        else:
            # For super admins, get all contacts not already in the pipeline
            if current_user.is_super_admin():
                people = Person.query.filter(~Person.id.in_(existing_contact_ids) if existing_contact_ids else True).all()
                churches = Church.query.filter(~Church.id.in_(existing_contact_ids) if existing_contact_ids else True).all()
            else:
                people = Person.query.filter_by(office_id=current_user.office_id)\
                                    .filter(~Person.id.in_(existing_contact_ids) if existing_contact_ids else True).all()
                churches = Church.query.filter_by(office_id=current_user.office_id)\
                                      .filter(~Church.id.in_(existing_contact_ids) if existing_contact_ids else True).all()
            return people, churches 

@pipeline_bp.app_context_processor
def inject_pipeline_utilities():
    """Add utility functions to the template context."""
    def get_pipeline_count(pipeline_id):
        """Get contact count for a pipeline directly from the database."""
        from sqlalchemy import text
        result = db.session.execute(
            text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
            {"pipeline_id": pipeline_id}
        )
        return result.scalar() or 0
    
    return dict(get_pipeline_count=get_pipeline_count) 