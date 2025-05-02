from flask import Blueprint, render_template, request, current_app, url_for, redirect, flash, g, session, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc, func, text
from app.extensions import db, cache
from app.models.pipeline import Pipeline, PipelineStage
from app.models.task import Task
from app.models.communication import Communication
from app.models.church import Church
from app.models.user import User
from app.models.person import Person
from app.utils.decorators import office_required
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
@office_required
def index():
    """Render the dashboard view with relevant statistics."""
    # First get a fresh user object to avoid DetachedInstanceError
    try:
        # First try to get the user ID safely
        try:
            # Try to get the ID directly from the session if possible
            from flask import session
            user_id = session.get('_user_id')
            if not user_id:
                # Fall back to the current_user object
                user_id = current_user.get_id()
        except Exception as id_error:
            current_app.logger.error(f"Error getting user ID: {str(id_error)}")
            # If we can't get the ID from current_user, try to get it from the session
            from flask import session
            user_id = session.get('_user_id')
            if not user_id:
                # If all else fails, redirect to login
                flash('Session expired. Please log in again.', 'warning')
                return redirect(url_for('auth.login'))
        
        # Now get a fresh user object
        from app.models.user import User
        fresh_user = User.query.get(user_id)
        if not fresh_user:
            # If user not found, redirect to login
            flash('User not found. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
            
        # Store the fresh user in g for this request
        g.fresh_user = fresh_user
        db.session.add(fresh_user)
        
        # Check if this is the user's first login
        if fresh_user.first_login:
            return redirect(url_for('onboarding.welcome'))
            
        # Get the office ID from the fresh user
        office_id = fresh_user.office_id
        
        # Get dashboard statistics
        stats = get_dashboard_stats()
        
        # Now check if the user is a super admin
        is_super_admin = fresh_user.role == 'super_admin'
    except Exception as e:
        current_app.logger.error(f"Error in dashboard index: {str(e)}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
        
    if is_super_admin:
        # Super admins see Main Office pipelines by default
        pipeline_query = Pipeline.query.filter(
            Pipeline.is_main_pipeline,
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
            Pipeline.is_main_pipeline,
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
    
    # Get pending tasks for the user
    pending_tasks_count = Task.query.filter(
        Task.assigned_to == user_id,
        Task.status == 'pending'
    ).count()
    
    # Get overdue tasks for the user
    overdue_tasks_count = Task.query.filter(
        Task.assigned_to == user_id,
        Task.status == 'pending',
        Task.due_date < datetime.now().date()
    ).count()
    
    # Log pipeline information for debugging
    if people_pipeline:
        # Convert AppenderQuery to list before getting length
        stages_count = len(list(people_pipeline.stages)) if hasattr(people_pipeline, 'stages') else 0
        current_app.logger.info(f"Found people pipeline: {people_pipeline.id} with {stages_count} stages")
    else:
        current_app.logger.warning(f"No people pipeline found for office {office_id}")
        
    if church_pipeline:
        # Convert AppenderQuery to list before getting length
        stages_count = len(list(church_pipeline.stages)) if hasattr(church_pipeline, 'stages') else 0
        current_app.logger.info(f"Found church pipeline: {church_pipeline.id} with {stages_count} stages")
    else:
        current_app.logger.warning(f"No church pipeline found for office {office_id}")
    
    # Get pending tasks for the sidebar
    pending_tasks = Task.query.filter(
        Task.assigned_to == user_id,
        Task.status == 'pending'
    ).order_by(Task.due_date).limit(5).all()
    
    # Render the dashboard template with the data
    return render_template('dashboard/index.html',
        stats=stats,
        people_pipeline=people_pipeline,
        church_pipeline=church_pipeline,
        pending_tasks_count=pending_tasks_count,
        overdue_tasks_count=overdue_tasks_count,
        pending_tasks=pending_tasks,
        user=fresh_user
    )


# Since dashboard_bp is mounted at '/', 
# this will be accessible at /dashboard/api/stats
@dashboard_bp.route('/dashboard/api/stats')
@login_required
def dashboard_stats_api():
    """API endpoint to get updated dashboard statistics."""
    try:
        # Get a fresh user object to avoid DetachedInstanceError
        try:
            # Try to get the user ID from session first
            user_id = session.get('_user_id')
            if not user_id:
                # Fall back to current_user
                user_id = current_user.get_id()
                
            # Get a fresh user object
            fresh_user = User.query.get(user_id)
            if not fresh_user:
                return jsonify({"error": "User not found"}), 401
        except Exception as e:
            current_app.logger.error(f"Error getting user in dashboard stats API: {str(e)}")
            return jsonify({"error": "Authentication error"}), 401
            
        # Get dashboard statistics
        stats = get_dashboard_stats()
        
        # Return the stats as JSON
        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f"Error in dashboard stats API: {str(e)}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route('/dashboard/api/chart-data/<pipeline_type>', methods=['GET'])
@dashboard_bp.route('/dashboard/pipeline-chart-data', methods=['GET'])
@login_required
def pipeline_chart_data(pipeline_type=None):
    """API endpoint to get pipeline chart data."""
    # If pipeline_type is None, get it from the query parameter
    if pipeline_type is None:
        pipeline_type = request.args.get('type')
        current_app.logger.info(f"Pipeline chart data requested with query param type={pipeline_type} by user {current_user.id}")
    else:
        current_app.logger.info(f"Pipeline chart data requested for path param type: {pipeline_type} by user {current_user.id}")
    try:
        # Get a fresh user object to avoid DetachedInstanceError
        try:
            # Try to get the user ID from session first
            user_id = session.get('_user_id')
            if not user_id:
                # Fall back to current_user
                user_id = current_user.get_id()
                
            # Get a fresh user object
            fresh_user = User.query.get(user_id)
            if not fresh_user:
                return jsonify({"error": "User not found"}), 401
                
            # Get the office ID from the fresh user
            office_id = fresh_user.office_id
            is_super_admin = fresh_user.role == 'super_admin'
        except Exception as e:
            current_app.logger.error(f"Error getting user in pipeline chart data: {str(e)}")
            return jsonify({"error": "Authentication error"}), 401
        
        # Validate pipeline type
        if pipeline_type not in ['person', 'church']:
            return jsonify({"error": f"Invalid pipeline type: {pipeline_type}"}), 400
        
        # Get statistics for totals
        stats = get_dashboard_stats()
        
        # Choose the right query and parameters based on pipeline type and user role
        if pipeline_type == 'person':
            # Find the main people pipeline
            current_app.logger.info("Looking for main people pipeline")
            main_pipeline = db.session.execute(
                text("SELECT id, name FROM pipelines WHERE pipeline_type IN ('person', 'people') AND is_main_pipeline = TRUE LIMIT 1")
            ).fetchone()
            
            if not main_pipeline:
                current_app.logger.warning("No main people pipeline found, looking for any people pipeline")
                main_pipeline = db.session.execute(
                    text("SELECT id, name FROM pipelines WHERE pipeline_type IN ('person', 'people') LIMIT 1")
                ).fetchone()
                
            if not main_pipeline:
                current_app.logger.error("No people pipeline found")
                return jsonify({
                    "error": "No people pipeline found",
                    "pipeline_id": None,
                    "pipeline_name": "People Pipeline",
                    "stages": [],
                    "total_contacts": 0
                })
                
            pipeline_id = main_pipeline[0]
            pipeline_name = main_pipeline[1] or "People Pipeline"
            current_app.logger.info(f"Found people pipeline: {pipeline_id} - {pipeline_name}")
            
            # Query pipeline stages
            query = """
            SELECT 
                ps.id as stage_id,
                ps.name as stage_name,
                ps.color as stage_color,
                COUNT(pc.id) as count
            FROM pipeline_stages ps
            LEFT JOIN pipeline_contacts pc ON ps.id = pc.current_stage_id
            WHERE ps.pipeline_id = :pipeline_id
            GROUP BY ps.id, ps.name, ps.color
            ORDER BY ps.order
            """
            
            # Get the main pipeline name
            total_contacts = stats.get('people_count', 0)
            params = {"pipeline_id": pipeline_id}
            
        else:  # church type
            # Find the main church pipeline
            current_app.logger.info("Looking for main church pipeline")
            main_pipeline = db.session.execute(
                text("SELECT id, name FROM pipelines WHERE pipeline_type = 'church' AND is_main_pipeline = TRUE LIMIT 1")
            ).fetchone()
            
            if not main_pipeline:
                current_app.logger.warning("No main church pipeline found, looking for any church pipeline")
                main_pipeline = db.session.execute(
                    text("SELECT id, name FROM pipelines WHERE pipeline_type = 'church' LIMIT 1")
                ).fetchone()
                
            if not main_pipeline:
                current_app.logger.error("No church pipeline found")
                return jsonify({
                    "error": "No church pipeline found",
                    "pipeline_id": None,
                    "pipeline_name": "Church Pipeline",
                    "stages": [],
                    "total_contacts": 0
                })
                
            pipeline_id = main_pipeline[0]
            pipeline_name = main_pipeline[1] or "Church Pipeline"
            current_app.logger.info(f"Found church pipeline: {pipeline_id} - {pipeline_name}")
            
            # Query pipeline stages
            query = """
            SELECT 
                ps.id as stage_id,
                ps.name as stage_name,
                ps.color as stage_color,
                COUNT(pc.id) as count
            FROM pipeline_stages ps
            LEFT JOIN pipeline_contacts pc ON ps.id = pc.current_stage_id
            WHERE ps.pipeline_id = :pipeline_id
            GROUP BY ps.id, ps.name, ps.color
            ORDER BY ps.order
            """
            
            # Get the main pipeline name
            total_contacts = stats.get('church_count', 0)
            params = {"pipeline_id": pipeline_id}
        
        # Execute the query
        connection = db.engine.connect()
        try:
            result = connection.execute(text(query), params)
            results = result.fetchall()
        finally:
            connection.close()
        
        # Process the results
        stages = []
        stage_total = 0
        
        # Calculate total for percentage
        for row in results:
            stage_total += row.count if row.count else 0
        
        if not results:
            current_app.logger.warning(f"No results found for {pipeline_type} pipeline stages")
            return jsonify({
                "pipeline_id": pipeline_id,
                "pipeline_name": pipeline_name,
                "stages": [],
                "total_contacts": total_contacts
            })
        
        current_app.logger.info(f"Found {len(results)} stages for {pipeline_type} pipeline with {stage_total} total contacts")
        
        for row in results:
            stage_name = row.stage_name or 'Unknown'
            count = row.count or 0
            
            # Calculate percentage
            percentage = 0
            if stage_total > 0:
                percentage = round((count / stage_total) * 100, 1)
            
            # Get color from the database or use a default
            color = row.stage_color or get_default_color(stage_name)
            
            # Add stage to the list
            stages.append({
                'id': len(stages) + 1,  # Generate sequential ID
                'name': stage_name,
                'count': count,
                'percentage': percentage,
                'color': color
            })
        
        # Define stage order for sorting
        stage_order = {
            'NEW': 1,
            'CONTACT': 2,
            'CONNECT': 3,
            'COMMITTED': 4,
            'COACHING': 5,
            'MULTIPLYING': 6
        }
        
        # Sort stages by defined order
        stages.sort(key=lambda x: stage_order.get(x['name'].upper(), 999))
        
        response_data = {
            "pipeline_id": 1,  # Use dummy ID
            "pipeline_name": pipeline_name,
            "stages": stages,
            "total_contacts": total_contacts
        }
        
        # Log the response data for debugging
        current_app.logger.info(f"Returning {len(stages)} stages for {pipeline_type} pipeline. Total contacts: {total_contacts}")
        
        return jsonify(response_data)
    
    except Exception as e:
        current_app.logger.error(f"Error getting pipeline chart data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "pipeline_id": None,
            "pipeline_name": f"Error loading {pipeline_type} pipeline",
            "stages": [],
            "total_contacts": 0
        }), 500


@dashboard_bp.route('/dashboard/debug/pipeline-data')
@login_required
def debug_pipeline_data():
    """Debug endpoint to check pipeline data directly from the database."""
    try:
        # Get a fresh user object to avoid DetachedInstanceError
        try:
            # Try to get the user ID from session first
            user_id = session.get('_user_id')
            if not user_id:
                # Fall back to current_user
                user_id = current_user.get_id()
                
            # Get a fresh user object
            fresh_user = User.query.get(user_id)
            if not fresh_user:
                return jsonify({"error": "User not found"}), 401
                
            # Only super admins can access this endpoint
            if fresh_user.role != 'super_admin':
                return jsonify({"error": "Unauthorized"}), 403
        except Exception as e:
            current_app.logger.error(f"Error getting user in debug pipeline data: {str(e)}")
            return jsonify({"error": "Authentication error"}), 401
        
        # Query all pipelines
        pipelines = Pipeline.query.all()
        pipeline_data = []
        
        for pipeline in pipelines:
            # Query stages for this pipeline
            stages = PipelineStage.query.filter_by(pipeline_id=pipeline.id).all()
            stage_data = []
            
            for stage in stages:
                stage_data.append({
                    "id": stage.id,
                    "name": stage.name,
                    "order": stage.order,
                    "color": stage.color
                })
            
            pipeline_data.append({
                "id": pipeline.id,
                "name": pipeline.name,
                "type": pipeline.pipeline_type,
                "office_id": pipeline.office_id,
                "is_main_pipeline": pipeline.is_main_pipeline,
                "stages": stage_data
            })
        
        return jsonify({
            "pipelines": pipeline_data
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in debug pipeline data: {str(e)}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route('/dashboard/debug/chart-data/<chart_type>')
@dashboard_bp.route('/dashboard/fallback-chart-data/<chart_type>')
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
            # Check if user has access to the requested pipeline
            # Get a fresh user object to avoid DetachedInstanceError
            from app.models.user import User
            fresh_user = User.query.get(current_user.id)
            
            if fresh_user.role == 'super_admin':
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
            else:
                # Regular user sees only their people
                query = """
                SELECT 
                    people_pipeline as stage_name,
                    COUNT(*) as count
                FROM people
                JOIN contacts ON people.id = contacts.id
                WHERE contacts.office_id = :office_id
                GROUP BY people_pipeline
                ORDER BY people_pipeline
                """
                params = {"office_id": office_id}
                
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
            else:
                # Regular user sees only their churches
                query = """
                SELECT 
                    church_pipeline as stage_name,
                    COUNT(*) as count
                FROM churches
                JOIN contacts ON churches.id = contacts.id
                WHERE contacts.office_id = :office_id
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
        
        # Process the results
        stages = []
        stage_total = 0
        
        # Calculate total for percentage
        for row in results:
            stage_total += row.count if row.count else 0
        
        if not results:
            current_app.logger.warning(f"No results found for {chart_type} pipeline stages")
            return jsonify({
                "pipeline_id": 1,  # Use dummy ID
                "pipeline_name": pipeline_name,
                "stages": [],
                "total_contacts": total_contacts
            })
        
        # Define colors for stages
        stage_colors = {
            'NEW': '#3498db',          # Blue
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
                percentage = round((count / stage_total) * 100, 1)
            
            # Get color for the stage
            color = stage_colors.get(stage_name.upper(), get_default_color(stage_name))
            
            # Add stage to the list
            stages.append({
                'id': len(stages) + 1,  # Generate sequential ID
                'name': stage_name,
                'count': count,
                'percentage': percentage,
                'color': color
            })
        
        # Define stage order for sorting
        stage_order = {
            'NEW': 1,
            'CONTACT': 2,
            'CONNECT': 3,
            'COMMITTED': 4,
            'COACHING': 5,
            'MULTIPLYING': 6
        }
        
        # Sort stages by defined order
        stages.sort(key=lambda x: stage_order.get(x['name'].upper(), 999))
        
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
    if 'interest' in name:
        return '#2ecc71'  # Green
    if 'application' in name:
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
    try:
        # Get a fresh user object to avoid DetachedInstanceError
        try:
            # Try to get the user ID from session first
            user_id = session.get('_user_id')
            if not user_id:
                # Fall back to current_user
                user_id = current_user.get_id()
                
            # Get a fresh user object
            fresh_user = User.query.get(user_id)
            if not fresh_user:
                current_app.logger.error("User not found in get_dashboard_stats")
                return {}
                
            # Get the office ID from the fresh user
            office_id = fresh_user.office_id
            is_super_admin = fresh_user.role == 'super_admin'
        except Exception as e:
            current_app.logger.error(f"Error getting user in dashboard stats: {str(e)}")
            return {}
            
        stats = {}
        
        # Use SQLAlchemy Core for more optimized queries
        from sqlalchemy import func, text
        
        # For super admins, count all people and churches across all offices
        if is_super_admin:
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
            "user_id": user_id,
            "today": datetime.now().date()
        }).fetchone()
        
        stats['pending_tasks'] = task_result[0] if task_result else 0
        stats['overdue_tasks'] = task_result[1] if task_result else 0
        
        # Count communications
        thirty_days_ago = datetime.now() - timedelta(days=30)
        if is_super_admin:
            communications_count = db.session.query(func.count(Communication.id)).filter(
                Communication.created_at >= thirty_days_ago
            ).scalar() or 0
        else:
            communications_count = db.session.query(func.count(Communication.id)).filter(
                Communication.office_id == office_id,
                Communication.created_at >= thirty_days_ago
            ).scalar() or 0
            
        stats['recent_communications'] = communications_count
        
        return stats
        
    except Exception as e:
        current_app.logger.error(f"Error fetching dashboard stats: {str(e)}")
        # Provide default values if there's an error
        return {
            'people_count': 0,
            'church_count': 0,
            'pending_tasks': 0,
            'overdue_tasks': 0,
            'recent_communications': 0
        }
