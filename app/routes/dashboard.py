from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import Person, Church, Task, Communication, Pipeline, PipelineStage, PipelineContact
from app.utils.decorators import office_required
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import or_, text
from app.extensions import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
@office_required
def index():
    """Render the dashboard view with relevant statistics."""
    office_id = current_user.office_id
    
    # Get dashboard statistics
    stats = get_dashboard_stats()
    
    # Get the main pipelines for people and churches
    people_pipeline = Pipeline.query.filter_by(is_main_pipeline=True, pipeline_type='person').first()
    church_pipeline = Pipeline.query.filter_by(is_main_pipeline=True, pipeline_type='church').first()
    
    # Get pending tasks for the current user
    pending_tasks = Task.query.filter_by(
        assigned_to=current_user.id, 
        status='pending'
    ).order_by(Task.due_date.asc()).limit(5).all()
    
    # Get recent communications
    # For super admins, show communications from all offices
    if current_user.is_super_admin():
        recent_communications = Communication.query.order_by(
            Communication.created_at.desc()
        ).limit(5).all()
    else:
        recent_communications = Communication.query.filter_by(
            office_id=office_id
        ).order_by(
            Communication.created_at.desc()
        ).limit(5).all()
    
    # Prepare recent activities list
    recent_activities = []
    
    # Add communications to activities
    for comm in recent_communications:
        contact_name = "Unknown"
        
        # Try to get the person's name
        if comm.person_id:
            person = Person.query.get(comm.person_id)
            if person:
                contact_name = f"{person.first_name} {person.last_name}"
        
        # Try to get the church's name
        elif comm.church_id:
            church = Church.query.get(comm.church_id)
            if church:
                contact_name = church.name
                
        comm_type = comm.type.capitalize() if comm.type else "Communication"
        activity = {
            'type': 'communication',
            'description': f"{comm_type} with {contact_name}",
            'timestamp': comm.created_at,
            'id': comm.id
        }
        recent_activities.append(activity)
    
    # Add completed tasks to activities (optional)
    # For super admins, show tasks from all offices
    if current_user.is_super_admin():
        recent_completed_tasks = Task.query.filter(
            Task.status == 'completed',
            Task.completed_date.isnot(None)
        ).order_by(Task.completed_date.desc()).limit(5).all()
    else:
        recent_completed_tasks = Task.query.filter(
            Task.office_id == office_id,
            Task.status == 'completed',
            Task.completed_date.isnot(None)
        ).order_by(Task.completed_date.desc()).limit(5).all()
    
    for task in recent_completed_tasks:
        activity = {
            'type': 'task',
            'description': f'Task completed: {task.title}',
            'timestamp': task.completed_date,
            'id': task.id
        }
        recent_activities.append(activity)
    
    # Sort all activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]  # Limit to 10 most recent
    
    return render_template(
        'dashboard/index.html',
        stats=stats,
        pending_tasks=pending_tasks,
        recent_activities=recent_activities,
        people_pipeline=people_pipeline,
        church_pipeline=church_pipeline
    )

# Since dashboard_bp is mounted at '/', 
# this will be accessible at /dashboard/api/stats
@dashboard_bp.route('/dashboard/api/stats')
@login_required
@office_required
def dashboard_stats_api():
    """API endpoint to get updated dashboard statistics."""
    stats = get_dashboard_stats()
    return jsonify(stats)

