#!/usr/bin/env python
"""
Data Protection Test Script for Mobilize CRM
Tests encryption, data masking, and sensitive data handling
"""

import os
import re
import json
import logging
import argparse
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("data_protection_test")

class DataProtectionTester:
    def __init__(self, base_url, report_dir='results/data_protection'):
        self.base_url = base_url
        self.report_dir = report_dir
        self.session = requests.Session()
        self.findings = []
        
        # Define patterns for sensitive data
        self.patterns = {
            "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "password": r"password.*?[\"\':].*?[\"\']",
            "api_key": r"api[_\-\s]?key.*?[\"\':].*?[\"\']",
            "private_key": r"-----BEGIN (?:RSA |DSA |EC )?PRIVATE KEY-----",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        }
        
        # Create report directory if it doesn't exist
        os.makedirs(report_dir, exist_ok=True)
    
    def login(self, username, password):
        """Login to the application"""
        login_url = urljoin(self.base_url, "/api/auth/login")
        try:
            response = self.session.post(login_url, json={
                "email": username,
                "password": password
            })
            
            if response.status_code == 200:
                logger.info(f"Login successful as {username}")
                return True
            else:
                logger.error(f"Login failed with status code {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def run_data_protection_tests(self):
        """Run all data protection tests"""
        logger.info("Starting data protection tests...")
        
        # List of tests to run
        self.check_https_usage()
        self.check_password_handling()
        self.check_data_masking()
        self.check_sensitive_data_exposure()
        self.check_data_download_protection()
        self.check_file_upload_protection()
        
        # Generate report
        self._generate_report()
        
        return self.findings
    
    def check_https_usage(self):
        """Check if the application uses HTTPS"""
        logger.info("Checking HTTPS usage...")
        
        try:
            # Check if the URL is HTTPS
            parsed_url = urlparse(self.base_url)
            is_https = parsed_url.scheme == "https"
            
            if not is_https and not self.base_url.startswith("http://localhost"):
                self.findings.append({
                    "category": "Transport Security",
                    "severity": "HIGH",
                    "description": "Application does not use HTTPS",
                    "location": self.base_url,
                    "recommendation": "Enable HTTPS for all traffic"
                })
            else:
                logger.info("Application uses HTTPS or is running on localhost")
        except Exception as e:
            logger.error(f"Error checking HTTPS: {str(e)}")
        
        # Check for mixed content (if HTTPS)
        if is_https:
            try:
                response = self.session.get(self.base_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for HTTP resources in an HTTPS page
                mixed_content = []
                for tag in soup.find_all(['script', 'link', 'img']):
                    src = tag.get('src') or tag.get('href')
                    if src and src.startswith('http://'):
                        mixed_content.append(src)
                
                if mixed_content:
                    self.findings.append({
                        "category": "Transport Security",
                        "severity": "MEDIUM",
                        "description": f"Mixed content detected ({len(mixed_content)} resources)",
                        "details": mixed_content[:5],  # Show first 5 examples
                        "recommendation": "Ensure all resources are loaded over HTTPS"
                    })
            except Exception as e:
                logger.error(f"Error checking mixed content: {str(e)}")
    
    def check_password_handling(self):
        """Check password handling practices"""
        logger.info("Checking password handling...")
        
        # Test password reset functionality
        try:
            reset_url = urljoin(self.base_url, "/api/auth/password-reset")
            response = self.session.post(reset_url, json={"email": "test@example.com"})
            
            # Check if passwords are returned in response
            if "password" in response.text.lower():
                self.findings.append({
                    "category": "Password Security",
                    "severity": "HIGH",
                    "description": "Password reset response may include password in plaintext",
                    "location": reset_url,
                    "recommendation": "Never include passwords in responses"
                })
        except Exception as e:
            logger.error(f"Error checking password reset: {str(e)}")
        
        # Try common passwords to test password policy
        try:
            login_url = urljoin(self.base_url, "/api/auth/login")
            common_passwords = ["password", "123456", "admin", "welcome"]
            weak_password_accepted = False
            
            for password in common_passwords:
                response = self.session.post(login_url, json={
                    "email": "test@example.com",
                    "password": password
                })
                
                # If login is successful with a weak password
                if response.status_code == 200:
                    weak_password_accepted = True
                    break
            
            # Try to register with a weak password
            register_url = urljoin(self.base_url, "/api/auth/register")
            response = self.session.post(register_url, json={
                "email": f"test_{os.urandom(4).hex()}@example.com",
                "password": "password123",
                "name": "Test User"
            })
            
            # If registration is successful with a weak password
            if response.status_code == 200 or response.status_code == 201:
                weak_password_accepted = True
            
            if weak_password_accepted:
                self.findings.append({
                    "category": "Password Security",
                    "severity": "MEDIUM",
                    "description": "Weak passwords may be accepted",
                    "recommendation": "Implement a strong password policy requiring length, complexity, and prevent common passwords"
                })
        except Exception as e:
            logger.error(f"Error checking password policy: {str(e)}")
    
    def check_data_masking(self):
        """Check data masking for sensitive fields"""
        logger.info("Checking data masking...")
        
        # Define sensitive fields that should be masked
        sensitive_fields = [
            {"endpoint": "/api/v1/people", "fields": ["ssn", "credit_card", "banking_info"]},
            {"endpoint": "/api/v1/users", "fields": ["password", "security_answer"]},
            {"endpoint": "/api/v1/settings", "fields": ["api_key", "secret_key"]}
        ]
        
        for config in sensitive_fields:
            endpoint = config["endpoint"]
            fields = config["fields"]
            
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.get(url)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Check if response is a list or single object
                        items = data if isinstance(data, list) else [data]
                        
                        for item in items:
                            for field in fields:
                                if field in item and item[field] and not re.match(r"^\*+$", str(item[field])):
                                    self.findings.append({
                                        "category": "Sensitive Data Masking",
                                        "severity": "HIGH",
                                        "description": f"Sensitive field '{field}' is not masked",
                                        "location": f"{endpoint} response",
                                        "recommendation": f"Mask the {field} field with asterisks or implement proper data masking"
                                    })
                    except json.JSONDecodeError:
                        logger.warning(f"Response from {endpoint} is not valid JSON")
            except Exception as e:
                logger.error(f"Error checking data masking for {endpoint}: {str(e)}")
    
    def check_sensitive_data_exposure(self):
        """Check for sensitive data exposure in responses"""
        logger.info("Checking for sensitive data exposure...")
        
        # Pages to check
        pages_to_check = [
            "/",
            "/people",
            "/churches",
            "/admin",
            "/settings"
        ]
        
        for page in pages_to_check:
            try:
                url = urljoin(self.base_url, page)
                response = self.session.get(url)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Check for each sensitive data pattern
                    for data_type, pattern in self.patterns.items():
                        matches = re.findall(pattern, content)
                        
                        if matches:
                            # Filter out false positives
                            if data_type == "email" and page == "/settings":
                                # Email on settings page is likely user's own email, which is OK
                                continue
                                
                            self.findings.append({
                                "category": "Sensitive Data Exposure",
                                "severity": "HIGH",
                                "description": f"Potential {data_type} exposure detected",
                                "location": page,
                                "matches_count": len(matches),
                                "recommendation": f"Ensure {data_type} is not included in page source"
                            })
            except Exception as e:
                logger.error(f"Error checking sensitive data exposure for {page}: {str(e)}")
        
        # Check API responses for sensitive data
        api_endpoints = [
            "/api/v1/people",
            "/api/v1/churches",
            "/api/v1/users",
            "/api/v1/settings"
        ]
        
        for endpoint in api_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.get(url)
                
                if response.status_code == 200:
                    try:
                        json_content = json.dumps(response.json())
                        
                        # Check for each sensitive data pattern
                        for data_type, pattern in self.patterns.items():
                            matches = re.findall(pattern, json_content)
                            
                            if matches:
                                self.findings.append({
                                    "category": "Sensitive Data Exposure",
                                    "severity": "HIGH",
                                    "description": f"Potential {data_type} exposure in API response",
                                    "location": endpoint,
                                    "matches_count": len(matches),
                                    "recommendation": f"Ensure {data_type} is not included in API responses"
                                })
                    except json.JSONDecodeError:
                        logger.warning(f"Response from {endpoint} is not valid JSON")
            except Exception as e:
                logger.error(f"Error checking API sensitive data exposure for {endpoint}: {str(e)}")
    
    def check_data_download_protection(self):
        """Check for protection of data downloads"""
        logger.info("Checking data download protection...")
        
        # Data export endpoints to check
        export_endpoints = [
            "/api/v1/people/export",
            "/api/v1/churches/export",
            "/api/v1/reports/export"
        ]
        
        for endpoint in export_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                
                # Try without authentication (if not already logged in)
                if not self.session.cookies:
                    no_auth_session = requests.Session()
                    response = no_auth_session.get(url)
                    
                    if response.status_code == 200:
                        self.findings.append({
                            "category": "Data Export",
                            "severity": "HIGH",
                            "description": "Data export endpoint accessible without authentication",
                            "location": endpoint,
                            "recommendation": "Require authentication for all data export endpoints"
                        })
                
                # Check for direct object reference vulnerability
                object_ids = ["1", "2", "999", "other_office_id"]
                for obj_id in object_ids:
                    object_url = f"{url}?id={obj_id}"
                    response = self.session.get(object_url)
                    
                    # If successful response for random IDs, might be IDOR
                    if response.status_code == 200:
                        self.findings.append({
                            "category": "Data Export",
                            "severity": "HIGH",
                            "description": "Potential insecure direct object reference in data export",
                            "location": f"{endpoint}?id={obj_id}",
                            "recommendation": "Implement proper access controls for data exports"
                        })
                        break
            except Exception as e:
                logger.error(f"Error checking data download protection for {endpoint}: {str(e)}")
    
    def check_file_upload_protection(self):
        """Check for file upload protections"""
        logger.info("Checking file upload protections...")
        
        # File upload endpoints to check
        upload_endpoints = [
            "/api/v1/people/import",
            "/api/v1/churches/import",
            "/api/v1/attachments/upload"
        ]
        
        for endpoint in upload_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                
                # Try uploading a small text file with js code
                files = {
                    'file': ('test.html', '<script>alert("XSS")</script>', 'text/html')
                }
                
                response = self.session.post(url, files=files)
                
                # If successful, might be vulnerable
                if response.status_code == 200:
                    self.findings.append({
                        "category": "File Upload",
                        "severity": "HIGH",
                        "description": "Potential unrestricted file upload vulnerability",
                        "location": endpoint,
                        "recommendation": "Validate file types, content, and extensions"
                    })
                
                # Try a different file type
                files = {
                    'file': ('test.exe', 'MZ\x90\x00\x03\x00\x00\x00', 'application/octet-stream')
                }
                
                response = self.session.post(url, files=files)
                
                # If successful, might be vulnerable
                if response.status_code == 200:
                    self.findings.append({
                        "category": "File Upload",
                        "severity": "HIGH",
                        "description": "Potential executable file upload vulnerability",
                        "location": endpoint,
                        "recommendation": "Block executable file uploads"
                    })
            except Exception as e:
                logger.error(f"Error checking file upload protection for {endpoint}: {str(e)}")
    
    def _generate_report(self):
        """Generate a comprehensive data protection report"""
        logger.info("Generating data protection report...")
        
        # Count findings by severity
        severity_counts = {
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "INFO": 0
        }
        
        for finding in self.findings:
            severity = finding.get("severity", "INFO")
            severity_counts[severity] += 1
        
        # Group findings by category
        categories = {}
        for finding in self.findings:
            category = finding.get("category", "Other")
            if category not in categories:
                categories[category] = []
            categories[category].append(finding)
        
        # Generate summary
        summary = {
            "application": self.base_url,
            "total_findings": len(self.findings),
            "severity_counts": severity_counts,
            "categories": {k: len(v) for k, v in categories.items()},
            "findings": self.findings
        }
        
        # Save report to file
        report_path = os.path.join(self.report_dir, "data_protection_report.json")
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Data protection report saved to {report_path}")
        
        # Print summary to console
        print("\n---- DATA PROTECTION TEST SUMMARY ----")
        print(f"Application: {self.base_url}")
        print(f"Total findings: {len(self.findings)}")
        print("\nFindings by severity:")
        for severity, count in severity_counts.items():
            print(f"- {severity}: {count}")
        
        print("\nFindings by category:")
        for category, count in summary["categories"].items():
            print(f"- {category}: {count}")
        
        if self.findings:
            print("\nTop findings:")
            for i, finding in enumerate(sorted(self.findings, 
                                              key=lambda x: ["HIGH", "MEDIUM", "LOW", "INFO"].index(x.get("severity", "INFO")))[:5], 1):
                print(f"{i}. [{finding['severity']}] {finding['category']}: {finding['description']}")
        
        print(f"\nDetailed report saved to {report_path}")

def main():
    parser = argparse.ArgumentParser(description="Data Protection Tester for Mobilize CRM")
    parser.add_argument("--url", default="http://localhost:5000",
                        help="Base URL of the application (default: http://localhost:5000)")
    parser.add_argument("--username", default="admin@example.com",
                        help="Username for login")
    parser.add_argument("--password", default="password",
                        help="Password for login")
    parser.add_argument("--report-dir", default="results/data_protection",
                        help="Directory to save the security report (default: results/data_protection)")
    
    args = parser.parse_args()
    
    # Create tester and run tests
    tester = DataProtectionTester(args.url, args.report_dir)
    
    # Try to login
    if tester.login(args.username, args.password):
        logger.info("Login successful, running data protection checks...")
    else:
        logger.warning("Login failed, running data protection checks with limited scope...")
    
    tester.run_data_protection_tests()

if __name__ == "__main__":
    main() 