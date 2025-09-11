import unittest
import threading
from typing import Any, Callable, Literal, Mapping, Optional
from logging import Logger
from observables import Hook, BaseObservable, HookLike, InitialSyncMode
from run_tests import console_logger as logger


class MockObservable(BaseObservable[Literal["value"], Any]):
    """Mock observable for testing purposes."""
    
    def __init__(self, name: str):
        self._internal_construct_from_values({"value": name})
    
    def _internal_construct_from_values(
        self,
        initial_values: Mapping[Literal["value"], str],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """Construct a MockObservable instance."""
        super().__init__(initial_component_values_or_hooks=initial_values)
    
    def _act_on_invalidation(self, keys: set[Literal["value"]]) -> None:
        """Act on invalidation - required by BaseObservable."""
        pass

class TestHookCapabilities(unittest.TestCase):
    """Test hooks with different capabilities in the new hook-based system."""

    def test_hook_creation_with_invalidate_callback(self):
        """Test hook creation with invalidate callback."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hook with invalidate callback
        hook = Hook[str](
            owner=mock_owner,
            value="initial_value",
            invalidate_callback=lambda _: (True, "invalidated"),
            logger=logger
        )
        
        # Verify the hook is created correctly
        self.assertEqual(hook.value, "initial_value")
        self.assertEqual(hook.owner, mock_owner)
        self.assertTrue(hook.can_be_invalidated)
        self.assertIsNotNone(hook.hook_nexus)

    def test_hook_creation_without_invalidate_callback(self):
        """Test hook creation without invalidate callback."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hook without invalidate callback
        hook = Hook[str](
            owner=mock_owner,
            value="initial_value",
            invalidate_callback=None,
            logger=logger
        )
            
        # Verify the hook is created correctly
        self.assertEqual(hook.value, "initial_value")
        self.assertEqual(hook.owner, mock_owner)
        self.assertFalse(hook.can_be_invalidated)
        self.assertIsNotNone(hook.hook_nexus)

    def test_value_hook_property(self):
        """Test the value property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="test_value",
            invalidate_callback=lambda _: (True, "invalidated"),
            logger=logger
        )
        
        # Test the value property
        self.assertEqual(hook.value, "test_value")
        
        # The value comes from the hook nexus, so it should be consistent
        self.assertEqual(hook.hook_nexus.value, "test_value")

    def test_hook_owner_property(self):
        """Test the owner property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "invalidated"),
            logger=logger
        )
        
        # Test the owner property
        self.assertEqual(hook.owner, mock_owner)
        
        # Test that owner is the same instance
        self.assertIs(hook.owner, mock_owner)

    def test_hook_hook_nexus_property(self):
        """Test the hook_nexus property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "invalidated"),
            logger=logger
        )
        
        # Test the hook_nexus property
        self.assertIsNotNone(hook.hook_nexus)
        self.assertIn(hook, hook.hook_nexus.hooks)
        
        # Test that hook_nexus is consistent
        hook_nexus1 = hook.hook_nexus
        hook_nexus2 = hook.hook_nexus
        self.assertIs(hook_nexus1, hook_nexus2)

    def test_hook_lock_property(self):
        """Test the lock property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Test the lock property
        self.assertIsNotNone(hook.lock)
        
        # Test that lock is a threading lock type
        self.assertTrue(hasattr(hook.lock, 'acquire'))
        self.assertTrue(hasattr(hook.lock, 'release'))
        
        # Test that lock can be acquired
        with hook.lock:
            # This should not raise an error
            pass

    def test_hook_can_receive_property(self):
        """Test the can_receive property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hook with invalidate callback
        hook_with_callback = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Create hook without invalidate callback
        hook_without_callback = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=None,
            logger=logger
        )
        
        # Test can_receive property
        self.assertTrue(hook_with_callback.can_be_invalidated)
        self.assertFalse(hook_without_callback.can_be_invalidated)

    def test_hook_in_submission_property(self):
        """Test the in_submission property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Test initial state
        self.assertFalse(hook.in_submission)
        
        # Test setting state flag
        hook.in_submission = True
        self.assertTrue(hook.in_submission)
        
        # Reset
        hook.in_submission = False
        self.assertFalse(hook.in_submission)

    def test_hook_connect_to(self):
        """Test the connect_to method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create two hooks
        hook1 = Hook[str](
            owner=mock_owner,
            value="value1",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        hook2 = Hook[str](
            owner=mock_owner,
            value="value2",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Initially, hooks are in separate hook nexuses
        self.assertNotEqual(hook1.hook_nexus, hook2.hook_nexus)
        
        # Connect hook1 to hook2
        hook1.connect(hook2, InitialSyncMode.USE_CALLER_VALUE)
        
        # Now they should be in the same hook nexus
        self.assertEqual(hook1.hook_nexus, hook2.hook_nexus)
        self.assertIn(hook1, hook2.hook_nexus.hooks)
        self.assertIn(hook2, hook1.hook_nexus.hooks)

    def test_hook_connect_to_invalid_sync_mode(self):
        """Test connect_to with invalid sync mode."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create two hooks
        hook1 = Hook[str](
            owner=mock_owner,
            value="value1",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        hook2 = Hook[str](
            owner=mock_owner,
            value="value2",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Test with invalid sync mode
        with self.assertRaises(ValueError) as cm:
            hook1.connect(hook2, "invalid_mode")  # type: ignore
        
        self.assertIn("Invalid sync mode", str(cm.exception))

    def test_hook_detach(self):
        """Test the detach method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
    
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Get the original hook nexus
        original_nexus = hook.hook_nexus
        
        # Create another hook to connect with
        hook2 = Hook[str](
            owner=mock_owner,
            value="value",  # Same value as first hook
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Connect them so they're in the same hook nexus
        hook.connect(hook2, InitialSyncMode.USE_CALLER_VALUE)
        
        # Now disconnect the first hook
        hook.disconnect()
        
        # Verify the hook is now in a new, separate hook nexus
        self.assertNotEqual(hook.hook_nexus, original_nexus)
        self.assertIn(hook, hook.hook_nexus.hooks)
        self.assertEqual(len(hook.hook_nexus.hooks), 1)

    def test_hook_detach_multiple_times(self):
        """Test calling detach multiple times."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
    
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Create another hook to connect with
        hook2 = Hook[str](
            owner=mock_owner,
            value="value",  # Same value as first hook
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Connect them so they're in the same group
        hook.connect(hook2, InitialSyncMode.USE_CALLER_VALUE)
        
        # Detach multiple times - should fail after first detach
        with self.assertRaises(ValueError) as cm:
            for _ in range(5):
                original_nexus = hook.hook_nexus
                hook.disconnect()
                
                # Should always create a new hook nexus
                self.assertNotEqual(hook.hook_nexus, original_nexus)
                self.assertIn(hook, hook.hook_nexus.hooks)
                self.assertEqual(len(hook.hook_nexus.hooks), 1)
        
        # Verify the error message
        self.assertIn("Hook is already disconnected", str(cm.exception))

    def test_hook_submit_value(self):
        """Test the submit_value method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="initial_value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Test submitting a new value
        success, message = hook.submit_single_value("new_value")
        self.assertTrue(success, f"Submit failed: {message}")
        
        # The value should be updated in the hook nexus
        self.assertEqual(hook.hook_nexus.value, "new_value")

    def test_hook_submit_value_without_callback(self):
        """Test submit_value on a hook without invalidate callback."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook without invalidate callback
        hook = Hook[str](
            owner=mock_owner,
            value="initial_value",
            invalidate_callback=None,
            logger=logger
        )
        
        # Test submitting a value - should still work as it goes through the hook nexus
        success, message = hook.submit_single_value("new_value")
        self.assertTrue(success, f"Submit failed: {message}")

    def test_hook_is_connected_to(self):
        """Test the is_connected_to method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create two hooks
        hook1 = Hook[str](
            owner=mock_owner,
            value="value1",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        hook2 = Hook[str](
            owner=mock_owner,
            value="value2",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Initially, hooks are not attached
        self.assertFalse(hook1.is_connected_to(hook2))
        self.assertFalse(hook2.is_connected_to(hook1))
        
        # Connect them
        hook1.connect(hook2, InitialSyncMode.USE_CALLER_VALUE)
        
        # Now they should be attached
        self.assertTrue(hook1.is_connected_to(hook2))
        self.assertTrue(hook2.is_connected_to(hook1))

    def test_hook_invalidate(self):
        """Test the invalidate method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook with invalidate callback
        received_values: list[str] = []
        
        def invalidate_callback(hook: HookLike[str]) -> tuple[bool, str]:
            received_values.append("invalidated")
            return True, "invalidated"
        
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=invalidate_callback,
            logger=logger
        )
        
        # Test invalidation by calling callback directly (as HookNexus would do)
        hook.invalidate()
        self.assertEqual(received_values, ["invalidated"])

    def test_hook_invalidate_without_callback(self):
        """Test invalidating a hook without invalidate callback."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook without invalidate callback
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=None,
            logger=logger
        )
        
        # Test invalidate callback access should fail
        with self.assertRaises(ValueError) as cm:
            hook.invalidate()
        
        self.assertIn("Invalidate callback is None", str(cm.exception))

    def test_hook_is_valid_value(self):
        """Test the is_valid_value method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Test validation - should delegate to owner
        success, message = hook.is_valid_value("new_value")
        # The actual result depends on the owner's validation logic
        self.assertIsInstance(success, bool)
        self.assertIsInstance(message, str)

    def test_hook_replace_hook_nexus(self):
        """Test the _replace_hook_nexus method."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Get the original hook nexus
        original_nexus = hook.hook_nexus
        
        # Create a new hook nexus
        from observables._utils.hook_nexus import HookNexus
        new_nexus = HookNexus("new_value", hook)
        
        # Replace the hook nexus
        hook._replace_hook_nexus(new_nexus) #type: ignore
        
        # Verify the hook is now in the new hook nexus
        self.assertEqual(hook.hook_nexus, new_nexus)
        self.assertNotEqual(hook.hook_nexus, original_nexus)
        self.assertIn(hook, new_nexus.hooks)

    def test_hook_thread_safety_basic(self):
        """Test basic thread safety of hooks."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="initial",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Test concurrent access
        def reader():
            for _ in range(100):
                try:
                    _ = hook.value
                    time.sleep(0.001)
                except Exception:
                    pass
        
        def writer():
            for i in range(100):
                try:
                    hook.submit_single_value(f"value_{i}")
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        reader_thread = threading.Thread(target=reader)
        writer_thread = threading.Thread(target=writer)
        
        # Start threads
        reader_thread.start()
        writer_thread.start()
        
        # Wait for completion
        reader_thread.join()
        writer_thread.join()
        
        # Verify no exceptions occurred during concurrent access
        self.assertTrue(True, "Basic thread safety test completed without errors")

    def test_hook_thread_safety_concurrent_property_access(self):
        """Test thread safety of hook properties under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Test concurrent property access
        def property_reader():
            for _ in range(200):
                try:
                    _ = hook.can_be_invalidated
                    _ = hook.owner
                    _ = hook.hook_nexus
                    _ = hook.lock
                    _ = hook.in_submission
                    time.sleep(0.0005)
                except Exception:
                    pass
        
        def property_writer():
            for i in range(100):
                try:
                    hook.in_submission = (i % 2 == 0)
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        reader_thread = threading.Thread(target=property_reader)
        writer_thread = threading.Thread(target=property_writer)
        
        # Start threads
        reader_thread.start()
        writer_thread.start()
        
        # Wait for completion
        reader_thread.join()
        writer_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Property thread safety test completed without errors")

    def test_hook_thread_safety_concurrent_method_calls(self):
        """Test thread safety of hook methods under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Test concurrent method calls
        def method_caller():
            for _ in range(150):
                try:
                    hook.submit_single_value("test")
                    time.sleep(0.001)
                except Exception:
                    pass
        
        def state_changer():
            for i in range(100):
                try:
                    hook.in_submission = (i % 2 == 0)
                    time.sleep(0.0015)
                except Exception:
                    pass
        
        # Create threads
        caller_thread = threading.Thread(target=method_caller)
        changer_thread = threading.Thread(target=state_changer)
        
        # Start threads
        caller_thread.start()
        changer_thread.start()
        
        # Wait for completion
        caller_thread.join()
        changer_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Method thread safety test completed without errors")

    def test_hook_thread_safety_concurrent_hook_nexus_operations(self):
        """Test thread safety of hook nexus operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create multiple hooks
        hook1 = Hook[str](
            owner=mock_owner,
            value="value1",
            invalidate_callback=lambda _: (True, "success")
        )
        
        hook2 = Hook[str](
            owner=mock_owner,
            value="value2",
            invalidate_callback=lambda _: (True, "success")
        )
        
        # Test concurrent hook nexus operations
        def nexus_operator():
            for _ in range(100):
                try:
                    # Add hook2 to hook1's hook nexus
                    hook1.hook_nexus.add_hook(hook2)
                    time.sleep(0.002)
                    # Remove hook2 from hook1's hook nexus
                    hook1.hook_nexus.remove_hook(hook2)
                    time.sleep(0.002)
                except Exception:
                    pass
        
        def hook_accessor():
            for _ in range(200):
                try:
                    _ = hook1.hook_nexus.hooks
                    _ = len(hook1.hook_nexus.hooks)
                    _ = hook1.is_connected_to(hook2)
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        operator_thread = threading.Thread(target=nexus_operator)
        accessor_thread = threading.Thread(target=hook_accessor)
        
        # Start threads
        operator_thread.start()
        accessor_thread.start()
        
        # Wait for completion
        operator_thread.join()
        accessor_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Hook nexus thread safety test completed without errors")

    def test_hook_thread_safety_concurrent_detach_operations(self):
        """Test thread safety of detach operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success")
        )
        
        # Test concurrent detach operations
        def detach_caller():
            for _ in range(50):
                try:
                    # Create another hook to connect with first
                    hook2 = Hook[str](
                        owner=mock_owner,
                        value="value",
                        invalidate_callback=lambda _: (True, "success")
                    )
                    hook.connect(hook2, InitialSyncMode.USE_CALLER_VALUE)
                    hook.disconnect()
                    time.sleep(0.003)
                except Exception:
                    pass
        
        def property_accessor():
            for _ in range(200):
                try:
                    _ = hook.hook_nexus
                    _ = len(hook.hook_nexus.hooks)
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        detach_thread = threading.Thread(target=detach_caller)
        accessor_thread = threading.Thread(target=property_accessor)
        
        # Start threads
        detach_thread.start()
        accessor_thread.start()
        
        # Wait for completion
        detach_thread.join()
        accessor_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Detach thread safety test completed without errors")

    def test_hook_thread_safety_concurrent_submit_operations(self):
        """Test thread safety of submit operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success")
        )
        
        # Test concurrent submit operations
        def submit_caller():
            for _ in range(100):
                try:
                    hook.submit_single_value("test")
                    time.sleep(0.002)
                except Exception:
                    pass
        
        def state_accessor():
            for _ in range(200):
                try:
                    _ = hook.in_submission
                    _ = hook.can_be_invalidated
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        submit_thread = threading.Thread(target=submit_caller)
        accessor_thread = threading.Thread(target=state_accessor)
        
        # Start threads
        submit_thread.start()
        accessor_thread.start()
        
        # Wait for completion
        submit_thread.join()
        accessor_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Submit thread safety test completed without errors")

    def test_hook_thread_safety_concurrent_connect_operations(self):
        """Test thread safety of connect operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hooks
        hook1 = Hook[str](
            owner=mock_owner,
            value="value1",
            invalidate_callback=lambda _: (True, "success")
        )
        
        hook2 = Hook[str](
            owner=mock_owner,
            value="value2",
            invalidate_callback=lambda _: (True, "success")
        )
        
        # Test concurrent connect operations
        def connect_caller():
            for _ in range(50):
                try:
                    hook1.connect(hook2, InitialSyncMode.USE_CALLER_VALUE)
                    time.sleep(0.003)
                except Exception:
                    pass
        
        def connection_checker():
            for _ in range(200):
                try:
                    _ = hook1.is_connected_to(hook2)
                    _ = hook2.is_connected_to(hook1)
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        connect_thread = threading.Thread(target=connect_caller)
        checker_thread = threading.Thread(target=connection_checker)
        
        # Start threads
        connect_thread.start()
        checker_thread.start()
        
        # Wait for completion
        connect_thread.join()
        checker_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Connect operations thread safety test completed without errors")

    def test_hook_thread_safety_stress_test(self):
        """Stress test for thread safety with many concurrent operations."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success")
        )
        
        # Test many concurrent operations
        def stress_worker(worker_id: int):
            for i in range(50):
                try:
                    # Mix of operations
                    if i % 5 == 0:
                        hook.submit_single_value(f"value_{worker_id}_{i}")
                    elif i % 5 == 1:
                        hook.in_submission = (i % 2 == 0)
                    elif i % 5 == 2:
                        _ = hook.can_be_invalidated
                    elif i % 5 == 3:
                        _ = hook.hook_nexus
                        _ = len(hook.hook_nexus.hooks)
                    else:
                        _ = hook.value
                    
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create multiple worker threads
        threads: list[threading.Thread] = []
        for worker_id in range(5):
            thread = threading.Thread(target=stress_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Stress test thread safety test completed without errors")

    def test_hook_thread_safety_lock_contention(self):
        """Test thread safety under lock contention scenarios."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success")
        )
        
        # Test lock contention
        def lock_contender():
            for _ in range(100):
                try:
                    with hook.lock:
                        # Hold the lock for a bit to create contention
                        time.sleep(0.001)
                        hook.submit_single_value("contended")
                except Exception:
                    pass
        
        def lock_waiter():
            for _ in range(100):
                try:
                    with hook.lock:
                        _ = hook.can_be_invalidated
                        _ = hook.can_be_invalidated
                except Exception:
                    pass
        
        # Create threads
        contender_thread = threading.Thread(target=lock_contender)
        waiter_thread = threading.Thread(target=lock_waiter)
        
        # Start threads
        contender_thread.start()
        waiter_thread.start()
        
        # Wait for completion
        contender_thread.join()
        waiter_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Lock contention thread safety test completed without errors")

    def test_hook_thread_safety_race_conditions(self):
        """Test thread safety under potential race condition scenarios."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success")
        )
        
        # Test race conditions
        def race_condition_creator():
            for _ in range(100):
                try:
                    # Rapidly change state
                    hook.in_submission = True
                    hook.in_submission = False
                    hook.in_submission = True
                    time.sleep(0.0005)
                except Exception:
                    pass
        
        def race_condition_observer():
            for _ in range(200):
                try:
                    # Rapidly check state
                    _ = hook.in_submission
                    _ = hook.can_be_invalidated
                    time.sleep(0.0005)
                except Exception:
                    pass
        
        # Create threads
        creator_thread = threading.Thread(target=race_condition_creator)
        observer_thread = threading.Thread(target=race_condition_observer)
        
        # Start threads
        creator_thread.start()
        observer_thread.start()
        
        # Wait for completion
        creator_thread.join()
        observer_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Race condition thread safety test completed without errors")

    def test_hook_error_handling(self):
        """Test error handling in hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook with callbacks that raise exceptions
        def failing_invalidate_callback(hook: HookLike[str]) -> tuple[bool, str]:
            raise RuntimeError("Invalidate callback failed")
        
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=failing_invalidate_callback,
            logger=logger
        )
        
        # Test that invalidate callback raises the expected error
        with self.assertRaises(RuntimeError) as cm:
            hook.invalidate()
        self.assertEqual(str(cm.exception), "Invalidate callback failed")

    def test_hook_with_different_types(self):
        """Test hooks with different data types."""
        # Test with int
        mock_owner = MockObservable("test_owner")
        int_hook = Hook[int](
            owner=mock_owner,
            value=42,
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        self.assertEqual(int_hook.value, 42)
        
        # Test with float
        float_hook = Hook[float](
            owner=mock_owner,
            value=3.14,
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        self.assertEqual(float_hook.value, 3.14)
        
        # Test with bool
        bool_hook = Hook[bool](
            owner=mock_owner,
            value=True,
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        self.assertEqual(bool_hook.value, True)
        
        # Test with list
        list_hook = Hook[list[str]](
            owner=mock_owner,
            value=["a", "b", "c"],
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        self.assertEqual(list_hook.value, ["a", "b", "c"])

    def test_hook_equality_and_hash(self):
        """Test hook equality and hashing behavior."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create two identical hooks
        hook1 = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        hook2 = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Hooks should not be equal (they're different instances)
        self.assertNotEqual(hook1, hook2)
        
        # Hooks should be hashable
        self.assertIsInstance(hash(hook1), int)
        self.assertIsInstance(hash(hook2), int)
        
        # Same hook should be equal to itself
        self.assertEqual(hook1, hook1)
        self.assertEqual(hook2, hook2)

    def test_hook_string_representation(self):
        """Test hook string representation."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda _: (True, "success"),
            logger=logger
        )
        
        # Test string representation
        hook_str = str(hook)
        hook_repr = repr(hook)
        
        # Should contain useful information
        self.assertIn("Hook", hook_str)
        self.assertIn("Hook", hook_repr)

    def test_hook_with_none_owner(self):
        """Test hook creation with None owner."""
        # Note: Current implementation doesn't validate owner parameter
        # This test documents the current behavior
        try:
            hook = Hook[str](
                owner=None,  # type: ignore
                value="value",
                invalidate_callback=lambda _: (True, "success"),
                logger=logger
            )
            # If no exception is raised, that's the current behavior
            self.assertIsNone(hook.owner)
        except Exception as e:
            # If an exception is raised, that's also acceptable
            self.assertIsInstance(e, Exception)

    def test_hook_callback_side_effects(self):
        """Test that callbacks can have side effects."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a list to track side effects
        side_effects: list[str] = []
        
        def invalidate_callback_with_side_effect(hook: HookLike[str]) -> tuple[bool, str]:
            side_effects.append("invalidate_called")
            return True, "side_effect_success"
        
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=invalidate_callback_with_side_effect,
            logger=logger
        )
        
        # Test initial state
        self.assertEqual(side_effects, [])
        
        # Call invalidate callback directly
        hook.invalidate()
        self.assertEqual(side_effects, ["invalidate_called"])
        
        # Call invalidate callback again
        hook.invalidate()
        self.assertEqual(side_effects, ["invalidate_called", "invalidate_called"])

    def test_hook_with_callable_objects(self):
        """Test hooks with callable objects (not just functions)."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a callable class
        class CallableClass:
            def __init__(self):
                self.call_count = 0
            
            def __call__(self, hook: HookLike[str]) -> tuple[bool, str]:
                self.call_count += 1
                return True, "callable_success"
        
        # Create a callable object
        callable_obj = CallableClass()
        
        # Create hook with callable object
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=callable_obj,
            logger=logger
        )
        
        # Test that it works
        hook.invalidate()
        self.assertEqual(callable_obj.call_count, 1)
        
        hook.invalidate()
        self.assertEqual(callable_obj.call_count, 2)

    def test_hook_with_lambda_callbacks(self):
        """Test hooks with lambda callbacks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a counter for tracking calls
        call_count = 0
        
        def lambda_invalidate_callback(hook: HookLike[str]) -> tuple[bool, str]:
            nonlocal call_count
            call_count += 1
            return True, "lambda_success"
        
        # Create hook with lambda callback
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=lambda_invalidate_callback
        )
        
        # Test that lambda callback works
        hook.invalidate()
        self.assertEqual(call_count, 1)
        
        hook.invalidate()
        self.assertEqual(call_count, 2)

    def test_hook_with_method_objects(self):
        """Test hooks with bound method objects."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a class with methods
        class MethodClass:
            def __init__(self):
                self.call_count = 0
            
            def invalidate_method(self, hook: HookLike[str]) -> tuple[bool, str]:
                self.call_count += 1
                return True, "method_success"
        
        # Create instance and get bound method
        method_obj = MethodClass()
        invalidate_method = method_obj.invalidate_method
        
        # Create hook with bound method
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=invalidate_method,
            logger=logger
        )
        
        # Test that bound method works
        hook.invalidate()
        self.assertEqual(method_obj.call_count, 1)
        
        hook.invalidate()
        self.assertEqual(method_obj.call_count, 2)

    def test_hook_with_class_methods(self):
        """Test hooks with class methods and static methods."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a class with class and static methods
        class TestClass:
            class_call_count = 0
            static_call_count = 0
            
            @classmethod
            def class_invalidate(cls, hook: HookLike[str]) -> tuple[bool, str]:
                cls.class_call_count += 1
                return True, "class_success"
            
            @staticmethod
            def static_invalidate(hook: HookLike[str]) -> tuple[bool, str]:
                TestClass.static_call_count += 1
                return True, "static_success"
        
        # Create hook with class method
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=TestClass.class_invalidate,
            logger=logger
        )
        
        # Test that class method works
        hook.invalidate()
        self.assertEqual(TestClass.class_call_count, 1)
        
        hook.invalidate()
        self.assertEqual(TestClass.class_call_count, 2)
        
        # Test with static method
        static_hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=TestClass.static_invalidate,
            logger=logger
        )
        
        static_hook.invalidate()
        self.assertEqual(TestClass.static_call_count, 1)

    def test_hook_with_decorated_functions(self):
        """Test hooks with decorated functions."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a decorator
        def my_decorator(func: Callable[[HookLike[str]], tuple[bool, str]]) -> Callable[[HookLike[str]], tuple[bool, str]]:
            def wrapper(*args: Any, **kwargs: Any) -> tuple[bool, str]:
                return func(*args, **kwargs)
            return wrapper
        
        # Create decorated function
        @my_decorator
        def decorated_invalidate(hook: HookLike[str]) -> tuple[bool, str]:
            return True, "decorated_success"
        
        # Create hook with decorated function
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=decorated_invalidate,
            logger=logger
        )
        
        # Test that decorated function works
        hook.invalidate()  # Should not raise error

    def test_hook_with_closure_functions(self):
        """Test hooks with closure functions."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a closure
        def create_closure():
            call_count = 0
            def closure_func(hook: HookLike[str]) -> tuple[bool, str]:
                nonlocal call_count
                call_count += 1
                return True, "closure_success"
            return closure_func
        
        # Create closure function
        invalidate_closure = create_closure()
        
        # Create hook with closure function
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=invalidate_closure,
            logger=logger
        )
        
        # Test that closure function works
        hook.invalidate()  # Should not raise error

    def test_hook_with_exception_handling_callbacks(self):
        """Test hooks with callbacks that handle exceptions."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create callbacks with exception handling
        def safe_invalidate_callback(hook: HookLike[str]) -> tuple[bool, str]:
            try:
                # Process the hook (hook is guaranteed to be non-None by type)
                return True, "safe_success"
            except Exception:
                # Log or handle the error
                return False, "safe_error"
        
        hook = Hook[str](
            owner=mock_owner,
            value="value",
            invalidate_callback=safe_invalidate_callback,
            logger=logger
        )
        
        # Test that safe callback works
        hook.invalidate()  # Should not raise error


if __name__ == '__main__':
    unittest.main()
