import requests
import webbrowser
import re
import time

# Configuration
BASE_URL = 'http://localhost:8000'
USERNAME = 'admin@example.com'  # Replace with a valid username
PASSWORD = 'password'  # Replace with a valid password

def test_login_dashboard():
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Get the login page to obtain CSRF token
    response = session.get(f'{BASE_URL}/api/auth/login-page')
    print(f'Login page status: {response.status_code}')
    
    # Extract CSRF token if present
    csrf_token = None
    if response.status_code == 200:
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        if match:
            csrf_token = match.group(1)
            print(f'Found CSRF token: {csrf_token}')
    
    # Step 2: Log in
    if csrf_token:
        login_data = {
            'csrf_token': csrf_token,
            'email': USERNAME,
            'password': PASSWORD
        }
        login_response = session.post(f'{BASE_URL}/api/auth/login', data=login_data)
        print(f'Login response status: {login_response.status_code}')
        
        # Check if login was successful
        if login_response.status_code == 200 or login_response.status_code == 302:
            print('Login successful!')
            
            # Step 3: Test the chart data API endpoints
            print('\nTesting API endpoints after authentication:')
            
            # Test person pipeline endpoint
            try:
                response = session.get(f'{BASE_URL}/api/chart-data/person')
                print(f'Person API status: {response.status_code}')
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f'Person API returned valid JSON with {len(data.get("stages", []))} stages')
                    except Exception as e:
                        print(f'Person API error: {str(e)}')
            except Exception as e:
                print(f'Error testing person API: {str(e)}')
            
            # Step 4: Open dashboard in browser
            dashboard_url = f'{BASE_URL}/'
            print(f'\nOpening dashboard at: {dashboard_url}')
            webbrowser.open(dashboard_url)
            
            print('\nTest completed. Please check the browser to see if the charts are displayed correctly.')
        else:
            print(f'Login failed with status code: {login_response.status_code}')
    else:
        print('No CSRF token found, cannot log in')

if __name__ == '__main__':
    test_login_dashboard()
