import os
import uuid
from werkzeug.utils import secure_filename

def save_uploaded_file(file, folder='uploads', allowed_extensions=None, max_size=5242880):
    """
    Save an uploaded file to the specified folder with a unique filename.
    
    Args:
        file: The file object from request.files
        folder: The subfolder within static/uploads/ to save the file (default: 'uploads')
        allowed_extensions: List of allowed file extensions (default: None = any extension)
        max_size: Maximum file size in bytes (default: 5MB)
    
    Returns:
        str: The URL path to the saved file (for use in templates/database) or None if failed
    
    Raises:
        ValueError: If the file is invalid, too large, or has an invalid extension
    """
    if not file or file.filename == '':
        raise ValueError("No file selected")
    
    # Check file size (request.content_length might be None if file is small)
    if hasattr(file, 'content_length') and file.content_length and file.content_length > max_size:
        raise ValueError(f"File too large (max {max_size/1024/1024:.1f}MB)")
    
    # Get filename and extension
    filename = secure_filename(file.filename)
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    # Validate extension if needed
    if allowed_extensions and extension not in allowed_extensions:
        raise ValueError(f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}")
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}.{extension}" if extension else f"{uuid.uuid4()}"
    
    # Ensure the upload directory exists
    upload_dir = os.path.join('app', 'static', 'uploads', folder)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    filepath = os.path.join(upload_dir, unique_filename)
    file.save(filepath)
    
    # Return the URL path for use in templates/database
    return f"/static/uploads/{folder}/{unique_filename}" 