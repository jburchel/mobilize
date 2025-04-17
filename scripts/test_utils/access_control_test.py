#!/usr/bin/env python
"""
Access Control Test Script for Mobilize CRM
Tests role-based access control and data isolation between offices
"""

import os
import sys
import json
import logging
import argparse
import requests
from urllib.parse import urljoin
from tabulate import tabulate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("access_control_test")

class AccessControlTester:
    def __init__(self, base_url, report_dir='results/access_control'):
        self.base_url = base_url
        self.report_dir = report_dir
        self.sessions = {}  # Sessions for different user roles
        self.results = []
        
        # Create report directory if it doesn't exist
        os.makedirs(report_dir, exist_ok=True)
    
    def login_user(self, role, email, password):
        """Login with specific user credentials"""
        session = requests.Session()
        login_url = urljoin(self.base_url, "/api/auth/login")
        
        try:
            response = session.post(login_url, json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                logger.info(f"Login successful for {role} user ({email})")
                self.sessions[role] = session
                return True
            else:
                logger.error(f"Login failed for {role} user ({email}): {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Login error for {role} user: {str(e)}")
            return False
    
    def run_access_control_tests(self):
        """Run all access control tests"""
        logger.info("Starting access control tests...")
        
        # Check which user roles we have sessions for
        if not self.sessions:
            logger.error("No user sessions available. Please login first.")
            return []
        
        # Run tests for user access to different endpoints
        self.test_endpoint_access()
        
        # If we have multiple roles, test data isolation
        if len(self.sessions) > 1:
            self.test_data_isolation()
        
        # Test office isolation if we have users from different offices
        self.test_office_isolation()
        
        # Generate report
        self._generate_report()
        
        return self.results
    
    def test_endpoint_access(self):
        """Test access to different endpoints based on user roles"""
        logger.info("Testing endpoint access by role...")
        
        # Define endpoints and expected access by role
        endpoints = {
            "/": {
                "description": "Dashboard",
                "expected_access": ["super_admin", "admin", "user", "viewer"]
            },
            "/people": {
                "description": "People List",
                "expected_access": ["super_admin", "admin", "user", "viewer"]
            },
            "/churches": {
                "description": "Churches List",
                "expected_access": ["super_admin", "admin", "user", "viewer"]
            },
            "/admin": {
                "description": "Admin Panel",
                "expected_access": ["super_admin", "admin"]
            },
            "/admin/offices": {
                "description": "Office Management",
                "expected_access": ["super_admin"]
            },
            "/api/v1/people": {
                "description": "People API",
                "expected_access": ["super_admin", "admin", "user", "viewer"]
            },
            "/api/v1/churches": {
                "description": "Churches API",
                "expected_access": ["super_admin", "admin", "user", "viewer"]
            },
            "/api/v1/admin/users": {
                "description": "User Management API",
                "expected_access": ["super_admin", "admin"]
            }
        }
        
        # Test each endpoint with each user role
        for endpoint, config in endpoints.items():
            description = config["description"]
            expected_access = config["expected_access"]
            
            logger.info(f"Testing access to {endpoint} ({description})")
            
            for role, session in self.sessions.items():
                url = urljoin(self.base_url, endpoint)
                
                try:
                    response = session.get(url)
                    has_access = response.status_code == 200
                    should_have_access = role in expected_access
                    
                    result = {
                        "endpoint": endpoint,
                        "description": description,
                        "role": role,
                        "status_code": response.status_code,
                        "has_access": has_access,
                        "should_have_access": should_have_access,
                        "result": "PASS" if has_access == should_have_access else "FAIL"
                    }
                    
                    self.results.append(result)
                    
                    if has_access != should_have_access:
                        if has_access:
                            logger.warning(f"Role {role} has unexpected access to {endpoint}")
                        else:
                            logger.warning(f"Role {role} is denied expected access to {endpoint}")
                    
                except Exception as e:
                    logger.error(f"Error testing {endpoint} with role {role}: {str(e)}")
                    self.results.append({
                        "endpoint": endpoint,
                        "description": description,
                        "role": role,
                        "error": str(e),
                        "result": "ERROR"
                    })
    
    def test_data_isolation(self):
        """Test if users can only access their authorized data"""
        logger.info("Testing data isolation between users...")
        
        # Test people data access
        self._test_resource_isolation("/api/v1/people", "people")
        
        # Test churches data access
        self._test_resource_isolation("/api/v1/churches", "churches")
        
        # Test communications data access
        self._test_resource_isolation("/api/v1/communications", "communications")
    
    def _test_resource_isolation(self, endpoint, resource_type):
        """Test isolation for a specific resource type"""
        resource_ids = {}
        
        # First, get resource IDs visible to each role
        for role, session in self.sessions.items():
            url = urljoin(self.base_url, endpoint)
            
            try:
                response = session.get(url)
                if response.status_code == 200:
                    data = response.json()
                    # Extract IDs from the response (assuming a typical format)
                    if isinstance(data, list):
                        ids = [item.get('id') for item in data if item.get('id')]
                    elif isinstance(data, dict) and 'items' in data:
                        ids = [item.get('id') for item in data['items'] if item.get('id')]
                    else:
                        ids = []
                    
                    resource_ids[role] = ids
                    logger.info(f"Role {role} sees {len(ids)} {resource_type}")
            except Exception as e:
                logger.error(f"Error getting {resource_type} for role {role}: {str(e)}")
        
        # Now, for each role's visible resources, check if other roles can access them
        for role, ids in resource_ids.items():
            # Take a sample of IDs to test (up to 5)
            sample_ids = ids[:5] if len(ids) > 5 else ids
            
            for item_id in sample_ids:
                detail_url = urljoin(self.base_url, f"{endpoint}/{item_id}")
                
                # Check which other roles can access this item
                for other_role, other_session in self.sessions.items():
                    if other_role == role:
                        continue  # Skip the owner role
                    
                    try:
                        response = other_session.get(detail_url)
                        can_access = response.status_code == 200
                        
                        # For super_admin and admin, they should be able to access all
                        should_access = other_role in ["super_admin", "admin"]
                        
                        self.results.append({
                            "test_type": "data_isolation",
                            "resource_type": resource_type,
                            "item_id": item_id,
                            "owner_role": role,
                            "accessing_role": other_role,
                            "status_code": response.status_code,
                            "has_access": can_access,
                            "should_have_access": should_access,
                            "result": "PASS" if can_access == should_access else "FAIL"
                        })
                        
                        if can_access != should_access:
                            logger.warning(f"Role {other_role} access to {resource_type}/{item_id} (owned by {role}): {'Unexpected' if can_access else 'Denied'}")
                    
                    except Exception as e:
                        logger.error(f"Error checking {resource_type}/{item_id} access for role {other_role}: {str(e)}")
    
    def test_office_isolation(self):
        """Test if data is properly isolated between offices"""
        logger.info("Testing office isolation...")
        
        # Get office information for each user
        office_info = {}
        for role, session in self.sessions.items():
            try:
                # Assuming there's an endpoint to get current user info with office
                user_info_url = urljoin(self.base_url, "/api/v1/users/me")
                response = session.get(user_info_url)
                
                if response.status_code == 200:
                    user_data = response.json()
                    office_id = user_data.get("office_id")
                    if office_id:
                        office_info[role] = {"office_id": office_id, "session": session}
            except Exception as e:
                logger.error(f"Error getting office info for role {role}: {str(e)}")
        
        # If we have users from different offices, test isolation
        office_ids = set(info["office_id"] for info in office_info.values())
        if len(office_ids) > 1:
            logger.info(f"Found users from {len(office_ids)} different offices. Testing isolation...")
            
            # Group users by office
            offices = {}
            for role, info in office_info.items():
                office_id = info["office_id"]
                if office_id not in offices:
                    offices[office_id] = []
                offices[office_id].append((role, info["session"]))
            
            # Test if users can access data from other offices
            for office_id, users in offices.items():
                # Get data from this office using the first user
                role, session = users[0]
                
                # Try to get people from this office
                people_url = urljoin(self.base_url, "/api/v1/people")
                try:
                    response = session.get(people_url)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list):
                            people = data
                        elif isinstance(data, dict) and 'items' in data:
                            people = data['items']
                        else:
                            people = []
                        
                        # If we have people, check if users from other offices can access them
                        if people:
                            person = people[0]  # Take first person
                            person_id = person.get('id')
                            
                            if person_id:
                                detail_url = urljoin(self.base_url, f"/api/v1/people/{person_id}")
                                
                                # Test access from users in other offices
                                for other_office_id, other_users in offices.items():
                                    if other_office_id == office_id:
                                        continue  # Skip same office
                                    
                                    other_role, other_session = other_users[0]
                                    
                                    try:
                                        response = other_session.get(detail_url)
                                        can_access = response.status_code == 200
                                        
                                        # Super admins should have access across offices
                                        should_access = other_role == "super_admin"
                                        
                                        self.results.append({
                                            "test_type": "office_isolation",
                                            "resource_type": "person",
                                            "item_id": person_id,
                                            "owner_office": office_id,
                                            "accessing_office": other_office_id,
                                            "accessing_role": other_role,
                                            "status_code": response.status_code,
                                            "has_access": can_access,
                                            "should_have_access": should_access,
                                            "result": "PASS" if can_access == should_access else "FAIL"
                                        })
                                        
                                        if can_access != should_access:
                                            logger.warning(f"Role {other_role} from office {other_office_id} access to person {person_id} (office {office_id}): {'Unexpected' if can_access else 'Denied'}")
                                    
                                    except Exception as e:
                                        logger.error(f"Error in office isolation test: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Error getting people for office {office_id}: {str(e)}")
    
    def _generate_report(self):
        """Generate a comprehensive access control report"""
        logger.info("Generating access control report...")
        
        # Count test results
        result_counts = {"PASS": 0, "FAIL": 0, "ERROR": 0}
        for result in self.results:
            result_status = result.get("result", "ERROR")
            result_counts[result_status] += 1
        
        # Group results by test type
        test_types = {}
        for result in self.results:
            test_type = result.get("test_type", "endpoint_access")
            if test_type not in test_types:
                test_types[test_type] = []
            test_types[test_type].append(result)
        
        # Generate summary report
        summary = {
            "total_tests": len(self.results),
            "passed": result_counts["PASS"],
            "failed": result_counts["FAIL"],
            "errors": result_counts["ERROR"],
            "results_by_type": {
                test_type: len(results) for test_type, results in test_types.items()
            },
            "detailed_results": self.results
        }
        
        # Save report to file
        report_path = os.path.join(self.report_dir, "access_control_report.json")
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Access control report saved to {report_path}")
        
        # Print summary to console
        print("\n---- ACCESS CONTROL TEST SUMMARY ----")
        print(f"Total tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Errors: {summary['errors']}")
        
        # Print test results by type
        print("\nResults by test type:")
        for test_type, count in summary['results_by_type'].items():
            print(f"- {test_type}: {count} tests")
        
        # Print endpoint access results in table format
        if "endpoint_access" in test_types:
            endpoint_results = []
            for result in test_types.get("endpoint_access", []):
                if "error" not in result:  # Skip error results
                    endpoint_results.append([
                        result.get("endpoint", ""),
                        result.get("role", ""),
                        "✅" if result.get("has_access") else "❌",
                        "✅" if result.get("should_have_access") else "❌",
                        "✅" if result.get("result") == "PASS" else "❌"
                    ])
            
            if endpoint_results:
                print("\nEndpoint Access Results:")
                print(tabulate(endpoint_results, 
                              headers=["Endpoint", "Role", "Has Access", "Should Access", "Result"],
                              tablefmt="grid"))
        
        # Print failed tests
        failed_results = [r for r in self.results if r.get("result") == "FAIL"]
        if failed_results:
            print("\nFailed tests:")
            for i, result in enumerate(failed_results[:5], 1):  # Show first 5
                print(f"{i}. {result.get('test_type', 'unknown')} - ", end="")
                if "endpoint" in result:
                    print(f"Role {result.get('role')} accessing {result.get('endpoint')}")
                elif "resource_type" in result:
                    print(f"{result.get('accessing_role')} accessing {result.get('resource_type')} {result.get('item_id')}")
                else:
                    print(str(result))
            
            if len(failed_results) > 5:
                print(f"...and {len(failed_results) - 5} more.")
        
        print(f"\nDetailed report saved to {report_path}")