@dashboard_bp.route('/dashboard/pipeline-chart-data')
@login_required
@office_required
def pipeline_chart_data():
    """API endpoint to get pipeline stage data for charts."""
    pipeline_type = request.args.get('type', 'person')
    
    # Log the original request
    current_app.logger.info(f"Pipeline chart data requested for type: {pipeline_type}")
    
    # Normalize pipeline type for database query
    db_pipeline_type = 'people' if pipeline_type == 'person' else pipeline_type
    
    office_id = current_user.office_id
    
    try:
        # Direct SQL query to get main pipeline, its stages, and contact counts in one go
        query = """
        WITH pipeline AS (
            SELECT id, name
            FROM pipelines
            WHERE pipeline_type = :pipeline_type
            AND is_main_pipeline = 1
            AND office_id = :office_id
            LIMIT 1
        ),
        fallback_pipeline AS (
            SELECT id, name
            FROM pipelines
            WHERE pipeline_type = :pipeline_type
            AND is_main_pipeline = 1
            LIMIT 1
        ),
        selected_pipeline AS (
            SELECT * FROM pipeline
            UNION ALL
            SELECT * FROM fallback_pipeline
            LIMIT 1
        )
        SELECT 
            p.id as pipeline_id,
            p.name as pipeline_name,
            ps.id as stage_id,
            ps.name as stage_name,
            ps.color,
            ps."order" as stage_order,
            COUNT(pc.id) as contact_count
        FROM selected_pipeline p
        LEFT JOIN pipeline_stages ps ON p.id = ps.pipeline_id
        LEFT JOIN pipeline_contacts pc ON ps.id = pc.current_stage_id
        GROUP BY p.id, p.name, ps.id, ps.name, ps.color, ps."order"
        ORDER BY ps."order"
        """
        
        current_app.logger.info(f"Executing direct SQL query for pipeline type '{db_pipeline_type}' and office {office_id}")
        results = db.session.execute(db.text(query), {
            "pipeline_type": db_pipeline_type,
            "office_id": office_id
        }).fetchall()
        
        # If no results, return empty response
        if not results:
            current_app.logger.error(f"No pipeline or stages found for type: {db_pipeline_type}")
            return jsonify({
                'pipeline_id': None,
                'pipeline_name': f"No {pipeline_type} pipeline found",
                'total_contacts': 0,
                'stages': []
            })
        
        # Get pipeline info from first result
        pipeline_id = results[0].pipeline_id
        pipeline_name = results[0].pipeline_name
        
        # Count total contacts
        total_contacts = sum(r.contact_count for r in results)
        
        # Verify with a direct count
        verify_query = "SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"
        direct_count = db.session.execute(
            db.text(verify_query), 
            {"pipeline_id": pipeline_id}
        ).scalar() or 0
        
        current_app.logger.info(f"Found pipeline: {pipeline_name} (ID: {pipeline_id}) with {direct_count} total contacts")
        
        # Process stages
        stages = []
        for r in results:
            # Skip if stage_id is None (means we have pipeline but no stages)
            if r.stage_id is None:
                continue
                
            # Calculate percentage
            percentage = 0
            if total_contacts > 0:
                percentage = round((r.contact_count / total_contacts) * 100, 1)
                
            # Use a default color if none is specified
            color = r.color
            if not color:
                stage_name = r.stage_name.lower() if r.stage_name else ""
                if "promotion" in stage_name:
                    color = "#3498db"  # Blue
                elif "information" in stage_name:
                    color = "#2ecc71"  # Green
                elif "invitation" in stage_name:
                    color = "#f1c40f"  # Yellow
                elif "confirmation" in stage_name:
                    color = "#e67e22"  # Orange
                elif "en42" in stage_name:
                    color = "#9b59b6"  # Purple
                elif "automation" in stage_name:
                    color = "#1abc9c"  # Teal
                else:
                    color = "#95a5a6"  # Gray
            
            current_app.logger.debug(f"Stage: {r.stage_name}, Count: {r.contact_count}, Percentage: {percentage}%")
            stages.append({
                'id': r.stage_id,
                'name': r.stage_name,
                'count': r.contact_count,
                'percentage': percentage,
                'color': color
            })
        
        response_data = {
            'pipeline_id': pipeline_id,
            'pipeline_name': pipeline_name,
            'total_contacts': total_contacts,
            'stages': stages
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        current_app.logger.error(f"Error fetching pipeline chart data: {str(e)}\n{error_traceback}")
        return jsonify({
            'error': f'Database error: {str(e)}',
            'pipeline_id': None,
            'pipeline_name': 'Error',
            'total_contacts': 0,
            'stages': []
        }), 500

@dashboard_bp.route('/dashboard/debug/pipeline-data')
@login_required
@office_required
def debug_pipeline_data():
    """Debug endpoint to check pipeline data directly from the database."""
    try:
        # Get all pipelines
        pipelines = Pipeline.query.all()
        result = []
        
        for pipeline in pipelines:
            # Get contacts count via direct SQL
            contacts_query = db.text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id")
            contacts_count = db.session.execute(contacts_query, {"pipeline_id": pipeline.id}).scalar() or 0
            
            # Get stages count
            stages_query = db.text("SELECT COUNT(*) FROM pipeline_stages WHERE pipeline_id = :pipeline_id")
            stages_count = db.session.execute(stages_query, {"pipeline_id": pipeline.id}).scalar() or 0
            
            # Get stage details with contact counts
            stages_detail_query = """
            SELECT 
                ps.id, 
                ps.name, 
                COUNT(pc.id) as count
            FROM 
                pipeline_stages ps
            LEFT JOIN 
                pipeline_contacts pc ON ps.id = pc.current_stage_id
            WHERE 
                ps.pipeline_id = :pipeline_id
            GROUP BY 
                ps.id, ps.name
            ORDER BY 
                ps.order
            """
            
            stages_detail = db.session.execute(db.text(stages_detail_query), {"pipeline_id": pipeline.id})
            stages = []
            
            for stage in stages_detail:
                stages.append({
                    'id': stage.id,
                    'name': stage.name,
                    'count': stage.count
                })
            
            result.append({
                'id': pipeline.id,
                'name': pipeline.name,
                'type': pipeline.pipeline_type,
                'is_main': pipeline.is_main_pipeline,
                'stages_count': stages_count,
                'contacts_count': contacts_count,
                'stages': stages
            })
        
        return jsonify({
            'pipelines': result,
            'total_pipelines': len(result)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in debug endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/debug/chart-data/<chart_type>')
def debug_chart_data(chart_type):
    """Debug endpoint to get pipeline chart data without authentication."""
    current_app.logger.info(f"DEBUG: Pipeline chart data requested for type: {chart_type}")
    try:
        # Normalize pipeline type for the database
        pipeline_type = chart_type
        if chart_type == 'person':
            pipeline_type = 'people'
        
        # First run the script to ensure data is present - DEBUG ONLY
        try:
            from sqlalchemy import text
            # Quick count to check if we have contacts
            count_query = "SELECT COUNT(*) FROM pipeline_contacts"
            count_result = db.session.execute(text(count_query)).scalar()
            
            current_app.logger.info(f"DEBUG: Current pipeline_contacts count: {count_result}")
            
            # If no contacts, automatically run the script to add them
            if count_result == 0:
                current_app.logger.warning("No pipeline contacts found - running assign_random_stages script")
                try:
                    import subprocess
                    import os
                    script_path = os.path.join(current_app.root_path, '..', 'scripts', 'assign_random_stages.py')
                    result = subprocess.run(['python', script_path], capture_output=True, text=True)
                    current_app.logger.info(f"Script output: {result.stdout}")
                    current_app.logger.info(f"Script errors: {result.stderr}")
                    if result.returncode != 0:
                        current_app.logger.error(f"Script failed with return code {result.returncode}")
                except Exception as script_e:
                    current_app.logger.error(f"Failed to run script: {script_e}")
        except Exception as count_e:
            current_app.logger.error(f"Failed to check or restore data: {count_e}")
        
        # Find the main pipeline for the given type
        query = """
        WITH pipeline AS (
            SELECT id, name
            FROM pipelines
            WHERE pipeline_type = :pipeline_type
            AND is_main_pipeline = 1
            LIMIT 1
        )
        SELECT 
            p.id as pipeline_id,
            p.name as pipeline_name,
            ps.id as stage_id,
            ps.name as stage_name,
            ps.color,
            ps."order" as stage_order,
            COUNT(pc.id) as contact_count
        FROM pipeline p
        LEFT JOIN pipeline_stages ps ON p.id = ps.pipeline_id
        LEFT JOIN pipeline_contacts pc ON ps.id = pc.current_stage_id
        GROUP BY p.id, p.name, ps.id, ps.name, ps.color, ps."order"
        ORDER BY ps."order"
        """
        
        # Execute the query with explicit connection management
        connection = db.engine.connect()
        try:
            # Execute the query
            result = connection.execute(text(query), {"pipeline_type": pipeline_type})
            results = result.fetchall()
        finally:
            connection.close()
        
        if not results:
            current_app.logger.warning(f"No results found for pipeline type: {pipeline_type}")
            return jsonify({
                "pipeline_id": None,
                "pipeline_name": f"No {chart_type} pipeline found",
                "stages": [],
                "total_contacts": 0
            })
        
        # Format the results
        pipeline_id = results[0].pipeline_id
        pipeline_name = results[0].pipeline_name
        total_contacts = sum(row.contact_count for row in results)
        
        # Format stages data
        stages = []
        for row in results:
            stage_data = {
                "id": row.stage_id,
                "name": row.stage_name,
                "color": row.color or get_default_color(row.stage_name),
                "count": row.contact_count,
                "percentage": round((row.contact_count / total_contacts * 100) if total_contacts > 0 else 0, 1)
            }
            stages.append(stage_data)
        
        response_data = {
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline_name,
            "stages": stages,
            "total_contacts": total_contacts
        }
        
        # Log the response data for debugging
        current_app.logger.info(f"DEBUG: Returning {len(stages)} stages for {chart_type} pipeline. Total contacts: {total_contacts}")
        
        return jsonify(response_data)
    
    except Exception as e:
        current_app.logger.error(f"Error getting pipeline chart data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "pipeline_id": None,
            "pipeline_name": f"Error loading {chart_type} pipeline",
            "stages": [],
            "total_contacts": 0
        }), 500

def get_default_color(stage_name):
    """Get a default color for a stage based on its name"""
    if not stage_name:
        return "#95a5a6"  # Gray
        
    name = stage_name.lower()
    
    if 'promotion' in name:
        return '#3498db'  # Blue
    if 'information' in name:
        return '#2ecc71'  # Green
    if 'invitation' in name:
        return '#f1c40f'  # Yellow
    if 'confirmation' in name:
        return '#e67e22'  # Orange
    if 'enr' in name or 'en42' in name:
        return '#9b59b6'  # Purple
    if 'automation' in name:
        return '#1abc9c'  # Teal
    
    return '#95a5a6'  # Gray

def get_dashboard_stats():
    """Helper function to generate dashboard statistics."""
    office_id = current_user.office_id
    
    # Count people and churches
    try:
        # For super admins, count all people across all offices
        if current_user.is_super_admin():
            people_count = Person.query.count()
        else:
            people_count = Person.query.filter_by(office_id=office_id).count()
    except Exception as e:
        current_app.logger.error(f"Error counting people: {str(e)}")
        people_count = 0
        
    try:
        # For super admins, count all churches across all offices
        if current_user.is_super_admin():
            church_count = Church.query.count()
        else:
            church_count = Church.query.filter_by(office_id=office_id).count()
    except Exception as e:
        current_app.logger.error(f"Error counting churches: {str(e)}")
        church_count = 0
        
    # Count tasks
    try:
        pending_tasks = Task.query.filter_by(
            assigned_to=current_user.id,
            status='pending',
        ).count()
        overdue_tasks = Task.query.filter(
            Task.assigned_to == current_user.id,
            Task.status == 'pending',
            Task.due_date < datetime.now().date(),
        ).count()
    except Exception as e:
        current_app.logger.error(f"Error counting tasks: {str(e)}")
        pending_tasks = 0
        overdue_tasks = 0
        
    # Count communications
    try:
        # For super admins, count communications from all offices
        if current_user.is_super_admin():
            recent_communications = Communication.query.filter(
                Communication.created_at >= (datetime.now() - timedelta(days=30))
            ).count()
        else:
            recent_communications = Communication.query.filter_by(
                office_id=office_id
            ).filter(
                Communication.created_at >= (datetime.now() - timedelta(days=30))
            ).count()
    except Exception as e:
        current_app.logger.error(f"Error counting communications: {str(e)}")
        recent_communications = 0
    
    return {
        'people_count': people_count,
        'church_count': church_count,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_communications': recent_communications
    } 