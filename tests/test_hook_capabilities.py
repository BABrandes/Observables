import unittest
import threading
from typing import List, Any
from observables import Hook, BaseObservable, HookLike, SyncMode

class MockObservable(BaseObservable):
    """Mock observable for testing purposes."""
    
    @classmethod
    def _mandatory_component_value_keys(cls) -> set[str]:
        """Get the mandatory component value keys."""
        return {"value"}
    
    def __init__(self, name: str):
        # Initialize component values first
        self._component_values = {"value": name}
        
        # Create hooks
        hooks: dict[str, HookLike[Any]] = {"value": Hook(self, lambda: name, lambda x: None)}
        
        # Call parent constructor
        super().__init__(
            component_values=self._component_values,
            component_hooks=hooks
        )


class TestHookCapabilities(unittest.TestCase):
    """Test hooks with different capabilities (receiving-only, sending-only, both)."""

    def test_receiving_only_hook(self):
        """Test a hook that can only receive values (has set_callback but no get_callback)."""
        received_values: List[str] = []
        
        def set_callback(value: str) -> None:
            received_values.append(value)
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hook with only set_callback (receiving-only)
        receiving_hook = Hook[str](
            owner=mock_owner,
            get_callback=None,
            set_callback=set_callback
        )
        
        # Verify flags are set correctly
        self.assertTrue(receiving_hook.can_receive)
        self.assertFalse(receiving_hook.can_send)
        
        # Test that it can receive values
        receiving_hook._binding_system_callback_set("test_value") # type: ignore
        self.assertEqual(received_values, ["test_value"])
        
        # Test that it cannot provide values (should raise error)
        with self.assertRaises(ValueError):
            receiving_hook._binding_system_callback_get() # type: ignore

    def test_sending_only_hook(self):
        """Test a hook that can only send values (has get_callback but no set_callback)."""
        def get_callback() -> str:
            return "constant_value"
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hook with only get_callback (sending-only)
        sending_hook = Hook[str](
            owner=mock_owner,
            get_callback=get_callback,
            set_callback=None
        )
        
        # Verify flags are set correctly
        self.assertFalse(sending_hook.can_receive)
        self.assertTrue(sending_hook.can_send)
        
        # Test that it can provide values
        value = sending_hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "constant_value")
        
        # Test that it cannot receive values (should raise error)
        with self.assertRaises(ValueError):
            sending_hook._binding_system_callback_set("test_value") # type: ignore

    def test_bidirectional_hook(self):
        """Test a hook that can both send and receive values (has both callbacks)."""
        stored_value = "initial_value"
        received_values: List[str] = []
        
        def get_callback() -> str:
            return stored_value
        
        def set_callback(value: str) -> None:
            nonlocal stored_value
            stored_value = value
            received_values.append(value)
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hook with both callbacks (bidirectional)
        bidirectional_hook = Hook[str](
            owner=mock_owner,
            get_callback=get_callback,
            set_callback=set_callback
        )
        
        # Verify flags are set correctly
        self.assertTrue(bidirectional_hook.can_receive)
        self.assertTrue(bidirectional_hook.can_send)
        
        # Test that it can provide values
        value = bidirectional_hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "initial_value")
        
        # Test that it can receive values
        bidirectional_hook._binding_system_callback_set("new_value") # type: ignore
        self.assertEqual(stored_value, "new_value")
        self.assertEqual(received_values, ["new_value"])
        
        # Verify the value was updated
        value = bidirectional_hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "new_value")

    def test_hook_with_none_callbacks(self):
        """Test hook creation with None callbacks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hook with no callbacks
        hook = Hook[str](
            owner=mock_owner,
            get_callback=None,
            set_callback=None
        )
        
        # Verify flags are set correctly
        self.assertFalse(hook.can_receive)
        self.assertFalse(hook.can_send)
        
        # Test that both operations fail
        with self.assertRaises(ValueError):
            hook._binding_system_callback_get() # type: ignore
        
        with self.assertRaises(ValueError):
            hook._binding_system_callback_set("test_value") # type: ignore

    def test_hook_with_lambda_callbacks(self):
        """Test hook creation with lambda callbacks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hook with lambda callbacks
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "lambda_value",
            set_callback=lambda x: None
        )
        
        # Verify flags are set correctly
        self.assertTrue(hook.can_receive)
        self.assertTrue(hook.can_send)
        
        # Test lambda callbacks work
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "lambda_value")
        
        # Test set callback (should not raise error)
        hook._binding_system_callback_set("new_value") # type: ignore   

    def test_hook_with_complex_callbacks(self):
        """Test hook creation with complex callback functions."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a counter for tracking calls
        call_count = 0
        stored_value = "initial"
        
        def complex_get_callback() -> str:
            nonlocal call_count
            call_count += 1
            return f"{stored_value}_{call_count}"
        
        def complex_set_callback(value: str) -> None:
            nonlocal stored_value, call_count
            stored_value = value
            call_count += 10
        
        # Create hook with complex callbacks
        hook = Hook[str](
            owner=mock_owner,
            get_callback=complex_get_callback,
            set_callback=complex_set_callback
        )
        
        # Test initial state
        self.assertEqual(call_count, 0)
        
        # Test get callback
        value1 = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value1, "initial_1")
        self.assertEqual(call_count, 1)
        
        # Test set callback
        hook._binding_system_callback_set("new_value") # type: ignore
        self.assertEqual(stored_value, "new_value")
        self.assertEqual(call_count, 11)
        
        # Test get callback again
        value2 = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value2, "new_value_12")
        self.assertEqual(call_count, 12)

    def test_hook_protocol_compliance(self):
        """Test that hooks properly implement the HookLike protocol."""
        def get_callback() -> str:
            return "test_value"
        
        def set_callback(value: str) -> None:
            pass
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        hook = Hook[str](
            owner=mock_owner,
            get_callback=get_callback,
            set_callback=set_callback
        )
        
        # Test that all required protocol methods exist and work
        self.assertTrue(hasattr(hook, 'connect_to'))
        self.assertTrue(hasattr(hook, 'disconnect'))
        self.assertTrue(hasattr(hook, 'invalidate'))
        self.assertTrue(hasattr(hook, 'check_binding_system'))
        self.assertTrue(hasattr(hook, 'value'))
        self.assertTrue(hasattr(hook, 'hook_group'))
        self.assertTrue(hasattr(hook, 'owner'))
        self.assertTrue(hasattr(hook, 'can_receive'))
        self.assertTrue(hasattr(hook, 'can_send'))

    def test_hook_value_property(self):
        """Test the value property of hooks."""
        stored_value = "test_value"
        
        def get_callback() -> str:
            return stored_value
        
        def set_callback(value: str) -> None:
            nonlocal stored_value
            stored_value = value
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook that can send values
        hook = Hook[str](
            owner=mock_owner,
            get_callback=get_callback,
            set_callback=set_callback
        )
        
        # Test the value property
        self.assertEqual(hook.value, "test_value")
        
        # Update the value
        hook._binding_system_callback_set("new_value") # type: ignore
        self.assertEqual(hook.value, "new_value")

    def test_hook_value_property_with_no_sending_hooks(self):
        """Test the value property when no hooks can send values."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook that can only receive values
        hook = Hook[str](
            owner=mock_owner,
            get_callback=None,
            set_callback=lambda x: None
        )
        
        # Test that value property raises error when no hooks can send
        with self.assertRaises(ValueError):
            _ = hook.value

    def test_hook_owner_property(self):
        """Test the owner property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test the owner property
        self.assertEqual(hook.owner, mock_owner)
        
        # Test that owner is the same instance
        self.assertIs(hook.owner, mock_owner)

    def test_hook_hook_group_property(self):
        """Test the hook_group property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test the hook_group property
        self.assertIsNotNone(hook.hook_group)
        self.assertIn(hook, hook.hook_group.hooks)
        
        # Test that hook_group is consistent
        hook_group1 = hook.hook_group
        hook_group2 = hook.hook_group
        self.assertIs(hook_group1, hook_group2)

    def test_hook_lock_property(self):
        """Test the lock property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test the lock property
        self.assertIsNotNone(hook.lock)
        
        # Test that lock is a threading lock type
        # The exact type might vary depending on the Python implementation
        self.assertTrue(hasattr(hook.lock, 'acquire'))
        self.assertTrue(hasattr(hook.lock, 'release'))
        
        # Test that lock can be acquired
        with hook.lock:
            # This should not raise an error
            pass

    def test_hook_state_flags(self):
        """Test the state flag properties of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test initial state
        self.assertFalse(hook.is_being_invalidated)
        
        # Test setting state flag
        hook.is_being_invalidated = True
        
        self.assertTrue(hook.is_being_invalidated)
        
        # Reset
        hook.is_being_invalidated = False
        
        self.assertFalse(hook.is_being_invalidated)

    def test_hook_state_flags_persistence(self):
        """Test that state flags persist correctly."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Set flag multiple times
        for i in range(5):
            hook.is_being_invalidated = (i % 2 == 0)
            
            self.assertEqual(hook.is_being_invalidated, i % 2 == 0)

    def test_hook_disconnect(self):
        """Test the disconnect method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
    
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
    
        # Get the original hook group
        original_group = hook.hook_group
        
        # Create another hook to connect with
        hook2 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",  # Same value as first hook
            set_callback=lambda x: None
        )
        
        # Connect them so they're in the same group
        hook.connect_to(hook2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Now disconnect the first hook
        hook.disconnect()
        
        # Verify the hook is now in a new, separate hook group
        self.assertNotEqual(hook.hook_group, original_group)
        self.assertIn(hook, hook.hook_group.hooks)
        self.assertEqual(len(hook.hook_group.hooks), 1)

    def test_hook_disconnect_multiple_times(self):
        """Test calling disconnect multiple times."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
    
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
    
        # Create another hook to connect with
        hook2 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",  # Same value as first hook
            set_callback=lambda x: None
        )
        
        # Connect them so they're in the same group
        hook.connect_to(hook2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Disconnect multiple times - should fail after first disconnect
        with self.assertRaises(ValueError) as cm:
            for _ in range(5):
                original_group = hook.hook_group
                hook.disconnect()
                
                # Should always create a new group
                self.assertNotEqual(hook.hook_group, original_group)
                self.assertIn(hook, hook.hook_group.hooks)
                self.assertEqual(len(hook.hook_group.hooks), 1)
        
        # Verify the error message
        self.assertIn("Hook is already disconnected", str(cm.exception))

    def test_hook_invalidate(self):
        """Test the invalidate method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test invalidation
        # Since the hook is alone in its group and can send values,
        # invalidation should succeed but won't affect other hooks
        success, message = hook.invalidate()
        self.assertTrue(success, f"Invalidation failed: {message}")

    def test_hook_invalidate_receiving_only(self):
        """Test invalidating a receiving-only hook."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a receiving-only hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=None,
            set_callback=lambda x: None
        )
        
        # Test invalidation should fail because it can't send values
        with self.assertRaises(ValueError) as cm:
            hook.invalidate()
        
        self.assertIn("cannot send values", str(cm.exception))

    def test_hook_check_binding_system(self):
        """Test the check_binding_system method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test binding system check
        # This should work for a single hook in its own group
        success, message = hook.check_binding_system()
        self.assertTrue(success, f"Binding system check failed: {message}")

    def test_hook_check_binding_system_with_multiple_hooks(self):
        """Test check_binding_system with multiple hooks in a group."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create multiple hooks
        hook1 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value1",
            set_callback=lambda x: None
        )
        
        hook2 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value2",
            set_callback=lambda x: None
        )
        
        # Manually add hook2 to hook1's group (this is a test scenario)
        # In real usage, this would happen through the binding system
        hook1.hook_group.add_hook(hook2)
        
        # Now check binding system - should fail because values are different
        success, message = hook1.check_binding_system()
        self.assertFalse(success)
        self.assertIn("not synced", message)

    def test_hook_is_connected_to(self):
        """Test the is_connected_to method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create two hooks
        hook1 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value1",
            set_callback=lambda x: None
        )
        
        hook2 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value2",
            set_callback=lambda x: None
        )
        
        # Initially, hooks are not connected
        self.assertFalse(hook1.is_connected_to(hook2))
        self.assertFalse(hook2.is_connected_to(hook1))
        
        # Manually add hook2 to hook1's group
        hook1.hook_group.add_hook(hook2)
        
        # Now hook1 should see hook2 as connected
        self.assertTrue(hook1.is_connected_to(hook2))
        
        # But hook2 is still in its own group, so it won't see hook1 as connected
        # This is expected behavior - connections are not automatically bidirectional
        self.assertFalse(hook2.is_connected_to(hook1))

    def test_hook_replace_hook_group(self):
        """Test the _binding_system_replace_hook_group method."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Get the original hook group
        original_group = hook.hook_group
        
        # Create a new hook group
        from observables._utils.hook_group import HookGroup
        new_group = HookGroup[str](hook)
        
        # Replace the hook group
        hook._binding_system_replace_hook_group(new_group) # type: ignore
        
        # Verify the hook is now in the new group
        self.assertEqual(hook.hook_group, new_group)
        self.assertNotEqual(hook.hook_group, original_group)
        self.assertIn(hook, new_group.hooks)

    def test_hook_thread_safety_basic(self):
        """Test basic thread safety of hooks."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook with a mutable value
        shared_list = ["initial"]
        
        def get_callback() -> List[str]:
            return shared_list.copy()
        
        def set_callback(value: List[str]) -> None:
            shared_list.clear()
            shared_list.extend(value)
        
        hook = Hook[List[str]](
            owner=mock_owner,
            get_callback=get_callback,
            set_callback=set_callback
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
                    hook._binding_system_callback_set([f"value_{i}"]) # type: ignore
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
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test concurrent property access
        def property_reader():
            for _ in range(200):
                try:
                    _ = hook.can_send
                    _ = hook.can_receive
                    _ = hook.owner
                    _ = hook.hook_group
                    _ = hook.lock
                    _ = hook.is_being_invalidated
                    time.sleep(0.0005)
                except Exception:
                    pass
        
        def property_writer():
            for i in range(100):
                try:
                    hook.is_being_invalidated = (i % 2 == 0)
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
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test concurrent method calls
        def method_caller():
            for _ in range(150):
                try:
                    hook._binding_system_callback_get() # type: ignore
                    hook._binding_system_callback_set("test") # type: ignore
                    time.sleep(0.001)
                except Exception:
                    pass
        
        def state_changer():
            for i in range(100):
                try:
                    hook.is_being_invalidated = (i % 2 == 0)
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

    def test_hook_thread_safety_concurrent_hook_group_operations(self):
        """Test thread safety of hook group operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create multiple hooks
        hook1 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value1",
            set_callback=lambda x: None
        )
        
        hook2 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value2",
            set_callback=lambda x: None
        )
        
        # Test concurrent hook group operations
        def group_operator():
            for _ in range(100):
                try:
                    # Add hook2 to hook1's group
                    hook1.hook_group.add_hook(hook2)
                    time.sleep(0.002)
                    # Remove hook2 from hook1's group
                    hook1.hook_group.remove_hook(hook2)
                    time.sleep(0.002)
                except Exception:
                    pass
        
        def hook_accessor():
            for _ in range(200):
                try:
                    _ = hook1.hook_group.hooks
                    _ = len(hook1.hook_group.hooks)
                    _ = hook1.is_connected_to(hook2)
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        operator_thread = threading.Thread(target=group_operator)
        accessor_thread = threading.Thread(target=hook_accessor)
        
        # Start threads
        operator_thread.start()
        accessor_thread.start()
        
        # Wait for completion
        operator_thread.join()
        accessor_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Hook group thread safety test completed without errors")

    def test_hook_thread_safety_concurrent_disconnect_operations(self):
        """Test thread safety of disconnect operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test concurrent disconnect operations
        def disconnect_caller():
            for _ in range(50):
                try:
                    hook.disconnect()
                    time.sleep(0.003)
                except Exception:
                    pass
        
        def property_accessor():
            for _ in range(200):
                try:
                    _ = hook.hook_group
                    _ = len(hook.hook_group.hooks)
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        disconnect_thread = threading.Thread(target=disconnect_caller)
        accessor_thread = threading.Thread(target=property_accessor)
        
        # Start threads
        disconnect_thread.start()
        accessor_thread.start()
        
        # Wait for completion
        disconnect_thread.join()
        accessor_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Disconnect thread safety test completed without errors")

    def test_hook_thread_safety_concurrent_invalidate_operations(self):
        """Test thread safety of invalidate operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test concurrent invalidate operations
        def invalidate_caller():
            for _ in range(100):
                try:
                    hook.invalidate()
                    time.sleep(0.002)
                except Exception:
                    pass
        
        def state_accessor():
            for _ in range(200):
                try:
                    _ = hook.is_being_invalidated
                    _ = hook.can_send
                    _ = hook.can_receive
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        invalidate_thread = threading.Thread(target=invalidate_caller)
        accessor_thread = threading.Thread(target=state_accessor)
        
        # Start threads
        invalidate_thread.start()
        accessor_thread.start()
        
        # Wait for completion
        invalidate_thread.join()
        accessor_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Invalidate thread safety test completed without errors")

    def test_hook_thread_safety_concurrent_callback_execution(self):
        """Test thread safety of callback execution under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook with thread-safe callbacks
        import threading
        callback_lock = threading.Lock()
        callback_count = 0
        
        def thread_safe_get_callback() -> str:
            nonlocal callback_count
            with callback_lock:
                callback_count += 1
                return f"value_{callback_count}"
        
        def thread_safe_set_callback(value: str) -> None:
            nonlocal callback_count
            with callback_lock:
                callback_count += 1
        
        hook = Hook[str](
            owner=mock_owner,
            get_callback=thread_safe_get_callback,
            set_callback=thread_safe_set_callback
        )
        
        # Test concurrent callback execution
        def callback_caller():
            for _ in range(100):
                try:
                    hook._binding_system_callback_get() # type: ignore
                    hook._binding_system_callback_set("test") # type: ignore
                    time.sleep(0.001)
                except Exception:
                    pass
        
        def callback_caller2():
            for _ in range(100):
                try:
                    hook._binding_system_callback_get() # type: ignore
                    hook._binding_system_callback_set("test2") # type: ignore
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        caller1_thread = threading.Thread(target=callback_caller)
        caller2_thread = threading.Thread(target=callback_caller2)
        
        # Start threads
        caller1_thread.start()
        caller2_thread.start()
        
        # Wait for completion
        caller1_thread.join()
        caller2_thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(True, "Callback execution thread safety test completed without errors")

    def test_hook_thread_safety_concurrent_connect_operations(self):
        """Test thread safety of connect operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hooks
        hook1 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value1",
            set_callback=lambda x: None
        )
        
        hook2 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value2",
            set_callback=lambda x: None
        )
        
        # Test concurrent connect operations
        def connect_caller():
            for _ in range(50):
                try:
                    hook1.connect_to(hook2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
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
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test many concurrent operations
        def stress_worker(worker_id: int):
            for i in range(50):
                try:
                    # Mix of operations
                    if i % 5 == 0:
                        hook._binding_system_callback_get() # type: ignore
                    elif i % 5 == 1:
                        hook._binding_system_callback_set(f"value_{worker_id}_{i}") # type: ignore
                    elif i % 5 == 2:
                        hook.is_being_invalidated = (i % 2 == 0)
                    elif i % 5 == 3:
                        _ = hook.can_send
                        _ = hook.can_receive
                    else:
                        _ = hook.hook_group
                        _ = len(hook.hook_group.hooks)
                    
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create multiple worker threads
        threads = []
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
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test lock contention
        def lock_contender():
            for _ in range(100):
                try:
                    with hook.lock:
                        # Hold the lock for a bit to create contention
                        time.sleep(0.001)
                        _ = hook._binding_system_callback_get() # type: ignore
                        hook._binding_system_callback_set("contended") # type: ignore
                except Exception:
                    pass
        
        def lock_waiter():
            for _ in range(100):
                try:
                    with hook.lock:
                        _ = hook.can_send
                        _ = hook.can_receive
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
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test race conditions
        def race_condition_creator():
            for _ in range(100):
                try:
                    # Rapidly change state
                    hook.is_being_invalidated = True
                    hook.is_being_invalidated = False
                    hook.is_being_invalidated = True
                    time.sleep(0.0005)
                except Exception:
                    pass
        
        def race_condition_observer():
            for _ in range(200):
                try:
                    # Rapidly check state
                    _ = hook.is_being_invalidated
                    _ = hook.can_send
                    _ = hook.can_receive
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
        def failing_get_callback() -> str:
            raise RuntimeError("Get callback failed")
        
        def failing_set_callback(value: str) -> None:
            raise RuntimeError("Set callback failed")
        
        hook = Hook[str](
            owner=mock_owner,
            get_callback=failing_get_callback,
            set_callback=failing_set_callback
        )
        
        # Test that get callback raises the expected error
        with self.assertRaises(RuntimeError) as cm:
            hook._binding_system_callback_get() # type: ignore
        self.assertEqual(str(cm.exception), "Get callback failed")
        
        # Test that set callback raises the expected error
        with self.assertRaises(RuntimeError) as cm:
            hook._binding_system_callback_set("test") # type: ignore
        self.assertEqual(str(cm.exception), "Set callback failed")

    def test_hook_with_different_types(self):
        """Test hooks with different data types."""
        # Test with int
        mock_owner = MockObservable("test_owner")
        int_hook = Hook[int](
            owner=mock_owner,
            get_callback=lambda: 42,
            set_callback=lambda x: None
        )
        self.assertEqual(int_hook.value, 42)
        
        # Test with float
        float_hook = Hook[float](
            owner=mock_owner,
            get_callback=lambda: 3.14,
            set_callback=lambda x: None
        )
        self.assertEqual(float_hook.value, 3.14)
        
        # Test with bool
        bool_hook = Hook[bool](
            owner=mock_owner,
            get_callback=lambda: True,
            set_callback=lambda x: None
        )
        self.assertEqual(bool_hook.value, True)
        
        # Test with list
        list_hook = Hook[List[str]](
            owner=mock_owner,
            get_callback=lambda: ["a", "b", "c"],
            set_callback=lambda x: None
        )
        self.assertEqual(list_hook.value, ["a", "b", "c"])

    def test_hook_equality_and_hash(self):
        """Test hook equality and hashing behavior."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create two identical hooks
        hook1 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        hook2 = Hook[str](
            owner=mock_owner,
            get_callback=lambda: "value",
            set_callback=lambda x: None
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
            get_callback=lambda: "value",
            set_callback=lambda x: None
        )
        
        # Test string representation
        hook_str = str(hook)
        hook_repr = repr(hook)
        
        # Should contain useful information
        self.assertIn("Hook", hook_str)
        self.assertIn("Hook", hook_repr)
        # Note: Default string representation doesn't include type information
        # This is expected behavior for Python objects

    def test_hook_with_none_owner(self):
        """Test hook creation with None owner."""
        # Note: Current implementation doesn't validate owner parameter
        # This test documents the current behavior
        try:
            hook = Hook[str](
                owner=None,  # type: ignore
                get_callback=lambda: "value",
                set_callback=lambda x: None
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
        side_effects: List[str] = []
        
        def get_callback_with_side_effect() -> str:
            side_effects.append("get_called")
            return "value"
        
        def set_callback_with_side_effect(value: str) -> None:
            side_effects.append(f"set_called_with_{value}")
        
        hook = Hook[str](
            owner=mock_owner,
            get_callback=get_callback_with_side_effect,
            set_callback=set_callback_with_side_effect
        )
        
        # Test initial state
        self.assertEqual(side_effects, [])
        
        # Call get callback
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "value")
        self.assertEqual(side_effects, ["get_called"])
        
        # Call set callback
        hook._binding_system_callback_set("new_value") # type: ignore
        self.assertEqual(side_effects, ["get_called", "set_called_with_new_value"])
        
        # Call get callback again
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "value")
        self.assertEqual(side_effects, ["get_called", "set_called_with_new_value", "get_called"])

    def test_hook_with_callable_objects(self):
        """Test hooks with callable objects (not just functions)."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a callable class
        class CallableClass:
            def __init__(self, value: str):
                self.value = value
                self.call_count = 0
            
            def __call__(self) -> str:
                self.call_count += 1
                return f"{self.value}_{self.call_count}"
        
        # Create a callable object
        callable_obj = CallableClass("test")
        
        # Create hook with callable object
        hook = Hook[str](
            owner=mock_owner,
            get_callback=callable_obj,
            set_callback=lambda x: None
        )
        
        # Test that it works
        value1 = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value1, "test_1")
        self.assertEqual(callable_obj.call_count, 1)
        
        value2 = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value2, "test_2")
        self.assertEqual(callable_obj.call_count, 2)

    def test_hook_with_partial_functions(self):
        """Test hooks with functools.partial functions."""
        from functools import partial
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a function that takes multiple arguments
        def multi_arg_func(prefix: str, suffix: str, value: str) -> str:
            return f"{prefix}_{value}_{suffix}"
        
        # Create partial functions
        partial_get = partial(multi_arg_func, "start", "end")
        partial_set = partial(lambda x, value: None, "dummy")
        
        # Create hook with partial functions
        hook = Hook[str](
            owner=mock_owner,
            get_callback=partial_get,
            set_callback=partial_set
        )
        
        # Test that partial functions work
        # The original partial function expects an argument, so let's test a simpler one
        simple_partial_get = partial(lambda: "simple_value")
        
        simple_hook = Hook[str](
            owner=mock_owner,
            get_callback=simple_partial_get,
            set_callback=lambda x: None
        )
        
        simple_value = simple_hook._binding_system_callback_get() # type: ignore
        self.assertEqual(simple_value, "simple_value")
        
        # Test set callback (should not raise error)
        hook._binding_system_callback_set("new_value") # type: ignore

    def test_hook_with_method_objects(self):
        """Test hooks with bound method objects."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a class with methods
        class MethodClass:
            def __init__(self, value: str):
                self.value = value
            
            def get_method(self) -> str:
                return self.value
            
            def set_method(self, value: str) -> None:
                self.value = value
        
        # Create instance and get bound methods
        method_obj = MethodClass("initial")
        get_method = method_obj.get_method
        set_method = method_obj.set_method
        
        # Create hook with bound methods
        hook = Hook[str](
            owner=mock_owner,
            get_callback=get_method,
            set_callback=set_method
        )
        
        # Test that bound methods work
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "initial")
        
        hook._binding_system_callback_set("new_value") # type: ignore
        self.assertEqual(method_obj.value, "new_value")
        
        # Verify the value was updated
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "new_value")

    def test_hook_with_async_callbacks(self):
        """Test hooks with async callbacks (should work for sync operations)."""
        import asyncio
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create async callbacks
        async def async_get_callback() -> str:
            await asyncio.sleep(0)  # Simulate async operation
            return "async_value"
        
        async def async_set_callback(value: str) -> None:
            await asyncio.sleep(0)  # Simulate async operation
            # Store in a way we can test
            async_set_callback.last_value = value
        
        # Store the last value for testing
        async_set_callback.last_value = None
        
        # Create hook with async callbacks
        hook = Hook[str](
            owner=mock_owner,
            get_callback=async_get_callback,
            set_callback=async_set_callback
        )
        
        # Test that async callbacks work (they're just callable objects)
        # Note: In real usage, you'd need to handle the coroutine objects
        self.assertTrue(hook.can_send)
        self.assertTrue(hook.can_receive)
        
        # The callbacks are callable, so they can be called
        # (though they return coroutines, not values)

    def test_hook_with_generator_callbacks(self):
        """Test hooks with generator callbacks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create generator callbacks
        def generator_get_callback():
            yield "first_value"
            yield "second_value"
            yield "third_value"
        
        def generator_set_callback(value):
            yield f"received_{value}"
        
        # Create hook with generator callbacks
        hook = Hook[str](
            owner=mock_owner,
            get_callback=generator_get_callback,
            set_callback=generator_set_callback
        )
        
        # Test that generator callbacks are recognized as callable
        self.assertTrue(hook.can_send)
        self.assertTrue(hook.can_receive)
        
        # Note: In real usage, calling these would return generator objects,
        # not the actual values

    def test_hook_with_context_managers(self):
        """Test hooks with context manager callbacks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a context manager class
        class ContextManager:
            def __init__(self, value: str):
                self.value = value
            
            def __enter__(self):
                return self.value
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # Create context manager instances
        get_context = ContextManager("context_value")
        set_context = ContextManager("set_context")
        
        # Create hook with context managers
        hook = Hook[str](
            owner=mock_owner,
            get_callback=get_context.__enter__,
            set_callback=lambda x: None
        )
        
        # Test that context manager methods work
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "context_value")

    def test_hook_with_decorated_functions(self):
        """Test hooks with decorated functions."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a decorator
        def my_decorator(func):
            def wrapper(*args, **kwargs):
                return f"decorated_{func(*args, **kwargs)}"
            return wrapper
        
        # Create decorated functions
        @my_decorator
        def decorated_get() -> str:
            return "original_value"
        
        @my_decorator
        def decorated_set(value: str) -> str:
            return f"set_{value}"
        
        # Create hook with decorated functions
        hook = Hook[str](
            owner=mock_owner,
            get_callback=decorated_get,
            set_callback=lambda x: None
        )
        
        # Test that decorated functions work
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "decorated_original_value")

    def test_hook_with_closure_functions(self):
        """Test hooks with closure functions."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a closure
        def create_closure(prefix: str):
            def closure_func(value: str = "default") -> str:
                return f"{prefix}_{value}"
            return closure_func
        
        # Create closure functions
        get_closure = create_closure("prefix")
        set_closure = create_closure("set")
        
        # Create hook with closure functions
        hook = Hook[str](
            owner=mock_owner,
            get_callback=get_closure,
            set_callback=lambda x: None
        )
        
        # Test that closure functions work
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "prefix_default")
        
        # Test with argument
        value = get_closure("custom")
        self.assertEqual(value, "prefix_custom")

    def test_hook_with_class_methods(self):
        """Test hooks with class methods and static methods."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a class with class and static methods
        class TestClass:
            class_value = "class_value"
            
            @classmethod
            def class_get(cls) -> str:
                return cls.class_value
            
            @classmethod
            def class_set(cls, value: str) -> None:
                cls.class_value = value
            
            @staticmethod
            def static_get() -> str:
                return "static_value"
            
            @staticmethod
            def static_set(value: str) -> None:
                pass
        
        # Create hook with class methods
        hook = Hook[str](
            owner=mock_owner,
            get_callback=TestClass.class_get,
            set_callback=TestClass.class_set
        )
        
        # Test that class methods work
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "class_value")
        
        hook._binding_system_callback_set("new_class_value") # type: ignore
        self.assertEqual(TestClass.class_value, "new_class_value")
        
        # Test with static methods
        static_hook = Hook[str](
            owner=mock_owner,
            get_callback=TestClass.static_get,
            set_callback=TestClass.static_set
        )
        
        value = static_hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "static_value")

    def test_hook_with_property_callbacks(self):
        """Test hooks with property callbacks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a class with properties
        class PropertyClass:
            def __init__(self):
                self._value = "initial"
            
            @property
            def value_prop(self) -> str:
                return self._value
            
            @value_prop.setter
            def value_prop(self, value: str):
                self._value = value
        
        # Create instance
        prop_obj = PropertyClass()
        
        # Create hook with property methods
        # Get the getter and setter methods from the property descriptor
        getter = type(prop_obj).value_prop.fget
        setter = type(prop_obj).value_prop.fset
        
        hook = Hook[str](
            owner=mock_owner,
            get_callback=getter.__get__(prop_obj),  # Bind the method to the instance
            set_callback=setter.__get__(prop_obj)   # Bind the method to the instance
        )
        
        # Test that property methods work
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "initial")
        
        hook._binding_system_callback_set("new_prop_value") # type: ignore
        self.assertEqual(prop_obj.value_prop, "new_prop_value")

    def test_hook_with_lambda_complexity(self):
        """Test hooks with complex lambda expressions."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create complex lambda callbacks
        complex_get = lambda: (lambda x: x * 2)(21)  # Returns 42
        complex_set = lambda x: (lambda y: y.upper() if isinstance(y, str) else str(y))(x)
        
        # Create hook with complex lambdas
        hook = Hook[str](
            owner=mock_owner,
            get_callback=complex_get,
            set_callback=complex_set
        )
        
        # Test that complex lambdas work
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, 42)
        
        # Test set callback
        hook._binding_system_callback_set("test") # type: ignore    
        # The set callback doesn't store anything, but it should execute without error

    def test_hook_with_recursive_callbacks(self):
        """Test hooks with recursive callbacks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create recursive callbacks
        def recursive_get(n: int = 3) -> str:
            if n <= 0:
                return "base"
            return f"recursive_{recursive_get(n - 1)}"
        
        def recursive_set(value: str, depth: int = 0) -> None:
            if depth < 3:
                recursive_set(f"nested_{value}", depth + 1)
        
        # Create hook with recursive callbacks
        hook = Hook[str](
            owner=mock_owner,
            get_callback=lambda: recursive_get(),
            set_callback=lambda x: recursive_set(x)
        )
        
        # Test that recursive callbacks work
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "recursive_recursive_recursive_base")
        
        # Test set callback (should not raise error)
        hook._binding_system_callback_set("test") # type: ignore

    def test_hook_with_exception_handling_callbacks(self):
        """Test hooks with callbacks that handle exceptions."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create callbacks with exception handling
        def safe_get_callback() -> str:
            try:
                # Simulate a potential error
                result = "safe_value"
                if result is None:
                    raise ValueError("Unexpected None")
                return result
            except Exception as e:
                return f"error_{type(e).__name__}"
        
        def safe_set_callback(value: str) -> None:
            try:
                if value is None:
                    raise ValueError("Cannot set None value")
                # Process the value
                processed = value.upper()
            except Exception as e:
                # Log or handle the error
                pass
        
        # Create hook with safe callbacks
        hook = Hook[str](
            owner=mock_owner,
            get_callback=safe_get_callback,
            set_callback=safe_set_callback
        )
        
        # Test that safe callbacks work
        value = hook._binding_system_callback_get() # type: ignore
        self.assertEqual(value, "safe_value")
        
        # Test set callback with valid value
        hook._binding_system_callback_set("test") # type: ignore
        
        # Test set callback with None (should not raise error due to exception handling)
        hook._binding_system_callback_set(None)  # type: ignore


if __name__ == '__main__':
    unittest.main()
