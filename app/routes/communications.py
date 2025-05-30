from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models.communication import Communication
from app.models.person import Person
from app.models.church import Church
from app.models.email_signature import EmailSignature
from app.models.email_template import EmailTemplate
from app.extensions import db, cache
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from sqlalchemy.orm import joinedload
import json
from app.utils.decorators import office_required
from app.utils.upload import save_uploaded_file
from app.utils.time import format_date
from app.utils.query_optimization import optimize_query, with_pagination, cached_query

communications_bp = Blueprint('communications', __name__, template_folder='../templates/communications')

# Helper function to get default signature
def get_default_signature(user_id):
    """Get the default signature for a user"""
    try:
        # Log the incoming user_id for debugging
        current_app.logger.info(f"Getting default signature for user_id: {user_id} (type: {type(user_id)})")
        
        # Try with the original user_id (likely an integer)
        signature = EmailSignature.query.filter_by(
            user_id=user_id,
            is_default=True
        ).first()
        
        if signature:
            current_app.logger.info(f"Found signature with original user_id: {user_id}")
            return signature
            
        # If not found, try with string conversion as fallback
        user_id_str = str(user_id)
        current_app.logger.info(f"No signature found with original user_id, trying string version: {user_id_str}")
        
        # Use raw SQL to avoid SQLAlchemy type casting
        signature = db.session.execute(
            text("SELECT * FROM email_signatures WHERE user_id = :user_id AND is_default = TRUE LIMIT 1"),
            {"user_id": user_id_str}
        ).fetchone()
        
        if signature:
            current_app.logger.info(f"Found signature with string user_id: {user_id_str}")
            # Convert row proxy to EmailSignature object
            return EmailSignature.query.get(signature.id)
            
        current_app.logger.warning(f"No default signature found for user_id: {user_id}")
        return None
    except Exception as e:
        current_app.logger.error(f"Error getting default signature: {str(e)}")
        current_app.logger.exception("Full traceback for signature error:")
        return None

@communications_bp.route('/')
@communications_bp.route('/index')
@login_required
def index():
    """Display communications hub."""
    try:
        # Check if database is configured properly
        if not current_app.config.get('SQLALCHEMY_DATABASE_URI') and not current_app.config.get('DATABASE_URL'):
            current_app.logger.error("Database connection not configured properly")
            flash('Database connection not configured. Please check your environment variables.', 'error')
            return render_template('error.html', error_message="Database connection not configured", page_title="Error")
            
        current_app.logger.info("Starting communications index route")
        start_time = datetime.now()
        
        # Manually load email signatures with proper type conversion
        try:
            # Log the current user ID for debugging
            current_app.logger.info(f"Loading email signatures for user_id: {current_user.id} (type: {type(current_user.id)})")
            
            # Try with the original user_id (integer)
            from app.models.email_signature import EmailSignature
            signatures = EmailSignature.query.filter_by(user_id=current_user.id).all()
            
            if signatures:
                current_app.logger.info(f"Found {len(signatures)} signatures with integer user_id")
                current_user.email_signatures = signatures
            else:
                # If not found, try with string conversion as fallback
                user_id_str = str(current_user.id)
                current_app.logger.info(f"No signatures found with integer ID, trying string version: {user_id_str}")
                
                # Use raw SQL to avoid SQLAlchemy type casting
                result = db.session.execute(
                    text("SELECT id FROM email_signatures WHERE user_id = :user_id"),
                    {"user_id": user_id_str}
                ).fetchall()
                
                if result:
                    signature_ids = [row[0] for row in result]
                    current_app.logger.info(f"Found {len(signature_ids)} signatures with string user_id: {signature_ids}")
                    current_user.email_signatures = EmailSignature.query.filter(EmailSignature.id.in_(signature_ids)).all()
                else:
                    current_app.logger.warning(f"No email signatures found for user_id: {current_user.id}")
                    current_user.email_signatures = []
            
            current_app.logger.info(f"Loaded {len(current_user.email_signatures)} email signatures")
        except Exception as e:
            current_app.logger.error(f"Error loading email signatures: {str(e)}")
            current_app.logger.exception("Full traceback for email signature error:")
            current_user.email_signatures = []
        
        # Get filter parameters
        person_id = request.args.get('person_id')
        church_id = request.args.get('church_id')
        
        # Convert IDs to integers if they exist to avoid type mismatch
        try:
            person_id = int(person_id) if person_id else None
        except (ValueError, TypeError):
            person_id = None
            current_app.logger.warning(f"Invalid person_id format: {person_id}")
        
        try:
            church_id = int(church_id) if church_id else None
        except (ValueError, TypeError):
            church_id = None
            current_app.logger.warning(f"Invalid church_id format: {church_id}")
            
        comm_type = request.args.get('type')
        direction = request.args.get('direction')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)  # Default to 50 items per page
        
        # Build query with eager loading to prevent N+1 query problems
        query = Communication.query.options(
            joinedload(Communication.person),
            joinedload(Communication.church)
        )
        
        # Apply filters
        if person_id:
            query = query.filter(Communication.person_id == person_id)
        if church_id:
            query = query.filter(Communication.church_id == church_id)
        if comm_type:
            query = query.filter(Communication.type == comm_type)
        if direction:
            query = query.filter(Communication.direction == direction)
        
        # Apply date range filter if provided
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                query = query.filter(Communication.date_sent >= start_date_obj)
            except ValueError:
                current_app.logger.warning(f"Invalid start_date format: {start_date}")
        
        if end_date:
            try:
                # Set end_date to end of day
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                query = query.filter(Communication.date_sent <= end_date_obj)
            except ValueError:
                current_app.logger.warning(f"Invalid end_date format: {end_date}")
        
        # Filter by office if not super admin
        if current_user.role != 'super_admin':
            # Use the office's ID (integer) instead of the office_id (which might be a UUID string)
            if hasattr(current_user, 'office') and current_user.office:
                query = query.filter(Communication.office_id == current_user.office.id)
            else:
                query = query.filter(Communication.office_id == current_user.office_id)
        
        # Order by date sent descending
        query = query.order_by(Communication.date_sent.desc())
        
        # Apply pagination to avoid loading too many records at once
        try:
            communications, pagination = with_pagination(query, page=page, per_page=per_page)
        except Exception as e:
            current_app.logger.error(f"Error in pagination: {str(e)}")
            communications = []
            pagination = {
                'page': 1,
                'per_page': 50,
                'total': 0,
                'pages': 0,
                'has_next': False,
                'has_prev': False
            }
        
        # Log performance metrics
        elapsed_time = (datetime.now() - start_time).total_seconds()
        if elapsed_time > 0.5:  # Log if it took more than 500ms
            current_app.logger.warning(f"Communications index took {elapsed_time:.2f}s to load")
        
        return render_template('communications/index.html', 
                              communications=communications,
                              pagination=pagination,
                              page_title="Communications Hub")
    except Exception as e:
        current_app.logger.error(f"Error in communications index: {str(e)}")
        current_app.logger.exception("Full traceback:")
        flash('Error loading communications. Please try again later.', 'error')
        return render_template('error.html', error_message=f"Error: {str(e)}", page_title="Error")

