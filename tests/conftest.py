import os
import sys

# Add the parent directory to the Python path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch, MagicMock
import firebase_admin
from firebase_admin import credentials
from app import create_app, db
from app.config.config import TestingConfig
from app.models.user import User
from app.models.contact import ContactModel
from app.models.person import Person
from app.models.church import Church
from app.models.office import Office
from app.models.task import Task
from app.models.communication import Communication
from app.models.relationships import setup_relationships
from app.models.email_signature import EmailSignature
from app.models.google_token import GoogleToken
from flask_jwt_extended import create_access_token
import base64
import json
from datetime import datetime
from app.models.user import User
from firebase_admin import auth
from sqlalchemy.orm import Query
from flask_login import LoginManager
import threading
import time
import socket

# Utility functions for testing
def mock_db_query(model_class, model_data, session=None):
    """
    Helper function to mock database queries.
    
    Args:
        model_class: The model class to mock
        model_data: Dictionary of data to use for the mock model
        session: Optional database session to use
        
    Returns:
        A mock instance of the model with data populated from model_data
    """
    # Create a mock instance of the model
    mock_model = MagicMock(spec=model_class)
    
    # Set attributes based on model_data
    for key, value in model_data.items():
        setattr(mock_model, key, value)
    
    # Set up common methods
    mock_model.to_dict.return_value = model_data
    
    # Create a patch context for the query
    return patch(f'{model_class.__module__}.{model_class.__name__}.query', new_callable=MagicMock)

@pytest.fixture
def mock_contact():
    """Fixture to create a mock contact for testing."""
    contact_data = {
        'id': 1,
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'office_id': 1,
        'type': 'contact_model',
        'phone': '123-456-7890',
        'address': '123 Test St',
        'city': 'Test City',
        'state': 'CA',
        'zip_code': '12345',
        'country': 'USA'
    }
    
    def _create_mock(mocker):
        # Create a mock ContactModel
        mock_contact = mocker.MagicMock(spec=ContactModel)
        
        # Set attributes based on contact_data
        for key, value in contact_data.items():
            setattr(mock_contact, key, value)
        
        # Set up to_dict method
        mock_contact.to_dict.return_value = contact_data
        
        return mock_contact, contact_data
    
    return _create_mock

@pytest.fixture
def mock_firebase(mocker):
    """Mock Firebase authentication."""
    # Create a proper JWT token with three segments
    header = base64.b64encode(json.dumps({"alg": "RS256", "kid": "test-key"}).encode()).decode()
    payload = base64.b64encode(json.dumps({
        "uid": "test_user_id",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
        "admin": True
    }).encode()).decode()
    signature = base64.b64encode(b"test_signature").decode()
    mock_token = f"{header}.{payload}.{signature}"

    def mock_verify_token(token):
        if token == mock_token:
            return {
                'uid': 'test_user_id',
                'email': 'test@example.com',
                'name': 'Test User',
                'picture': 'https://example.com/photo.jpg',
                'admin': True
            }
        raise auth.InvalidIdTokenError('Invalid token')

    # Mock the database operations
    mock_user = User(
        id=1,
        email='test@example.com',
        firebase_uid='test_user_id',
        first_name='Test',
        last_name='User',
        last_login=datetime.utcnow(),
        is_active=True,
        role='standard_user'
    )

    # Create a mock query
    mock_query = MagicMock(spec=Query)
    mock_query.filter_by.return_value = mock_query
    mock_query.first.return_value = mock_user
    mock_query.limit.return_value = mock_query
    mock_query.offset.return_value = mock_query

    # Mock User.query
    mocker.patch('app.models.user.User.query', mock_query)
    mocker.patch('app.extensions.db.session.add')
    mocker.patch('app.extensions.db.session.commit')

    # Patch both the firebase_admin.auth.verify_id_token and our custom function
    mocker.patch('firebase_admin.auth.verify_id_token', side_effect=mock_verify_token)
    mocker.patch('app.auth.firebase.verify_firebase_token', side_effect=mock_verify_token)
    return mock_token

