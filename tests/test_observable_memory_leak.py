"""
Test to identify what's preventing garbage collection of observables.
"""

import unittest
import gc
import weakref
import sys
from typing import Any

from observables._build_in_observables.observable_single_value import ObservableSingleValue


class TestObservableMemoryLeak(unittest.TestCase):
    """Test to identify observable memory leaks."""

    def test_observable_without_validator(self):
        """Test observable without validator."""
        # Create an observable without validator
        obs = ObservableSingleValue("test_value")
        obs_ref = weakref.ref(obs)
        
        # Verify it exists
        self.assertIsNotNone(obs_ref())
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Check if it was garbage collected
        if obs_ref() is not None:
            print(f"Observable still exists: {obs_ref()}")
            print(f"Reference count: {sys.getrefcount(obs_ref())}")
            
            # Try to find what's referencing it
            for obj in gc.get_objects():
                if hasattr(obj, '__dict__'):
                    for attr_name, attr_value in obj.__dict__.items():
                        if attr_value is obs_ref():
                            print(f"Found reference in {type(obj).__name__}.{attr_name}")
        
        # For now, let's just check if it exists
        self.assertIsNotNone(obs_ref())  # This will fail, showing the leak

    def test_observable_with_validator(self):
        """Test observable with validator."""
        def validator(value: Any) -> tuple[bool, str]:
            return True, "Valid"
        
        # Create an observable with validator
        obs = ObservableSingleValue("test_value", validator=validator)
        obs_ref = weakref.ref(obs)
        
        # Verify it exists
        self.assertIsNotNone(obs_ref())
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Check if it was garbage collected
        self.assertIsNotNone(obs_ref())  # This will fail, showing the leak


if __name__ == "__main__":
    unittest.main()
