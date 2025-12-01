"""
Test runner script
"""
import sys
import pytest

def run_all_tests():
    """Run all tests"""
    print("Running all tests...")
    return pytest.main([
        "tests/",
        "-v",
        "--tb=short"
    ])

def run_unit_tests():
    """Run only unit tests"""
    print("Running unit tests...")
    return pytest.main([
        "tests/",
        "-v",
        "-m", "unit",
        "--tb=short"
    ])

def run_integration_tests():
    """Run only integration tests"""
    print("Running integration tests...")
    return pytest.main([
        "tests/",
        "-v",
        "-m", "integration",
        "--tb=short"
    ])

def run_with_coverage():
    """Run tests with coverage report"""
    print("Running tests with coverage...")
    return pytest.main([
        "tests/",
        "-v",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term"
    ])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "unit":
            sys.exit(run_unit_tests())
        elif command == "integration":
            sys.exit(run_integration_tests())
        elif command == "coverage":
            sys.exit(run_with_coverage())
        else:
            print(f"Unknown command: {command}")
            print("Available commands: unit, integration, coverage")
            sys.exit(1)
    else:
        sys.exit(run_all_tests())
