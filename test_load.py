#!/usr/bin/env python3
"""
Load testing script for Mobilize CRM app with PostgreSQL
"""
import os
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Set environment to production to use PostgreSQL
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'app.py'

# Load environment variables
load_dotenv('.env.production')

# Import app after environment is set
from app import create_app

app = create_app()
test_client = app.test_client()

def make_request(endpoint):
    """Make a request to the specified endpoint and record the time taken"""
    start_time = time.time()
    response = test_client.get(endpoint)
    end_time = time.time()
    return {
        'endpoint': endpoint,
        'status_code': response.status_code,
        'time': end_time - start_time,
        'response_length': len(response.data)
    }

def run_load_test(endpoint, num_requests=50, concurrent_requests=10):
    """Run a load test against the specified endpoint"""
    print(f"\n=== LOAD TESTING {endpoint} ===")
    print(f"Making {num_requests} requests with {concurrent_requests} concurrent connections")
    
    results = []
    with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        futures = [executor.submit(make_request, endpoint) for _ in range(num_requests)]
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if len(results) % 10 == 0:
                print(f"Completed {len(results)} requests")
    
    # Analyze results
    times = [r['time'] for r in results]
    status_codes = [r['status_code'] for r in results]
    
    print("\nResults Summary:")
    print(f"Total requests: {len(results)}")
    print(f"Successful requests: {status_codes.count(200)}")
    print(f"Failed requests: {len(results) - status_codes.count(200)}")
    print(f"Average response time: {statistics.mean(times):.4f} seconds")
    print(f"Median response time: {statistics.median(times):.4f} seconds")
    print(f"Min response time: {min(times):.4f} seconds")
    print(f"Max response time: {max(times):.4f} seconds")
    print(f"Requests per second: {num_requests / sum(times):.2f}")
    
    return results

def main():
    """Run load tests against several endpoints"""
    print("Running load tests against PostgreSQL database...")
    
    # Test endpoints
    endpoints = [
        '/health',                # Basic health check
        '/api/health-check',      # API health check that verifies database
        '/api/debug/db-config'    # Database configuration check
    ]
    
    for endpoint in endpoints:
        run_load_test(endpoint)
    
    print("\n✅ Load testing completed")

if __name__ == "__main__":
    main() 