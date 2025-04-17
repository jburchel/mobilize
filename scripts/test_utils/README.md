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

# Performance Testing Utilities

This directory contains scripts for performance testing and load testing the Mobilize CRM application.

## Load Testing Utilities

Scripts for performance and load testing:

- `load_test.py`: Uses Locust to simulate multiple users accessing the application
- `page_load_time.py`: Measures and reports page load times across different endpoints
- `large_dataset_test.py`: Tests application performance with large datasets

## Prerequisites

Install the required dependencies:

```bash
pip install locust matplotlib pandas tabulate tqdm
```

## Running Load Tests

### Locust Load Testing

1. Install Locust:
   ```bash
   pip install locust
   ```

2. Run the Locust server:
   ```bash
   locust -f scripts/test_utils/load_test.py
   ```

3. Open http://localhost:8089 in your browser to access the Locust web interface.

4. Set the number of users, spawn rate, and host (e.g., http://localhost:5000), then start the test.

### Page Load Time Testing

```bash
python scripts/test_utils/page_load_time.py --env local --username admin@example.com --password password --samples 5 --output results/page_load_times
```

Options:
- `--env`: Environment to test (local, dev, prod)
- `--username`: Username for login
- `--password`: Password for login
- `--samples`: Number of samples per endpoint
- `--output`: Output file path (without extension)

### Large Dataset Testing

Generate test data and run performance tests:

```bash
# Generate large dataset
python scripts/test_utils/large_dataset_test.py --generate --people 5000 --churches 500

# Run query performance tests
python scripts/test_utils/large_dataset_test.py --query-test

# Test caching effectiveness
python scripts/test_utils/large_dataset_test.py --cache-test
```

Options:
- `--generate`: Generate test data
- `--people`: Number of people to generate (default: 1000)
- `--churches`: Number of churches to generate (default: 200)
- `--query-test`: Run query performance tests
- `--cache-test`: Test caching effectiveness

## Interpreting Results

Each tool generates different types of results:

- **Locust**: Provides real-time metrics on the web interface, including request rates, response times, and failure rates.
- **Page Load Time**: Generates both console output and visual charts showing the load times for different endpoints.
- **Large Dataset Test**: Provides console output with query performance statistics.

## Best Practices

1. Run tests in a controlled environment that resembles production as closely as possible.
2. Start with a small number of virtual users and gradually increase the load.
3. Monitor server resources during tests to identify bottlenecks.
4. Compare results over time to track performance improvements or regressions. 