# SEC Data Application: Comprehensive Testing Guide

## Overview

This document provides a comprehensive guide to the testing infrastructure for the SEC Data Application. Our testing suite is designed to ensure data accuracy, performance, and reliability across various components of the application.

## Testing Architecture

The testing infrastructure is built with the following key components:
- `pytest` as the primary testing framework
- Comprehensive test types: Unit, Integration, Performance
- Centralized logging
- Coverage reporting
- API-based test execution

## Test Types

### 1. Unit Tests
Location: `tests/unit/`
- Focus on testing individual functions and methods
- Verify core logic and edge cases
- Quick to execute and provide immediate feedback

#### Example:
```bash
# Run all unit tests
python -m pytest tests/unit/

# Run specific unit test file
python -m pytest tests/unit/test_sec_filings.py
```

### 2. Integration Tests
Location: `tests/integration/`
- Test interactions between different modules
- Verify data flow and processing pipelines
- Ensure components work together correctly

#### Example:
```bash
# Run all integration tests
python -m pytest tests/integration/

# Run specific integration test file
python -m pytest tests/integration/test_data_pipeline.py
```

### 3. Performance Tests
Location: `tests/performance/`
- Measure execution time and memory usage
- Test scalability of data retrieval and processing
- Identify potential bottlenecks

#### Example:
```bash
# Run all performance tests
python -m pytest tests/performance/

# Run specific performance test file
python -m pytest tests/performance/test_retrieval_performance.py
```

## CLI Test Runner

We provide a flexible CLI for running tests with various options:

```bash
# Basic usage
python -m utils.test_utils test

# Specify test type
python -m utils.test_utils test --type unit
python -m utils.test_utils test --type integration
python -m utils.test_utils test --type performance
python -m utils.test_utils test --type all

# Additional options
# Verbose output
python -m utils.test_utils test --verbose

# Generate coverage report
python -m utils.test_utils test --coverage

# Specify custom test data path
python -m utils.test_utils test --data-path /path/to/test/data

# Choose coverage report format
python -m utils.test_utils test --coverage --output-format html
```

## Test API Endpoints

We provide a Flask-based API for programmatic test execution:

### Endpoints

1. **Run Tests**
   - **URL**: `/api/tests/run`
   - **Method**: POST
   - **Parameters**:
     ```json
     {
       "type": "all|unit|integration|performance",
       "verbose": false,
       "data_path": "optional/path/to/test/data",
       "coverage": false,
       "output_format": "html|xml|json"
     }
     ```

2. **Get Test Results**
   - **URL**: `/api/tests/results/<session_id>`
   - **Method**: GET
   - **Returns**: JSON with test results

3. **Download Coverage Report**
   - **URL**: `/api/tests/coverage/<session_id>`
   - **Method**: GET
   - **Returns**: Downloadable ZIP with coverage report

### Example API Usage with cURL

```bash
# Run tests
curl -X POST http://localhost:5001/api/tests/run \
     -H "Content-Type: application/json" \
     -d '{"type": "integration", "coverage": true}'

# Get test results
curl http://localhost:5001/api/tests/results/SESSION_ID

# Download coverage report
curl -O http://localhost:5001/api/tests/coverage/SESSION_ID
```

## Logging

- Centralized logging with `structlog`
- Log files stored in `logs/` directory
- Logs include:
  - Timestamp
  - Log level
  - Module name
  - Function name
  - Line number
  - Detailed message

### Log Locations
- Session-based log files: `logs/session_<UUID>.log`
- Rotated log files to prevent excessive disk usage

## Best Practices

1. Write tests for new features before implementation
2. Aim for high code coverage
3. Keep tests focused and independent
4. Use mock objects to simulate external dependencies
5. Include both positive and negative test scenarios

## Troubleshooting

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check `logs/` for detailed error information
- Verify Python and dependency versions
- Run tests in a virtual environment

## Contributing

1. Add new tests in appropriate directories
2. Follow existing test structure
3. Add docstrings and comments
4. Run full test suite before submitting changes

## Performance Optimization Tips

- Use `@pytest.mark.skip` for long-running tests
- Utilize mocking to reduce external API calls
- Profile and optimize test performance

## Security

- Test data and logs are stored with restricted permissions
- Sensitive information is not logged
- Coverage reports are generated locally

## Contact

For issues or questions about the testing infrastructure, contact the development team.
