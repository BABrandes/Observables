"""Test that reentrancy protection works correctly."""

from observables import FloatingHook
import pytest

def test_recursive_submit_values_raises_error():
    """Test that recursive submit_values calls are detected and raise RuntimeError."""
    
    hook1 = FloatingHook[int](42)
    hook2 = FloatingHook[int](100)
    
    # Create a listener that tries to submit values (BAD - should not do this!)
    def bad_listener():
        # This listener tries to submit a value during the notification phase
        # This should be caught and raise RuntimeError
        hook2.submit_value(200)
    
    hook1.add_listeners(bad_listener)
    
    # Try to update hook1 - this should trigger the listener which tries to submit to hook2
    with pytest.raises(RuntimeError, match="Recursive submit_values call detected"):
        hook1.submit_value(99)
    
    print("✓ Reentrancy protection works correctly!")

if __name__ == "__main__":
    test_recursive_submit_values_raises_error()
    print("\nAll reentrancy protection tests passed!")

