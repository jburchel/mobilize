#!/usr/bin/env python
"""
Security Audit Script for Mobilize CRM
Scans the application for common security vulnerabilities and issues
"""

import os
import re
import sys
import json
import argparse
import logging
import requests
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("security_audit")

class SecurityAuditor:
    def __init__(self, base_url, report_dir='results/security_audit'):
        self.base_url = base_url
        self.report_dir = report_dir
        self.session = requests.Session()
        self.findings = []
        self.csrf_token = None
        
        # Create report directory if it doesn't exist
        os.makedirs(report_dir, exist_ok=True)
    
    def login(self, username, password):
        """Login to get a valid session for testing"""
        login_url = urljoin(self.base_url, "/api/auth/login")
        try:
            response = self.session.post(login_url, json={
                "email": username,
                "password": password
            })
            if response.status_code != 200:
                logger.error(f"Login failed with status code {response.status_code}")
                return False
                
            # Check if CSRF token is being set
            self._check_csrf()
            return True
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def _check_csrf(self):
        """Check if CSRF token is available in the session"""
        try:
            # First try to get it from cookies
            csrf_cookie = self.session.cookies.get('csrf_token')
            
            # If not in cookies, try to fetch from a page
            if not csrf_cookie:
                response = self.session.get(urljoin(self.base_url, "/"))
                match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
                if match:
                    self.csrf_token = match.group(1)
                else:
                    logger.warning("CSRF token not found in page")
                    self.findings.append({
                        "severity": "HIGH",
                        "category": "CSRF",
                        "description": "CSRF token not found in page or cookies",
                        "recommendation": "Implement proper CSRF protection using Flask-WTF"
                    })
            else:
                self.csrf_token = csrf_cookie
                logger.info("Found CSRF token in cookies")
        except Exception as e:
            logger.error(f"Error checking CSRF: {str(e)}")
    
    def run_security_checks(self):
        """Run all security checks and compile a report"""
        logger.info("Starting security audit...")
        
        # List of security checks to run
        checks = [
            self.check_csrf_protection,
            self.check_xss_vulnerabilities,
            self.check_http_security_headers,
            self.check_open_redirects,
            self.check_authentication_issues,
            self.check_rate_limiting,
            self.check_sql_injection
        ]
        
        # Run all checks
        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.map(lambda check: check(), checks)
        
        # Generate report
        self._generate_report()
        
        return self.findings
    
    def check_csrf_protection(self):
        """Check CSRF protection on forms and API endpoints"""
        logger.info("Checking CSRF protection...")
        
        # List of endpoints to test
        endpoints = [
            "/people/create",
            "/churches/create",
            "/tasks/create",
            "/api/v1/people",
            "/api/v1/churches"
        ]
        
        for endpoint in endpoints:
            url = urljoin(self.base_url, endpoint)
            
            # Try without CSRF token
            try:
                response = self.session.post(url, json={"test": "data"})
                
                # If successful without CSRF token, it might be vulnerable
                if response.status_code < 400:  # 200 or 300 range
                    self.findings.append({
                        "severity": "HIGH",
                        "category": "CSRF",
                        "endpoint": endpoint,
                        "description": f"Endpoint accepts POST without CSRF token (status: {response.status_code})",
                        "recommendation": "Ensure all forms and API endpoints require valid CSRF tokens"
                    })
                elif response.status_code == 403:
                    logger.info(f"Endpoint {endpoint} correctly rejects requests without CSRF token")
            except Exception as e:
                logger.error(f"Error testing CSRF on {endpoint}: {str(e)}")
    
    def check_xss_vulnerabilities(self):
        """Check for potential XSS vulnerabilities"""
        logger.info("Checking XSS vulnerabilities...")
        
        # XSS test payloads
        xss_payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)"
        ]
        
        # Parameters to test
        params = {
            "/people": ["q", "sort", "filter"],
            "/churches": ["q", "sort", "filter"],
            "/tasks": ["q", "status", "priority"]
        }
        
        for path, parameters in params.items():
            url = urljoin(self.base_url, path)
            for param in parameters:
                for payload in xss_payloads:
                    try:
                        params = {param: payload}
                        response = self.session.get(url, params=params)
                        
                        # Check if payload is reflected without encoding
                        if payload in response.text:
                            self.findings.append({
                                "severity": "HIGH",
                                "category": "XSS",
                                "endpoint": f"{path}?{param}={payload}",
                                "description": f"Potential XSS: Payload reflected without encoding",
                                "recommendation": "Implement proper output encoding and Content-Security-Policy"
                            })
                    except Exception as e:
                        logger.error(f"Error testing XSS on {path}: {str(e)}")
    
    def check_http_security_headers(self):
        """Check for important security headers"""
        logger.info("Checking HTTP security headers...")
        
        # Important security headers to check
        security_headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "Content-Security-Policy": None,  # Any value is acceptable
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": None  # Any value is acceptable
        }
        
        try:
            response = self.session.get(self.base_url)
            headers = response.headers
            
            missing_headers = []
            for header, expected_value in security_headers.items():
                if header not in headers:
                    missing_headers.append(header)
                elif expected_value and headers[header] != expected_value:
                    self.findings.append({
                        "severity": "MEDIUM",
                        "category": "Security Headers",
                        "header": header,
                        "current_value": headers[header],
                        "expected_value": expected_value,
                        "description": f"Security header has unexpected value",
                        "recommendation": f"Set {header} to '{expected_value}'"
                    })
            
            if missing_headers:
                self.findings.append({
                    "severity": "MEDIUM",
                    "category": "Security Headers",
                    "description": f"Missing security headers: {', '.join(missing_headers)}",
                    "recommendation": "Implement all recommended security headers using Flask-Talisman"
                })
        except Exception as e:
            logger.error(f"Error checking security headers: {str(e)}")
    
    def check_open_redirects(self):
        """Check for open redirect vulnerabilities"""
        logger.info("Checking open redirect vulnerabilities...")
        
        # Redirect test payloads
        redirect_payloads = [
            "https://malicious-site.com",
            "//evil.com",
            "/\\evil.com"
        ]
        
        # Parameters to test
        redirect_params = {
            "/login": ["next", "redirect", "url"],
            "/auth/login": ["next", "redirect", "url"]
        }
        
        for path, parameters in redirect_params.items():
            url = urljoin(self.base_url, path)
            for param in parameters:
                for payload in redirect_payloads:
                    try:
                        params = {param: payload}
                        response = self.session.get(url, params=params, allow_redirects=False)
                        
                        # Check if it's attempting to redirect to our payload
                        if response.status_code in (301, 302, 303, 307, 308):
                            location = response.headers.get('Location', '')
                            if any(p in location for p in redirect_payloads):
                                self.findings.append({
                                    "severity": "MEDIUM",
                                    "category": "Open Redirect",
                                    "endpoint": f"{path}?{param}={payload}",
                                    "location": location,
                                    "description": "Potential open redirect vulnerability",
                                    "recommendation": "Validate redirect URLs against a whitelist"
                                })
                    except Exception as e:
                        logger.error(f"Error testing open redirect on {path}: {str(e)}")
    
    def check_authentication_issues(self):
        """Check for authentication and session issues"""
        logger.info("Checking authentication and session management...")
        
        try:
            # Check for secure cookies
            response = self.session.get(self.base_url)
            for cookie in self.session.cookies:
                secure_issues = []
                
                if not cookie.secure and not self.base_url.startswith("http://localhost"):
                    secure_issues.append("missing Secure flag")
                if not cookie.has_nonstandard_attr("HttpOnly") and cookie.name in ('session', 'remember_token'):
                    secure_issues.append("missing HttpOnly flag")
                if cookie.has_nonstandard_attr("SameSite") and cookie.get_nonstandard_attr("SameSite").lower() == "none":
                    if not cookie.secure:
                        secure_issues.append("SameSite=None without Secure flag")
                
                if secure_issues:
                    self.findings.append({
                        "severity": "MEDIUM",
                        "category": "Session Security",
                        "cookie_name": cookie.name,
                        "issues": secure_issues,
                        "description": f"Cookie security issues: {', '.join(secure_issues)}",
                        "recommendation": "Set Secure, HttpOnly, and appropriate SameSite attributes on cookies"
                    })
        except Exception as e:
            logger.error(f"Error checking authentication: {str(e)}")
        
        # Check session expiration (if logged in)
        if self.csrf_token:
            try:
                # Make request with old CSRF token after 10 min (simulated)
                logger.info("Testing session expiration behavior...")
                self.findings.append({
                    "severity": "INFO",
                    "category": "Session Management",
                    "description": "Session expiration should be verified manually",
                    "recommendation": "Ensure sessions expire after inactivity and have a maximum lifetime"
                })
            except Exception as e:
                logger.error(f"Error checking session expiration: {str(e)}")
    
    def check_rate_limiting(self):
        """Check if rate limiting is implemented"""
        logger.info("Checking rate limiting...")
        
        # Endpoints to test for rate limiting
        rate_limit_endpoints = [
            "/api/auth/login",
            "/api/v1/people",
            "/api/v1/churches"
        ]
        
        for endpoint in rate_limit_endpoints:
            url = urljoin(self.base_url, endpoint)
            too_many_requests = False
            
            # Make multiple requests to trigger rate limiting
            for i in range(30):  # Try 30 times
                try:
                    response = self.session.get(url)
                    
                    # Check for rate limit headers
                    has_rate_limit_headers = any(h in response.headers for h in 
                                               ["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"])
                    
                    # Check if we got rate limited
                    if response.status_code == 429:
                        too_many_requests = True
                        logger.info(f"Rate limiting confirmed on {endpoint}")
                        break
                except Exception as e:
                    logger.error(f"Error checking rate limiting on {endpoint}: {str(e)}")
                    break
            
            if not too_many_requests and not has_rate_limit_headers:
                self.findings.append({
                    "severity": "MEDIUM",
                    "category": "Rate Limiting",
                    "endpoint": endpoint,
                    "description": "No rate limiting detected after multiple requests",
                    "recommendation": "Implement rate limiting using Flask-Limiter"
                })
    
    def check_sql_injection(self):
        """Check for potential SQL injection vulnerabilities"""
        logger.info("Checking SQL injection vulnerabilities...")
        
        # SQL injection test payloads
        sqli_payloads = [
            "' OR '1'='1", 
            "1; DROP TABLE users", 
            "1 UNION SELECT username, password FROM users"
        ]
        
        # Parameters to test
        params = {
            "/people": ["q", "id"],
            "/churches": ["q", "id"],
            "/tasks": ["q", "id"]
        }
        
        for path, parameters in params.items():
            url = urljoin(self.base_url, path)
            for param in parameters:
                for payload in sqli_payloads:
                    try:
                        params = {param: payload}
                        response = self.session.get(url, params=params)
                        
                        # Look for SQL error messages in the response
                        sql_errors = [
                            "SQL syntax", "ORA-", "MySQL", "SQLSTATE",
                            "SQLite", "on line", "postgresql"
                        ]
                        
                        for error in sql_errors:
                            if error.lower() in response.text.lower():
                                self.findings.append({
                                    "severity": "HIGH",
                                    "category": "SQL Injection",
                                    "endpoint": f"{path}?{param}={payload}",
                                    "description": f"Potential SQL injection: Error message exposed",
                                    "recommendation": "Use parameterized queries and SQLAlchemy ORM instead of raw SQL"
                                })
                                break
                    except Exception as e:
                        logger.error(f"Error testing SQL injection on {path}: {str(e)}")
    
    def _generate_report(self):
        """Generate a comprehensive security report"""
        logger.info("Generating security report...")
        
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
        
        # Generate summary
        summary = {
            "scan_time": logging.Formatter.formatTime(logging.Formatter(), logging.LogRecord("", 0, "", 0, None, None, None, None)),
            "target": self.base_url,
            "findings_count": len(self.findings),
            "severity_counts": severity_counts,
            "findings": self.findings
        }
        
        # Save report to file
        report_path = os.path.join(self.report_dir, "security_audit_report.json")
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Security report saved to {report_path}")
        
        # Print summary to console
        print("\n---- SECURITY AUDIT SUMMARY ----")
        print(f"Target: {self.base_url}")
        print(f"Total findings: {len(self.findings)}")
        for severity, count in severity_counts.items():
            print(f"{severity}: {count}")
        
        if self.findings:
            print("\nTop findings:")
            for finding in sorted(self.findings, key=lambda x: ["HIGH", "MEDIUM", "LOW", "INFO"].index(x.get("severity", "INFO")))[:5]:
                print(f"- [{finding['severity']}] {finding['category']}: {finding['description']}")
        
        print(f"\nDetailed report saved to {report_path}")

def main():
    parser = argparse.ArgumentParser(description="Security Audit for Mobilize CRM")
    parser.add_argument("--url", default="http://localhost:5000",
                        help="Base URL of the application (default: http://localhost:5000)")
    parser.add_argument("--username", default="admin@example.com",
                        help="Username for login")
    parser.add_argument("--password", default="password",
                        help="Password for login")
    parser.add_argument("--report-dir", default="results/security_audit",
                        help="Directory to save the security report (default: results/security_audit)")
    
    args = parser.parse_args()
    
    # Create auditor and run tests
    auditor = SecurityAuditor(args.url, args.report_dir)
    
    # Try to login
    if auditor.login(args.username, args.password):
        logger.info("Login successful, running security checks...")
        auditor.run_security_checks()
    else:
        logger.error("Login failed, running security checks with limited scope...")
        auditor.run_security_checks()

if __name__ == "__main__":
    main() 