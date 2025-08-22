#!/usr/bin/env python3
"""
Test runner for the observables library.
"""

import sys
import os
import unittest
import logging
from pathlib import Path

# Set up console logging for all tests
def setup_logging():
    """Set up console logging configuration."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Create a global logger instance that tests can import
console_logger = setup_logging()

def main():
    """Run the test suite."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Add project root to Python path so tests can import observables
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Change to project root
    os.chdir(project_root)
    
    print("Running observables test suite...")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
    print()
    
    try:
        # Discover and run all tests
        loader = unittest.TestLoader()
        start_dir: str = str(Path(__file__).parent)
        suite = loader.discover(start_dir, pattern='test_*.py')
        
        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print("\n✅ All tests passed!")
            return 0
        else:
            print(f"\n❌ Tests failed!")
            print(f"Failures: {len(result.failures)}")
            print(f"Errors: {len(result.errors)}")
            return 1
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
