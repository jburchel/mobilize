from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models.communication import Communication
from app.models.person import Person
from app.models.church import Church
from app.models.email_signature import EmailSignature
from app.models.email_template import EmailTemplate
from app.extensions import db, cache
from datetime import datetime, timezone, timedelta
from sqlalchemy import text, or_
from sqlalchemy.orm import joinedload
import json
import traceback
from app.utils.decorators import office_required
from app.utils.upload import save_uploaded_file
from app.utils.time import format_date
from app.utils.query_optimization import optimize_query, with_pagination, cached_query

communications_bp = Blueprint('communications', __name__, template_folder='../templates/communications')

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
            EmailSignature.is_default == True
        ).first()
        
        if signature:
            current_app.logger.info(f"Found default signature for user: {user_id}")
            return signature
            
        # If still not found, try with raw SQL as a last resort
        current_app.logger.info(f"No signature found with ORM query, trying raw SQL as last resort")
        
        # Use raw SQL to avoid SQLAlchemy type casting
        result = db.session.execute(
            text("SELECT id FROM email_signatures WHERE user_id::TEXT = :user_id_str AND is_default = TRUE LIMIT 1"),
            {"user_id_str": user_id_str}
        ).fetchone()
        
        if result:
            current_app.logger.info(f"Found signature with raw SQL query")
            # Convert row proxy to EmailSignature object
            return EmailSignature.query.get(result.id)
            
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
        
        # Ensure office_id is treated as an integer in queries
        office_id = int(current_user.office_id) if current_user.office_id else None
        
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
        
        # Restrict to user's office with explicit type conversion
        if office_id:
            query = query.filter(Communication.office_id == office_id)
            current_app.logger.info(f"Filtering communications by office_id: {office_id}")
        
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
                              per_page=per_page)
    except Exception as e:
        # Rollback any failed transactions to prevent cascading errors
        db.session.rollback()
        
        current_app.logger.error(f"Error in communications index: {str(e)}")
        current_app.logger.exception("Full traceback for communications index error:")
        current_app.logger.info(f"Request URL at error: {request.url}")
        current_app.logger.info(f"Request Headers at error: {dict(request.headers)}")
        current_app.logger.info(f"Request Args at error: {request.args}")
        current_app.logger.info(f"User ID at error: {current_user.id}, Type: {type(current_user.id)}")
        if hasattr(current_user, 'office'):
            current_app.logger.info(f"User Office at error: {current_user.office}, Office ID: {getattr(current_user.office, 'id', None)}, Type: {type(getattr(current_user.office, 'id', None))}")
        else:
            current_app.logger.info("User has no office attribute at error")
        flash('An error occurred while loading communications. Please try again later.', 'error')
        return render_template('error.html', error_message="An error occurred", page_title="Error")

@communications_bp.route('/signatures', methods=['GET', 'POST'])
@login_required
def signatures():
    """Manage email signatures"""
    try:
        current_app.logger.info(f"User {current_user.id} accessed signatures page")
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'create' or action == 'update':
                # Get form data
                signature_id = request.form.get('signature_id')
                name = request.form.get('name')
                content = request.form.get('content', '')
                is_default = request.form.get('is_default') == 'on'
                
                # Convert line breaks to HTML
                content = content.replace('\n', '<br>').replace('\r', '<br>')
                
                # Handle logo upload if present
                logo_url = None
                if 'logo' in request.files and request.files['logo'].filename:
                    try:
                        logo_url = save_uploaded_file(request.files['logo'], 'signatures')
                    except Exception as e:
                        current_app.logger.error(f"Error uploading signature logo: {str(e)}")
                        flash(f"Error uploading logo: {str(e)}", 'danger')
                
                try:
                    if action == 'create':
                        # Create new signature
                        signature = EmailSignature(
                            name=name,
                            content=content,
                            logo_url=logo_url,
                            is_default=is_default,
                            user_id=current_user.id
                        )
                        db.session.add(signature)
                        flash('Signature created successfully', 'success')
                    else:
                        # Update existing signature
                        signature = EmailSignature.query.get(signature_id)
                        if signature and signature.user_id == current_user.id:
                            signature.name = name
                            signature.content = content
                            if logo_url:
                                signature.logo_url = logo_url
                            signature.is_default = is_default
                            flash('Signature updated successfully', 'success')
                        else:
                            flash('Signature not found', 'danger')
                            return redirect(url_for('communications_fixed.signatures'))
                    
                    # If this is set as default, unset other defaults
                    if is_default:
                        other_signatures = EmailSignature.query.filter(
                            EmailSignature.user_id == current_user.id,
                            EmailSignature.id != (signature.id if action == 'update' else None)
                        ).all()
                        for other in other_signatures:
                            other.is_default = False
                    
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Database error with signature: {str(e)}")
                    flash(f"Error saving signature: {str(e)}", 'danger')
            
            elif action == 'delete':
                signature_id = request.form.get('signature_id')
                signature = EmailSignature.query.get(signature_id)
                
                if signature and signature.user_id == current_user.id:
                    db.session.delete(signature)
                    db.session.commit()
                    flash('Signature deleted successfully', 'success')
                else:
                    flash('Signature not found or you do not have permission', 'danger')
            
            elif action == 'set_default':
                signature_id = request.form.get('signature_id')
                
                # First, unset all defaults for this user
                signatures = EmailSignature.query.filter_by(user_id=current_user.id).all()
                for sig in signatures:
                    sig.is_default = (str(sig.id) == signature_id)
                
                db.session.commit()
                flash('Default signature updated', 'success')
        
        # Get all signatures for this user
        signatures = EmailSignature.query.filter_by(
            user_id=current_user.id
        ).order_by(EmailSignature.is_default.desc(), EmailSignature.name).all()
        
        return render_template('communications/signatures.html', 
                              signatures=signatures,
                              page_title="Email Signatures")
    except Exception as e:
        current_app.logger.error(f"Error in signatures page: {str(e)}")
        current_app.logger.exception("Full traceback for signatures error:")
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
