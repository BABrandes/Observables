#!/usr/bin/env python3
"""
Simple test runner for observables that handles import issues
"""
import sys
import os
import unittest

# Add current directory to Python path to handle relative imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now import the test modules
from test_observables import *

if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestObservableSingleValue,
        TestObservableSet,
        TestObservableList,
        TestObservableSelectionOption,
        TestObservableIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(not result.wasSuccessful())
