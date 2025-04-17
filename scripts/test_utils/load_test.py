#!/usr/bin/env python
"""
Load Testing Script for Mobilize CRM
Uses Locust for load testing
"""

import os
import sys
import time
import random
from locust import HttpUser, task, between

class MobilizeUser(HttpUser):
    wait_time = between(1, 5)  # Wait between 1 and 5 seconds between tasks
    
    def on_start(self):
        """Log in at the start of the test"""
        # For this load test, we'll use a test account
        # In a real scenario, you might want to create test users dynamically
        self.client.post("/api/auth/login", {
            "email": "test@example.com",
            "password": "testpassword"
        })
    
    @task(1)
    def view_dashboard(self):
        """Load the dashboard page"""
        self.client.get("/")
    
    @task(2)
    def view_people_list(self):
        """View the people list page"""
        self.client.get("/people")
    
    @task(2)
    def view_churches_list(self):
        """View the churches list page"""
        self.client.get("/churches")
    
    @task(3)
    def view_communications(self):
        """View communications page"""
        self.client.get("/communications")
    
    @task(1)
    def view_reports(self):
        """View reports page"""
        self.client.get("/reports")
    
    @task(2)
    def api_calls(self):
        """Make API calls"""
        self.client.get("/api/v1/people")
        self.client.get("/api/v1/churches")
    
    @task(1)
    def search_contacts(self):
        """Search for contacts"""
        search_terms = ["church", "pastor", "member", "volunteer", "donor"]
        term = random.choice(search_terms)
        self.client.get(f"/people?q={term}")

# If run directly, provide info on how to use with Locust
if __name__ == "__main__":
    print("This script is designed to be run with Locust.")
    print("Install Locust with: pip install locust")
    print("Run with: locust -f scripts/test_utils/load_test.py")
    print("Then open http://localhost:8089 in your browser") 