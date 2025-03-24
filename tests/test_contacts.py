import pytest
from app import create_app
from app.config.config import TestingConfig
from flask import url_for
from unittest.mock import patch

class TestContactsAPI:
    def test_get_contact_mock(self, client, auth_headers, mocker):
        """Test getting a contact route works with mocking."""
        # Create a mock response
        mock_data = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'office_id': 1,
            'type': 'contact_model'
        }
        
        # Create a patch at the view function level
        @patch('app.models.contact.ContactModel.query')
        def run_test(mock_query):
            # Set up the mock to return our data
            from app.models.contact import ContactModel
            import flask
            
            # Create a mock contact
            mock_contact = mocker.MagicMock(spec=ContactModel)
            mock_contact.id = 1
            mock_contact.first_name = 'John'
            mock_contact.last_name = 'Doe'
            mock_contact.email = 'john@example.com'
            mock_contact.office_id = 1
            mock_contact.type = 'contact_model'
            
            # Set up the to_dict method
            mock_contact.to_dict.return_value = mock_data
            
            # Set up the query mock
            mock_query.get_or_404.return_value = mock_contact
            
            # Make the request
            response = client.get('/api/v1/contacts/1', headers=auth_headers)
            
            # Print debug info
            print(f"Request URL: /api/v1/contacts/1")
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
            
            # Assert the response is correct
            assert response.status_code == 200
            assert response.get_json() == mock_data
            
        # Run the test
        run_test() 