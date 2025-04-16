from flask import Blueprint, render_template, request, jsonify, send_file, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
import io
import csv
import json
import datetime
from ..models.user import User
from ..models.person import Person
from ..models.church import Church
from ..models.task import Task
from ..models.communication import Communication
from ..models.office import Office
from ..models.pipeline import Pipeline, PipelineStage, PipelineContact
from ..auth.permissions import admin_required, office_member_required
from ..utils.export import generate_csv, generate_excel
from ..extensions import db

# Create Blueprint for reports
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/', methods=['GET'])
@login_required
@office_member_required
def reports_dashboard():
    """
    Main reports dashboard showing available reports and widgets
    """
    return render_template('reports/dashboard.html')


@reports_bp.route('/widget-test', methods=['GET'])
@login_required
@office_member_required
def widget_test():
    """
    Test page for widgets
    """
    current_app.logger.info(f"Widget test page accessed by user {current_user.id}")
    return render_template('reports/widget_test.html')


@reports_bp.route('/widgets/contacts', methods=['GET'])
@login_required
@office_member_required
def contacts_widget():
    """
    Widget showing contact statistics
    """
    try:
        # Add debug logging
        current_app.logger.info(f"Contacts widget accessed by user {current_user.id}, office_id={current_user.office_id}")
        
        office_id = current_user.office_id
        if not office_id:
            current_app.logger.warning(f"User {current_user.id} has no office_id")
            return jsonify({
                'total_contacts': 0,
                'new_contacts_30d': 0
            })
        
        # Use explicit session query with error handling
        try:
            # Total contacts - use scalar() with fallback
            total_contacts_query = db.session.query(db.func.count(Person.id)).filter(
                Person.office_id == office_id
            )
            current_app.logger.debug(f"Total contacts query: {str(total_contacts_query)}")
            total_contacts = total_contacts_query.scalar() or 0
            
            # New contacts within last 30 days
            thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
            new_contacts_query = db.session.query(db.func.count(Person.id)).filter(
                Person.office_id == office_id,
                Person.created_at >= thirty_days_ago
            )
            current_app.logger.debug(f"New contacts query: {str(new_contacts_query)}")
            new_contacts_30d = new_contacts_query.scalar() or 0
            
        except Exception as db_error:
            current_app.logger.error(f"Database error in contacts_widget: {str(db_error)}")
            import traceback
            current_app.logger.error(f"DB Error details: {traceback.format_exc()}")
            return jsonify({
                'error': f"Database error: {str(db_error)}",
                'total_contacts': 0,
                'new_contacts_30d': 0
            }), 200
        
        # Successfully retrieved data
        response_data = {
            'total_contacts': total_contacts,
            'new_contacts_30d': new_contacts_30d
        }
        current_app.logger.info(f"Contacts widget data: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error in contacts_widget: {str(e)}")
        current_app.logger.error(f"Error details: {error_details}")
        return jsonify({
            'error': str(e),
            'total_contacts': 0,
            'new_contacts_30d': 0
        }), 200  # Return 200 instead of 500 to allow client to handle the data


@reports_bp.route('/widgets/churches', methods=['GET'])
@login_required
@office_member_required
def churches_widget():
    """
    Widget showing church statistics
    """
    try:
        # Add debug logging
        current_app.logger.debug(f"Churches widget accessed by user {current_user.id}, office_id={current_user.office_id}")
        
        office_id = current_user.office_id
        if not office_id:
            current_app.logger.warning(f"User {current_user.id} has no office_id")
            return jsonify({
                'total_churches': 0,
                'new_churches_30d': 0
            })
        
        total_churches = Church.query.filter_by(office_id=office_id).count()
        new_churches_30d = Church.query.filter_by(office_id=office_id).filter(
            Church.created_at >= datetime.datetime.now() - datetime.timedelta(days=30)
        ).count()
        
        response_data = {
            'total_churches': total_churches,
            'new_churches_30d': new_churches_30d
        }
        current_app.logger.debug(f"Churches widget data: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error in churches_widget: {str(e)}")
        current_app.logger.error(f"Error details: {error_details}")
        return jsonify({
            'error': str(e),
            'total_churches': 0,
            'new_churches_30d': 0
        }), 200  # Return 200 instead of 500 to allow client to handle the data


