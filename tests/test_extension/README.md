// tests/test_extension/README.md
# VS Code Extension Test Suite

This test suite provides comprehensive testing for the Python Code Autocompletion VS Code extension.

## Test Categories

### 1. Unit Tests
- **extension.test.ts**: Tests extension activation and basic functionality
- **completionProvider.test.ts**: Tests the completion provider logic
- **apiClient.test.ts**: Tests API communication
- **config.test.ts**: Tests configuration management

### 2. Integration Tests
- **integration.test.ts**: End-to-end workflow testing
- **performance.test.ts**: Performance and load testing

### 3. Test Setup
- **setup.ts**: Test workspace and file creation utilities
- **runTest.ts**: Test runner configuration
- **index.ts**: Mocha test suite setup

## Running Tests

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Run all tests
npm test

# Run tests in watch mode
npm run watch
```

## Test Structure

Each test file follows the pattern:
- `suiteSetup()`: Initialize test environment
- `setup()`: Per-test setup
- `test()`: Individual test cases
- `teardown()`: Per-test cleanup  
- `suiteTeardown()`: Clean up test environment

## Test Configuration

The tests use the following configuration:
- Mocha as test runner
- Sinon for mocking
- VS Code Test API for integration testing
- 10 second timeout for each test

## Mock Data

Tests use mock responses and test workspaces to avoid dependencies on external services during testing.

## Coverage

The test suite covers:
- ✅ Extension activation
- ✅ Completion provider functionality
- ✅ API client communication
- ✅ Configuration management
- ✅ Error handling
- ✅ Performance characteristics
- ✅ Multi-language support
- ✅ Integration workflows