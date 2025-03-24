import pytest
from flask import current_app
from app import create_app, db
from app.models import User, Office, Contact, Person, Church, Task, Communication

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_database_connection(app):
    """Test that we can connect to the database and perform basic operations."""
    assert current_app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///')
    
    # Create test office
    office = Office(
        name="Test Office",
        address="123 Test St",
        city="Test City",
        state="TS",
        country="Test Country",
        timezone="America/New_York"
    )
    db.session.add(office)
    db.session.commit()
    assert office.id is not None

    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        role="standard_user",
        office_id=office.id
    )
    user.first_name = "Test"
    user.last_name = "User"
    db.session.add(user)
    db.session.commit()
    assert user.id is not None

    # Create test person
    person = Person(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        user_id=user.id,
        office_id=office.id
    )
    db.session.add(person)
    db.session.commit()
    assert person.id is not None

    # Test relationships
    assert person.office == office
    assert person.user == user 