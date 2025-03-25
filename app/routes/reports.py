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


@reports_bp.route('/widgets/contacts', methods=['GET'])
@login_required
@office_member_required
def contacts_widget():
    """
    Widget showing contact statistics
    """
    office_id = current_user.current_office_id
    total_contacts = Person.query.filter_by(office_id=office_id).count()
    new_contacts_30d = Person.query.filter_by(office_id=office_id).filter(
        Person.created_at >= datetime.datetime.now() - datetime.timedelta(days=30)
    ).count()
    
    return jsonify({
        'total_contacts': total_contacts,
        'new_contacts_30d': new_contacts_30d
    })


@reports_bp.route('/widgets/churches', methods=['GET'])
@login_required
@office_member_required
def churches_widget():
    """
    Widget showing church statistics
    """
    office_id = current_user.current_office_id
    total_churches = Church.query.filter_by(office_id=office_id).count()
    new_churches_30d = Church.query.filter_by(office_id=office_id).filter(
        Church.created_at >= datetime.datetime.now() - datetime.timedelta(days=30)
    ).count()
    
    return jsonify({
        'total_churches': total_churches,
        'new_churches_30d': new_churches_30d
    })


@reports_bp.route('/widgets/tasks', methods=['GET'])
@login_required
@office_member_required
def tasks_widget():
    """
    Widget showing task statistics
    """
    office_id = current_user.current_office_id
    total_tasks = Task.query.filter_by(office_id=office_id).count()
    completed_tasks = Task.query.filter_by(office_id=office_id, status='completed').count()
    overdue_tasks = Task.query.filter_by(office_id=office_id, status='open').filter(
        Task.due_date < datetime.datetime.now().date()
    ).count()
    
    return jsonify({
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2)
    })


@reports_bp.route('/widgets/communications', methods=['GET'])
@login_required
@office_member_required
def communications_widget():
    """
    Widget showing communication statistics
    """
    office_id = current_user.current_office_id
    total_comms = Communication.query.filter_by(office_id=office_id).count()
    emails = Communication.query.filter_by(office_id=office_id, type='email').count()
    calls = Communication.query.filter_by(office_id=office_id, type='call').count()
    meetings = Communication.query.filter_by(office_id=office_id, type='meeting').count()
    
    return jsonify({
        'total_communications': total_comms,
        'emails': emails,
        'calls': calls,
        'meetings': meetings
    })


@reports_bp.route('/export/<entity_type>', methods=['POST'])
@login_required
@office_member_required
def export_data(entity_type):
    """
    Export data in CSV or Excel format
    """
    format_type = request.form.get('format', 'csv')
    office_id = current_user.current_office_id
    
    if entity_type == 'contacts':
        data = Person.query.filter_by(office_id=office_id).all()
        columns = ['id', 'first_name', 'last_name', 'email', 'phone', 'address', 'status', 'created_at']
        filename = f"contacts_export_{datetime.datetime.now().strftime('%Y%m%d')}"
    
    elif entity_type == 'churches':
        data = Church.query.filter_by(office_id=office_id).all()
        columns = ['id', 'name', 'pastor_name', 'email', 'phone', 'address', 'created_at']
        filename = f"churches_export_{datetime.datetime.now().strftime('%Y%m%d')}"
    
    elif entity_type == 'tasks':
        data = Task.query.filter_by(office_id=office_id).all()
        columns = ['id', 'title', 'description', 'status', 'priority', 'due_date', 'assigned_to_id', 'created_at']
        filename = f"tasks_export_{datetime.datetime.now().strftime('%Y%m%d')}"
    
    elif entity_type == 'communications':
        data = Communication.query.filter_by(office_id=office_id).all()
        columns = ['id', 'person_id', 'type', 'subject', 'content', 'created_at']
        filename = f"communications_export_{datetime.datetime.now().strftime('%Y%m%d')}"
    
    else:
        return jsonify({'error': 'Invalid entity type'}), 400
    
    # Convert data to list of dicts
    data_list = []
    for item in data:
        item_dict = {}
        for col in columns:
            item_dict[col] = getattr(item, col)
        data_list.append(item_dict)
    
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
        
        office_id = current_user.current_office_id
        
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