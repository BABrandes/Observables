"""
Test to identify what's preventing garbage collection of observables.
"""

import unittest
import gc
import weakref
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
        # This should be None if garbage collection worked properly
        self.assertIsNone(obs_ref())

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
        # This should be None if garbage collection worked properly
        self.assertIsNone(obs_ref())


if __name__ == "__main__":
    unittest.main()
