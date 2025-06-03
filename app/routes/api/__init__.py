# Import the API blueprint from the v1 subpackage
from app.routes.api.v1 import api_bp

# For backward compatibility, export the API blueprint
__all__ = ['api_bp']