@reports_bp.route('/widgets/tasks', methods=['GET'])
@login_required
@office_member_required
def tasks_widget():
    """
    Widget showing task statistics
    """
    try:
        # Add debug logging
        current_app.logger.debug(f"Tasks widget accessed by user {current_user.id}, office_id={current_user.office_id}")
        
        office_id = current_user.office_id
        if not office_id:
            current_app.logger.warning(f"User {current_user.id} has no office_id")
            return jsonify({
                'total_tasks': 0,
                'completed_tasks': 0,
                'overdue_tasks': 0,
                'completion_rate': 0
            })
        
        # Get total tasks count
        total_tasks = db.session.query(db.func.count(Task.id)).filter(Task.office_id == office_id).scalar() or 0
        
        # Fix: use 'completed' status instead of 'open'
        completed_tasks = db.session.query(db.func.count(Task.id)).filter(
            Task.office_id == office_id, 
            Task.status == 'completed'
        ).scalar() or 0
        
        # Fix: use 'pending' or other statuses for overdue tasks, not 'open'
        overdue_tasks = db.session.query(db.func.count(Task.id)).filter(
            Task.office_id == office_id,
            Task.status.in_(['pending', 'in_progress', 'on_hold']),
            Task.due_date < datetime.datetime.now().date()
        ).scalar() or 0
        
        # Fix: avoid division by zero
        completion_rate = 0
        if total_tasks > 0:
            completion_rate = round((completed_tasks / total_tasks * 100), 2)
        
        response_data = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'overdue_tasks': overdue_tasks,
            'completion_rate': completion_rate
        }
        current_app.logger.debug(f"Tasks widget data: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error in tasks_widget: {str(e)}")
        current_app.logger.error(f"Error details: {error_details}")
        return jsonify({
            'error': str(e),
            'total_tasks': 0,
            'completed_tasks': 0,
            'overdue_tasks': 0,
            'completion_rate': 0
        }), 200  # Return 200 instead of 500 to allow client to handle the data


@reports_bp.route('/widgets/communications', methods=['GET'])
@login_required
@office_member_required
def communications_widget():
    """
    Widget showing communication statistics
    """
    try:
        # Add debug logging
        current_app.logger.debug(f"Communications widget accessed by user {current_user.id}, office_id={current_user.office_id}")
        
        office_id = current_user.office_id
        if not office_id:
            current_app.logger.warning(f"User {current_user.id} has no office_id")
            return jsonify({
                'total_communications': 0,
                'emails': 0,
                'calls': 0,
                'meetings': 0
            })
        
        # Use scalar() with fallback to 0 to handle None values
        total_comms = db.session.query(db.func.count(Communication.id)).filter(
            Communication.office_id == office_id
        ).scalar() or 0
        
        # Fix: use the correct field names for the communication types
        emails = db.session.query(db.func.count(Communication.id)).filter(
            Communication.office_id == office_id, 
            Communication.type == 'email'
        ).scalar() or 0
        
        calls = db.session.query(db.func.count(Communication.id)).filter(
            Communication.office_id == office_id, 
            Communication.type == 'phone'
        ).scalar() or 0
        
        meetings = db.session.query(db.func.count(Communication.id)).filter(
            Communication.office_id == office_id, 
            Communication.type == 'meeting'
        ).scalar() or 0
        
        response_data = {
            'total_communications': total_comms,
            'emails': emails,
            'calls': calls,
            'meetings': meetings
        }
        current_app.logger.debug(f"Communications widget data: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error in communications_widget: {str(e)}")
        current_app.logger.error(f"Error details: {error_details}")
        return jsonify({
            'error': str(e),
            'total_communications': 0,
            'emails': 0,
            'calls': 0,
            'meetings': 0
        }), 200  # Return 200 instead of 500 to allow client to handle the data