@pytest.fixture(autouse=True)
def mock_firebase_app(mocker):
    """Mock Firebase app initialization."""
    # Mock the get_app function to return a mock app
    mock_app = MagicMock()
    mocker.patch('firebase_admin.get_app', return_value=mock_app)
    
    # Mock the environment variables check
    mocker.patch.dict(os.environ, {
        'FIREBASE_PRIVATE_KEY_ID': 'test_key_id',
        'FIREBASE_PRIVATE_KEY': 'test_private_key',
        'FIREBASE_CLIENT_EMAIL': 'test@example.com',
        'FIREBASE_CLIENT_ID': 'test_client_id',
        'FIREBASE_CLIENT_CERT_URL': 'https://test.cert.url'
    })
    
    # Mock the credentials
    mock_cred = MagicMock()
    mocker.patch('firebase_admin.credentials.Certificate', return_value=mock_cred)
    
    # Mock the initialize_app function
    mocker.patch('firebase_admin.initialize_app')
    
    return mock_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create the app with test config
    app = create_app(TestingConfig)
    
    # Configure Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Create all tables and set up relationships
    with app.app_context():
        # Import all models to ensure they are registered with SQLAlchemy
        from app.models import (
            User, Contact, Person, Church, Office,
            Task, Communication, EmailSignature, GoogleToken
        )
        
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()
        
        # Set up relationships
        setup_relationships()
    
    yield app
    
    # Clean up
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def test_db(app):
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_user(test_db, test_office):
    user = User(
        username='testuser',
        email='test@example.com',
        first_name='Test',
        last_name='User',
        firebase_uid='test123',
        google_token='test_token',
        role='standard_user',
        office_id=test_office.id  # Use the actual office ID
    )
    test_db.session.add(user)
    test_db.session.commit()
    return user

@pytest.fixture
def auth_headers(mock_firebase):
    """Create authentication headers."""
    return {'Authorization': f'Bearer {mock_firebase}'}

@pytest.fixture
def auth_client(client, mock_firebase):
    """Create a client with auth capabilities for frontend tests."""
    class AuthClient:
        def __init__(self, client, token):
            self.client = client
            self.token = token
            self.user_data = {
                'uid': 'test_user_id',
                'email': 'test@example.com',
                'name': 'Test User',
                'picture': 'https://example.com/photo.jpg',
                'admin': True
            }
        
        def login(self):
            """Simulate login and return cookies."""
            return {'status': 'success'}
        
        def get_cookies(self):
            """Get cookies after login for Selenium."""
            return [
                {
                    'name': 'session',
                    'value': 'test-session-value',
                    'path': '/',
                    'domain': 'localhost'
                },
                {
                    'name': 'csrf_token',
                    'value': 'test-csrf-token',
                    'path': '/',
                    'domain': 'localhost'
                }
            ]
    
    return AuthClient(client, mock_firebase)

@pytest.fixture
def db_session(app):
    """Create a fresh database session for a test."""
    with app.app_context():
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()
        
        # Set up relationships
        setup_relationships()
        
        # Print out the tables that were created
        print("Created tables:", db.engine.table_names())
        
        # Use the application's session
        yield db.session
        
        # Clean up
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_office(app, db_session):
    """Create a test office."""
    with app.app_context():
        # Print out the tables that were created
        print("Tables before office creation:", db.engine.table_names())
        
        office = Office(
            name='Test Office',
            address='123 Test St',
            city='Test City',
            state='TS',
            zip_code='12345'
        )
        print("Created office object:", office)
        print("Office ID before save:", office.id)
        
        db_session.add(office)
        db_session.flush()  # Flush to get the ID
        print("Office ID after flush:", office.id)
        
        db_session.commit()  # Commit the changes
        print("Office ID after commit:", office.id)
        
        # Verify the office was created
        saved_office = db_session.get(Office, office.id)
        print("Retrieved office:", saved_office)
        if saved_office:
            print("Retrieved office ID:", saved_office.id)
        
        if not saved_office:
            raise Exception("Failed to create test office")
        
        return saved_office

@pytest.fixture
def live_server(app):
    """
    Provides a live server fixture for testing with Selenium.
    """
    from werkzeug.serving import make_server
    import threading
    
    # Find a free port
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]
    
    port = find_free_port()
    server = make_server('localhost', port, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    # Wait for server to start
    time.sleep(1)
    
    live_server_url = f'http://localhost:{port}'
    
    # Create a LiveServer object with app and url attributes
    class LiveServer:
        def __init__(self):
            self.app = app
            self.url = live_server_url
    
    yield LiveServer()
    
    # Shutdown server
    server.shutdown()