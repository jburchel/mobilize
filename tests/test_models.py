import pytest
from datetime import datetime, timedelta, UTC
from app.models import (
    User, Contact, Person, Church, Task, Communication,
    Office, GoogleToken, EmailSignature
)
from app.models.base import db
from sqlalchemy.exc import IntegrityError
from app.config.config import TestingConfig

@pytest.fixture
def app():
    from app import create_app
    app = create_app(TestingConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_session(app):
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_office(db_session):
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
def test_user(db_session, test_office):
    user = User(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        firebase_uid="test123",
        office_id=test_office.id
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_person(db_session, test_office):
    person = Person(
        first_name="Test",
        last_name="Person",
        email="person@test.com",
        phone="123-456-7890",
        office_id=test_office.id
    )
    db_session.add(person)
    db_session.commit()
    return person

@pytest.fixture
def test_church(db_session, test_office, test_user):
    church = Church(
        name="Test Church",
        email="church@test.com",
        phone="123-456-7890",
        office_id=test_office.id,
        owner_id=test_user.id
    )
    db_session.add(church)
    db_session.commit()
    return church

def test_office_creation(db_session):
    office = Office(
        name="Test Office",
        address="123 Test St",
        city="Test City",
        state="CA",
        zip_code="12345"
    )
    db_session.add(office)
    db_session.commit()
    
    retrieved_office = db_session.get(Office, office.id)
    assert retrieved_office is not None
    assert retrieved_office.name == "Test Office"

def test_user_creation(db_session, test_office):
    user = User(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        firebase_uid="test123",
        office_id=test_office.id
    )
    db_session.add(user)
    db_session.commit()
    
    retrieved_user = db_session.get(User, user.id)
    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"

def test_person_creation(db_session, test_office):
    person = Person(
        first_name="Test",
        last_name="Person",
        email="person@test.com",
        phone="123-456-7890",
        office_id=test_office.id
    )
    db_session.add(person)
    db_session.commit()
    
    retrieved_person = db_session.get(Person, person.id)
    assert retrieved_person is not None
    assert retrieved_person.email == "person@test.com"

def test_church_creation(db_session, test_user, test_office):
    church = Church(
        name='Test Church',
        owner_id=test_user.id,  # Set the owner_id
        office_id=test_office.id  # Set the office_id
    )
    db_session.add(church)
    db_session.commit()
    
    retrieved_church = db_session.get(Church, church.id)
    assert retrieved_church is not None
    assert retrieved_church.name == 'Test Church'
    assert retrieved_church.owner_id == test_user.id
    assert retrieved_church.office_id == test_office.id

def test_relationships(db_session, test_person, test_church, test_user, test_office):
    # Create a communication
    communication = Communication(
        message="Test Message",
        person=test_person,
        church=test_church,
        sender=test_user,
        owner_id=test_user.id,
        office_id=test_office.id,
        email_status="pending",
        type="Email"
    )
    db_session.add(communication)
    db_session.commit()

    # Test relationships
    assert communication.person == test_person
    assert communication.church == test_church
    assert communication.sender == test_user
    assert communication.owner_id == test_user.id
    assert communication.office_id == test_office.id

def test_crud_operations(db_session, test_office):
    # Create
    person = Person(
        first_name="Test",
        last_name="Person",
        email="person@test.com",
        phone="123-456-7890",
        office_id=test_office.id
    )
    db_session.add(person)
    db_session.commit()
    
    # Read
    retrieved_person = db_session.get(Person, person.id)
    assert retrieved_person is not None
    assert retrieved_person.email == "person@test.com"
    
    # Update
    retrieved_person.email = "updated@test.com"
    db_session.commit()
    
    updated_person = db_session.get(Person, person.id)
    assert updated_person.email == "updated@test.com"
    
    # Delete
    db_session.delete(updated_person)
    db_session.commit()
    
    deleted_person = db_session.get(Person, person.id)
    assert deleted_person is None

def test_data_integrity(db_session, test_office):
    # Test required fields
    with pytest.raises(IntegrityError):
        task = Task(description="Test Description")
        db_session.add(task)
        db_session.commit()
    db_session.rollback()
    
    # Test unique constraints
    user1 = User(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        firebase_uid="test123",
        office_id=test_office.id
    )
    db_session.add(user1)
    db_session.commit()
    
    with pytest.raises(IntegrityError):
        user2 = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            firebase_uid="test456",
            office_id=test_office.id
        )
        db_session.add(user2)
        db_session.commit()

def test_task_creation(db_session, test_person, test_church, test_user):
    task = Task(
        title="Test Task",
        description="Test Description",
        person=test_person,
        church=test_church,
        assigned_user=test_user,
        owner_id=test_user.id,
        status="pending"
    )
    db_session.add(task)
    db_session.commit()
    
    retrieved_task = db_session.get(Task, task.id)
    assert retrieved_task is not None
    assert retrieved_task.title == "Test Task"
    assert retrieved_task.person == test_person
    assert retrieved_task.church == test_church
    assert retrieved_task.assigned_user == test_user
    assert retrieved_task.owner_id == test_user.id

def test_communication_creation(db_session, test_person, test_church, test_user, test_office):
    communication = Communication(
        message="Test Message",
        person=test_person,
        church=test_church,
        sender=test_user,
        owner_id=test_user.id,
        office_id=test_office.id,
        email_status="pending",
        type="Email"
    )
    db_session.add(communication)
    db_session.commit()
    
    retrieved_communication = db_session.get(Communication, communication.id)
    assert retrieved_communication is not None
    assert retrieved_communication.message == "Test Message"
    assert retrieved_communication.person == test_person
    assert retrieved_communication.church == test_church
    assert retrieved_communication.owner_id == test_user.id 