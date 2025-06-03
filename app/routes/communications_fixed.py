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

communications_fixed_bp = Blueprint('communications_fixed', __name__, template_folder='../templates/communications')

@communications_fixed_bp.route('/')
@login_required
def index():
    """Display a list of communications with pagination and filtering"""
    try:
        current_app.logger.info(f"User {current_user.email} accessed communications index")
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Get filter parameters
        filters = {}
        for key in ['method', 'direction', 'person_id', 'church_id']:
            if request.args.get(key):
                filters[key] = request.args.get(key)
        
        # Apply office filter for non-admin users
        office_id = int(current_user.office_id) if current_user.office_id else None
        if office_id and not current_user.is_super_admin():
            filters['office_id'] = office_id
        
        # Build query with eager loading for better performance
        query = Communication.query
        query = query.options(
            joinedload(Communication.person),
            joinedload(Communication.church),
            joinedload(Communication.user)
        )
        
        # Apply filters
        for key, value in filters.items():
            if value:
                query = query.filter(getattr(Communication, key) == value)
        
        # Order by most recent first
        query = query.order_by(Communication.date_sent.desc())
        
        # Get paginated results
        paginated = query.paginate(page=page, per_page=per_page)
        
        # Load email signatures with robust type handling
        try:
            # Log the current user ID for debugging
            current_app.logger.info(f"Loading email signatures for user_id: {current_user.id} (type: {type(current_user.id)})")
            
            # Try with the original user_id (integer)
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
        
        # Prepare pagination data for template
        pagination = {
            'page': paginated.page,
            'per_page': paginated.per_page,
            'total': paginated.total,
            'pages': paginated.pages,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
        }
        
        return render_template('index.html', 
                              communications=paginated.items,
                              pagination=pagination,
                              filters=filters,
                              page_title="Communications")
    except Exception as e:
        db.session.rollback()  # Ensure any failed transaction is rolled back
        current_app.logger.error(f"Error in communications index: {str(e)}")
        current_app.logger.exception("Full traceback:")
        flash('An error occurred while loading communications. Please try again later.', 'error')
        return render_template('error.html', error_message=f"Error: {str(e)}", page_title="Error")

@communications_fixed_bp.route('/signatures', methods=['GET', 'POST'])
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
                content = content.replace('\r\n', '<br>').replace('\n', '<br>')
                
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
        
        return render_template('signatures.html', 
                              signatures=signatures,
                              page_title="Email Signatures")
    except Exception as e:
        db.session.rollback()  # Ensure any failed transaction is rolled back
        current_app.logger.error(f"Error in signatures page: {str(e)}")
        current_app.logger.exception("Full traceback for signatures error:")
        return render_template('error.html', error_message=f"Error: {str(e)}", page_title="Error")
