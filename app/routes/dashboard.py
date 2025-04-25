from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from app.models import Person, Church, Task, Communication, Pipeline, PipelineStage, PipelineContact
from app.utils.decorators import office_required
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import or_, text, func, and_
from sqlalchemy.orm import joinedload
from app.extensions import db, cache

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
@office_required
def index():
    """Render the dashboard view with relevant statistics."""
    # Check if this is the user's first login
    if current_user.first_login:
        return redirect(url_for('onboarding.welcome'))
    
    office_id = current_user.office_id
    
    # Get dashboard statistics
    stats = get_dashboard_stats()
    
    # Get the main pipelines using a single query with OR condition
    if current_user.is_super_admin():
        # Super admins see Main Office pipelines by default
        pipeline_query = Pipeline.query.filter(
            Pipeline.is_main_pipeline == True,
            Pipeline.office_id == 1,  # Main Office
            or_(
                Pipeline.pipeline_type == 'person',
                Pipeline.pipeline_type == 'people',
                Pipeline.pipeline_type == 'church'
            )
        ).all()
    else:
        # Regular users see their office's pipelines
        pipeline_query = Pipeline.query.filter(
            Pipeline.is_main_pipeline == True,
            Pipeline.office_id == office_id,
            or_(
                Pipeline.pipeline_type == 'person',
                Pipeline.pipeline_type == 'people',
                Pipeline.pipeline_type == 'church'
            )
        ).all()
    
    # Extract people and church pipelines from the results
    people_pipeline = None
    church_pipeline = None
    for pipeline in pipeline_query:
        if pipeline.pipeline_type in ('person', 'people'):
            people_pipeline = pipeline
        elif pipeline.pipeline_type == 'church':
            church_pipeline = pipeline
    
    # Log pipeline information for debugging
    current_app.logger.info(f"Dashboard - User: {current_user.id}, Office: {office_id}")
    current_app.logger.info(f"People Pipeline: {people_pipeline.id if people_pipeline else 'None'}")
    current_app.logger.info(f"Church Pipeline: {church_pipeline.id if church_pipeline else 'None'}")
    
    # Get pending tasks for the current user with efficient loading
    pending_tasks = Task.query.options(
        joinedload(Task.person),
        joinedload(Task.church)
    ).filter_by(
        assigned_to=current_user.id, 
        status='pending'
    ).order_by(Task.due_date.asc()).limit(5).all()
    
    # Get recent communications with efficient loading
    comm_query = Communication.query.options(
        joinedload(Communication.person),
        joinedload(Communication.church)
    )
    
    # For super admins, show communications from all offices
    if current_user.is_super_admin():
        recent_communications = comm_query.order_by(
            Communication.created_at.desc()
        ).limit(5).all()
    else:
        recent_communications = comm_query.filter_by(
            office_id=office_id
        ).order_by(
            Communication.created_at.desc()
        ).limit(5).all()
    
    # Prepare recent activities list
    recent_activities = []
    
    # Add communications to activities - no need for additional queries now
    for comm in recent_communications:
        contact_name = "Unknown"
        
        # Use already loaded person data
        if comm.person:
            contact_name = f"{comm.person.first_name or ''} {comm.person.last_name or ''}".strip()
        # Use already loaded church data
        elif comm.church:
            contact_name = comm.church.name or "Unknown Church"
                
        comm_type = comm.type.capitalize() if comm.type else "Communication"
        activity = {
            'type': 'communication',
            'description': f"{comm_type} with {contact_name}",
            'timestamp': comm.created_at,
            'id': comm.id
        }
        recent_activities.append(activity)
    
    # Add completed tasks to activities (optional) with efficient loading
    completed_tasks_query = Task.query.options(
        joinedload(Task.person),
        joinedload(Task.church)
    ).filter(
        Task.status == 'completed',
        Task.completed_date.isnot(None)
    )
    
    # For super admins, show tasks from all offices
    if current_user.is_super_admin():
        recent_completed_tasks = completed_tasks_query.order_by(
            Task.completed_date.desc()
        ).limit(5).all()
    else:
        recent_completed_tasks = completed_tasks_query.filter(
            Task.office_id == office_id
        ).order_by(
            Task.completed_date.desc()
        ).limit(5).all()
    
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
        church_pipeline=church_pipeline,
        people_main_pipeline=people_pipeline,
        church_main_pipeline=church_pipeline
    )

