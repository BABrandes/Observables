import unittest
from enum import Enum
from observables import ObservableEnum, InitialSyncMode

class TestColor(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

class TestSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

class TestObservableEnum(unittest.TestCase):
    """Test cases for ObservableEnum"""
    
    def setUp(self):
        self.observable = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.enum_value, TestColor.RED)
        self.assertEqual(self.observable.enum_options, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
    
    def test_set_enum_value(self):
        """Test setting a new enum value"""
        self.observable.enum_value = TestColor.GREEN
        self.assertEqual(self.observable.enum_value, TestColor.GREEN)
    
    def test_set_enum_options(self):
        """Test setting new enum options"""
        new_options = {TestColor.RED, TestColor.BLUE}
        self.observable.enum_options = new_options
        self.assertEqual(self.observable.enum_options, new_options)
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.enum_value = TestColor.BLUE
        self.assertEqual(self.notification_count, 1)
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.enum_value = TestColor.RED  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_listeners(self.notification_callback)
        self.observable.enum_value = TestColor.GREEN
        self.assertEqual(self.notification_count, 0)
    
    def test_multiple_listeners(self):
        """Test multiple listeners"""
        count1, count2 = 0, 0
        
        def callback1():
            nonlocal count1
            count1 += 1
        
        def callback2():
            nonlocal count2
            count2 += 1
        
        self.observable.add_listeners(callback1)
        self.observable.add_listeners(callback2)
        self.observable.enum_value = TestColor.BLUE
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_initialization_with_carries_bindable_enum(self):
        """Test initialization with CarriesBindableEnum"""
        # Create a source observable enum
        source = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        
        # Create a new observable enum initialized with the source
        target = ObservableEnum(source)
        
        # Check that the target has the same initial value
        self.assertEqual(target.enum_value, TestColor.RED)
        self.assertEqual(target.enum_options, {TestColor.RED, TestColor.GREEN})
        
        # Check that they are bound together
        source.enum_value = TestColor.GREEN
        self.assertEqual(target.enum_value, TestColor.GREEN)
        
        # Check bidirectional binding
        target.enum_value = TestColor.RED
        self.assertEqual(source.enum_value, TestColor.RED)
    
    def test_initialization_with_carries_bindable_enum_chain(self):
        """Test initialization with CarriesBindableEnum in a chain"""
        # Create a chain of observable enums
        obs1 = ObservableEnum(TestSize.SMALL, {TestSize.SMALL, TestSize.MEDIUM})
        obs2 = ObservableEnum(obs1)
        obs3 = ObservableEnum(obs2)
        
        # Check initial values
        self.assertEqual(obs1.enum_value, TestSize.SMALL)
        self.assertEqual(obs2.enum_value, TestSize.SMALL)
        self.assertEqual(obs3.enum_value, TestSize.SMALL)
        
        # Change the first observable
        obs1.enum_value = TestSize.MEDIUM
        self.assertEqual(obs1.enum_value, TestSize.MEDIUM)
        self.assertEqual(obs2.enum_value, TestSize.MEDIUM)
        self.assertEqual(obs3.enum_value, TestSize.MEDIUM)
        
        # Change the middle observable
        obs2.enum_value = TestSize.MEDIUM
        self.assertEqual(obs1.enum_value, TestSize.MEDIUM)
        self.assertEqual(obs2.enum_value, TestSize.MEDIUM)
        self.assertEqual(obs3.enum_value, TestSize.MEDIUM)
    
    def test_initialization_with_carries_bindable_enum_unbinding(self):
        """Test that initialization with CarriesBindableEnum can be unbound"""
        source = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        target = ObservableEnum(source)
        
        # Verify they are bound
        self.assertEqual(target.enum_value, TestColor.RED)
        source.enum_value = TestColor.GREEN
        self.assertEqual(target.enum_value, TestColor.GREEN)
        
        # Unbind them
        target.disconnect()
        
        # Change source, target should not update
        source.enum_value = TestColor.RED
        self.assertEqual(target.enum_value, TestColor.GREEN)  # Should remain unchanged
        
        # Change target, source should not update
        target.enum_value = TestColor.RED
        self.assertEqual(source.enum_value, TestColor.RED)  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_enum_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        target1 = ObservableEnum(source)
        target2 = ObservableEnum(source)
        target3 = ObservableEnum(source)
        
        # Check initial values
        self.assertEqual(target1.enum_value, TestColor.RED)
        self.assertEqual(target2.enum_value, TestColor.RED)
        self.assertEqual(target3.enum_value, TestColor.RED)
        
        # Change source, all targets should update
        source.enum_value = TestColor.GREEN
        self.assertEqual(target1.enum_value, TestColor.GREEN)
        self.assertEqual(target2.enum_value, TestColor.GREEN)
        self.assertEqual(target3.enum_value, TestColor.GREEN)
        
        # Change one target, source and other targets should update
        target1.enum_value = TestColor.RED
        self.assertEqual(source.enum_value, TestColor.RED)
        self.assertEqual(target2.enum_value, TestColor.RED)
        self.assertEqual(target3.enum_value, TestColor.RED)
    
    def test_initialization_with_carries_bindable_enum_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableEnum"""
        # Test with single option in source
        source_single = ObservableEnum(TestColor.RED, {TestColor.RED})
        target_single = ObservableEnum(source_single)
        self.assertEqual(target_single.enum_value, TestColor.RED)
        self.assertEqual(target_single.enum_options, {TestColor.RED})
        
        # Test with None value in source
        source_none = ObservableEnum(None, {TestColor.RED, TestColor.GREEN})
        target_none = ObservableEnum(source_none)
        self.assertIsNone(target_none.enum_value)
        self.assertEqual(target_none.enum_options, {TestColor.RED, TestColor.GREEN})
    
    def test_initialization_with_carries_bindable_enum_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableEnum"""
        source = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        target = ObservableEnum(source)
        
        # Check binding consistency
        
        # Check that they are properly bound
        self.assertTrue(target.distinct_single_value_hook.is_attached_to(source.distinct_single_value_hook))
        self.assertTrue(source.distinct_single_value_hook.is_attached_to(target.distinct_single_value_hook))
    
    def test_initialization_with_carries_bindable_enum_performance(self):
        """Test performance of initialization with CarriesBindableEnum"""
        import time
        
        # Create source
        source = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableEnum(source)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 6 seconds)
        self.assertLess(end_time - start_time, 6.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableEnum(source)
        source.enum_value = TestColor.GREEN
        self.assertEqual(target.enum_value, TestColor.GREEN)
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs2 = ObservableEnum(TestColor.BLUE, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        
        # Bind obs1 to obs2
        obs1.bind_to(obs2)
        
        # Change obs1, obs2 should update
        obs1.enum_value = TestColor.GREEN
        self.assertEqual(obs2.enum_value, TestColor.GREEN)
        
        # Change obs2, obs1 should also update (bidirectional)
        obs2.enum_value = TestColor.RED
        self.assertEqual(obs1.enum_value, TestColor.RED)
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs2 = ObservableEnum(TestColor.BLUE, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        
        # Test default mode (obs2 gets updated with obs1's value)
        obs1.bind_to(obs2)
        self.assertEqual(obs2.enum_value, TestColor.RED)  # obs2 gets updated with obs1's value
        
        # Test update_observable_from_self mode (obs4 gets updated with obs3's value)
        obs3 = ObservableEnum(TestSize.SMALL, {TestSize.SMALL, TestSize.MEDIUM, TestSize.LARGE})
        obs4 = ObservableEnum(TestSize.LARGE, {TestSize.SMALL, TestSize.MEDIUM, TestSize.LARGE})
        obs3.bind_to(obs4, InitialSyncMode.SELF_UPDATES)
        self.assertEqual(obs4.enum_value, TestSize.SMALL)  # obs4 gets updated with obs3's value
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs2 = ObservableEnum(TestColor.BLUE, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        
        obs1.bind_to(obs2)
        
        # After binding, obs2 should have obs1's value
        self.assertEqual(obs2.enum_value, TestColor.RED)
        
        obs1.disconnect()
        
        # After disconnecting, obs2 keeps its current value but changes no longer propagate
        self.assertEqual(obs2.enum_value, TestColor.RED)
        
        # Changes should no longer propagate
        obs1.enum_value = TestColor.GREEN
        self.assertEqual(obs2.enum_value, TestColor.RED)  # Should remain unchanged
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        with self.assertRaises(ValueError):
            obs.bind_to(obs)
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs2 = ObservableEnum(TestColor.BLUE, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs3 = ObservableEnum(TestColor.GREEN, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.bind_to(obs2)
        obs2.bind_to(obs3)
        
        # Verify chain works
        obs1.enum_value = TestColor.GREEN
        self.assertEqual(obs2.enum_value, TestColor.GREEN)
        self.assertEqual(obs3.enum_value, TestColor.GREEN)
        
        # Break the chain by unbinding obs2 from obs3
        obs2.disconnect()
        
        # After obs2 disconnects, obs1 and obs3 should remain bound (transitive binding)
        # Change obs1, obs3 should update but obs2 should not
        obs1.enum_value = TestColor.RED
        self.assertEqual(obs2.enum_value, TestColor.GREEN)  # obs2 is isolated
        self.assertEqual(obs3.enum_value, TestColor.RED)    # obs3 gets updated from obs1
        
        # Change obs3, obs1 should update but obs2 should not
        obs3.enum_value = TestColor.BLUE
        self.assertEqual(obs1.enum_value, TestColor.BLUE)   # obs1 gets updated from obs3
        self.assertEqual(obs2.enum_value, TestColor.GREEN)  # obs2 remains isolated
    
    def test_string_representation(self):
        """Test string and repr methods"""
        # The order depends on the enum values, so we check that all elements are present
        str_repr = str(self.observable)
        self.assertTrue("enum_value=TestColor.RED" in str_repr)
        self.assertTrue("TestColor.RED" in str_repr)
        self.assertTrue("TestColor.GREEN" in str_repr)
        self.assertTrue("TestColor.BLUE" in str_repr)
        
        repr_repr = repr(self.observable)
        self.assertTrue("enum_value=TestColor.RED" in repr_repr)
        self.assertTrue("TestColor.RED" in repr_repr)
        self.assertTrue("TestColor.GREEN" in repr_repr)
        self.assertTrue("TestColor.BLUE" in repr_repr)
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs2 = ObservableEnum(TestColor.BLUE, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs3 = ObservableEnum(TestColor.GREEN, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        
        # Bind obs2 and obs3 to obs1
        obs2.bind_to(obs1)
        obs3.bind_to(obs1)
        
        # Change obs1, both should update
        obs1.enum_value = TestColor.GREEN
        self.assertEqual(obs2.enum_value, TestColor.GREEN)
        self.assertEqual(obs3.enum_value, TestColor.GREEN)
        
        # Change obs2, obs1 should also update (bidirectional), obs3 should also update
        obs2.enum_value = TestColor.RED
        self.assertEqual(obs1.enum_value, TestColor.RED)
        self.assertEqual(obs3.enum_value, TestColor.RED)
    
    def test_enum_methods(self):
        """Test standard enum methods"""
        obs = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        
        # Test enum_value_not_none
        self.assertEqual(obs.enum_value_not_none, TestColor.RED)
        
        # Test set_enum_value_and_options
        obs.set_enum_value_and_options(TestColor.BLUE, {TestColor.BLUE, TestColor.GREEN, TestColor.RED})
        self.assertEqual(obs.enum_value, TestColor.BLUE)
        self.assertEqual(obs.enum_options, {TestColor.BLUE, TestColor.GREEN, TestColor.RED})
    
    def test_enum_copy_behavior(self):
        """Test that enum_options returns a copy"""
        obs = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        
        # Get the enum options
        options_copy = obs.enum_options
        
        # Modify the copy
        options_copy.add(TestSize.SMALL) # type: ignore
        
        # Original should not change
        self.assertEqual(obs.enum_options, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        
        # The copy should have the modification
        self.assertEqual(options_copy, {TestColor.RED, TestColor.GREEN, TestColor.BLUE, TestSize.SMALL})
    
    def test_enum_validation(self):
        """Test enum validation"""
        # Test with valid enum value
        obs = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        self.assertEqual(obs.enum_value, TestColor.RED)
        self.assertEqual(obs.enum_options, {TestColor.RED, TestColor.GREEN})
        
        # Test with None value
        obs_none = ObservableEnum(None, {TestColor.RED, TestColor.GREEN})
        self.assertIsNone(obs_none.enum_value)
        self.assertEqual(obs_none.enum_options, {TestColor.RED, TestColor.GREEN})
    
    def test_enum_binding_edge_cases(self):
        """Test edge cases for enum binding"""
        # Test binding enums with same initial values
        obs1 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs2 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs1.bind_to(obs2)
        
        obs1.enum_value = TestColor.GREEN
        self.assertEqual(obs2.enum_value, TestColor.GREEN)
        
        # Test binding enums with different options
        obs3 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs4 = ObservableEnum(TestColor.GREEN, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs3.bind_to(obs4)
        
        obs3.enum_value = TestColor.BLUE
        self.assertEqual(obs4.enum_value, TestColor.BLUE)
    
    def test_enum_performance(self):
        """Test enum performance characteristics"""
        import time
        
        # Test enum_value access performance
        obs = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        start_time = time.time()
        
        for _ in range(10000):
            _ = obs.enum_value
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Enum value access should be fast")
        
        # Test binding performance
        source = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        start_time = time.time()
        
        for _ in range(100):
            ObservableEnum(source)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Binding operations should be fast")
    
    def test_enum_error_handling(self):
        """Test enum error handling"""
        obs = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        
        # Test setting invalid enum value
        with self.assertRaises(ValueError):
            obs.enum_value = TestColor.BLUE  # Not in options
        
        # Test enum_value_not_none when value is None
        obs_none = ObservableEnum(None, {TestColor.RED, TestColor.GREEN})
        with self.assertRaises(ValueError):
            _ = obs_none.enum_value_not_none
    
    def test_enum_binding_consistency(self):
        """Test binding system consistency"""
        source = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        target = ObservableEnum(source)
        
        # Check binding consistency
        
        # Check that they are properly bound
        self.assertTrue(target.distinct_single_value_hook.is_attached_to(source.distinct_single_value_hook))
        self.assertTrue(source.distinct_single_value_hook.is_attached_to(target.distinct_single_value_hook))
    
    def test_enum_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        with self.assertRaises(ValueError):
            obs.bind_to(None)  # type: ignore
    
    def test_enum_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        obs2 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
        
        obs1.bind_to(obs2)
        # Both should still have the same value
        self.assertEqual(obs1.enum_value, TestColor.RED)
        self.assertEqual(obs2.enum_value, TestColor.RED)
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        callback = lambda: None
        
        obs.add_listeners(callback, callback)
        self.assertEqual(len(obs.listeners), 1)
        
        obs.add_listeners(callback)
        self.assertEqual(len(obs.listeners), 1)
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN})
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listeners(callback)
        self.assertEqual(len(obs.listeners), 0)


if __name__ == '__main__':
    unittest.main()