@reports_bp.route('/export/<entity_type>', methods=['POST'])
@login_required
@office_member_required
def export_data(entity_type):
    """
    Export data in CSV or Excel format
    """
    try:
        current_app.logger.info(f"Export requested for {entity_type} by user {current_user.id}")
        format_type = request.form.get('format', 'csv')
        current_app.logger.debug(f"Export format: {format_type}")
        
        # Check if entity type is valid
        valid_types = ['contacts', 'churches', 'tasks', 'communications']
        if entity_type not in valid_types:
            current_app.logger.warning(f"Invalid entity type for export: {entity_type}")
            flash('Invalid entity type', 'error')
            return redirect(url_for('reports.reports_dashboard'))
            
        # Use office_id directly 
        office_id = current_user.office_id
        if not office_id:
            current_app.logger.warning(f"User {current_user.id} has no office_id for export")
            flash('You must be associated with an office to export data', 'error')
            return redirect(url_for('reports.reports_dashboard'))
        
        # Configure export based on entity type
        if entity_type == 'contacts':
            query = db.session.query(Person).filter(Person.office_id == office_id)
            columns = ['id', 'first_name', 'last_name', 'email', 'phone', 'address', 'status', 'created_at']
            filename = f"contacts_export_{datetime.datetime.now().strftime('%Y%m%d')}"
        
        elif entity_type == 'churches':
            query = db.session.query(Church).filter(Church.office_id == office_id)
            columns = ['id', 'name', 'pastor_name', 'email', 'phone', 'address', 'created_at']
            filename = f"churches_export_{datetime.datetime.now().strftime('%Y%m%d')}"
        
        elif entity_type == 'tasks':
            query = db.session.query(Task).filter(Task.office_id == office_id)
            columns = ['id', 'title', 'description', 'status', 'priority', 'due_date', 'assigned_to_id', 'created_at']
            filename = f"tasks_export_{datetime.datetime.now().strftime('%Y%m%d')}"
        
        elif entity_type == 'communications':
            query = db.session.query(Communication).filter(Communication.office_id == office_id)
            columns = ['id', 'person_id', 'type', 'subject', 'content', 'created_at']
            filename = f"communications_export_{datetime.datetime.now().strftime('%Y%m%d')}"
            
        # Execute query with exception handling
        try:
            data = query.all()
            current_app.logger.info(f"Found {len(data)} records for {entity_type} export")
        except Exception as db_error:
            current_app.logger.error(f"Database error during export: {str(db_error)}")
            import traceback
            current_app.logger.error(f"DB Error details: {traceback.format_exc()}")
            flash(f'Database error while fetching data: {str(db_error)}', 'error')
            return redirect(url_for('reports.reports_dashboard'))
        
        # Convert data to list of dicts
        data_list = []
        for item in data:
            item_dict = {}
            for col in columns:
                # Handle AttributeError for any missing attributes
                try:
                    value = getattr(item, col)
                    # Handle datetime objects
                    if isinstance(value, (datetime.date, datetime.datetime)):
                        value = value.isoformat()
                    item_dict[col] = value
                except AttributeError:
                    item_dict[col] = None
            data_list.append(item_dict)
        
        current_app.logger.debug(f"Generating {format_type} export with {len(data_list)} rows")
        
        # Generate and return the export file
        try:
            if format_type == 'csv':
                return generate_csv(data_list, columns, filename)
            elif format_type == 'excel':
                return generate_excel(data_list, columns, filename)
            else:
                current_app.logger.warning(f"Invalid format type for export: {format_type}")
                flash('Invalid format type', 'error')
                return redirect(url_for('reports.reports_dashboard'))
        except Exception as export_error:
            current_app.logger.error(f"Error generating export file: {str(export_error)}")
            import traceback
            current_app.logger.error(f"Export error details: {traceback.format_exc()}")
            flash(f'Error generating export file: {str(export_error)}', 'error')
            return redirect(url_for('reports.reports_dashboard'))
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error exporting {entity_type}: {str(e)}")
        current_app.logger.error(f"Error details: {error_details}")
        flash(f'An error occurred while exporting data: {str(e)}', 'error')
        return redirect(url_for('reports.reports_dashboard'))


