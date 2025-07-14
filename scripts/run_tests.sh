#!/bin/bash

# run_tests.sh - Comprehensive test runner for Python Code Autocompletion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="$PROJECT_ROOT/tests"
COVERAGE_DIR="$PROJECT_ROOT/coverage"
COVERAGE_MIN=80

# Default test settings
RUN_UNIT_TESTS=true
RUN_INTEGRATION_TESTS=true
RUN_API_TESTS=true
RUN_MODEL_TESTS=true
RUN_COVERAGE=true
RUN_LINTING=true
RUN_TYPE_CHECKING=true
VERBOSE=false
FAIL_FAST=false
PARALLEL=false
SPECIFIC_TEST=""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Test runner for Python Code Autocompletion project

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -f, --fail-fast         Stop on first test failure
    -p, --parallel          Run tests in parallel
    -c, --coverage          Run with coverage analysis (default: enabled)
    -l, --lint              Run linting checks (default: enabled)
    -t, --type-check        Run type checking (default: enabled)
    -s, --specific TEST     Run specific test file or directory
    
    --unit-only             Run only unit tests
    --integration-only      Run only integration tests
    --api-only              Run only API tests
    --model-only            Run only model tests
    --no-coverage           Skip coverage analysis
    --no-lint               Skip linting checks
    --no-type-check         Skip type checking
    
    --coverage-min N        Set minimum coverage percentage (default: 80)
    --clean                 Clean test artifacts before running

Examples:
    $0                      # Run all tests with default settings
    $0 --verbose --fail-fast    # Run with verbose output, stop on first failure
    $0 --unit-only --no-lint    # Run only unit tests without linting
    $0 -s tests/test_api        # Run specific test directory
    $0 --clean --coverage       # Clean artifacts and run with coverage
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -f|--fail-fast)
                FAIL_FAST=true
                shift
                ;;
            -p|--parallel)
                PARALLEL=true
                shift
                ;;
            -c|--coverage)
                RUN_COVERAGE=true
                shift
                ;;
            -l|--lint)
                RUN_LINTING=true
                shift
                ;;
            -t|--type-check)
                RUN_TYPE_CHECKING=true
                shift
                ;;
            -s|--specific)
                SPECIFIC_TEST="$2"
                shift 2
                ;;
            --unit-only)
                RUN_UNIT_TESTS=true
                RUN_INTEGRATION_TESTS=false
                RUN_API_TESTS=false
                RUN_MODEL_TESTS=false
                shift
                ;;
            --integration-only)
                RUN_UNIT_TESTS=false
                RUN_INTEGRATION_TESTS=true
                RUN_API_TESTS=false
                RUN_MODEL_TESTS=false
                shift
                ;;
            --api-only)
                RUN_UNIT_TESTS=false
                RUN_INTEGRATION_TESTS=false
                RUN_API_TESTS=true
                RUN_MODEL_TESTS=false
                shift
                ;;
            --model-only)
                RUN_UNIT_TESTS=false
                RUN_INTEGRATION_TESTS=false
                RUN_API_TESTS=false
                RUN_MODEL_TESTS=true
                shift
                ;;
            --no-coverage)
                RUN_COVERAGE=false
                shift
                ;;
            --no-lint)
                RUN_LINTING=false
                shift
                ;;
            --no-type-check)
                RUN_TYPE_CHECKING=false
                shift
                ;;
            --coverage-min)
                COVERAGE_MIN="$2"
                shift 2
                ;;
            --clean)
                CLEAN_ARTIFACTS=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Function to check if we're in a virtual environment
check_venv() {
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        print_warning "Not running in a virtual environment"
        print_warning "Consider activating your virtual environment first"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_status "Running in virtual environment: $VIRTUAL_ENV"
    fi
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking test dependencies..."
    
    local deps=("pytest" "pytest-cov" "pytest-asyncio" "black" "flake8" "mypy")
    local missing_deps=()
    
    for dep in "${deps[@]}"; do
        if ! python -c "import $dep" 2>/dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Installing missing dependencies..."
        pip install "${missing_deps[@]}"
    fi
}

