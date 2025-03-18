# Test Utilities and Support Scripts

This directory contains utility scripts and tools to support testing the Mobilize CRM application. Note that actual tests should be placed in the root-level `tests/` directory.

## Script Categories

### Load Testing Utilities
Scripts for performance and load testing:
- Load test data generators
- Performance monitoring tools
- Resource usage analyzers
- Stress test scenario generators

### Integration Test Support
Tools for supporting integration tests:
- Mock service providers
- Test environment configurators
- Integration test data generators
- Authentication test helpers

### Test Data Generation
Scripts for generating test data:
- Mock user data generators
- Sample contact creators
- Test communication generators
- Fake task data generators

### Test Automation Tools
Tools for automating test processes:
- Test environment setup scripts
- Test report generators
- CI/CD test helpers
- Test data cleanup utilities

## Adding New Scripts

When adding new test utility scripts:
1. Follow the naming convention: `generate_category_data.py` or `setup_category_environment.py`
2. Include proper documentation and usage examples
3. Add documentation in this README
4. Consider cleanup and resource management
5. Add error handling and logging 