@reports_bp.route('/export/pipeline/<int:pipeline_id>', methods=['POST'])
@login_required
@office_member_required
def export_pipeline(pipeline_id):
    """
    Export pipeline contacts with their stages in CSV or Excel format
    """
    format_type = request.form.get('format', 'csv')
    office_id = current_user.office_id
    
    # Get pipeline and verify access
    pipeline = Pipeline.query.get_or_404(pipeline_id)
    if pipeline.office_id != office_id and not current_user.is_super_admin():
        flash('You do not have permission to export this pipeline.', 'danger')
        return redirect(url_for('pipeline.index'))
    
    # Get all contacts in this pipeline
    pipeline_contacts = PipelineContact.query.filter_by(pipeline_id=pipeline_id).all()
    
    # Prepare data for export
    data_list = []
    for pc in pipeline_contacts:
        contact = pc.contact
        stage = pc.current_stage
        
        if not contact or not stage:
            continue
            
        # Skip if contact type doesn't match pipeline type
        if pipeline.pipeline_type not in ['both', contact.contact_type]:
            continue
            
        contact_data = {
            'pipeline_contact_id': pc.id,
            'stage_name': stage.name,
            'days_in_stage': (datetime.datetime.utcnow() - pc.last_updated).days if pc.last_updated else 0,
            'entered_pipeline': pc.entered_at.strftime('%Y-%m-%d') if pc.entered_at else '',
            'last_updated': pc.last_updated.strftime('%Y-%m-%d') if pc.last_updated else ''
        }
        
        # Add contact-specific fields based on type
        if contact.contact_type == 'person':
            contact_data.update({
                'contact_id': contact.id,
                'contact_type': 'Person',
                'first_name': getattr(contact, 'first_name', ''),
                'last_name': getattr(contact, 'last_name', ''),
                'email': getattr(contact, 'email', ''),
                'phone': getattr(contact, 'phone', ''),
                'status': getattr(contact, 'status', '')
            })
        else:  # church
            contact_data.update({
                'contact_id': contact.id,
                'contact_type': 'Church',
                'name': getattr(contact, 'name', ''),
                'pastor_name': getattr(contact, 'pastor_name', ''),
                'email': getattr(contact, 'email', ''),
                'phone': getattr(contact, 'phone', '')
            })
            
        data_list.append(contact_data)
    
    # Define columns based on pipeline type
    if pipeline.pipeline_type == 'person':
        columns = ['pipeline_contact_id', 'contact_id', 'first_name', 'last_name', 'email', 'phone', 
                  'status', 'stage_name', 'days_in_stage', 'entered_pipeline', 'last_updated']
    elif pipeline.pipeline_type == 'church':
        columns = ['pipeline_contact_id', 'contact_id', 'name', 'pastor_name', 'email', 'phone',
                  'stage_name', 'days_in_stage', 'entered_pipeline', 'last_updated']
    else:  # both
        columns = ['pipeline_contact_id', 'contact_id', 'contact_type', 'first_name', 'last_name', 'name', 
                  'pastor_name', 'email', 'phone', 'stage_name', 'days_in_stage', 'entered_pipeline', 'last_updated']
    
    filename = f"{pipeline.name.replace(' ', '_')}_export_{datetime.datetime.now().strftime('%Y%m%d')}"
    
    if format_type == 'csv':
        return generate_csv(data_list, columns, filename)
    elif format_type == 'excel':
        return generate_excel(data_list, columns, filename)
    else:
        return jsonify({'error': 'Invalid format type'}), 400


