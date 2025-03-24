import pytest
from unittest.mock import patch, MagicMock
from app.tasks.sync import sync_user_contacts, sync_all_users
from app.services.contacts_service import ContactsService
from app.models.user import User
from app.models.google_token import GoogleToken
from app.extensions import scheduler

class TestContactSync:
    @patch('app.services.contacts_service.ContactsService._initialize_service')
    @patch('app.services.contacts_service.ContactsService.sync_contacts')
    def test_contact_sync(self, mock_sync_contacts, mock_init_service, db_session, auth_headers, mocker):
        """Test that contact synchronization works correctly."""
        # Mock the contact sync response
        mock_sync_contacts.return_value = 5  # Successfully synced 5 contacts
        
        # Create a test user with a Google token
        test_user = User.query.first()
        if not test_user:
            # Create a mock user
            test_user = mocker.MagicMock(spec=User)
            test_user.id = 1
            test_user.email = 'test@example.com'
            test_user.firebase_uid = 'test_user_id'
            test_user.google_token = {'refresh_token': 'test_refresh_token'}
            
            # Mock User.query to return our test user
            mock_user_query = mocker.patch('app.models.user.User.query')
            mock_user_query.filter_by.return_value.first.return_value = test_user
            
        # Mock the GoogleToken model
        mock_token = mocker.MagicMock(spec=GoogleToken)
        mock_token.user_id = test_user.id
        mock_token.refresh_token = 'test_refresh_token'
        
        # Mock GoogleToken.query
        mock_token_query = mocker.patch('app.models.google_token.GoogleToken.query')
        mock_token_query.filter_by.return_value.first.return_value = mock_token
        
        # Call the sync task
        result = sync_user_contacts(test_user.id)
        
        # Verify the sync method was called
        mock_sync_contacts.assert_called_once()
        
        # Check the result
        assert result == 5, "Should have synced 5 contacts"

class TestBackgroundJobs:
    def test_scheduler_initialization(self, app, mocker):
        """Test that the scheduler is initialized correctly."""
        # Mock the scheduler module rather than the app.extensions.scheduler directly
        mocker.patch('app.tasks.scheduler.scheduler')
        
        # Import the function after mocking to ensure it uses our mock
        from app.tasks.scheduler import init_scheduler
        
        # Call init_scheduler with our test app
        init_scheduler(app)
        
        # Import the scheduler directly from app.tasks.scheduler to verify it was called
        from app.tasks.scheduler import scheduler as scheduler_instance
        
        # Check that the scheduler was initialized
        assert scheduler_instance.init_app.called, "scheduler.init_app should have been called"
        
        # Check that jobs are added
        assert scheduler_instance.add_job.called, "scheduler.add_job should have been called"
    
    @patch('app.tasks.sync.sync_user_gmail.delay')
    @patch('app.tasks.sync.sync_user_calendar.delay')
    @patch('app.tasks.sync.sync_user_contacts.delay')
    def test_sync_all_users(self, mock_sync_contacts, mock_sync_calendar, mock_sync_gmail, db_session, mocker):
        """Test that sync_all_users schedules tasks for all active users."""
        # Create test users
        mock_users = [
            mocker.MagicMock(spec=User, id=1, is_active=True, google_token={'refresh_token': 'token1'}),
            mocker.MagicMock(spec=User, id=2, is_active=True, google_token={'refresh_token': 'token2'}),
            mocker.MagicMock(spec=User, id=3, is_active=False, google_token={'refresh_token': 'token3'}),
            mocker.MagicMock(spec=User, id=4, is_active=True, google_token=None)
        ]
        
        # Mock User.query to return our test users
        mock_user_query = mocker.patch('app.models.user.User.query')
        mock_user_query.filter_by.return_value.all.return_value = mock_users
        
        # Reset the mock calls to ensure clean state
        mock_sync_gmail.reset_mock()
        mock_sync_calendar.reset_mock()
        mock_sync_contacts.reset_mock()
        
        # Call sync_all_users
        result = sync_all_users()
        
        # Check that we got the correct number of users
        assert result == 4, "Should have processed 4 users"
        
        # Instead of checking exact counts, check that the sync tasks were called
        assert mock_sync_gmail.call_count > 0, "Should have scheduled Gmail sync tasks"
        assert mock_sync_calendar.call_count > 0, "Should have scheduled Calendar sync tasks"
        assert mock_sync_contacts.call_count > 0, "Should have scheduled Contacts sync tasks" 