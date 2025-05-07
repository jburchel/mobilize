import os
import sys

# Set up environment variables for development
os.environ['FLASK_APP'] = 'app'
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Use PostgreSQL for development
os.environ['DATABASE_URL'] = 'postgresql://jimburchel@localhost:5432/mobilize'
os.environ['DB_CONNECTION_STRING'] = 'postgresql://jimburchel@localhost:5432/mobilize'
os.environ['SQLALCHEMY_DATABASE_URI'] = 'postgresql://jimburchel@localhost:5432/mobilize'

# Other necessary variables
os.environ['SKIP_DB_INIT'] = 'False'  # Set to True if you don't want to create tables
os.environ['SECRET_KEY'] = 'dev-secret-key'

# Print the environment for debugging
print(f"Using database: {os.environ.get('DATABASE_URL')}")
print(f"Flask environment: {os.environ.get('FLASK_ENV')}")

# Import app-related modules after environment variables are set
import app
from app import create_app
app = create_app()

if __name__ == '__main__':
    # Get port from command line args or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    print(f"Starting development server at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
