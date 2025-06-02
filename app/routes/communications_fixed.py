from flask import Blueprint, render_template, request, flash, current_app
from flask_login import login_required, current_user
from app.models.communication import Communication
from app.models.email_signature import EmailSignature
from app.extensions import db
from datetime import datetime, timezone
from sqlalchemy import text, or_
from sqlalchemy.orm import joinedload
import traceback

communications_fixed_bp = Blueprint('communications_fixed', __name__, template_folder='../templates')

# Helper function to get default signature
def get_default_signature(user_id):
    """Get the default signature for a user with robust type handling"""
    try:
        # Log the incoming user_id for debugging
        current_app.logger.info(f"Getting default signature for user_id: {user_id} (type: {type(user_id)})")
        
        # Try with both integer and string versions using SQLAlchemy OR condition
        # This is more efficient than running two separate queries
        user_id_str = str(user_id)
        
        signature = EmailSignature.query.filter(
            or_(
                EmailSignature.user_id == user_id,  # Try with original type
                EmailSignature.user_id == user_id_str  # Try with string conversion
            ),
            EmailSignature.is_default.is_(True)
        ).first()
        
        if signature:
            current_app.logger.info(f"Found default signature for user: {user_id}")
            return signature
            
        # If still not found, try with raw SQL as a last resort
        current_app.logger.info("No signature found with ORM query, trying raw SQL as last resort")
        
        # Use raw SQL to avoid SQLAlchemy type casting
        result = db.session.execute(
            text("SELECT id FROM email_signatures WHERE user_id::TEXT = :user_id_str AND is_default = TRUE LIMIT 1"),
            {"user_id_str": user_id_str}
        ).fetchone()
        
        if result:
            current_app.logger.info("Found signature with raw SQL query")
            # Convert row proxy to EmailSignature object
            return EmailSignature.query.get(result.id)
            
        current_app.logger.warning(f"No default signature found for user_id: {user_id}")
        return None
    except Exception as e:
        current_app.logger.error(f"Error getting default signature: {str(e)}")
        current_app.logger.exception("Full traceback for signature error:")
        return None

