"""Test that reentrancy protection works correctly."""

from observables import FloatingHook

import pytest

class TestReentrancyProtection:
    """Test reentrancy protection for submit_values."""

    def test_overlapping_recursive_submit_raises_error(self):
        """Test that recursive submit to the SAME hook raises RuntimeError."""
        
        hook = FloatingHook[int](42)
        
        # Create a listener that tries to modify the same hook (BAD!)
        def bad_listener():
            # This listener tries to submit to the same hook being updated
            # This should be caught and raise RuntimeError
            hook.submit_value(200)
        
        hook.add_listeners(bad_listener)
        
        # Try to update hook - this should trigger the listener which tries to submit to the same hook
        with pytest.raises(RuntimeError, match="overlapping hook nexuses"):
            hook.submit_value(99)

    def test_independent_recursive_submit_allowed(self):
        """Test that recursive submit to DIFFERENT hooks is allowed."""
        
        hook1 = FloatingHook[int](1)
        hook2 = FloatingHook[int](2)
        
        # Create a listener that updates a different, independent hook (OK!)
        def listener_updates_independent_hook():
            # This is fine - hook2 is independent from hook1
            hook2.submit_value(99)
        
        hook1.add_listeners(listener_updates_independent_hook)
        
        # Update hook1 - this should trigger the listener which updates hook2
        # This should NOT raise an error because the hooks are independent
        result = hook1.submit_value(42)
        
        assert result == (True, 'Values are submitted')
        assert hook1.value == 42
        assert hook2.value == 99  # Updated by the listener

    def test_chained_independent_submissions(self):
        """Test that a chain of independent submissions works."""
        
        hook1 = FloatingHook[int](1)
        hook2 = FloatingHook[int](2)
        hook3 = FloatingHook[int](3)
        
        # hook1 listener updates hook2
        def listener1():
            hook2.submit_value(hook1.value * 10)
        
        # hook2 listener updates hook3
        def listener2():
            hook3.submit_value(hook2.value * 10)
        
        hook1.add_listeners(listener1)
        hook2.add_listeners(listener2)
        
        # Update hook1 - should cascade through hook2 to hook3
        hook1.submit_value(5)
        
        assert hook1.value == 5
        assert hook2.value == 50   # 5 * 10
        assert hook3.value == 500  # 50 * 10

