import requests
import json

# Configuration
BASE_URL = 'http://localhost:8000'

def test_api_json():
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Get the login page first to establish a session
    response = session.get(f'{BASE_URL}/api/auth/login-page')
    print(f'Login page status: {response.status_code}')
    
    # Test the chart data API endpoints directly
    print('\nTesting API endpoints directly:')
    
    # Test person pipeline endpoint
    try:
        response = session.get(f'{BASE_URL}/api/chart-data/person')
        print(f'Person API status: {response.status_code}')
        print(f'Content-Type: {response.headers.get("Content-Type", "None")}')
        
        # Print the raw response content
        print(f'\nRaw response content (first 200 chars):\n{response.text[:200]}...')
        
        # Try to parse as JSON
        try:
            data = response.json()
            print('Successfully parsed as JSON!')
            print(f'JSON structure:\n{json.dumps(data, indent=2)}')
        except json.JSONDecodeError as e:
            print(f'\nFailed to parse as JSON: {str(e)}')
            
    except Exception as e:
        print(f'Error testing person API: {str(e)}')

if __name__ == '__main__':
    test_api_json()
