#!/usr/bin/env python3
"""
Test runner for the observables library.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the test suite."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Change to project root
    import os
    os.chdir(project_root)
    
    print("Running observables test suite...")
    print(f"Project root: {project_root}")
    print()
    
    try:
        # Run pytest with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "--cov=observables",
            "--cov-report=term-missing",
            "--cov-report=html",
            "-v"
        ], capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with exit code {result.returncode}")
            sys.exit(result.returncode)
            
    except FileNotFoundError:
        print("❌ pytest not found. Please install it with: pip install pytest pytest-cov")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