@communications_fixed_bp.route('/')
@communications_fixed_bp.route('/index')
@login_required
def index():
    """Display communications hub with robust type handling."""
    try:
        # Check if database is configured properly
        if not current_app.config.get('SQLALCHEMY_DATABASE_URI') and not current_app.config.get('DATABASE_URL'):
            current_app.logger.error("Database connection not configured properly")
            flash('Database connection not configured. Please check your environment variables.', 'error')
            return render_template('error.html', error_message="Database connection not configured", page_title="Error")
            
        current_app.logger.info("Starting fixed communications index route")
        start_time = datetime.now()
        
        # Manually load email signatures with robust type handling
        try:
            # Log the current user ID for debugging
            current_app.logger.info(f"Loading email signatures for user_id: {current_user.id} (type: {type(current_user.id)})")
            
            # Try with both integer and string versions using SQLAlchemy OR condition
            user_id_str = str(current_user.id)
            
            signatures = EmailSignature.query.filter(
                or_(
                    EmailSignature.user_id == current_user.id,  # Try with original type
                    EmailSignature.user_id == user_id_str  # Try with string conversion
                )
            ).all()
            
            if signatures:
                current_app.logger.info(f"Found {len(signatures)} signatures with OR condition query")
                current_user.email_signatures = signatures
            else:
                # If still not found, try with raw SQL as a last resort
                current_app.logger.info("No signatures found with ORM query, trying raw SQL as last resort")
                
                # Use raw SQL with explicit text casting to handle type differences
                result = db.session.execute(
                    text("SELECT id FROM email_signatures WHERE user_id::TEXT = :user_id_str"),
                    {"user_id_str": user_id_str}
                ).fetchall()
                
                if result:
                    signature_ids = [row[0] for row in result]
                    current_app.logger.info(f"Found {len(signature_ids)} signatures with raw SQL query")
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
                start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                query = query.filter(Communication.date >= start_date)
            except ValueError:
                current_app.logger.warning(f"Invalid start_date format: {start_date}")
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                query = query.filter(Communication.date <= end_date)
            except ValueError:
                current_app.logger.warning(f"Invalid end_date format: {end_date}")
        
        # Filter by current user's office with robust type handling
        try:
            if hasattr(current_user, 'office') and current_user.office:
                # Use the office.id (integer) instead of office_id (which might be a string UUID)
                office_id = current_user.office.id if hasattr(current_user.office, 'id') else None
                
                if office_id is not None:
                    current_app.logger.info(f"Filtering by office_id: {office_id} (type: {type(office_id)})")
                    query = query.filter(Communication.office_id == office_id)
                else:
                    current_app.logger.warning("User has office but office.id is None")
            else:
                current_app.logger.warning("User has no office attribute or it's None")
        except Exception as e:
            current_app.logger.error(f"Error filtering by office: {str(e)}")
            current_app.logger.exception("Full traceback for office filter error:")
        
        # Order by date descending (newest first)
        query = query.order_by(Communication.date.desc())
        
        # Apply pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        communications = pagination.items
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        current_app.logger.info(f"Communications query executed in {execution_time:.2f} seconds")
        
        # Log the number of communications found
        current_app.logger.info(f"Found {len(communications)} communications (page {page} of {pagination.pages})")
        
        # Render template with data
        return render_template('communications/index.html',
                            communications=communications,
                            pagination=pagination,
                            person_id=person_id,
                            church_id=church_id,
                            type=comm_type,
                            direction=direction,
                            start_date=request.args.get('start_date'),
                            end_date=request.args.get('end_date'),
                            page_title="Communications Hub")
    
    except Exception as e:
        current_app.logger.error(f"Error in communications index: {str(e)}")
        current_app.logger.exception("Full traceback for communications index error:")
        
        # Return a more detailed error page
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'user_id': current_user.id if hasattr(current_user, 'id') else 'Unknown',
            'user_id_type': type(current_user.id).__name__ if hasattr(current_user, 'id') else 'Unknown'
        }
        
        # Convert error_details to a string for display
        error_details_str = '\n'.join([f"{k}: {v}" for k, v in error_details.items()])
        
        flash(f"Error: {str(e)}", 'danger')
        return render_template('error.html', 
                            error_message=f"Error: {str(e)}", 
                            error_details=error_details_str,
                            page_title="Error")

@communications_fixed_bp.route('/test')
@login_required
def test_page():
    """Test page that uses the actual template but with empty data"""
    try:
        current_app.logger.info("Loading test communications page with actual template")
        
        # Manually load email signatures with robust type handling
        try:
            # Log the current user ID for debugging
            current_app.logger.info(f"Loading email signatures for user_id: {current_user.id} (type: {type(current_user.id)})")
            
            # Try with both integer and string versions using SQLAlchemy OR condition
            user_id_str = str(current_user.id)
            
            signatures = EmailSignature.query.filter(
                or_(
                    EmailSignature.user_id == current_user.id,  # Try with original type
                    EmailSignature.user_id == user_id_str  # Try with string conversion
                )
            ).all()
            
            if signatures:
                current_app.logger.info(f"Found {len(signatures)} signatures with OR condition query")
                current_user.email_signatures = signatures
            else:
                # If still not found, try with raw SQL as a last resort
                current_app.logger.info("No signatures found with ORM query, trying raw SQL as last resort")
                
                # Use raw SQL with explicit text casting to handle type differences
                result = db.session.execute(
                    text("SELECT id FROM email_signatures WHERE user_id::TEXT = :user_id_str"),
                    {"user_id_str": user_id_str}
                ).fetchall()
                
                if result:
                    signature_ids = [row[0] for row in result]
                    current_app.logger.info(f"Found {len(signature_ids)} signatures with raw SQL query")
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
        
        # Convert error details to a string for display
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'user_id': current_user.id if hasattr(current_user, 'id') else 'Unknown',
            'user_id_type': type(current_user.id).__name__ if hasattr(current_user, 'id') else 'Unknown'
        }
        error_details_str = '\n'.join([f"{k}: {v}" for k, v in error_details.items()])
        
        flash(f"Error: {str(e)}", 'danger')
        return render_template('error.html', 
                            error_message=f"Error: {str(e)}", 
                            error_details=error_details_str,
                            page_title="Error")
