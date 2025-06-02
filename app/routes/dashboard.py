from flask import Blueprint, render_template, request, current_app, url_for, redirect, flash, g, session, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc, func, text
from app.extensions import db, cache
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.task import Task
from app.models.communication import Communication
from app.models.church import Church
from app.models.user import User
from app.models.person import Person
from app.utils.decorators import office_required
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/debug')
@login_required
@office_required
def debug():
    """Render the dashboard debug page."""
    return render_template('dashboard/debug.html')

@dashboard_bp.route('/api/debug/pipelines')
@login_required
@office_required
def debug_pipelines():
    """Debug endpoint to check pipeline data."""
    try:
        # Get main pipelines
        main_pipelines = Pipeline.query.filter_by(is_main_pipeline=True).all()
        
        result = []
        for pipeline in main_pipelines:
            pipeline_data = {
                'id': pipeline.id,
                'name': pipeline.name,
                'type': pipeline.pipeline_type,
                'stages': []
            }
            
            # Get stages for this pipeline
            stages = PipelineStage.query.filter_by(pipeline_id=pipeline.id).order_by(PipelineStage.order).all()
            for stage in stages:
                # Count contacts in this stage
                if pipeline.pipeline_type in ['person', 'people']:
                    count = db.session.query(PipelineContact).join(
                        Person, Person.id == PipelineContact.contact_id
                    ).filter(
                        PipelineContact.pipeline_id == pipeline.id,
                        PipelineContact.current_stage_id == stage.id
                    ).count()
                    
                    # Also get the actual people
                    people = db.session.query(Person).join(
                        PipelineContact, Person.id == PipelineContact.contact_id
                    ).filter(
                        PipelineContact.pipeline_id == pipeline.id,
                        PipelineContact.current_stage_id == stage.id
                    ).all()
                    
                    people_list = [{'id': p.id, 'name': f"{p.first_name} {p.last_name}"} for p in people]
                else:
                    count = db.session.query(PipelineContact).join(
                        Church, Church.id == PipelineContact.contact_id
                    ).filter(
                        PipelineContact.pipeline_id == pipeline.id,
                        PipelineContact.current_stage_id == stage.id
                    ).count()
                    
                    # Also get the actual churches
                    churches = db.session.query(Church).join(
                        PipelineContact, Church.id == PipelineContact.contact_id
                    ).filter(
                        PipelineContact.pipeline_id == pipeline.id,
                        PipelineContact.current_stage_id == stage.id
                    ).all()
                    
                    people_list = [{'id': c.id, 'name': c.name} for c in churches]
                
                pipeline_data['stages'].append({
                    'id': stage.id,
                    'name': stage.name,
                    'order': stage.order,
                    'color': stage.color,
                    'count': count,
                    'contacts': people_list
                })
                
            result.append(pipeline_data)
            
        # Also get all people and churches
        all_people = Person.query.count()
        all_churches = Church.query.count()
        
        # Get all pipeline contacts
        all_pipeline_contacts = PipelineContact.query.count()
        
        # Add summary info
        result.append({
            'summary': {
                'total_people': all_people,
                'total_churches': all_churches,
                'total_pipeline_contacts': all_pipeline_contacts
            }
        })
            
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in debug_pipelines: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
        office_id = int(current_user.office_id) if current_user.office_id else None
        
        # Get dashboard statistics
        stats = get_dashboard_stats()
        
        # Now check if the user is a super admin
        is_super_admin = fresh_user.role == 'super_admin'
    except Exception as e:
        current_app.logger.error(f"Error in dashboard index: {str(e)}")
        current_app.logger.exception("Full traceback for dashboard index error:")
        current_app.logger.info(f"Request URL at error: {request.url}")
        current_app.logger.info(f"Request Headers at error: {dict(request.headers)}")
        current_app.logger.info(f"Request Args at error: {request.args}")
        current_app.logger.info(f"User ID at error: {current_user.id}, Type: {type(current_user.id)}")
        if hasattr(current_user, 'office'):
            current_app.logger.info(f"User Office at error: {current_user.office}, Office ID: {getattr(current_user.office, 'id', None)}, Type: {type(getattr(current_user.office, 'id', None))}")
        else:
            current_app.logger.info("User has no office attribute at error")
        flash('An error occurred while loading the dashboard. Please try again later.', 'error')
        return render_template('error.html', error_message="An error occurred", page_title="Error")
        
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


# Old chart data endpoints have been removed to avoid route conflicts
# All chart data requests now use the new endpoint at /api/chart-data/<pipeline_type>


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

@dashboard_bp.route('/api/chart-data/<pipeline_type>', methods=['GET'])
def pipeline_chart_data(pipeline_type=None):
    """API endpoint to get pipeline chart data (legacy).
    This endpoint has been temporarily disabled.
    """
    # Return a message indicating the endpoint is disabled
    return jsonify({
        'error': 'Charts disabled',
        'message': 'Chart functionality has been temporarily disabled'
    }), 503  # Service Unavailable