# Since dashboard_bp is mounted at '/', 
# this will be accessible at /dashboard/api/stats
@dashboard_bp.route('/dashboard/api/stats')
@login_required
@office_required
def dashboard_stats_api():
    """API endpoint to get updated dashboard statistics."""
    # Generate a cache key based on user and office
    cache_key = f"dashboard_stats_{current_user.id}_{current_user.office_id}"
    
    # Try to get stats from cache
    cached_stats = cache.get(cache_key)
    if cached_stats:
        current_app.logger.debug(f"Using cached dashboard stats for user {current_user.id}")
        return jsonify(cached_stats)
    
    # If not in cache, generate stats
    stats = get_dashboard_stats()
    
    # Cache the stats for 5 minutes (300 seconds)
    cache.set(cache_key, stats, timeout=300)
    
    return jsonify(stats)

@dashboard_bp.route('/dashboard/pipeline-chart-data')
@login_required
@office_required
def pipeline_chart_data():
    """API endpoint to get pipeline stage data for charts."""
    pipeline_type = request.args.get('type', 'person')
    
    # Generate a cache key based on user, office, and pipeline type
    cache_key = f"pipeline_chart_{current_user.id}_{current_user.office_id}_{pipeline_type}"
    
    # Try to get data from cache
    cached_data = cache.get(cache_key)
    if cached_data:
        current_app.logger.debug(f"Using cached pipeline chart data for user {current_user.id} and type {pipeline_type}")
        return jsonify(cached_data)
    
    # Log the original request
    current_app.logger.info(f"Pipeline chart data requested for type: {pipeline_type}")
    
    office_id = current_user.office_id
    
    try:
        # Use a more efficient query with proper indexing and caching
        # Convert pipeline type to a list for IN clause
        pipeline_types = ['person', 'people'] if pipeline_type == 'person' else [pipeline_type]
        
        # Build an optimized query that gets all the data at once
        query = """
        WITH pipeline_data AS (
            -- Select the appropriate pipeline
            SELECT p.id, p.name
            FROM pipelines p
            WHERE p.pipeline_type IN :pipeline_types
            AND p.is_main_pipeline = 1
            AND (p.office_id = :office_id OR :is_super_admin = 1)
            ORDER BY 
                CASE WHEN p.office_id = :office_id THEN 0 ELSE 1 END,
                p.id
            LIMIT 1
        )
        -- Get the stage data with counts in a single query
        SELECT 
            pd.id AS pipeline_id,
            pd.name AS pipeline_name,
            ps.id AS stage_id,
            ps.name AS stage_name,
            ps.color AS stage_color,
            ps."order" AS stage_order,
            COALESCE(pc_count.contact_count, 0) AS contact_count
        FROM 
            pipeline_data pd
        LEFT JOIN 
            pipeline_stages ps ON pd.id = ps.pipeline_id
        LEFT JOIN (
            -- Pre-compute contact counts per stage
            SELECT 
                current_stage_id, 
                COUNT(*) AS contact_count
            FROM 
                pipeline_contacts
            GROUP BY 
                current_stage_id
        ) pc_count ON ps.id = pc_count.current_stage_id
        ORDER BY 
            ps."order"
        """
        
        # Execute the query with proper parameter binding
        results = db.session.execute(text(query), {
            "pipeline_types": tuple(pipeline_types),
            "office_id": office_id,
            "is_super_admin": 1 if current_user.is_super_admin() else 0
        }).fetchall()
        
        # If no results, return empty response
        if not results:
            current_app.logger.error(f"No pipeline or stages found for types: {pipeline_types}")
            empty_response = {
                'pipeline_id': None,
                'pipeline_name': None,
                'stages': []
            }
            return jsonify(empty_response)
        
        # Extract pipeline info from first result
        pipeline_id = results[0].pipeline_id
        pipeline_name = results[0].pipeline_name
        
        # Process stages
        stages = []
        total_contacts = 0
        
        for row in results:
            if row.stage_id:  # Skip None values if any
                contact_count = row.contact_count or 0
                total_contacts += contact_count
                
                stages.append({
                    'id': row.stage_id,
                    'name': row.stage_name,
                    'color': row.stage_color or get_default_color(row.stage_name),
                    'order': row.stage_order,
                    'contact_count': contact_count
                })
        
        # Calculate percentages in a single pass
        for stage in stages:
            stage['percentage'] = round((stage['contact_count'] / total_contacts * 100) if total_contacts > 0 else 0, 1)
        
        # Prepare the response data
        response_data = {
            'pipeline_id': pipeline_id,
            'pipeline_name': pipeline_name,
            'stages': stages,
            'total_contacts': total_contacts
        }
        
        # Cache the result for 5 minutes
        cache.set(cache_key, response_data, timeout=300)
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Error fetching pipeline chart data: {str(e)}")
        error_response = {
            'error': str(e),
            'pipeline_id': None,
            'pipeline_name': None,
            'stages': []
        }
        return jsonify(error_response), 500

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
@login_required
def debug_chart_data(chart_type):
    """Endpoint to get pipeline chart data based on user role."""
    current_app.logger.info(f"Pipeline chart data requested for type: {chart_type} by user {current_user.id}")
    try:
        # Get statistics for totals
        stats = get_dashboard_stats()
        office_id = current_user.office_id
        
        # Choose the right query and parameters based on chart type
        if chart_type == 'person':
            # Query directly from the people table using the people_pipeline field
            if current_user.is_super_admin():
                # Super admin sees all people
                query = """
                SELECT 
                    people_pipeline as stage_name,
                    COUNT(*) as count
                FROM people
                GROUP BY people_pipeline
                ORDER BY people_pipeline
                """
                params = {}
            elif current_user.role == 'office_admin':
                # Office admin sees people in their office
                query = """
                SELECT 
                    people_pipeline as stage_name,
                    COUNT(*) as count
                FROM people
                WHERE office_id = :office_id
                GROUP BY people_pipeline
                ORDER BY people_pipeline
                """
                params = {"office_id": office_id}
            else:
                # Regular user sees only their people
                query = """
                SELECT 
                    people_pipeline as stage_name,
                    COUNT(*) as count
                FROM people
                WHERE user_id = :user_id
                GROUP BY people_pipeline
                ORDER BY people_pipeline
                """
                params = {"user_id": current_user.id}
                
            # Get the main pipeline name
            pipeline_name = "People Pipeline"
            total_contacts = stats['people_count']
            
        else:  # church type
            # Query directly from the churches table using the church_pipeline field
            if current_user.is_super_admin():
                # Super admin sees all churches
                query = """
                SELECT 
                    church_pipeline as stage_name,
                    COUNT(*) as count
                FROM churches
                GROUP BY church_pipeline
                ORDER BY church_pipeline
                """
                params = {}
            elif current_user.role == 'office_admin' or True:  # Regular users see office churches
                # Office admin or regular user sees churches in their office
                query = """
                SELECT 
                    church_pipeline as stage_name,
                    COUNT(*) as count
                FROM churches
                WHERE office_id = :office_id
                GROUP BY church_pipeline
                ORDER BY church_pipeline
                """
                params = {"office_id": office_id}
                
            # Get the main pipeline name
            pipeline_name = "Church Pipeline"
            total_contacts = stats['church_count']
        
        # Execute the query
        connection = db.engine.connect()
        try:
            result = connection.execute(text(query), params)
            results = result.fetchall()
        finally:
            connection.close()
        
        if not results:
            current_app.logger.warning(f"No results found for {chart_type} pipeline stages")
            return jsonify({
                "pipeline_id": 1,  # Use dummy ID
                "pipeline_name": pipeline_name,
                "stages": [],
                "total_contacts": total_contacts
            })
        
        # Format stages data
        stages = []
        stage_total = sum(row.count for row in results)
        
        # Define stage colors based on pipeline choices
        stage_colors = {
            # People pipeline stages
            'INFORMATION': '#2ecc71',  # Green
            'INVITATION': '#f1c40f',   # Yellow
            'CONFIRMATION': '#e67e22', # Orange
            'PROMOTION': '#3498db',    # Blue
            'AUTOMATION': '#1abc9c',   # Teal
            'EN42': '#9b59b6',         # Purple
            
            # Church pipeline stages
            'RESEARCH': '#3498db',     # Blue
            'CONTACT': '#2ecc71',      # Green
            'CONNECT': '#f1c40f',      # Yellow
            'COMMITTED': '#e67e22',    # Orange
            'COACHING': '#9b59b6',     # Purple
            'MULTIPLYING': '#1abc9c',  # Teal
        }
        
        for row in results:
            stage_name = row.stage_name or 'Unknown'
            count = row.count or 0
            
            # Calculate percentage
            percentage = 0
            if stage_total > 0:
                percentage = round((count / stage_total * 100), 1)
                
            # Get color for this stage
            color = stage_colors.get(stage_name, '#95a5a6')  # Default gray if not found
                
            stage_data = {
                "id": ord(stage_name[0]) if stage_name else 0,  # Use dummy ID based on first letter
                "name": stage_name,
                "color": color,
                "count": count,
                "percentage": percentage
            }
            stages.append(stage_data)
        
        # Sort stages by predefined order if needed
        stage_order = {
            # People pipeline order
            'INFORMATION': 1,
            'INVITATION': 2,
            'CONFIRMATION': 3,
            'PROMOTION': 4,
            'AUTOMATION': 5,
            'EN42': 6,
            
            # Church pipeline order
            'RESEARCH': 1,
            'CONTACT': 2,
            'CONNECT': 3,
            'COMMITTED': 4,
            'COACHING': 5,
            'MULTIPLYING': 6
        }
        
        # Sort stages by defined order
        stages.sort(key=lambda x: stage_order.get(x['name'], 999))
        
        response_data = {
            "pipeline_id": 1,  # Use dummy ID
            "pipeline_name": pipeline_name,
            "stages": stages,
            "total_contacts": total_contacts
        }
        
        # Log the response data for debugging
        current_app.logger.info(f"Returning {len(stages)} stages for {chart_type} pipeline. Total contacts: {total_contacts}")
        
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
    stats = {}
    
    try:
        # Use SQLAlchemy Core for more optimized queries
        from sqlalchemy import func, and_, text
        
        # For super admins, count all people and churches across all offices
        if current_user.is_super_admin():
            # Get counts in a single query using UNION
            counts_query = """
                SELECT 
                    (SELECT COUNT(*) FROM people) AS people_count,
                    (SELECT COUNT(*) FROM churches) AS church_count
            """
            result = db.session.execute(text(counts_query)).fetchone()
            stats['people_count'] = result[0] if result else 0
            stats['church_count'] = result[1] if result else 0
        else:
            # Get counts for specific office in a single query using UNION
            counts_query = """
                SELECT 
                    (SELECT COUNT(*) FROM people JOIN contacts ON people.id = contacts.id WHERE contacts.office_id = :office_id) AS people_count,
                    (SELECT COUNT(*) FROM churches JOIN contacts ON churches.id = contacts.id WHERE contacts.office_id = :office_id) AS church_count
            """
            result = db.session.execute(text(counts_query), {"office_id": office_id}).fetchone()
            stats['people_count'] = result[0] if result else 0
            stats['church_count'] = result[1] if result else 0
            
        # Get task counts in a single query
        tasks_query = """
            SELECT 
                (SELECT COUNT(*) FROM tasks WHERE assigned_to = :user_id AND status = 'pending') AS pending_tasks,
                (SELECT COUNT(*) FROM tasks WHERE assigned_to = :user_id AND status = 'pending' AND due_date < :today) AS overdue_tasks
        """
        task_result = db.session.execute(text(tasks_query), {
            "user_id": current_user.id,
            "today": datetime.now().date()
        }).fetchone()
        
        stats['pending_tasks'] = task_result[0] if task_result else 0
        stats['overdue_tasks'] = task_result[1] if task_result else 0
        
        # Count communications
        thirty_days_ago = datetime.now() - timedelta(days=30)
        if current_user.is_super_admin():
            communications_count = db.session.query(func.count(Communication.id)).filter(
                Communication.created_at >= thirty_days_ago
            ).scalar() or 0
        else:
            communications_count = db.session.query(func.count(Communication.id)).filter(
                Communication.office_id == office_id,
                Communication.created_at >= thirty_days_ago
            ).scalar() or 0
            
        stats['recent_communications'] = communications_count
        
    except Exception as e:
        current_app.logger.error(f"Error fetching dashboard stats: {str(e)}")
        # Provide default values if there's an error
        stats = {
            'people_count': 0,
            'church_count': 0,
            'pending_tasks': 0,
            'overdue_tasks': 0,
            'recent_communications': 0
        }
    
    return stats 