# Function to clean test artifacts
clean_artifacts() {
    print_status "Cleaning test artifacts..."
    
    # Remove coverage files
    rm -rf "$COVERAGE_DIR"
    rm -f "$PROJECT_ROOT/.coverage"
    rm -f "$PROJECT_ROOT/coverage.xml"
    
    # Remove pytest cache
    rm -rf "$PROJECT_ROOT/.pytest_cache"
    find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -name "*.pyc" -type f -delete 2>/dev/null || true
    
    # Remove mypy cache
    rm -rf "$PROJECT_ROOT/.mypy_cache"
    
    # Remove test output files
    rm -rf "$PROJECT_ROOT/test-results"
    rm -f "$PROJECT_ROOT/junit.xml"
    
    print_status "Cleaned test artifacts"
}

# Function to setup test environment
setup_test_env() {
    print_status "Setting up test environment..."
    
    # Create necessary directories
    mkdir -p "$TEST_DIR"
    mkdir -p "$COVERAGE_DIR"
    mkdir -p "$PROJECT_ROOT/test-results"
    
    # Set environment variables for testing
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export TESTING=true
    export LOG_LEVEL=WARNING
    
    # Create test database if needed
    if [[ -f "$PROJECT_ROOT/backend-api/app/database.py" ]]; then
        export DATABASE_URL="sqlite:///./test.db"
    fi
}

# Function to run linting checks
run_linting() {
    if [[ "$RUN_LINTING" != "true" ]]; then
        return 0
    fi
    
    print_section "Running Code Linting"
    
    local lint_failed=false
    
    # Run Black formatting check
    print_status "Checking code formatting with Black..."
    if ! black --check --diff "$PROJECT_ROOT"; then
        print_error "Code formatting issues found. Run 'black .' to fix them."
        lint_failed=true
    fi
    
    # Run flake8 linting
    print_status "Running flake8 linting..."
    if ! flake8 "$PROJECT_ROOT" --max-line-length=88 --extend-ignore=E203,W503; then
        print_error "Linting issues found"
        lint_failed=true
    fi
    
    if [[ "$lint_failed" == "true" ]]; then
        if [[ "$FAIL_FAST" == "true" ]]; then
            print_error "Linting failed and --fail-fast is enabled"
            exit 1
        fi
        return 1
    fi
    
    print_status "Linting passed"
    return 0
}

# Function to run type checking
run_type_checking() {
    if [[ "$RUN_TYPE_CHECKING" != "true" ]]; then
        return 0
    fi
    
    print_section "Running Type Checking"
    
    print_status "Running mypy type checking..."
    if ! mypy "$PROJECT_ROOT" --ignore-missing-imports; then
        print_error "Type checking failed"
        if [[ "$FAIL_FAST" == "true" ]]; then
            exit 1
        fi
        return 1
    fi
    
    print_status "Type checking passed"
    return 0
}

# Function to build pytest command
build_pytest_cmd() {
    local cmd="pytest"
    
    # Add verbosity
    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd -v"
    fi
    
    # Add fail fast
    if [[ "$FAIL_FAST" == "true" ]]; then
        cmd="$cmd -x"
    fi
    
    # Add parallel execution
    if [[ "$PARALLEL" == "true" ]]; then
        cmd="$cmd -n auto"
    fi
    
    # Add coverage
    if [[ "$RUN_COVERAGE" == "true" ]]; then
        cmd="$cmd --cov=$PROJECT_ROOT --cov-report=html:$COVERAGE_DIR --cov-report=xml:$PROJECT_ROOT/coverage.xml --cov-report=term-missing"
    fi
    
    # Add JUnit XML output
    cmd="$cmd --junitxml=$PROJECT_ROOT/junit.xml"
    
    echo "$cmd"
}

