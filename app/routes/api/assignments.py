from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app.models.user import User
from app.models.person import Person
from app.models.church import Church
from app.extensions import db
from app.utils.decorators import admin_required

assignments_api_bp = Blueprint('assignments_api', __name__)

@assignments_api_bp.route('/api/assign-people', methods=['POST'])
@assignments_api_bp.route('/assign-people', methods=['POST'])
@login_required
@admin_required
def api_assign_people():
    """API endpoint to assign people to a user."""
    current_app.logger.info('=== API ASSIGN PEOPLE REQUEST ===')    
    data = request.get_json()
    
    if not data:
        current_app.logger.error('No JSON data in request')
        return jsonify({'error': 'No data provided'}), 400
    
    user_id = data.get('user_id')
    person_ids = data.get('person_ids', [])
    
    current_app.logger.info(f'User ID: {user_id}, Person IDs: {person_ids}')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    if not person_ids:
        return jsonify({'error': 'At least one person must be selected'}), 400
    
    # Create a new session for this operation to avoid connection pool issues
    session = db.create_scoped_session()
    
    try:
        # Get the user to assign to
        user = session.query(User).get(user_id)
        if not user:
            return jsonify({'error': 'Selected user not found'}), 404
        
        # Check if office admin is trying to assign to users outside their office
        if not current_user.is_super_admin() and user.office_id != current_user.office_id:
            return jsonify({'error': 'You can only assign to users in your office'}), 403
        
        # Use a more efficient query approach with fewer connections
        query = session.query(Person).filter(Person.id.in_(person_ids))
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            query = query.filter_by(office_id=current_user.office_id)
        
        # Update all records in a single query to reduce database load
        updated_count = query.update({
            Person.assigned_to: user.username,
            Person.updated_at: datetime.now()
        }, synchronize_session=False)
        
        current_app.logger.info(f'Updated {updated_count} people assignments')
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{updated_count} people assigned to {user.full_name}',
            'count': updated_count
        })
    except Exception as e:
        session.rollback()
        current_app.logger.error(f'Error assigning people: {str(e)}')
        current_app.logger.error(f'Error details: {type(e).__name__}')
        current_app.logger.exception('Full traceback:')
        return jsonify({'error': f'Error assigning people: {str(e)}'}), 500
    finally:
        # Ensure the session is closed to return connection to pool
        try:
            session.close()
        except Exception as e:
            current_app.logger.error(f'Error closing session: {str(e)}')

@assignments_api_bp.route('/api/assign-churches', methods=['POST'])
@assignments_api_bp.route('/assign-churches', methods=['POST'])
@login_required
@admin_required
def api_assign_churches():
    """API endpoint to assign churches to a user."""
    current_app.logger.info('=== API ASSIGN CHURCHES REQUEST ===')
    data = request.get_json()
    
    if not data:
        current_app.logger.error('No JSON data in request')
        return jsonify({'error': 'No data provided'}), 400
    
    user_id = data.get('user_id')
    church_ids = data.get('church_ids', [])
    
    current_app.logger.info(f'User ID: {user_id}, Church IDs: {church_ids}')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    if not church_ids:
        return jsonify({'error': 'At least one church must be selected'}), 400
    
    # Create a new session for this operation to avoid connection pool issues
    session = db.create_scoped_session()
    
    try:
        # Get the user to assign to
        user = session.query(User).get(user_id)
        if not user:
            return jsonify({'error': 'Selected user not found'}), 404
        
        # Check if office admin is trying to assign to users outside their office
        if not current_user.is_super_admin() and user.office_id != current_user.office_id:
            return jsonify({'error': 'You can only assign to users in your office'}), 403
        
        # Use a more efficient query approach with fewer connections
        query = session.query(Church).filter(Church.id.in_(church_ids))
        
        # Filter by office for non-super admins
        if not current_user.is_super_admin():
            query = query.filter_by(office_id=current_user.office_id)
        
        # Update all records in a single query to reduce database load
        updated_count = query.update({
            Church.assigned_to: user.username,
            Church.updated_at: datetime.now()
        }, synchronize_session=False)
        
        current_app.logger.info(f'Updated {updated_count} church assignments')
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{updated_count} churches assigned to {user.full_name}',
            'count': updated_count
        })
    except Exception as e:
        session.rollback()
        current_app.logger.error(f'Error assigning churches: {str(e)}')
        current_app.logger.error(f'Error details: {type(e).__name__}')
        current_app.logger.exception('Full traceback:')
        return jsonify({'error': f'Error assigning churches: {str(e)}'}), 500
    finally:
        # Ensure the session is closed to return connection to pool
        try:
            session.close()
        except Exception as e:
            current_app.logger.error(f'Error closing session: {str(e)}')
