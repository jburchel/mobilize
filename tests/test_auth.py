import pytest
from flask import session
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.models.user import User
from app.auth.firebase import verify_firebase_token
from flask_login import login_user

@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test_key',
        'WTF_CSRF_ENABLED': False
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def mock_firebase_verify():
    """Mock Firebase token verification."""
    with patch('firebase_admin.auth.verify_id_token') as mock:
        mock.return_value = {
            'uid': 'test_uid',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/photo.jpg'
        }
        yield mock

def test_login_endpoint(client, mock_firebase_verify):
    """Test the login endpoint with Firebase token."""
    response = client.post('/auth/login', json={
        'idToken': 'test_token'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'user' in data
    assert data['user']['email'] == 'test@example.com'
    
    # Verify user was created in database
    user = User.query.filter_by(firebase_uid='test_uid').first()
    assert user is not None
    assert user.email == 'test@example.com'
    assert user.first_name == 'Test'
    assert user.last_name == 'User'

def test_login_no_token(client):
    """Test the login endpoint without a token."""
    response = client.post('/auth/login', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_verify_token_endpoint(client, mock_firebase_verify):
    """Test the token verification endpoint."""
    response = client.post('/auth/verify-token', json={
        'idToken': 'test_token'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'user' in data
    assert data['user']['email'] == 'test@example.com'

def test_google_auth_flow(client):
    """Test the Google OAuth flow."""
    with patch('app.auth.google_oauth.get_google_auth_url') as mock_auth_url:
        mock_auth_url.return_value = 'https://accounts.google.com/o/oauth2/auth'
        response = client.get('/auth/google/authorize')
        assert response.status_code == 302
        assert response.headers['Location'].startswith('https://accounts.google.com/o/oauth2/auth')

def test_google_callback(client):
    """Test Google OAuth callback route."""
    with patch('app.auth.routes.handle_oauth2_callback') as mock_callback, \
         patch('app.auth.routes.create_oauth_flow') as mock_flow_create, \
         patch('app.auth.routes.store_credentials') as mock_store_creds:
        
        # Mock the OAuth flow
        mock_flow = MagicMock()
        mock_flow_create.return_value = mock_flow
        mock_flow.fetch_token.return_value = None
        mock_flow.credentials = MagicMock()
        
        # Mock the callback response
        mock_callback.return_value = ({
            'email': 'test@example.com',
            'given_name': 'Test',
            'family_name': 'User',
            'picture': 'http://example.com/pic.jpg'
        }, None)
        
        response = client.get('/auth/google/callback')
        
        assert response.status_code == 302
        assert response.headers['Location'] == '/dashboard'
        
        # Verify the user was created and stored
        user = User.query.filter_by(email='test@example.com').first()
        assert user is not None
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.profile_picture_url == 'http://example.com/pic.jpg'
        
        # Verify credentials were stored
        mock_store_creds.assert_called_once_with(mock_flow.credentials, user.id)

def test_role_based_access(client, mock_firebase_verify):
    """Test role-based access control."""
    # Create an admin user
    admin = User(
        email='admin@example.com',
        firebase_uid='admin_uid',
        role='super_admin'
    )
    db.session.add(admin)
    db.session.commit()

    # Create a standard user
    user = User(
        email='user@example.com',
        firebase_uid='user_uid',
        role='standard_user'
    )
    db.session.add(user)
    db.session.commit()

    # Test admin access
    with client.session_transaction() as sess:
        sess['user_id'] = admin.id
        sess['_fresh'] = True  # Mark the session as fresh
    
    # Log in the admin user
    login_user(admin)
    response = client.get('/admin/dashboard')
    assert response.status_code == 200

    # Test standard user access
    with client.session_transaction() as sess:
        sess['user_id'] = user.id
        sess['_fresh'] = True  # Mark the session as fresh
    
    # Log in the standard user
    login_user(user)
    response = client.get('/admin/dashboard')
    assert response.status_code == 403

def test_logout(client):
    """Test the logout functionality."""
    # Create and login a user
    user = User(
        email='test@example.com',
        firebase_uid='test_uid',
        role='standard_user'
    )
    db.session.add(user)
    db.session.commit()

    with client.session_transaction() as sess:
        sess['user_id'] = user.id
        sess['_fresh'] = True  # Mark the session as fresh
    
    # Log in the user
    login_user(user)

    # Test logout
    response = client.post('/auth/logout')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'

    # Verify session is cleared
    with client.session_transaction() as sess:
        assert 'user_id' not in sess 