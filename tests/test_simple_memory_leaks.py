"""
Simple memory leak test to isolate the issue.
"""

import unittest
import gc
import weakref

from observables._hooks.hook import Hook
from observables._utils.hook_nexus import HookNexus
from observables._hooks.floating_hook import FloatingHook


class TestSimpleMemoryLeaks(unittest.TestCase):
    """Simple test for memory leaks."""

    def test_simple_hook_gc(self):
        """Test simple hook garbage collection."""
        # Create a hook
        hook = Hook("test_value")
        hook_ref = weakref.ref(hook)
        
        # Verify the hook exists
        self.assertIsNotNone(hook_ref())
        
        # Delete the hook
        del hook
        
        # Force garbage collection
        gc.collect()
        
        # Verify the hook was garbage collected
        self.assertIsNone(hook_ref())

    def test_hook_with_callback_gc(self):
        """Test hook with callback garbage collection."""
        # Create a callback that might hold a reference
        def callback(value: str) -> tuple[bool, str]:
            return True, "Successfully validated"
        
        # Create a hook with callback
        hook = FloatingHook("test_value", validate_value_in_isolation_callback=callback)
        hook_ref = weakref.ref(hook)
        
        # Verify the hook exists
        self.assertIsNotNone(hook_ref())
        
        # Delete the hook
        del hook
        
        # Force garbage collection
        gc.collect()
        
        # Verify the hook was garbage collected
        self.assertIsNone(hook_ref())

    def test_nexus_gc(self):
        """Test nexus garbage collection."""
        # Create a nexus
        nexus = HookNexus("test_value")
        nexus_ref = weakref.ref(nexus)
        
        # Verify the nexus exists
        self.assertIsNotNone(nexus_ref())
        
        # Delete the nexus
        del nexus
        
        # Force garbage collection
        gc.collect()
        
        # Verify the nexus was garbage collected
        self.assertIsNone(nexus_ref())


if __name__ == "__main__":
    unittest.main()
