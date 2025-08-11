#!/usr/bin/env python3
"""
Simple test script for observables that avoids import issues
"""
import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_observable_single_value():
    """Test ObservableSingleValue functionality"""
    print("Testing ObservableSingleValue...")
    
    try:
        from ..observables import ObservableSingleValue
        
        # Test basic functionality
        obs = ObservableSingleValue(42)
        assert obs.value == 42, f"Expected 42, got {obs.value}"
        print("✓ Initial value set correctly")
        
        # Test value change
        obs.set_value(100)
        assert obs.value == 100, f"Expected 100, got {obs.value}"
        print("✓ Value change works")
        
        # Test listener notification
        notification_count = 0
        def callback():
            nonlocal notification_count
            notification_count += 1
        
        obs.add_listeners(callback)
        obs.set_value(200)
        assert notification_count == 1, f"Expected 1 notification, got {notification_count}"
        print("✓ Listener notification works")
        
        print("✓ ObservableSingleValue tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ ObservableSingleValue test failed: {e}")
        return False

def test_observable_set():
    """Test ObservableSet functionality"""
    print("\nTesting ObservableSet...")
    
    try:
        from ..observables import ObservableSet
        
        # Test basic functionality
        obs = ObservableSet({1, 2, 3})
        assert obs.options == {1, 2, 3}, f"Expected {{1, 2, 3}}, got {obs.options}"
        print("✓ Initial options set correctly")
        
        # Test options change
        obs.set_set({4, 5, 6})
        assert obs.options == {4, 5, 6}, f"Expected {{4, 5, 6}}, got {obs.options}"
        print("✓ Options change works")
        
        # Test listener notification
        notification_count = 0
        def callback():
            nonlocal notification_count
            notification_count += 1
        
        obs.add_listeners(callback)
        obs.set_set({7, 8, 9})
        assert notification_count == 1, f"Expected 1 notification, got {notification_count}"
        print("✓ Listener notification works")
        
        print("✓ ObservableSet tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ ObservableSet test failed: {e}")
        return False

def test_observable_selection_option():
    """Test ObservableSelectionOption functionality"""
    print("\nTesting ObservableSelectionOption...")
    
    try:
        from ..observables import ObservableSelectionOption
        
        # Test basic functionality
        obs = ObservableSelectionOption({1, 2, 3, 4}, 2)
        assert obs.options == {1, 2, 3, 4}, f"Expected {{1, 2, 3, 4}}, got {obs.options}"
        assert obs.selected_option == 2, f"Expected 2, got {obs.selected_option}"
        print("✓ Initial state set correctly")
        
        # Test selected option change
        obs.change_selected_option(3)
        assert obs.selected_option == 3, f"Expected 3, got {obs.selected_option}"
        print("✓ Selected option change works")
        
        # Test options change
        obs.change_options({3, 4, 5})
        assert obs.options == {3, 4, 5}, f"Expected {{3, 4, 5}}, got {obs.options}"
        print("✓ Options change works")
        
        print("✓ ObservableSelectionOption tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ ObservableSelectionOption test failed: {e}")
        return False

def test_binding():
    """Test binding functionality between observables"""
    print("\nTesting binding functionality...")
    
    try:
        from ..observables import ObservableSingleValue
        
        # Test bidirectional binding
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        # Bind obs1 to obs2
        obs1.bind_to_observable(obs2)
        
        # Change obs1, obs2 should update
        obs1.set_value(30)
        assert obs2.value == 30, f"Expected 30, got {obs2.value}"
        print("✓ Forward binding works")
        
        # Change obs2, obs1 should update
        obs2.set_value(40)
        assert obs1.value == 40, f"Expected 40, got {obs1.value}"
        print("✓ Reverse binding works")
        
        print("✓ Binding tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Binding test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Running Observable Tests...")
    print("=" * 50)
    
    tests = [
        test_observable_single_value,
        test_observable_set,
        test_observable_selection_option,
        test_binding
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