@dashboard_bp.route('/api/simple-chart-data/<pipeline_type>', methods=['GET'])
def simple_pipeline_chart_data(pipeline_type=None):
    """API endpoint to get simplified pipeline chart data.
    This endpoint requires authentication and will return a 401 if not authenticated.
    """
    # Check if user is authenticated
    if not current_user.is_authenticated:
        return jsonify({
            'error': 'Authentication required',
            'message': 'You must be logged in to access this endpoint'
        }), 401
        
    # Check if user has an office
    if not current_user.office_id:
        return jsonify({
            'error': 'Office required',
            'message': 'You must be assigned to an office to access this endpoint'
        }), 403
    
    try:
        # Log request details for debugging
        current_app.logger.info(f"Simple chart data requested for pipeline type: {pipeline_type}")
        
        # Validate pipeline type
        if pipeline_type not in ['person', 'church']:
            current_app.logger.warning(f"Invalid pipeline type requested: {pipeline_type}")
            return jsonify({
                'error': f"Invalid pipeline type: {pipeline_type}"
            }), 400
            
        # Get user's office
        office_id = int(current_user.office_id) if current_user.office_id else None
        is_super_admin = current_user.role == 'super_admin'
        
        # Find the appropriate pipeline
        if pipeline_type == 'person':
            # For person type, check both 'person' and 'people' types
            pipeline_query = Pipeline.query.filter(
                Pipeline.is_main_pipeline == True,
                or_(Pipeline.pipeline_type == 'person', Pipeline.pipeline_type == 'people')
            )
        else:
            # For church type
            pipeline_query = Pipeline.query.filter(
                Pipeline.is_main_pipeline == True,
                Pipeline.pipeline_type == pipeline_type
            )
        
        # Filter by office unless super admin
        if not is_super_admin:
            pipeline_query = pipeline_query.filter(Pipeline.office_id == office_id)
            
        pipeline = pipeline_query.first()
        
        if not pipeline:
            current_app.logger.warning(f"No {pipeline_type} pipeline found for office {office_id}")
            return jsonify({
                'error': f"No {pipeline_type} pipeline found for your office"
            }), 404
            
        # Get pipeline stages with counts
        stages_data = []
        total_contacts = 0
        
        # Get all stages for this pipeline
        stages = PipelineStage.query.filter_by(pipeline_id=pipeline.id).order_by(PipelineStage.order).all()
        
        if not stages:
            current_app.logger.warning(f"No stages found for pipeline {pipeline.id}")
            return jsonify({
                'error': f"No stages found for {pipeline_type} pipeline"
            }), 404
            
        # For each stage, get the count of contacts
        for stage in stages:
            try:
                if pipeline_type == 'person':
                    # Count people in this stage using the PipelineContact table
                    count = db.session.query(PipelineContact).join(
                        Person, Person.id == PipelineContact.contact_id
                    ).filter(
                        PipelineContact.pipeline_id == pipeline.id,
                        PipelineContact.current_stage_id == stage.id
                    ).count()
                else:
                    # Count churches in this stage using the PipelineContact table
                    count = db.session.query(PipelineContact).join(
                        Church, Church.id == PipelineContact.contact_id
                    ).filter(
                        PipelineContact.pipeline_id == pipeline.id,
                        PipelineContact.current_stage_id == stage.id
                    ).count()
                
                # Log the count for debugging
                current_app.logger.info(f"Stage {stage.name} has {count} contacts")
                    
                stages_data.append({
                    'id': stage.id,
                    'name': stage.name,
                    'position': stage.order,
                    'color': stage.color or get_default_color(stage.name),
                    'contact_count': count
                })
                
                total_contacts += count
            except Exception as stage_error:
                current_app.logger.error(f"Error processing stage {stage.id}: {str(stage_error)}")
                # Continue with other stages even if one fails
            
        # Calculate percentages
        for stage in stages_data:
            if total_contacts > 0:
                stage['percentage'] = round((stage['contact_count'] / total_contacts) * 100)
            else:
                stage['percentage'] = 0
                
        # Return the data
        response_data = {
            'pipeline_id': pipeline.id,
            'pipeline_name': pipeline.name,
            'pipeline_type': pipeline_type,
            'total_contacts': total_contacts,
            'stages': stages_data
        }
        
        current_app.logger.info(f"Successfully generated simple chart data for {pipeline_type} pipeline with {total_contacts} total contacts")
        return jsonify(response_data)
            
    except Exception as e:
        current_app.logger.error(f"Error generating simple chart data: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@dashboard_bp.route('/dashboard/debug/chart-data/<chart_type>')
@dashboard_bp.route('/dashboard/fallback-chart-data/<chart_type>')
@login_required
def debug_chart_data(chart_type):
    """Endpoint to get pipeline chart data based on user role."""
    current_app.logger.info(f"Pipeline chart data requested for type: {chart_type} by user {current_user.id}")
    
    try:
        # Get statistics for totals
        stats = get_dashboard_stats()
        office_id = int(current_user.office_id) if current_user.office_id else None
        
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
                "pipeline_id": pipeline_id,  # Use actual pipeline ID
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
            "pipeline_id": pipeline_id,  # Use actual pipeline ID
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
            office_id = int(current_user.office_id) if current_user.office_id else None
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