# Function to run unit tests
run_unit_tests() {
    if [[ "$RUN_UNIT_TESTS" != "true" ]]; then
        return 0
    fi
    
    print_section "Running Unit Tests"
    
    local pytest_cmd=$(build_pytest_cmd)
    local test_path="$TEST_DIR"
    
    if [[ -n "$SPECIFIC_TEST" ]]; then
        test_path="$SPECIFIC_TEST"
    else
        test_path="$TEST_DIR -m 'not integration and not slow'"
    fi
    
    print_status "Running: $pytest_cmd $test_path"
    
    if ! $pytest_cmd $test_path; then
        print_error "Unit tests failed"
        if [[ "$FAIL_FAST" == "true" ]]; then
            exit 1
        fi
        return 1
    fi
    
    print_status "Unit tests passed"
    return 0
}

# Function to run integration tests
run_integration_tests() {
    if [[ "$RUN_INTEGRATION_TESTS" != "true" ]]; then
        return 0
    fi
    
    print_section "Running Integration Tests"
    
    local pytest_cmd=$(build_pytest_cmd)
    local test_path="$TEST_DIR -m integration"
    
    if [[ -n "$SPECIFIC_TEST" ]]; then
        test_path="$SPECIFIC_TEST"
    fi
    
    print_status "Running: $pytest_cmd $test_path"
    
    if ! $pytest_cmd $test_path; then
        print_error "Integration tests failed"
        if [[ "$FAIL_FAST" == "true" ]]; then
            exit 1
        fi
        return 1
    fi
    
    print_status "Integration tests passed"
    return 0
}

# Function to run API tests
run_api_tests() {
    if [[ "$RUN_API_TESTS" != "true" ]]; then
        return 0
    fi
    
    print_section "Running API Tests"
    
    local pytest_cmd=$(build_pytest_cmd)
    local test_path="$TEST_DIR/test_api"
    
    if [[ -n "$SPECIFIC_TEST" ]]; then
        test_path="$SPECIFIC_TEST"
    fi
    
    if [[ ! -d "$test_path" ]]; then
        print_warning "API test directory not found: $test_path"
        return 0
    fi
    
    print_status "Running: $pytest_cmd $test_path"
    
    if ! $pytest_cmd $test_path; then
        print_error "API tests failed"
        if [[ "$FAIL_FAST" == "true" ]]; then
            exit 1
        fi
        return 1
    fi
    
    print_status "API tests passed"
    return 0
}

# Function to run model tests
run_model_tests() {
    if [[ "$RUN_MODEL_TESTS" != "true" ]]; then
        return 0
    fi
    
    print_section "Running Model Tests"
    
    local pytest_cmd=$(build_pytest_cmd)
    local test_path="$TEST_DIR/test_model"
    
    if [[ -n "$SPECIFIC_TEST" ]]; then
        test_path="$SPECIFIC_TEST"
    fi
    
    if [[ ! -d "$test_path" ]]; then
        print_warning "Model test directory not found: $test_path"
        return 0
    fi
    
    print_status "Running: $pytest_cmd $test_path"
    
    if ! $pytest_cmd $test_path; then
        print_error "Model tests failed"
        if [[ "$FAIL_FAST" == "true" ]]; then
            exit 1
        fi
        return 1
    fi
    
    print_status "Model tests passed"
    return 0
}

# Function to check coverage
check_coverage() {
    if [[ "$RUN_COVERAGE" != "true" ]]; then
        return 0
    fi
    
    print_section "Coverage Analysis"
    
    if [[ -f "$PROJECT_ROOT/.coverage" ]]; then
        print_status "Generating coverage report..."
        
        # Get coverage percentage
        local coverage_pct=$(coverage report --format=total)
        
        print_status "Coverage: ${coverage_pct}%"
        
        if [[ $(echo "$coverage_pct < $COVERAGE_MIN" | bc -l) -eq 1 ]]; then
            print_error "Coverage ${coverage_pct}% is below minimum ${COVERAGE_MIN}%"
            if [[ "$FAIL_FAST" == "true" ]]; then
                exit 1
            fi
            return 1
        fi
        
        print_status "Coverage HTML report generated at: $COVERAGE_DIR/index.html"
        print_status "Coverage XML report generated at: $PROJECT_ROOT/coverage.xml"
    else
        print_warning "No coverage data found"
    fi
    
    return 0
}

