import pytest
from app import create_app, db
from app.models.user import User
from app.models.person import Person
from app.models.office import Office
from flask_login import current_user, login_user
import datetime
import json
from flask import url_for


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    app.config['TESTING'] = True
    app.config['LOGIN_DISABLED'] = False
    app.config['SERVER_NAME'] = 'localhost'  # Required for url_for to work in test context
    
    with app.app_context():
        db.create_all()
        
        # Create test office
        office = Office(name="Test Office")
        db.session.add(office)
        db.session.flush()  # Flush to get the office ID
        
        # Create test user
        user = User(
            username="test_user",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role="super_admin",
            office_id=office.id
        )
        user.set_password("password123")
        user.current_office_id = office.id
        db.session.add(user)
        
        # Create test person
        person = Person(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-123-4567",
            office_id=office.id,
            created_at=datetime.datetime.now() - datetime.timedelta(days=10)
        )
        db.session.add(person)
        
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    with app.test_client() as client:
        client.testing = True
        yield client


@pytest.fixture
def auth_client(client, app):
    """Create a test client with authenticated user."""
    with app.test_request_context():
        user = User.query.filter_by(username="test_user").first()
        login_user(user)
        
    # Create a new test client that preserves the session
    with app.test_client() as authenticated_client:
        authenticated_client.testing = True
        # Pass cookies from the login session to this client
        with authenticated_client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['_fresh'] = True
            
        yield authenticated_client


def test_reports_dashboard_requires_login(client):
    """Test that reports dashboard requires login."""
    response = client.get("/reports/")
    assert response.status_code == 302  # Redirects to login page


def test_reports_dashboard_accessible_after_login(auth_client):
    """Test that reports dashboard is accessible after login."""
    response = auth_client.get("/reports/")
    assert response.status_code == 200


def test_contacts_widget_api(auth_client):
    """Test the contacts widget API endpoint."""
    response = auth_client.get("/reports/widgets/contacts")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "total_contacts" in data
    assert "new_contacts_30d" in data


def test_export_data_endpoint(auth_client):
    """Test the data export endpoint."""
    response = auth_client.post(
        "/reports/export/contacts",
        data={"format": "csv"}
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["Content-Type"]
    assert "attachment" in response.headers["Content-Disposition"]


def test_custom_report_page(auth_client):
    """Test the custom report page."""
    response = auth_client.get("/reports/custom")
    assert response.status_code == 200
    assert b"Custom Report Generator" in response.data 