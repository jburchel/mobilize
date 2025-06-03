import requests
import json
import re
import time
from bs4 import BeautifulSoup

# Configuration
BASE_URL = 'http://localhost:8000'
USERNAME = 'admin@example.com'  # Replace with a valid username
PASSWORD = 'password'  # Replace with a valid password

def test_api_with_auth():
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Get the login page to obtain CSRF token
    response = session.get(f'{BASE_URL}/api/auth/login-page')
    print(f'Login page status: {response.status_code}')
    
    # Extract CSRF token if present
    csrf_token = None
    if response.status_code == 200:
        # Use BeautifulSoup to parse the HTML
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrf_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
                print(f'Found CSRF token: {csrf_token}')
            else:
                print('No CSRF token input found in the HTML')
                # Try direct login without CSRF
                print('Attempting direct login...')
        except Exception as e:
            print(f'Error parsing HTML: {str(e)}')
            # Try the regex approach as fallback
            match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
            if match:
                csrf_token = match.group(1)
                print(f'Found CSRF token with regex: {csrf_token}')
    
    # Step 2: Log in
    # Try with or without CSRF token
    login_data = {
        'email': USERNAME,
        'password': PASSWORD
    }
    
    # Add CSRF token if found
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    # Try to log in
    login_response = session.post(f'{BASE_URL}/api/auth/login', data=login_data)
    print(f'Login response status: {login_response.status_code}')
    
    # Check if we were redirected to the dashboard
    if login_response.status_code == 200 or login_response.status_code == 302:
        print('Login appears successful!')
        
        # Get the dashboard to ensure we're logged in
        dashboard_response = session.get(f'{BASE_URL}/')
        print(f'Dashboard response status: {dashboard_response.status_code}')
        
        # Check if we're actually logged in by looking for logout link
        if 'Logout' in dashboard_response.text:
            print('Confirmed logged in successfully!')
        else:
            print('Warning: May not be fully logged in')
    else:
        print(f'Login failed with status: {login_response.status_code}')
    
    # Step 3: Test the chart data API endpoints
    print('\nTesting API endpoints after authentication:')
    
    # Test person pipeline endpoint
    try:
        response = session.get(f'{BASE_URL}/api/chart-data/person')
        print(f'Person API status: {response.status_code}')
        content_type = response.headers.get('Content-Type', '')
        print(f'Content-Type: {content_type}')
        
        if response.status_code == 200:
            if 'application/json' in content_type:
                data = response.json()
                print(f'Person API data: {json.dumps(data, indent=2)}')
                # Save the data to a file for inspection
                with open('person_chart_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print('Saved person chart data to person_chart_data.json')
            else:
                print(f'Person API response is not JSON: {response.text[:200]}...')
        else:
            print(f'Person API response: {response.text[:200]}...')
    except Exception as e:
        print(f'Error testing person API: {str(e)}')
    
    # Test church pipeline endpoint
    try:
        response = session.get(f'{BASE_URL}/api/chart-data/church')
        print(f'Church API status: {response.status_code}')
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            print(f'Content-Type: {content_type}')
            if 'application/json' in content_type:
                data = response.json()
                print(f'Church API data: {json.dumps(data, indent=2)}')
            else:
                print(f'Church API response is not JSON: {response.text[:200]}...')
        else:
            print(f'Church API response: {response.text[:200]}...')
    except Exception as e:
        print(f'Error testing church API: {str(e)}')

if __name__ == '__main__':
    test_api_with_auth()