@reports_bp.route('/custom', methods=['GET', 'POST'])
@login_required
@office_member_required
def custom_report():
    """
    Custom report generator
    """
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        include_fields = request.form.getlist('fields')
        format_type = request.form.get('format', 'csv')
        
        # Convert string dates to datetime objects
        try:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('reports.custom_report'))
        
        # Ensure we use office_id
        office_id = current_user.office_id
        
        # Generate the appropriate report based on report type
        if report_type == 'contact_activity':
            # Query communications related to contacts in date range
            report_data = generate_contact_activity_report(office_id, start_date, end_date, include_fields)
            filename = f"contact_activity_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            
        elif report_type == 'volunteer_activity':
            # Query tasks and activities by volunteers
            report_data = generate_volunteer_report(office_id, start_date, end_date, include_fields)
            filename = f"volunteer_activity_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            
        elif report_type == 'church_engagement':
            # Query church engagement metrics
            report_data = generate_church_report(office_id, start_date, end_date, include_fields)
            filename = f"church_engagement_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            
        else:
            flash('Invalid report type', 'error')
            return redirect(url_for('reports.custom_report'))
        
        if format_type == 'csv':
            return generate_csv(report_data['data'], report_data['columns'], filename)
        elif format_type == 'excel':
            return generate_excel(report_data['data'], report_data['columns'], filename)
        else:
            flash('Invalid format type', 'error')
            return redirect(url_for('reports.custom_report'))
    
    return render_template('reports/custom_report.html')


def generate_contact_activity_report(office_id, start_date, end_date, include_fields):
    """Helper function to generate contact activity report"""
    query = db.session.query(
        Person,
        db.func.count(Communication.id).label('communication_count')
    ).outerjoin(
        Communication, Person.id == Communication.person_id
    ).filter(
        Person.office_id == office_id,
        Communication.created_at.between(start_date, end_date)
    ).group_by(Person.id)
    
    results = query.all()
    
    data = []
    for person, comm_count in results:
        person_data = {
            'id': person.id,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'email': person.email,
            'communication_count': comm_count
        }
        data.append(person_data)
    
    columns = ['id', 'first_name', 'last_name', 'email', 'communication_count']
    
    return {'data': data, 'columns': columns}


def generate_volunteer_report(office_id, start_date, end_date, include_fields):
    """Helper function to generate volunteer activity report"""
    query = db.session.query(
        User,
        db.func.count(Task.id).label('task_count'),
        db.func.sum(db.case([(Task.status == 'completed', 1)], else_=0)).label('completed_tasks')
    ).outerjoin(
        Task, User.id == Task.assigned_to_id
    ).filter(
        User.offices.any(Office.id == office_id),
        Task.created_at.between(start_date, end_date)
    ).group_by(User.id)
    
    results = query.all()
    
    data = []
    for user, task_count, completed_tasks in results:
        user_data = {
            'id': user.id,
            'name': f"{user.first_name} {user.last_name}",
            'email': user.email,
            'assigned_tasks': task_count,
            'completed_tasks': completed_tasks,
            'completion_rate': round((completed_tasks / task_count * 100) if task_count > 0 else 0, 2)
        }
        data.append(user_data)
    
    columns = ['id', 'name', 'email', 'assigned_tasks', 'completed_tasks', 'completion_rate']
    
    return {'data': data, 'columns': columns}


def generate_church_report(office_id, start_date, end_date, include_fields):
    """Helper function to generate church engagement report"""
    # Implementation will depend on your specific data model and relationships
    # This is a placeholder implementation
    churches = Church.query.filter_by(office_id=office_id).all()
    
    data = []
    for church in churches:
        church_data = {
            'id': church.id,
            'name': church.name,
            'pastor_name': church.pastor_name,
            'contact_count': Person.query.filter_by(church_id=church.id).count(),
        }
        data.append(church_data)
    
    columns = ['id', 'name', 'pastor_name', 'contact_count']
    
    return {'data': data, 'columns': columns} 