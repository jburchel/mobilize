from flask import Blueprint, render_template, request, flash, current_app
from flask_login import login_required, current_user
from app.models.communication import Communication
from app.models.email_signature import EmailSignature
from app.extensions import db
from sqlalchemy import text, or_
from sqlalchemy.orm import joinedload
from app.utils.upload import save_uploaded_file

communications_fixed_bp = Blueprint('communications_fixed', __name__, template_folder='../templates/communications')

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
            
        current_app.logger.info("Starting communications index route")
        # Record start time for potential future performance tracking
        
        # Get filter parameters
        person_id = request.args.get('person_id')
        church_id = request.args.get('church_id')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Build base query with eager loading
        query = Communication.query
        query = query.options(
            joinedload(Communication.person),
            joinedload(Communication.church),
            joinedload(Communication.created_by)
        )
        
        # Apply filters
        filters = {}
        
        # Filter by person if provided
        if person_id:
            try:
                person_id = int(person_id)
                query = query.filter(Communication.person_id == person_id)
                filters['person_id'] = person_id
            except ValueError:
                current_app.logger.warning(f"Invalid person_id provided: {person_id}")
        
        # Filter by church if provided
        if church_id:
            try:
                church_id = int(church_id)
                query = query.filter(Communication.church_id == church_id)
                filters['church_id'] = church_id
            except ValueError:
                current_app.logger.warning(f"Invalid church_id provided: {church_id}")
        
        # Order by date sent descending
        query = query.order_by(Communication.date_sent.desc())
        
        # Get paginated results
        paginated = query.paginate(page=page, per_page=per_page)
        
        # Load email signatures with robust type handling
        try:
            # Log the current user ID for debugging
            current_app.logger.info(f"Loading email signatures for user_id: {current_user.id} (type: {type(current_user.id)})")
            
            # Try with both integer and string versions using OR condition
            user_id_int = current_user.id
            user_id_str = str(current_user.id)
            
            current_app.logger.info(f"Trying both integer ({user_id_int}) and string ({user_id_str}) user_id types")
            
            # Use SQLAlchemy's or_ to try both types
            signatures = EmailSignature.query.filter(
                or_(
                    EmailSignature.user_id == user_id_int,
                    EmailSignature.user_id == user_id_str
                )
            ).all()
            
            if signatures:
                current_app.logger.info(f"Found {len(signatures)} signatures with OR condition")
                current_user.email_signatures = signatures
            else:
                current_app.logger.warning("No signatures found with either type, trying raw SQL as last resort")
                
                # Use raw SQL with explicit casting as last resort
                result = db.session.execute(
                    text("SELECT id FROM email_signatures WHERE user_id::TEXT = :user_id_str"),
                    {"user_id_str": user_id_str}
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
            # Rollback any failed transactions to prevent cascading errors
            db.session.rollback()
            
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
                content = request.form.get('content')
                is_default = request.form.get('is_default') == 'on'
                
                # Convert line breaks to HTML
                content = content.replace('\n', '<br>')
                
                # Handle logo upload if provided
                logo_url = None
                if 'logo' in request.files and request.files['logo'].filename:
                    logo_url = save_uploaded_file(request.files['logo'], 'signatures')
                
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
                    
                    if is_default:
                        # Unset other default signatures
                        EmailSignature.query.filter(
                            EmailSignature.user_id == current_user.id,
                            EmailSignature.id != signature.id
                        ).update({EmailSignature.is_default: False})
                    
                    db.session.commit()
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
                        
                        if is_default:
                            # Unset other default signatures
                            EmailSignature.query.filter(
                                EmailSignature.user_id == current_user.id,
                                EmailSignature.id != signature.id
                            ).update({EmailSignature.is_default: False})
                        
                        db.session.commit()
                        flash('Signature updated successfully', 'success')
                    else:
                        flash('Signature not found or you do not have permission', 'danger')
            
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
        
        # Get all signatures for this user - use both integer and string user_id with OR condition
        user_id_int = current_user.id
        user_id_str = str(current_user.id)
        
        signatures = EmailSignature.query.filter(
            or_(
                EmailSignature.user_id == user_id_int,
                EmailSignature.user_id == user_id_str
            )
        ).order_by(EmailSignature.is_default.desc(), EmailSignature.name).all()
        
        return render_template('signatures.html', 
                              signatures=signatures,
                              page_title="Email Signatures")
    except Exception as e:
        db.session.rollback()  # Ensure any failed transaction is rolled back
        current_app.logger.error(f"Error in signatures page: {str(e)}")
        current_app.logger.exception("Full traceback for signatures error:")
        return render_template('error.html', error_message=f"Error: {str(e)}", page_title="Error")
