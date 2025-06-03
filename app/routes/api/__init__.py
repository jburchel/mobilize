# Import the API blueprint from the v1 subpackage
from app.routes.api.v1 import api_bp as v1_bp

# For backward compatibility, export the v1 API blueprint as the main api_bp
api_bp = v1_bp
