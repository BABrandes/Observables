import unittest
from unittest.mock import Mock
from typing import Any
from observables._utils.hook import Hook, HookLike
from observables._utils.carries_hooks import CarriesHooks


class MockCarriesHooks(CarriesHooks[Any]):
    """Mock class that implements CarriesHooks interface for testing."""
    
    def __init__(self, name: str = "MockOwner"):
        self.name = name
        self._hooks: dict[str, HookLike[Any]] = {}
    
    def _is_valid_value(self, hook: HookLike[Any], value: Any) -> tuple[bool, str]:
        return True, "Valid"
    
    def __repr__(self) -> str:
        return f"MockCarriesHooks({self.name})"


class TestHookListeners(unittest.TestCase):
    """Test the listener functionality of the Hook class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.owner = MockCarriesHooks("TestOwner") # type: ignore
        # Create a mock invalidate callback for testing
        self.invalidate_callback = Mock()
        self.hook = Hook(self.owner, "initial_value", self.invalidate_callback)
    
    def test_hook_inherits_from_base_listening(self):
        """Test that Hook inherits from BaseListening."""
        from observables._utils.base_listening import BaseListening
        self.assertIsInstance(self.hook, BaseListening)
    
    def test_initial_listeners_state(self):
        """Test initial state of listeners."""
        self.assertEqual(len(self.hook.listeners), 0)
        self.assertFalse(self.hook.is_listening_to(lambda: None))
    
    def test_add_single_listener(self):
        """Test adding a single listener."""
        callback = Mock()
        self.hook.add_listeners(callback)
        
        self.assertEqual(len(self.hook.listeners), 1)
        self.assertTrue(self.hook.is_listening_to(callback))
        self.assertIn(callback, self.hook.listeners)
    
    def test_add_multiple_listeners(self):
        """Test adding multiple listeners at once."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        self.hook.add_listeners(callback1, callback2, callback3)
        
        self.assertEqual(len(self.hook.listeners), 3)
        self.assertTrue(self.hook.is_listening_to(callback1))
        self.assertTrue(self.hook.is_listening_to(callback2))
        self.assertTrue(self.hook.is_listening_to(callback3))
    
    def test_add_duplicate_listener_prevention(self):
        """Test that duplicate listeners are prevented."""
        callback = Mock()
        
        # Add the same callback multiple times
        self.hook.add_listeners(callback)
        self.hook.add_listeners(callback)
        self.hook.add_listeners(callback)
        
        # Should only be added once
        self.assertEqual(len(self.hook.listeners), 1)
        self.assertTrue(self.hook.is_listening_to(callback))
    
    def test_remove_single_listener(self):
        """Test removing a single listener."""
        callback = Mock()
        self.hook.add_listeners(callback)
        
        # Verify listener was added
        self.assertEqual(len(self.hook.listeners), 1)
        
        # Remove listener
        self.hook.remove_listeners(callback)
        
        # Verify listener was removed
        self.assertEqual(len(self.hook.listeners), 0)
        self.assertFalse(self.hook.is_listening_to(callback))
    
    def test_remove_multiple_listeners(self):
        """Test removing multiple listeners at once."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        self.hook.add_listeners(callback1, callback2, callback3)
        self.assertEqual(len(self.hook.listeners), 3)
        
        # Remove two listeners
        self.hook.remove_listeners(callback1, callback3)
        
        # Verify only callback2 remains
        self.assertEqual(len(self.hook.listeners), 1)
        self.assertFalse(self.hook.is_listening_to(callback1))
        self.assertTrue(self.hook.is_listening_to(callback2))
        self.assertFalse(self.hook.is_listening_to(callback3))
    
    def test_remove_nonexistent_listener_safe(self):
        """Test that removing non-existent listeners is safe."""
        callback = Mock()
        
        # Try to remove a listener that was never added
        self.hook.remove_listeners(callback)
        
        # Should not raise an error
        self.assertEqual(len(self.hook.listeners), 0)
    
    def test_remove_all_listeners(self):
        """Test removing all listeners at once."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        self.hook.add_listeners(callback1, callback2, callback3)
        self.assertEqual(len(self.hook.listeners), 3)
        
        # Remove all listeners
        removed = self.hook.remove_all_listeners()
        
        # Verify all listeners were removed
        self.assertEqual(len(self.hook.listeners), 0)
        self.assertEqual(len(removed), 3)
        self.assertIn(callback1, removed)
        self.assertIn(callback2, removed)
        self.assertIn(callback3, removed)
    
    def test_invalidate_callback_works(self):
        """Test that invalidate callback works when called directly."""
        callback1 = Mock()
        callback2 = Mock()
        
        self.hook.add_listeners(callback1, callback2)
        
        # Set up invalidate callback
        invalidate_callback = Mock()
        self.hook._invalidate_callback = invalidate_callback # type: ignore
        
        # Call invalidate callback directly (as HookNexus would do)
        self.hook.invalidation_callback(self.hook)
        
        # Verify invalidate callback was called
        invalidate_callback.assert_called_once_with(self.hook)
        
        # Note: Listeners are only notified when HookNexus processes the invalidation
        # This test verifies the callback works, not the listener notification
    
    def test_value_change_through_hook_nexus(self):
        """Test that value changes work through HookNexus with listener notification."""
        callback = Mock()
        self.hook.add_listeners(callback)
        
        # Change the value through the proper HookNexus process
        self.hook.value = "new_value"
        
        # Verify value was changed
        self.assertEqual(self.hook.value, "new_value")
        
        # With the new architecture, hooks always notify their own listeners
        # This ensures consistent behavior across all hook types
        callback.assert_called_once()
    
    def test_listeners_copy_is_returned(self):
        """Test that listeners property returns a copy, not the original set."""
        callback = Mock()
        self.hook.add_listeners(callback)
        
        listeners_copy = self.hook.listeners
        
        # Modify the copy
        listeners_copy.add(Mock())
        
        # Original hook listeners should be unchanged
        self.assertEqual(len(self.hook.listeners), 1)
        self.assertNotEqual(len(listeners_copy), len(self.hook.listeners))
    
    def test_listener_notification_order(self):
        """Test that listeners are notified when called."""
        notifications: list[str] = []
        
        def make_callback(name: str):
            def callback():
                notifications.append(name)
            return callback
        
        callback1 = make_callback("first")
        callback2 = make_callback("second")
        callback3 = make_callback("third")
        
        self.hook.add_listeners(callback1, callback2, callback3)
        
        # Trigger notification
        self.hook._notify_listeners() # type: ignore
        
        # Verify all listeners were called (order doesn't matter for sets)
        self.assertEqual(len(notifications), 3)
        self.assertIn("first", notifications)
        self.assertIn("second", notifications)
        self.assertIn("third", notifications)
    
    def test_listener_removal_during_notification(self):
        """Test that removing listeners during notification doesn't break the system."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        # callback2 will remove itself when called
        def self_removing_callback():
            self.hook.remove_listeners(callback2)
        
        callback2.side_effect = self_removing_callback
        
        self.hook.add_listeners(callback1, callback2, callback3)
        
        # Trigger notification - should not raise RuntimeError
        self.hook._notify_listeners() # type: ignore
        
        # Verify all callbacks were called
        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_called_once()
        
        # Verify callback2 was removed
        self.assertFalse(self.hook.is_listening_to(callback2))
        self.assertTrue(self.hook.is_listening_to(callback1))
        self.assertTrue(self.hook.is_listening_to(callback3))
    
    def test_multiple_hooks_independent_listeners(self):
        """Test that different hooks have independent listener sets."""
        owner1: CarriesHooks[str] = MockCarriesHooks("Owner1") # type: ignore
        owner2: CarriesHooks[str] = MockCarriesHooks("Owner2") # type: ignore
        
        hook1 = Hook(owner1, "value1")
        hook2 = Hook(owner2, "value2")
        
        callback1 = Mock()
        callback2 = Mock()
        
        hook1.add_listeners(callback1)
        hook2.add_listeners(callback2)
        
        # Verify each hook has its own listeners
        self.assertEqual(len(hook1.listeners), 1)
        self.assertEqual(len(hook2.listeners), 1)
        self.assertTrue(hook1.is_listening_to(callback1))
        self.assertTrue(hook2.is_listening_to(callback2))
        self.assertFalse(hook1.is_listening_to(callback2))
        self.assertFalse(hook2.is_listening_to(callback1))
        
        # Trigger notification on hook1
        hook1._notify_listeners() # type: ignore
        
        # Only callback1 should be called
        callback1.assert_called_once()
        callback2.assert_not_called()
    
    def test_hook_with_invalidate_callback(self):
        """Test hook behavior with invalidate callback."""
        invalidate_callback = Mock()
        hook = Hook(self.owner, "test_value", invalidate_callback)
        
        callback = Mock()
        hook.add_listeners(callback)
        
        # Call invalidate callback directly (as HookNexus would do)
        hook.invalidation_callback(hook)
        
        # Verify invalidate callback was called
        invalidate_callback.assert_called_once_with(hook)
        
        # Note: Listeners are only notified when HookNexus processes the invalidation
        # This test verifies the callback works, not the listener notification
    
    def test_hook_without_invalidate_callback(self):
        """Test that calling invalidate without callback raises error."""
        hook = Hook(self.owner, "test_value")  # No invalidate callback
        
        # Should raise ValueError when invalidate callback is accessed
        with self.assertRaises(ValueError):
            _ = hook.invalidation_callback


if __name__ == "__main__":
    unittest.main()