@communications_bp.route('/test')
@login_required
def test_page():
    """Test page that uses the actual template but with empty data"""
    try:
        current_app.logger.info("Loading test communications page with actual template")
        
        # Manually load email signatures with proper type conversion
        try:
            # Log the current user ID for debugging
            current_app.logger.info(f"Loading email signatures for user_id: {current_user.id} (type: {type(current_user.id)})")
            
            # Try with the original user_id (integer)
            from app.models.email_signature import EmailSignature
            signatures = EmailSignature.query.filter_by(user_id=current_user.id).all()
            
            if signatures:
                current_app.logger.info(f"Found {len(signatures)} signatures with integer user_id")
                current_user.email_signatures = signatures
            else:
                # If not found, try with string conversion as fallback
                user_id_str = str(current_user.id)
                current_app.logger.info(f"No signatures found with integer ID, trying string version: {user_id_str}")
                
                # Use raw SQL to avoid SQLAlchemy type casting
                result = db.session.execute(
                    text("SELECT id FROM email_signatures WHERE user_id = :user_id"),
                    {"user_id": user_id_str}
                ).fetchall()
                
                if result:
                    signature_ids = [row[0] for row in result]
                    current_app.logger.info(f"Found {len(signature_ids)} signatures with string user_id: {signature_ids}")
                    current_user.email_signatures = EmailSignature.query.filter(EmailSignature.id.in_(signature_ids)).all()
                else:
                    current_app.logger.warning(f"No email signatures found for user_id: {current_user.id}")
                    current_user.email_signatures = []
            
            current_app.logger.info(f"Loaded {len(current_user.email_signatures)} email signatures")
        except Exception as e:
            current_app.logger.error(f"Error loading email signatures: {str(e)}")
            current_app.logger.exception("Full traceback for email signature error:")
            current_user.email_signatures = []
        
        # Try to render the actual template but with empty data
        return render_template('communications/index.html', 
                              communications=[],
                              pagination={
                                  'page': 1,
                                  'per_page': 50,
                                  'total': 0,
                                  'pages': 0,
                                  'has_next': False,
                                  'has_prev': False
                              },
                              page_title="Communications Test")
    except Exception as e:
        current_app.logger.error(f"Error in test communications page: {str(e)}")
        current_app.logger.exception("Full traceback:")
        return render_template('error.html', error_message=f"Error: {str(e)}", page_title="Error")
