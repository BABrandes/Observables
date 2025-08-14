import unittest
from observables import ObservableSingleValue, SyncMode


class TestObservableSingleValue(unittest.TestCase):
    """Test cases for ObservableSingleValue"""
    
    def setUp(self):
        self.observable = ObservableSingleValue(42)
        self.notification_count = 0
        self.last_notified_value = None
    
    def notification_callback(self):
        self.notification_count += 1
    
    def value_callback(self, value):
        self.last_notified_value = value
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.value, 42)
    
    def test_set_value(self):
        """Test setting a new value"""
        self.observable.set_value(100)
        self.assertEqual(self.observable.value, 100)
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_value(50)
        self.assertEqual(self.notification_count, 1)
    
    def test_multiple_listeners(self):
        """Test multiple listeners are notified"""
        count1, count2 = 0, 0
        
        def callback1():
            nonlocal count1
            count1 += 1
        
        def callback2():
            nonlocal count2
            count2 += 1
        
        self.observable.add_listeners(callback1, callback2)
        self.observable.set_value(75)
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_remove_listener(self):
        """Test removing a listener"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_listeners(self.notification_callback)
        self.observable.set_value(200)
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_all_listeners(self):
        """Test removing all listeners"""
        self.observable.add_listeners(self.notification_callback)
        removed = self.observable.remove_all_listeners()
        self.assertEqual(len(removed), 1)
        self.observable.set_value(300)
        self.assertEqual(self.notification_count, 0)
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        # Bind obs1 to obs2
        obs1.bind_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change obs1, obs2 should update
        obs1.set_value(30)
        self.assertEqual(obs2.value, 30)
        
        # Change obs2, obs1 should also update (bidirectional)
        obs2.set_value(40)
        self.assertEqual(obs1.value, 40)  # Should also update
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = ObservableSingleValue(100)
        obs2 = ObservableSingleValue(200)
        
        # Test update_value_from_observable mode
        obs1.bind_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        self.assertEqual(obs1.value, 200)  # obs1 gets updated with obs2's value
        
        # Test update_observable_from_self mode
        obs3 = ObservableSingleValue(300)
        obs4 = ObservableSingleValue(400)
        obs3.bind_to(obs4, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        self.assertEqual(obs4.value, 300)  # obs4 gets updated with obs3's value
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        obs1.bind_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        obs1.unbind_from(obs2)
        
        # Changes should no longer propagate
        obs1.set_value(50)
        self.assertEqual(obs2.value, 20)
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        obs1.bind_to(obs2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        obs1.unbind_from(obs2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            obs1.unbind_from(obs2)
        
        # Changes should still not propagate
        obs1.set_value(50)
        # Since we used UPDATE_OBSERVABLE_FROM_SELF, obs2 was updated to obs1's value (10) during binding
        # After unbinding, obs2 should still have that value, not the original 20
        self.assertEqual(obs2.value, 10)
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableSingleValue(10)
        with self.assertRaises(ValueError):
            obs.bind_to(obs, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        obs3 = ObservableSingleValue(30)
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.bind_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        obs2.bind_to(obs3, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Verify chain works
        obs1.set_value(100)
        self.assertEqual(obs2.value, 100)
        self.assertEqual(obs3.value, 100)
        
        # Break the chain by unbinding obs2 from obs3
        obs2.unbind_from(obs3)
        
        # Change obs1, obs2 should update but obs3 should not
        obs1.set_value(200)
        self.assertEqual(obs2.value, 200)
        self.assertEqual(obs3.value, 100)  # Should remain unchanged
        
        # Change obs3, obs1 and obs2 should not update
        obs3.set_value(300)
        self.assertEqual(obs1.value, 200)
        self.assertEqual(obs2.value, 200)
    
    def test_string_representation(self):
        """Test string and repr methods"""
        self.assertEqual(str(self.observable), "OSV(value=42)")
        self.assertEqual(repr(self.observable), "OSV(value=42)")
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableSingleValue(10)
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        obs3 = ObservableSingleValue(30)
        
        # Bind obs2 and obs3 to obs1
        obs2.bind_to(obs1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        obs3.bind_to(obs1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change obs1, both should update
        obs1.set_value(100)
        self.assertEqual(obs2.value, 100)
        self.assertEqual(obs3.value, 100)
        
        # Change obs2, obs1 should also update (bidirectional), obs3 should also update
        obs2.set_value(200)
        self.assertEqual(obs1.value, 200)  # Should also update
        self.assertEqual(obs3.value, 200)  # Should also update
    
    def test_initialization_with_carries_bindable_single_value(self):
        """Test initialization with CarriesBindableSingleValue"""
        # Create a source observable
        source = ObservableSingleValue(100)
        
        # Create a new observable initialized with the source
        target = ObservableSingleValue(source)
        
        # Check that the target has the same initial value
        self.assertEqual(target.value, 100)
        
        # Check that they are bound together
        source.set_value(200)
        self.assertEqual(target.value, 200)
        
        # Check bidirectional binding
        target.set_value(300)
        self.assertEqual(source.value, 300)
    
    def test_initialization_with_carries_bindable_single_value_with_validator(self):
        """Test initialization with CarriesBindableSingleValue and validator"""
        def validate_positive(value):
            return value > 0
        
        # Create a source observable with validator
        source = ObservableSingleValue(50, validator=validate_positive)
        
        # Create a target observable initialized with the source and validator
        target = ObservableSingleValue(source, validator=validate_positive)
        
        # Check that the target has the same initial value
        self.assertEqual(target.value, 50)
        
        # Check that they are bound together
        source.set_value(75)
        self.assertEqual(target.value, 75)
        
        # Check that validation still works
        with self.assertRaises(ValueError):
            source.set_value(-10)
        
        # Target should still have the previous valid value
        self.assertEqual(target.value, 75)
    
    def test_initialization_with_carries_bindable_single_value_different_types(self):
        """Test initialization with CarriesBindableSingleValue of different types"""
        # Test with string type
        source_str = ObservableSingleValue("hello")
        target_str = ObservableSingleValue(source_str)
        self.assertEqual(target_str.value, "hello")
        
        # Test with float type
        source_float = ObservableSingleValue(3.14)
        target_float = ObservableSingleValue(source_float)
        self.assertEqual(target_float.value, 3.14)
        
        # Test with list type
        source_list = ObservableSingleValue([1, 2, 3])
        target_list = ObservableSingleValue(source_list)
        self.assertEqual(target_list.value, [1, 2, 3])
    
    def test_initialization_with_carries_bindable_single_value_chain(self):
        """Test initialization with CarriesBindableSingleValue in a chain"""
        # Create a chain of observables
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(obs1)
        obs3 = ObservableSingleValue(obs2)
        
        # Check initial values
        self.assertEqual(obs1.value, 10)
        self.assertEqual(obs2.value, 10)
        self.assertEqual(obs3.value, 10)
        
        # Change the first observable
        obs1.set_value(20)
        self.assertEqual(obs1.value, 20)
        self.assertEqual(obs2.value, 20)
        self.assertEqual(obs3.value, 20)
        
        # Change the middle observable
        obs2.set_value(30)
        self.assertEqual(obs1.value, 30)
        self.assertEqual(obs2.value, 30)
        self.assertEqual(obs3.value, 30)
    
    def test_initialization_with_carries_bindable_single_value_unbinding(self):
        """Test that initialization with CarriesBindableSingleValue can be unbound"""
        source = ObservableSingleValue(100)
        target = ObservableSingleValue(source)
        
        # Verify they are bound
        self.assertEqual(target.value, 100)
        source.set_value(200)
        self.assertEqual(target.value, 200)
        
        # Unbind them
        target.unbind_from(source)
        
        # Change source, target should not update
        source.set_value(300)
        self.assertEqual(target.value, 200)  # Should remain unchanged
        
        # Change target, source should not update
        target.set_value(400)
        self.assertEqual(source.value, 300)  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_single_value_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableSingleValue(100)
        target1 = ObservableSingleValue(source)
        target2 = ObservableSingleValue(source)
        target3 = ObservableSingleValue(source)
        
        # Check initial values
        self.assertEqual(target1.value, 100)
        self.assertEqual(target2.value, 100)
        self.assertEqual(target3.value, 100)
        
        # Change source, all targets should update
        source.set_value(200)
        self.assertEqual(target1.value, 200)
        self.assertEqual(target2.value, 200)
        self.assertEqual(target3.value, 200)
        
        # Change one target, source and other targets should update
        target1.set_value(300)
        self.assertEqual(source.value, 300)
        self.assertEqual(target2.value, 300)
        self.assertEqual(target3.value, 300)
    
    def test_initialization_with_carries_bindable_single_value_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableSingleValue"""
        # Test with None value in source
        source_none = ObservableSingleValue(None)
        target_none = ObservableSingleValue(source_none)
        self.assertIsNone(target_none.value)
        
        # Test with zero value
        source_zero = ObservableSingleValue(0)
        target_zero = ObservableSingleValue(source_zero)
        self.assertEqual(target_zero.value, 0)
        
        # Test with empty string
        source_empty = ObservableSingleValue("")
        target_empty = ObservableSingleValue(source_empty)
        self.assertEqual(target_empty.value, "")
    
    def test_initialization_with_carries_bindable_single_value_validation_errors(self):
        """Test validation errors when initializing with CarriesBindableSingleValue"""
        def validate_even(value):
            return value % 2 == 0
        
        # Create source with even value
        source = ObservableSingleValue(10, validator=validate_even)
        
        # Target should initialize successfully with even value
        target = ObservableSingleValue(source, validator=validate_even)
        self.assertEqual(target.value, 10)
        
        # Try to set odd value in source, should fail
        with self.assertRaises(ValueError):
            source.set_value(11)
        
        # Target should still have the previous valid value
        self.assertEqual(target.value, 10)
        
        # Set valid even value
        source.set_value(12)
        self.assertEqual(target.value, 12)
    
    def test_initialization_with_carries_bindable_single_value_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableSingleValue"""
        source = ObservableSingleValue(100)
        target = ObservableSingleValue(source)
        
        # Check binding consistency
        is_consistent, message = target.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Check that they are properly bound
        self.assertTrue(target._get_single_value_hook().is_bound_to(source._get_single_value_hook()))
        self.assertTrue(source._get_single_value_hook().is_bound_to(target._get_single_value_hook()))
    
    def test_initialization_with_carries_bindable_single_value_performance(self):
        """Test performance of initialization with CarriesBindableSingleValue"""
        import time
        
        # Create source
        source = ObservableSingleValue(100)
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableSingleValue(source)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 6 seconds)
        self.assertLess(end_time - start_time, 6.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableSingleValue(source)
        source.set_value(200)
        self.assertEqual(target.value, 200)

    def test_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = ObservableSingleValue(10)
        with self.assertRaises(ValueError):
            obs.bind_to(None) # type: ignore
    
    def test_binding_with_invalid_sync_mode(self):
        """Test that invalid sync mode raises an error"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        with self.assertRaises(ValueError):
            obs1.bind_to(obs2, "invalid_mode") # type: ignore
    

    
    def test_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = ObservableSingleValue(42)
        obs2 = ObservableSingleValue(42)
        
        obs1.bind_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        # Both should still have the same value
        self.assertEqual(obs1.value, 42)
        self.assertEqual(obs2.value, 42)
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = ObservableSingleValue(10)
        callback = lambda: None
        
        obs.add_listeners(callback, callback)
        self.assertEqual(len(obs.listeners), 1)
        
        obs.add_listeners(callback)
        self.assertEqual(len(obs.listeners), 1)
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = ObservableSingleValue(10)
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listeners(callback)
        self.assertEqual(len(obs.listeners), 0)




if __name__ == '__main__':
    unittest.main()
