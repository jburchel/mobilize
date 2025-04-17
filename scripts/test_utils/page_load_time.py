#!/usr/bin/env python
"""
Page Load Time Measurement Script
Measures and reports loading times for different pages in the application
"""

import time
import argparse
import statistics
import requests
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from tabulate import tabulate

# URLs to test - these should be updated to match your deployment
BASE_URLS = {
    'local': 'http://localhost:5000',
    'dev': 'http://dev-server-url',
    'prod': 'https://production-url'
}

# List of endpoints to test
ENDPOINTS = [
    '/',  # Dashboard
    '/people',  # People list
    '/churches',  # Churches list
    '/communications',  # Communications
    '/tasks',  # Tasks
    '/pipeline',  # Pipeline
    '/reports',  # Reports
    '/admin',  # Admin panel
    '/api/v1/people',  # API endpoints
    '/api/v1/churches'
]

def login(session, base_url, username, password):
    """Log in to get a valid session for testing"""
    login_url = f"{base_url}/api/auth/login"
    response = session.post(login_url, json={
        "email": username,
        "password": password
    })
    if response.status_code != 200:
        print(f"Login failed with status code {response.status_code}")
        return False
    return True

def measure_page_load(session, url, num_samples=5):
    """Measure load time for a given URL with multiple samples"""
    load_times = []
    
    for _ in range(num_samples):
        start_time = time.time()
        response = session.get(url)
        end_time = time.time()
        
        if response.status_code == 200:
            load_time = (end_time - start_time) * 1000  # Convert to milliseconds
            load_times.append(load_time)
        else:
            print(f"Request to {url} failed with status code {response.status_code}")
        
        # Small delay between requests
        time.sleep(0.5)
    
    if load_times:
        avg_time = statistics.mean(load_times)
        min_time = min(load_times)
        max_time = max(load_times)
        return {
            'avg': avg_time,
            'min': min_time,
            'max': max_time,
            'samples': load_times
        }
    return None

def run_load_test(environment, username, password, num_samples=5, output_file=None):
    """Run load tests for all endpoints and aggregate results"""
    base_url = BASE_URLS.get(environment)
    if not base_url:
        print(f"Unknown environment: {environment}")
        return
    
    session = requests.Session()
    
    # Log in first
    if not login(session, base_url, username, password):
        return
    
    results = {}
    print(f"Testing {len(ENDPOINTS)} endpoints on {base_url} with {num_samples} samples each...")
    
    for endpoint in tqdm(ENDPOINTS):
        url = f"{base_url}{endpoint}"
        result = measure_page_load(session, url, num_samples)
        if result:
            results[endpoint] = result
    
    # Create a report
    report_data = []
    for endpoint, data in results.items():
        report_data.append([
            endpoint,
            f"{data['avg']:.2f}",
            f"{data['min']:.2f}",
            f"{data['max']:.2f}"
        ])
    
    # Sort by average load time (descending)
    report_data.sort(key=lambda x: float(x[1]), reverse=True)
    
    # Display the report
    headers = ["Endpoint", "Avg Time (ms)", "Min Time (ms)", "Max Time (ms)"]
    print("\nPage Load Time Results:")
    print(tabulate(report_data, headers=headers, tablefmt="grid"))
    
    # Generate a plot
    endpoints = [r[0] for r in report_data]
    avg_times = [float(r[1]) for r in report_data]
    
    plt.figure(figsize=(12, 6))
    bars = plt.barh(endpoints, avg_times)
    plt.xlabel('Average Load Time (ms)')
    plt.title(f'Page Load Times - {environment.capitalize()} Environment')
    plt.tight_layout()
    
    # Save the results if an output file is specified
    if output_file:
        plt.savefig(f"{output_file}.png")
        # Also save as CSV
        df = pd.DataFrame(report_data, columns=headers)
        df.to_csv(f"{output_file}.csv", index=False)
        print(f"Results saved to {output_file}.png and {output_file}.csv")
    
    plt.show()
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure page load times across the application")
    parser.add_argument("--env", choices=["local", "dev", "prod"], default="local",
                        help="Environment to test (default: local)")
    parser.add_argument("--username", default="admin@example.com",
                        help="Username for login")
    parser.add_argument("--password", default="password",
                        help="Password for login")
    parser.add_argument("--samples", type=int, default=5,
                        help="Number of samples per endpoint (default: 5)")
    parser.add_argument("--output", help="Output file name (without extension)")
    
    args = parser.parse_args()
    
    run_load_test(args.env, args.username, args.password, args.samples, args.output) 