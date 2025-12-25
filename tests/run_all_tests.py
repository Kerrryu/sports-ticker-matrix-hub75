#!/usr/bin/env python3
"""
Test Runner for Sports Ticker

Runs all test suites and reports results.

Usage:
    python tests/run_all_tests.py
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))


def run_all_tests():
    """Run all test modules."""
    print("=" * 60)
    print("Sports Ticker - Test Suite")
    print("=" * 60)

    results = {}

    # Import and run each test module
    test_modules = [
        ('test_display', 'Display Module'),
        ('test_api', 'API Module'),
        ('test_config', 'Config Module'),
        ('test_ota', 'OTA Module'),
    ]

    for module_name, description in test_modules:
        print(f"\n{'#' * 60}")
        print(f"# {description}")
        print(f"{'#' * 60}")

        try:
            # Import the test module
            module = __import__(module_name)

            # Run tests
            if hasattr(module, 'run_tests'):
                success = module.run_tests()
                results[module_name] = 'PASS' if success else 'FAIL'
            else:
                print(f"  No run_tests() function in {module_name}")
                results[module_name] = 'SKIP'

        except Exception as e:
            print(f"  Error running {module_name}: {e}")
            results[module_name] = 'ERROR'

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r == 'PASS')
    failed = sum(1 for r in results.values() if r == 'FAIL')
    errors = sum(1 for r in results.values() if r == 'ERROR')
    skipped = sum(1 for r in results.values() if r == 'SKIP')

    for module, result in results.items():
        status = {
            'PASS': '\033[92mPASS\033[0m',
            'FAIL': '\033[91mFAIL\033[0m',
            'ERROR': '\033[93mERROR\033[0m',
            'SKIP': '\033[94mSKIP\033[0m',
        }.get(result, result)
        print(f"  {module}: {status}")

    print()
    print(f"Results: {passed} passed, {failed} failed, {errors} errors, {skipped} skipped")
    print("=" * 60)

    return failed == 0 and errors == 0


if __name__ == '__main__':
    # Change to tests directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    success = run_all_tests()
    sys.exit(0 if success else 1)
