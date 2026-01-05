#!/bin/bash
# Quick reference script for running API edge case tests
# Usage: bash tests/RUN_EDGE_CASE_TESTS.sh [option]

set -e

echo "🧪 Dora API Edge Case Tests Runner"
echo "===================================="
echo ""

# Parse command line argument
TEST_TYPE="${1:-all}"

case "$TEST_TYPE" in
  "all")
    echo "Running ALL edge case tests (71 tests)..."
    pytest tests/test_api_edge_cases.py -v --tb=short
    ;;

  "security")
    echo "Running SECURITY tests..."
    pytest tests/test_api_edge_cases.py -k "injection or xss or sanitization or auth" -v
    ;;

  "validation")
    echo "Running VALIDATION tests..."
    pytest tests/test_api_edge_cases.py::TestRequestValidationEdgeCases -v
    ;;

  "rate-limit")
    echo "Running RATE LIMITING tests..."
    pytest tests/test_api_edge_cases.py::TestRateLimitingEdgeCases -v
    ;;

  "file-upload")
    echo "Running FILE UPLOAD tests..."
    pytest tests/test_api_edge_cases.py::TestFileUploadEdgeCases -v
    ;;

  "errors")
    echo "Running ERROR HANDLING tests..."
    pytest tests/test_api_edge_cases.py::TestErrorResponseEdgeCases -v
    ;;

  "performance")
    echo "Running PERFORMANCE tests..."
    pytest tests/test_api_edge_cases.py -k "concurrent or exhaustion or rate" -v
    ;;

  "headers")
    echo "Running HEADER tests..."
    pytest tests/test_api_edge_cases.py::TestHeaderEdgeCases -v
    ;;

  "quick")
    echo "Running QUICK smoke tests (first 10)..."
    pytest tests/test_api_edge_cases.py --maxfail=3 -x
    ;;

  "coverage")
    echo "Running tests with COVERAGE report..."
    pytest tests/test_api_edge_cases.py --cov=src/api --cov-report=html --cov-report=term-missing
    echo ""
    echo "📊 Coverage report generated at: htmlcov/index.html"
    ;;

  "parallel")
    echo "Running tests in PARALLEL..."
    pytest tests/test_api_edge_cases.py -n auto -v
    ;;

  "summary")
    echo "Test Summary:"
    echo "============="
    echo ""
    grep "def test_" tests/test_api_edge_cases.py | wc -l | xargs echo "Total Tests:"
    grep "^class Test" tests/test_api_edge_cases.py | wc -l | xargs echo "Test Classes:"
    wc -l tests/test_api_edge_cases.py | awk '{print "Lines of Code:", $1}'
    echo ""
    echo "Test Categories:"
    grep "^class Test" tests/test_api_edge_cases.py | sed 's/class Test/  - /' | sed 's/://'
    ;;

  "list")
    echo "Available test categories:"
    echo ""
    grep "^class Test" tests/test_api_edge_cases.py | sed 's/class Test/  /' | sed 's/://' | nl
    ;;

  "help"|"-h"|"--help")
    echo "Usage: bash tests/RUN_EDGE_CASE_TESTS.sh [option]"
    echo ""
    echo "Options:"
    echo "  all         - Run all 71 tests (default)"
    echo "  security    - Run security-focused tests (SQL injection, XSS, etc.)"
    echo "  validation  - Run request validation tests"
    echo "  rate-limit  - Run rate limiting tests"
    echo "  file-upload - Run file upload tests"
    echo "  errors      - Run error handling tests"
    echo "  performance - Run performance/concurrency tests"
    echo "  headers     - Run HTTP header tests"
    echo "  quick       - Run quick smoke tests"
    echo "  coverage    - Run with coverage report"
    echo "  parallel    - Run tests in parallel (requires pytest-xdist)"
    echo "  summary     - Show test statistics"
    echo "  list        - List all test categories"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  bash tests/RUN_EDGE_CASE_TESTS.sh all"
    echo "  bash tests/RUN_EDGE_CASE_TESTS.sh security"
    echo "  bash tests/RUN_EDGE_CASE_TESTS.sh coverage"
    ;;

  *)
    echo "❌ Unknown option: $TEST_TYPE"
    echo "Run with 'help' to see available options"
    exit 1
    ;;
esac

echo ""
echo "✅ Test execution complete!"
