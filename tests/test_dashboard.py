import requests
import webbrowser
import json
import time

# Configuration
BASE_URL = 'http://localhost:8000'
USERNAME = 'admin@example.com'  # Replace with a valid username
PASSWORD = 'password'  # Replace with a valid password

def test_dashboard():
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Get the login page
    response = session.get(f'{BASE_URL}/api/auth/login-page')
    print(f'Login page status: {response.status_code}')
    
    # Step 2: Open the dashboard in a browser
    dashboard_url = f'{BASE_URL}/'
    print(f'Opening dashboard at: {dashboard_url}')
    webbrowser.open(dashboard_url)
    
    # Step 3: Test the chart API endpoints directly
    print('\nTesting chart API endpoints directly...')
    time.sleep(2)  # Give the browser time to open
    
    try:
        # Test person chart endpoint
        print('\nTesting person chart endpoint:')
        response = requests.get(f'{BASE_URL}/api/chart-data/person')
        print(f'Status code: {response.status_code}')
        print(f'Content type: {response.headers.get("Content-Type", "unknown")}')
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f'Successfully parsed JSON response with {len(data.get("stages", []))} stages')
                # Save to file for inspection
                with open('person_chart_data_direct.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print('Saved data to person_chart_data_direct.json')
            except Exception as e:
                print(f'Error parsing JSON: {str(e)}')
                print(f'Raw response: {response.text[:200]}...')
        else:
            print(f'Response: {response.text[:200]}...')
            
        # Test church chart endpoint
        print('\nTesting church chart endpoint:')
        response = requests.get(f'{BASE_URL}/api/chart-data/church')
        print(f'Status code: {response.status_code}')
        print(f'Content type: {response.headers.get("Content-Type", "unknown")}')
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f'Successfully parsed JSON response with {len(data.get("stages", []))} stages')
                # Save to file for inspection
                with open('church_chart_data_direct.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print('Saved data to church_chart_data_direct.json')
            except Exception as e:
                print(f'Error parsing JSON: {str(e)}')
                print(f'Raw response: {response.text[:200]}...')
        else:
            print(f'Response: {response.text[:200]}...')
    except Exception as e:
        print(f'Error testing API endpoints: {str(e)}')
    
    print('\nTest completed. Please check the browser to see if the charts are displayed correctly.')
    print('If you need to log in, use the credentials provided in the script.')

if __name__ == '__main__':
    test_dashboard()
