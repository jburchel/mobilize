# Security Testing Suite for Mobilize CRM

This directory contains security testing scripts that help verify the application's security controls and identify potential vulnerabilities.

## Available Security Testing Tools

### 1. Security Audit Script

The `security_audit.py` script scans the application for common security vulnerabilities:

- CSRF protection
- XSS vulnerabilities
- HTTP security headers
- Open redirects
- Authentication issues
- Rate limiting
- SQL injection

```bash
python scripts/test_utils/security_audit.py --url http://localhost:5000 --username admin@example.com --password password
```

### 2. Access Control Test Script

The `access_control_test.py` script tests role-based access control and data isolation between offices:

- Tests access to endpoints based on user roles
- Verifies data isolation between users
- Tests office isolation for multi-tenant functionality

```bash
python scripts/test_utils/access_control_test.py --url http://localhost:5000 \
  --super-admin-email sadmin@example.com --super-admin-password password \
  --admin-email admin@example.com --admin-password password \
  --user-email user@example.com --user-password password
```

### 3. Data Protection Test Script

The `data_protection_test.py` script tests encryption, data masking, and sensitive data handling:

- HTTPS usage
- Password handling practices
- Data masking for sensitive fields
- Sensitive data exposure
- Data download protections
- File upload security

```bash
python scripts/test_utils/data_protection_test.py --url http://localhost:5000 --username admin@example.com --password password
```

## Running the Complete Security Test Suite

To run a complete security assessment, execute all three scripts:

```bash
mkdir -p results/security_audit results/access_control results/data_protection

# Run security audit
python scripts/test_utils/security_audit.py --url http://localhost:5000 --username admin@example.com --password password

# Run access control tests
python scripts/test_utils/access_control_test.py --url http://localhost:5000 \
  --super-admin-email sadmin@example.com --super-admin-password password \
  --admin-email admin@example.com --admin-password password \
  --user-email user@example.com --user-password password

# Run data protection tests
python scripts/test_utils/data_protection_test.py --url http://localhost:5000 --username admin@example.com --password password
```

## Test Results

All test scripts generate detailed reports in JSON format in the `results/` directory:

- `results/security_audit/security_audit_report.json`
- `results/access_control/access_control_report.json`
- `results/data_protection/data_protection_report.json`

A summary is also displayed in the console.

## Security Test Coverage

The security test suite covers the following security areas:

| Security Area | Tool | Description |
|---------------|------|-------------|
| Authentication | Security Audit | Tests login security, session management |
| Authorization | Access Control Test | Tests role-based access and data isolation |
| Input Validation | Security Audit | Tests for SQL injection and XSS |
| Output Encoding | Security Audit | Tests for XSS in responses |
| Transport Security | Data Protection | Tests HTTPS and security headers |
| Session Management | Security Audit | Tests for secure session handling |
| Error Handling | Security Audit | Tests for proper error responses |
| Data Protection | Data Protection | Tests for sensitive data exposure |
| Rate Limiting | Security Audit | Tests for API rate limiting |
| Security Headers | Security Audit | Tests for proper security headers |

## Requirements

The security testing scripts require the following Python packages:

```
requests
beautifulsoup4
tabulate
```

Install dependencies with:

```bash
pip install requests beautifulsoup4 tabulate
```

## Best Practices for Security Testing

1. Run tests in a controlled environment, not in production
2. Use test accounts, not real user accounts
3. Coordinate with the development team before running tests
4. Keep security reports confidential
5. Retest after fixing identified issues 