def main():
    parser = argparse.ArgumentParser(description="Access Control Tester for Mobilize CRM")
    parser.add_argument("--url", default="http://localhost:5000",
                        help="Base URL of the application (default: http://localhost:5000)")
    parser.add_argument("--report-dir", default="results/access_control",
                        help="Directory to save the report (default: results/access_control)")
    
    # User credentials for different roles
    parser.add_argument("--super-admin-email", help="Super Admin email")
    parser.add_argument("--super-admin-password", help="Super Admin password")
    parser.add_argument("--admin-email", help="Admin email")
    parser.add_argument("--admin-password", help="Admin password")
    parser.add_argument("--user-email", help="Regular user email")
    parser.add_argument("--user-password", help="Regular user password")
    parser.add_argument("--viewer-email", help="Viewer email")
    parser.add_argument("--viewer-password", help="Viewer password")
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = AccessControlTester(args.url, args.report_dir)
    
    # Login with provided credentials
    logged_in = False
    
    if args.super_admin_email and args.super_admin_password:
        if tester.login_user("super_admin", args.super_admin_email, args.super_admin_password):
            logged_in = True
    
    if args.admin_email and args.admin_password:
        if tester.login_user("admin", args.admin_email, args.admin_password):
            logged_in = True
    
    if args.user_email and args.user_password:
        if tester.login_user("user", args.user_email, args.user_password):
            logged_in = True
    
    if args.viewer_email and args.viewer_password:
        if tester.login_user("viewer", args.viewer_email, args.viewer_password):
            logged_in = True
    
    if not logged_in:
        logger.error("No successful logins. Please provide valid credentials.")
        sys.exit(1)
    
    # Run tests
    tester.run_access_control_tests()

if __name__ == "__main__":
    main() 