# Function to run security checks
run_security_checks() {
    print_section "Running Security Checks"
    
    # Check if bandit is installed
    if ! command -v bandit &> /dev/null; then
        print_warning "Bandit not installed. Installing..."
        pip install bandit
    fi
    
    print_status "Running security checks with bandit..."
    if ! bandit -r "$PROJECT_ROOT" -f json -o "$PROJECT_ROOT/bandit-report.json"; then
        print_warning "Security issues found. Check bandit-report.json for details."
    else
        print_status "No security issues found"
    fi
}

# Function to generate test report
generate_test_report() {
    print_section "Test Report Summary"
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # Parse JUnit XML if available
    if [[ -f "$PROJECT_ROOT/junit.xml" ]]; then
        if command -v xmllint &> /dev/null; then
            total_tests=$(xmllint --xpath "//testsuite/@tests" "$PROJECT_ROOT/junit.xml" 2>/dev/null | grep -o '[0-9]*' || echo "0")
            failed_tests=$(xmllint --xpath "//testsuite/@failures" "$PROJECT_ROOT/junit.xml" 2>/dev/null | grep -o '[0-9]*' || echo "0")
            passed_tests=$((total_tests - failed_tests))
        fi
    fi
    
    echo "Test Results:"
    echo "  Total Tests: $total_tests"
    echo "  Passed: $passed_tests"
    echo "  Failed: $failed_tests"
    echo ""
    
    if [[ -f "$PROJECT_ROOT/.coverage" ]]; then
        echo "Coverage Report:"
        coverage report --show-missing
        echo ""
    fi
    
    echo "Generated Reports:"
    echo "  JUnit XML: $PROJECT_ROOT/junit.xml"
    if [[ -f "$PROJECT_ROOT/coverage.xml" ]]; then
        echo "  Coverage XML: $PROJECT_ROOT/coverage.xml"
    fi
    if [[ -d "$COVERAGE_DIR" ]]; then
        echo "  Coverage HTML: $COVERAGE_DIR/index.html"
    fi
    if [[ -f "$PROJECT_ROOT/bandit-report.json" ]]; then
        echo "  Security Report: $PROJECT_ROOT/bandit-report.json"
    fi
}

# Main function
main() {
    print_section "Python Code Autocompletion Test Runner"
    
    # Parse arguments
    parse_args "$@"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check virtual environment
    check_venv
    
    # Check dependencies
    check_dependencies
    
    # Clean artifacts if requested
    if [[ "$CLEAN_ARTIFACTS" == "true" ]]; then
        clean_artifacts
    fi
    
    # Setup test environment
    setup_test_env
    
    local overall_success=true
    
    # Run linting
    if ! run_linting; then
        overall_success=false
    fi
    
    # Run type checking
    if ! run_type_checking; then
        overall_success=false
    fi
    
    # Run tests
    if [[ -n "$SPECIFIC_TEST" ]]; then
        # Run specific test
        print_section "Running Specific Test: $SPECIFIC_TEST"
        local pytest_cmd=$(build_pytest_cmd)
        if ! $pytest_cmd "$SPECIFIC_TEST"; then
            overall_success=false
        fi
    else
        # Run all requested test suites
        if ! run_unit_tests; then
            overall_success=false
        fi
        
        if ! run_integration_tests; then
            overall_success=false
        fi
        
        if ! run_api_tests; then
            overall_success=false
        fi
        
        if ! run_model_tests; then
            overall_success=false
        fi
    fi
    
    # Check coverage
    if ! check_coverage; then
        overall_success=false
    fi
    
    # Run security checks
    run_security_checks
    
    # Generate test report
    generate_test_report
    
    # Final result
    if [[ "$overall_success" == "true" ]]; then
        print_section "All Tests Passed! "
        exit 0
    else
        print_section "Some Tests Failed! "
        exit 1
    fi
}

# Run main function with all arguments
main "$@"