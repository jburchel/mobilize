import requests
import json

# Configuration
BASE_URL = 'http://localhost:8000'

def test_api_response():
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Test the chart data API endpoints directly
    print('Testing API endpoints directly:')
    
    # Test person pipeline endpoint
    try:
        response = session.get(f'{BASE_URL}/api/chart-data/person')
        print(f'Person API status: {response.status_code}')
        if response.status_code == 200:
            try:
                data = response.json()
                print(f'Person API data structure: {json.dumps(data, indent=2)}')
                
                # Check for required fields
                if 'stages' in data:
                    print(f'Number of stages: {len(data["stages"])}')
                    for i, stage in enumerate(data['stages']):
                        print(f'Stage {i+1}: {stage.get("name", "N/A")} - Count: {stage.get("contact_count", 0)}')
                else:
                    print('No stages found in the response')
            except json.JSONDecodeError:
                print(f'Response is not valid JSON: {response.text[:200]}...')
        else:
            print(f'Person API response: {response.text[:200]}...')
    except Exception as e:
        print(f'Error testing person API: {str(e)}')

if __name__ == '__main__':
    test_api_response()
