"""
Simplified memory leak test for observables.
"""

import unittest
import gc
import weakref
from typing import Any

from observables._build_in_observables.observable_single_value import ObservableSingleValue
from observables._other_observables.observable_selection_dict import ObservableSelectionDict


class TestObservableMemoryLeaks(unittest.TestCase):
    """Test for observable memory leaks."""

    def test_simple_observable_gc(self):
        """Test that simple observables can be garbage collected."""
        # Create an observable
        obs = ObservableSingleValue("test_value")
        obs_ref = weakref.ref(obs)
        
        # Verify it exists
        self.assertIsNotNone(obs_ref())
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Verify it was garbage collected
        self.assertIsNone(obs_ref())

    def test_complex_observable_gc(self):
        """Test that complex observables can be garbage collected."""
        # Create a complex observable
        obs = ObservableSelectionDict(
            dict_hook={"a": 1, "b": 2},
            key_hook="a",
            value_hook=None
        )
        obs_ref = weakref.ref(obs)
        
        # Verify it exists
        self.assertIsNotNone(obs_ref())
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Verify it was garbage collected
        self.assertIsNone(obs_ref())

    def test_observable_with_listeners_gc(self):
        """Test that observables with listeners can be garbage collected."""
        # Create an observable
        obs = ObservableSingleValue("test_value")
        obs_ref = weakref.ref(obs)
        
        # Add a listener
        def listener():
            pass
        
        obs.add_listeners(listener)
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Verify it was garbage collected
        self.assertIsNone(obs_ref())

    def test_observable_with_validator_gc(self):
        """Test that observables with validators can be garbage collected."""
        def validator(value: Any) -> tuple[bool, str]:
            return True, "Valid"
        
        # Create an observable with validator
        obs = ObservableSingleValue("test_value", validator=validator)
        obs_ref = weakref.ref(obs)
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Verify it was garbage collected
        self.assertIsNone(obs_ref())


if __name__ == "__main__":
    unittest.main()
