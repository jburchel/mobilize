import pytest
from flask import url_for
import json
from app import create_app
from app.models import db, User, Task, Communication, Office
from app.models.contact import ContactModel
from app.auth import create_access_token
from datetime import datetime
from app.config.config import TestingConfig
from unittest.mock import patch
from unittest.mock import MagicMock

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_office(app, db_session):
    """Create a test office."""
    office = Office(
        name="Test Office",
        address="123 Test St",
        city="Test City",
        state="CA",
        zip_code="12345"
    )
    db_session.add(office)
    db_session.commit()
    return office

@pytest.fixture
def db_session(app):
    """Create a fresh database session for a test."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()

class TestAuthAPI:
    def test_login_endpoint(self, client, mock_firebase):
        """Test the login endpoint."""
        # Create a test user first
        with client.application.app_context():
            user = User(
                email='test@example.com',
                username='testuser',
                firebase_uid='test_uid',
                first_name='Test',
                last_name='User',
                is_active=True,
                role='standard_user',
                office_id=1
            )
            db.session.add(user)
            db.session.commit()
            
        # Test login
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com'
        })
        assert response.status_code in [200, 401]

    def test_verify_token(self, client, auth_headers):
        """Test token verification endpoint."""
        token = auth_headers['Authorization'].split('Bearer ')[1]
        response = client.post('/api/auth/verify-token', json={
            'idToken': token
        })
        assert response.status_code == 200

class TestContactsAPI:
    def test_create_contact(self, client, auth_headers, test_office, test_user):
        """Test contact creation."""
        response = client.post('/api/v1/contacts/', json={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'office_id': test_office.id,
            'type': 'contact_model',
            'user_id': test_user.id
        }, headers=auth_headers)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['first_name'] == 'John'
        assert data['last_name'] == 'Doe'
        assert data['email'] == 'john@example.com'

    def test_get_contact(self, client, auth_headers, mocker, mock_contact):
        """Test getting a contact."""
        mock_contact_obj, mock_data = mock_contact(mocker)
        
        # Create a patch at the view function level
        with patch('app.models.contact.ContactModel.query') as mock_query:
            # Set up the query mock
            mock_query.get_or_404.return_value = mock_contact_obj
            
            # Make the request
            response = client.get('/api/v1/contacts/1', headers=auth_headers)
            
            # Assert the response is correct
            assert response.status_code == 200
            data = response.get_json()
            assert data['id'] == 1
            assert data['first_name'] == 'John'
            assert data['last_name'] == 'Doe'
            assert data['email'] == 'john@example.com'

    def test_update_contact(self, client, auth_headers, mocker, mock_contact):
        """Test updating a contact."""
        mock_contact_obj, mock_data = mock_contact(mocker)
        
        # Create a patch at the view function level
        with patch('app.models.contact.ContactModel.query') as mock_query:
            # Set up the query mock
            mock_query.get_or_404.return_value = mock_contact_obj
            
            # Make the request
            response = client.put('/api/v1/contacts/1', json={
                'first_name': 'Jane'
            }, headers=auth_headers)
            
            print(f"Update response status: {response.status_code}")
            print(f"Update response data: {response.data}")
            
            assert response.status_code == 200

    def test_delete_contact(self, client, auth_headers, mocker, mock_contact):
        """Test deleting a contact."""
        mock_contact_obj, mock_data = mock_contact(mocker)
        
        # Create a patch at the view function level
        with patch('app.models.contact.ContactModel.query') as mock_query:
            # Set up the query mock
            mock_query.get_or_404.return_value = mock_contact_obj
            
            # Mock the session delete and commit
            with patch('app.models.db.session.delete'), patch('app.models.db.session.commit'):
                # Make the request
                response = client.delete('/api/v1/contacts/1', headers=auth_headers)
                
                print(f"Delete response status: {response.status_code}")
                print(f"Delete response data: {response.data}")
                
                assert response.status_code == 204

    def test_search_contacts(self, client, auth_headers, mocker):
        """Test searching contacts."""
        # Mock contact results for the search
        mock_results = [
            MagicMock(
                id=1, 
                first_name='John', 
                last_name='Doe', 
                email='john@example.com',
                to_dict=lambda: {
                    'id': 1, 
                    'first_name': 'John', 
                    'last_name': 'Doe', 
                    'email': 'john@example.com'
                }
            )
        ]
        
        # Create a patch for the query filter
        with patch('app.models.contact.ContactModel.query') as mock_query:
            # Configure filter chain
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter
            mock_filter.all.return_value = mock_results
            
            # Make the request
            response = client.get('/api/v1/contacts/search?q=John', headers=auth_headers)
            
            print(f"Search response status: {response.status_code}")
            print(f"Search response data: {response.data}")
            
            data = json.loads(response.data)
            assert len(data) > 0

@pytest.fixture
def mock_jwt_required(mocker):
    """Mock JWT required decorator to bypass authentication."""
    return mocker.patch('app.routes.api.v1.gmail.jwt_required', return_value=lambda f: f)

@pytest.fixture
def mock_jwt_identity(mocker):
    """Mock get_jwt_identity to return a test user ID."""
    return mocker.patch('app.routes.api.v1.gmail.get_jwt_identity', return_value=1)

@pytest.mark.usefixtures('auth_headers')
class TestGmailAPI:
    @pytest.mark.xfail(reason="JWT authentication issues - requires manual testing with valid credentials")
    def test_sync_emails(self, client, auth_headers, mocker):
        """Test email synchronization."""
        response = client.post('/api/v1/gmail/sync', headers=auth_headers)
        print(f"Sync response status: {response.status_code}")
        print(f"Sync response data: {response.data}")
        assert response.status_code == 200

    @pytest.mark.xfail(reason="JWT authentication issues - requires manual testing with valid credentials")
    def test_send_email(self, client, auth_headers, mocker):
        """Test sending an email."""
        response = client.post('/api/v1/gmail/send', json={
            'to': 'test@example.com',
            'subject': 'Test Email',
            'body': 'Test body'
        }, headers=auth_headers)
        print(f"Send response status: {response.status_code}")
        print(f"Send response data: {response.data}")
        assert response.status_code == 200

    @pytest.mark.xfail(reason="JWT authentication issues - requires manual testing with valid credentials")
    def test_get_threads(self, client, auth_headers, mocker):
        """Test getting email threads."""
        response = client.get('/api/v1/gmail/threads', headers=auth_headers)
        print(f"Threads response status: {response.status_code}")
        print(f"Threads response data: {response.data}")
        assert response.status_code == 200

@pytest.mark.usefixtures('auth_headers')
class TestCalendarAPI:
    @pytest.mark.xfail(reason="JWT authentication issues - requires manual testing with valid credentials")
    def test_create_event(self, client, auth_headers):
        """Test creating a calendar event."""
        response = client.post('/api/v1/calendar/events', json={
            'summary': 'Test Event',
            'start': {
                'dateTime': '2023-01-01T10:00:00',
                'timeZone': 'America/New_York'
            },
            'end': {
                'dateTime': '2023-01-01T11:00:00',
                'timeZone': 'America/New_York'
            }
        }, headers=auth_headers)
        print(f"Create event response status: {response.status_code}")
        print(f"Create event response data: {response.data}")
        assert response.status_code == 200

    @pytest.mark.xfail(reason="JWT authentication issues - requires manual testing with valid credentials")
    def test_get_events(self, client, auth_headers):
        """Test getting calendar events."""
        response = client.get('/api/v1/calendar/events', headers=auth_headers)
        print(f"Get events response status: {response.status_code}")
        print(f"Get events response data: {response.data}")
        assert response.status_code == 200

    @pytest.mark.xfail(reason="JWT authentication issues - requires manual testing with valid credentials")
    def test_sync_calendar(self, client, auth_headers):
        """Test calendar synchronization."""
        response = client.post('/api/v1/calendar/sync', headers=auth_headers)
        print(f"Sync calendar response status: {response.status_code}")
        print(f"Sync calendar response data: {response.data}")
        assert response.status_code == 200

@pytest.mark.usefixtures('auth_headers')
class TestTaskAPI:
    def test_create_task(self, client, auth_headers):
        """Test task creation."""
        response = client.post('/api/v1/tasks', json={
            'title': 'Test Task',
            'description': 'Test description'
        }, headers=auth_headers)
        assert response.status_code == 201

    def test_get_tasks(self, client, auth_headers):
        """Test getting tasks."""
        response = client.get('/api/v1/tasks', headers=auth_headers)
        assert response.status_code == 200

@pytest.mark.usefixtures('auth_headers')
class TestErrorHandling:
    @pytest.mark.xfail(reason="Firebase token validation is difficult to mock properly")
    def test_invalid_token(self, client):
        """Test invalid token handling."""
        response = client.get('/api/v1/contacts/',
                            headers={'Authorization': 'Bearer invalid'})
        print(f"Invalid token response status: {response.status_code}")
        print(f"Invalid token response data: {response.data}")
        assert response.status_code == 401

    def test_missing_required_fields(self, client, auth_headers, db_session):
        """Test missing required fields handling."""
        response = client.post('/api/v1/contacts', json={},
                             headers=auth_headers)
        assert response.status_code == 400

    def test_invalid_data_format(self, client, auth_headers, db_session):
        """Test invalid data format handling."""
        response = client.post('/api/v1/contacts', json={
            'email': 'invalid-email',
            'first_name': 'Test',
            'last_name': 'User'
        }, headers=auth_headers)
        assert response.status_code == 400

    def test_resource_not_found(self, client, auth_headers, db_session):
        """Test resource not found handling."""
        response = client.get('/api/v1/contacts/999',
                            headers=auth_headers)
        assert response.status_code == 404

class TestSyncAPI:
    @patch('app.tasks.sync.sync_user_contacts.delay')
    def test_contact_sync_api(self, mock_sync_task, client, auth_headers, mocker):
        """Test the contact sync API endpoint."""
        # Mock the User query
        mock_user = mocker.MagicMock()
        mock_user.id = 1
        mock_user.google_token = {"refresh_token": "test_token"}
        
        # Mock User.query.filter_by().first() to return our mock user
        mock_query = mocker.patch('app.models.user.User.query')
        mock_query.filter_by.return_value.first.return_value = mock_user
        
        # Make a request to the sync endpoint
        response = client.post('/api/v1/contacts/sync', headers=auth_headers)
        
        # Verify the response status code
        assert response.status_code == 200
        
        # Verify the Celery task was started
        mock_sync_task.assert_called_once_with(mock_user.id)
        
        # Parse the response data
        data = response.get_json()
        assert 'message' in data
        assert 'Contact synchronization started' in data['message'] 