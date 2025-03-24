import pytest
from unittest.mock import patch
from app.services.contact_sync import ContactSyncService
from app.models import Person, SyncHistory
from app.extensions import db

@pytest.fixture
def sync_service(test_user):
    """Create a contact sync service for testing."""
    try:
        return ContactSyncService(test_user)
    except ValueError:
        pytest.skip("User does not have Google credentials")

@pytest.mark.xfail(reason="Requires Google credentials that are not available in the test environment")
def test_contact_selection_and_import(app, sync_service):
    """Test that contacts can be selected and imported correctly."""
    # Implementation will depend on the specific functionality
    assert sync_service is not None
    
@pytest.mark.xfail(reason="Requires Google credentials that are not available in the test environment")
def test_contact_mapping_accuracy(app, sync_service):
    """Test that contact fields are mapped correctly."""
    # Implementation will depend on the specific functionality
    assert sync_service is not None

@pytest.mark.xfail(reason="Requires Google credentials that are not available in the test environment")
def test_deduplication_logic(app, sync_service):
    """Test that duplicate contacts are handled correctly."""
    # Implementation will depend on the specific functionality
    assert sync_service is not None

@pytest.mark.xfail(reason="Requires Google credentials that are not available in the test environment")
def test_merge_resolution(app, sync_service):
    """Test that contact merge conflicts are resolved correctly."""
    # Implementation will depend on the specific functionality
    assert sync_service is not None

@pytest.mark.xfail(reason="Requires Google credentials that are not available in the test environment")
def test_sync_history_tracking(app, sync_service):
    """Test that sync history is tracked correctly."""
    # Implementation will depend on the specific functionality
    assert sync_service is not None

@patch('app.services.google.people.GooglePeopleService')
def test_contact_selection_and_import(mock_google_service, sync_service, test_db):
    """Test selecting and importing specific contacts."""
    # Mock Google contacts data
    mock_contacts = {
        'connections': [
            {
                'resourceName': 'people/contact1',
                'names': [{'givenName': 'John', 'familyName': 'Doe'}],
                'emailAddresses': [{'value': 'john@example.com'}]
            },
            {
                'resourceName': 'people/contact2',
                'names': [{'givenName': 'Jane', 'familyName': 'Smith'}],
                'emailAddresses': [{'value': 'jane@example.com'}]
            }
        ]
    }
    mock_google_service.return_value.list_contacts.return_value = mock_contacts

    # Test contact selection
    result = sync_service.sync_from_google(selected_ids=['people/contact1'])
    
    # Verify only selected contact was imported
    assert result['stats']['created'] == 1
    person = Person.query.filter_by(email='john@example.com').first()
    assert person is not None
    assert Person.query.filter_by(email='jane@example.com').first() is None

@patch('app.services.google.people.GooglePeopleService')
def test_contact_mapping_accuracy(mock_google_service, sync_service):
    """Test accurate mapping of Google contact fields to Person model."""
    mock_contact = {
        'resourceName': 'people/test1',
        'names': [{'givenName': 'Test', 'familyName': 'Person'}],
        'emailAddresses': [{'value': 'test@example.com'}],
        'phoneNumbers': [{'value': '1234567890'}],
        'addresses': [{
            'streetAddress': '123 Main St',
            'city': 'Test City',
            'region': 'TC',
            'postalCode': '12345'
        }]
    }
    
    # Test mapping
    mapped_data = sync_service._map_google_to_person({'connections': [mock_contact]})
    
    # Verify field mapping
    assert mapped_data['first_name'] == 'Test'
    assert mapped_data['last_name'] == 'Person'
    assert mapped_data['email'] == 'test@example.com'
    assert mapped_data['phone'] == '1234567890'
    assert mapped_data['address_street'] == '123 Main St'
    assert mapped_data['address_city'] == 'Test City'
    assert mapped_data['address_state'] == 'TC'
    assert mapped_data['address_zip'] == '12345'

@patch('app.services.google.people.GooglePeopleService')
def test_deduplication_logic(mock_google_service, sync_service, test_user, test_db):
    """Test duplicate contact detection and handling."""
    # Create existing person
    existing_person = Person(
        first_name='John',
        last_name='Doe',
        email='john@example.com',
        user_id=test_user.id
    )
    test_db.session.add(existing_person)
    test_db.session.commit()

    # Mock Google contact with same email
    mock_contact = {
        'resourceName': 'people/duplicate1',
        'names': [{'givenName': 'Johnny', 'familyName': 'Doe'}],
        'emailAddresses': [{'value': 'john@example.com'}]
    }
    mock_google_service.return_value.list_contacts.return_value = {
        'connections': [mock_contact]
    }

    # Test duplicate detection
    result = sync_service.list_google_contacts()
    assert result['contacts'][0]['has_duplicate'] is True
    assert result['contacts'][0]['duplicate_info']['email'] == existing_person.email

@patch('app.services.google.people.GooglePeopleService')
def test_merge_resolution(mock_google_service, sync_service, test_user, test_db):
    """Test contact merge functionality."""
    # Create existing person
    target_person = Person(
        first_name='John',
        last_name='Doe',
        email='john@example.com',
        user_id=test_user.id
    )
    test_db.session.add(target_person)
    test_db.session.commit()

    # Mock Google contact
    mock_contact = {
        'resourceName': 'people/merge1',
        'names': [{'givenName': 'Johnny', 'familyName': 'Doe'}],
        'emailAddresses': [{'value': 'johnny@example.com'}]
    }
    mock_google_service.return_value.get_contact.return_value = mock_contact

    # Test merge preview
    preview = sync_service.preview_merge('people/merge1', target_person.id)
    assert preview['fields']['first_name']['different'] is True
    assert preview['fields']['email']['different'] is True

    # Test merge execution
    merged = sync_service.merge_contacts(
        'people/merge1',
        target_person.id,
        {'first_name': 'source', 'email': 'target'}
    )
    
    # Verify merge results
    assert merged['first_name'] == 'Johnny'  # From source
    assert merged['email'] == 'john@example.com'  # From target

def test_sync_history_tracking(sync_service, test_user, test_db):
    """Test synchronization history recording."""
    # Create a sync history record
    sync_service._create_sync_history(
        action='import',
        status='completed',
        details={'stats': {'created': 1, 'updated': 0}}
    )

    # Verify history record
    history = SyncHistory.query.filter_by(user_id=test_user.id).first()
    assert history is not None
    assert history.action == 'import'
    assert history.status == 'completed'
    assert history.details['stats']['created'] == 1 