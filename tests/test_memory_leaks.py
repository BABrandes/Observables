"""
Test for memory leaks in the hook-based architecture.

This test verifies that hooks and hook nexuses can be properly garbage collected
when they are no longer referenced.
"""

import unittest
import gc
import weakref

from observables._hooks.hook import Hook
from observables._utils.hook_nexus import HookNexus
from observables._build_in_observables.observable_single_value import ObservableSingleValue
from observables._other_observables.observable_selection_dict import ObservableSelectionDict

class TestMemoryLeaks(unittest.TestCase):
    """Test for memory leaks in the hook-based architecture."""

    def test_hook_garbage_collection(self):
        """Test that standalone hooks can be garbage collected."""
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

    def test_hook_nexus_garbage_collection(self):
        """Test that hook nexuses can be garbage collected when empty."""
        # Create a hook nexus
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

    def test_hook_with_nexus_garbage_collection(self):
        """Test that hooks and their nexuses can be garbage collected together."""
        # Create a hook (which creates its own nexus)
        hook = Hook("test_value")
        hook_ref = weakref.ref(hook)
        nexus_ref = weakref.ref(hook.hook_nexus)
        
        # Verify both exist
        self.assertIsNotNone(hook_ref())
        self.assertIsNotNone(nexus_ref())
        
        # Delete the hook
        del hook
        
        # Force garbage collection
        gc.collect()
        
        # Verify both were garbage collected
        self.assertIsNone(hook_ref())
        self.assertIsNone(nexus_ref())

    def test_connected_hooks_garbage_collection(self):
        """Test that connected hooks can be garbage collected when disconnected."""
        # Create two hooks
        hook1 = Hook("value1")
        hook2 = Hook("value2")
        
        hook1_ref = weakref.ref(hook1)
        hook2_ref = weakref.ref(hook2)
        
        # Connect them
        from observables._utils.initial_sync_mode import InitialSyncMode
        success, _ = hook1.connect_hook(hook2, "dummy_key", 
                                        InitialSyncMode.USE_CALLER_VALUE)
        self.assertTrue(success)
        
        # Verify they're connected (same nexus)
        self.assertEqual(hook1.hook_nexus, hook2.hook_nexus)
        
        # Disconnect hook1
        hook1.disconnect()
        
        # Verify they're now disconnected (different nexuses)
        self.assertNotEqual(hook1.hook_nexus, hook2.hook_nexus)
        
        # Delete hook1
        del hook1
        
        # Force garbage collection
        gc.collect()
        
        # Verify hook1 was garbage collected but hook2 still exists
        self.assertIsNone(hook1_ref())
        self.assertIsNotNone(hook2_ref())
        
        # Delete hook2
        del hook2
        
        # Force garbage collection
        gc.collect()
        
        # Verify hook2 was also garbage collected
        self.assertIsNone(hook2_ref())

    def test_observable_garbage_collection(self):
        """Test that observables and their hooks can be garbage collected."""
        # Create an observable
        obs = ObservableSingleValue("test_value")
        obs_ref = weakref.ref(obs)
        
        # Get references to its hooks
        hook_refs = []
        nexus_refs = []
        for hook_key in obs.get_hook_keys():
            hook = obs.get_hook(hook_key)
            hook_refs.append(weakref.ref(hook)) # type: ignore
            nexus_refs.append(weakref.ref(hook.hook_nexus)) # type: ignore
        
        # Verify everything exists
        self.assertIsNotNone(obs_ref())
        for hook_ref in hook_refs: # type: ignore
            self.assertIsNotNone(hook_ref()) # type: ignore
        for nexus_ref in nexus_refs: # type: ignore
            self.assertIsNotNone(nexus_ref()) # type: ignore
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Verify everything was garbage collected
        self.assertIsNone(obs_ref())
        for hook_ref in hook_refs: # type: ignore
            self.assertIsNone(hook_ref()) # type: ignore
        for nexus_ref in nexus_refs: # type: ignore
            self.assertIsNone(nexus_ref()) # type: ignore

    def test_complex_observable_garbage_collection(self):
        """Test that complex observables can be garbage collected."""
        # Create a complex observable
        obs = ObservableSelectionDict(
            dict_hook={"a": 1, "b": 2},
            key_hook="a",
            value_hook=None
        )
        obs_ref = weakref.ref(obs)
        
        # Get references to all hooks and nexuses
        hook_refs = []
        nexus_refs = []
        for hook_key in obs.get_hook_keys():
            hook = obs.get_hook(hook_key)
            hook_refs.append(weakref.ref(hook)) # type: ignore
            nexus_refs.append(weakref.ref(hook.hook_nexus)) # type: ignore
        
        # Verify everything exists
        self.assertIsNotNone(obs_ref())
        for hook_ref in hook_refs: # type: ignore
            self.assertIsNotNone(hook_ref()) # type: ignore
        for nexus_ref in nexus_refs: # type: ignore
            self.assertIsNotNone(nexus_ref()) # type: ignore
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Verify everything was garbage collected
        self.assertIsNone(obs_ref())
        for hook_ref in hook_refs: # type: ignore
            self.assertIsNone(hook_ref()) # type: ignore
        for nexus_ref in nexus_refs: # type: ignore
            self.assertIsNone(nexus_ref()) # type: ignore

    def test_nexus_manager_no_memory_leaks(self):
        """Test that NexusManager doesn't hold references to hooks."""
        # Create hooks
        hook1 = Hook("value1")
        hook2 = Hook("value2")
        
        hook1_ref = weakref.ref(hook1)
        hook2_ref = weakref.ref(hook2)
        
        # Connect them through NexusManager
        from observables._utils.initial_sync_mode import InitialSyncMode
        success, _ = hook1.connect_hook(hook2, "dummy_key",
                                        InitialSyncMode.USE_CALLER_VALUE)
        self.assertTrue(success)
        
        # Delete the hooks
        del hook1
        del hook2
        
        # Force garbage collection
        gc.collect()
        
        # Verify hooks were garbage collected despite NexusManager still existing
        self.assertIsNone(hook1_ref())
        self.assertIsNone(hook2_ref())

    def test_circular_reference_prevention(self):
        """Test that circular references don't prevent garbage collection."""
        # Create hooks that reference each other through nexuses
        hook1 = Hook("value1")
        hook2 = Hook("value2")
        
        # Connect them (creates circular references through nexus)
        from observables._utils.initial_sync_mode import InitialSyncMode
        success, _ = hook1.connect_hook(hook2, "dummy_key",
                                        InitialSyncMode.USE_CALLER_VALUE)
        self.assertTrue(success)
        
        # Create weak references
        hook1_ref = weakref.ref(hook1)
        hook2_ref = weakref.ref(hook2)
        nexus_ref = weakref.ref(hook1.hook_nexus)
        
        # Delete both hooks
        del hook1
        del hook2
        
        # Force garbage collection
        gc.collect()
        
        # Verify everything was garbage collected despite circular references
        self.assertIsNone(hook1_ref())
        self.assertIsNone(hook2_ref())
        self.assertIsNone(nexus_ref())

    def test_listener_memory_leaks(self):
        """Test that listeners don't prevent garbage collection."""
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
        
        # Verify the observable was garbage collected
        self.assertIsNone(obs_ref())

    def test_callback_memory_leaks(self):
        """Test that callbacks don't prevent garbage collection."""
        # Create an observable with callbacks
        
        obs = ObservableSingleValue("test_value")
        obs_ref = weakref.ref(obs)
        
        # Delete the observable
        del obs
        
        # Force garbage collection
        gc.collect()
        
        # Verify the observable was garbage collected
        self.assertIsNone(obs_ref())

if __name__ == "__main__":
    unittest.main()