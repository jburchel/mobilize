#!/bin/bash

# Install test dependencies
pip install -r tests/requirements-test.txt

# Run backend tests with coverage
pytest -xvs tests/ --cov=app --cov-report=term-missing --cov-report=html

# Run frontend tests separately (these may require browsers and can be slower)
echo "Running frontend tests..."
pytest -xvs tests/frontend/ --html=frontend-test-report.html

echo "Tests completed. Coverage report available in htmlcov/ directory"
echo "Frontend test report available in frontend-test-report.html" 