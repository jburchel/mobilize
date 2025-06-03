import requests
import json

# Configuration
BASE_URL = 'http://localhost:8000'

def test_api():
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Get the login page to obtain CSRF token
    response = session.get(f'{BASE_URL}/api/auth/login-page')
    print(f'Login page status: {response.status_code}')
    
    # Step 2: Test the chart data API endpoints directly
    print('\nTesting API endpoints directly (will require authentication):')
    
    # Test person pipeline endpoint
    try:
        response = session.get(f'{BASE_URL}/api/chart-data/person')
        print(f'Person API status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print(f'Person API data: {json.dumps(data, indent=2)}')
        else:
            print(f'Person API response: {response.text}')
    except Exception as e:
        print(f'Error testing person API: {str(e)}')
    
    # Test church pipeline endpoint
    try:
        response = session.get(f'{BASE_URL}/api/chart-data/church')
        print(f'Church API status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print(f'Church API data: {json.dumps(data, indent=2)}')
        else:
            print(f'Church API response: {response.text}')
    except Exception as e:
        print(f'Error testing church API: {str(e)}')

if __name__ == '__main__':
    test_api()
