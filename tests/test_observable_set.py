import unittest
from observables import ObservableSet, InitialSyncMode

class TestObservableSet(unittest.TestCase):
    """Test cases for ObservableSet"""
    
    def setUp(self):
        self.observable = ObservableSet({1, 2, 3})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.value, {1, 2, 3})
    
    def test_add(self):
        """Test adding a new value"""
        self.observable.add(4)
        self.assertEqual(self.observable.value, {1, 2, 3, 4})
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.add(7)
        self.assertEqual(self.notification_count, 1)
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.add(1)  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_listeners(self.notification_callback)
        self.observable.add(10)
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
        self.observable.add(13)
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_initialization_with_carries_bindable_set(self):
        """Test initialization with CarriesBindableSet"""
        # Create a source observable set
        source = ObservableSet({1, 2, 3})
        
        # Create a new observable set initialized with the source
        target = ObservableSet(source.value_hook)
        
        # Check that the target has the same initial value
        self.assertEqual(target.value, {1, 2, 3})
        
        # Check that they are bound together
        source.add(4)
        self.assertEqual(target.value, {1, 2, 3, 4})
        
        # Check bidirectional binding
        target.add(5)
        self.assertEqual(source.value, {1, 2, 3, 4, 5})
    
    def test_initialization_with_carries_bindable_set_chain(self):
        """Test initialization with CarriesBindableSet in a chain"""
        # Create a chain of observable sets
        obs1 = ObservableSet({10})
        obs2 = ObservableSet(obs1.value_hook)
        obs3 = ObservableSet(obs2.value_hook)
        
        # Check initial values
        self.assertEqual(obs1.value, {10})
        self.assertEqual(obs2.value, {10})
        self.assertEqual(obs3.value, {10})
        
        # Change the first observable
        obs1.add(20)
        self.assertEqual(obs1.value, {10, 20})
        self.assertEqual(obs2.value, {10, 20})
        self.assertEqual(obs3.value, {10, 20})
        
        # Change the middle observable
        obs2.add(30)
        self.assertEqual(obs1.value, {10, 20, 30})
        self.assertEqual(obs2.value, {10, 20, 30})
        self.assertEqual(obs3.value, {10, 20, 30})
    
    def test_initialization_with_carries_bindable_set_unbinding(self):
        """Test that initialization with CarriesBindableSet can be unbound"""
        source = ObservableSet({100})
        target = ObservableSet(source.value_hook)
        
        # Verify they are bound
        self.assertEqual(target.value, {100})
        source.add(200)
        self.assertEqual(target.value, {100, 200})
        
        # Unbind them
        target.disconnect()
        
        # Change source, target should not update
        source.add(300)
        self.assertEqual(target.value, {100, 200})  # Should remain unchanged
        
        # Change target, source should not update
        target.add(400)
        self.assertEqual(source.value, {100, 200, 300})  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_set_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableSet({100})
        target1 = ObservableSet(source.value_hook)
        target2 = ObservableSet(source.value_hook)
        target3 = ObservableSet(source.value_hook)
        
        # Check initial values
        self.assertEqual(target1.value, {100})
        self.assertEqual(target2.value, {100})
        self.assertEqual(target3.value, {100})
        
        # Change source, all targets should update
        source.add(200)
        self.assertEqual(target1.value, {100, 200})
        self.assertEqual(target2.value, {100, 200})
        self.assertEqual(target3.value, {100, 200})
        
        # Change one target, source and other targets should update
        target1.add(300)
        self.assertEqual(source.value, {100, 200, 300})
        self.assertEqual(target2.value, {100, 200, 300})
        self.assertEqual(target3.value, {100, 200, 300})
    
    def test_initialization_with_carries_bindable_set_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableSet"""
        # Test with empty set in source
        source_empty: ObservableSet[int] = ObservableSet(set())
        target_empty = ObservableSet(source_empty.value_hook)
        self.assertEqual(target_empty.value, set())
        
        # Test with None in source
        source_none: ObservableSet[int] = ObservableSet(None)
        target_none = ObservableSet(source_none.value_hook)
        self.assertEqual(target_none.value, set())
        
        # Test with single item
        source_single = ObservableSet({42})
        target_single = ObservableSet(source_single.value_hook)
        self.assertEqual(target_single.value, {42})
    
    def test_initialization_with_carries_bindable_set_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableSet"""
        source = ObservableSet({100})
        target = ObservableSet(source.value_hook)
        
        # Check binding consistency
        
        # Check that they are properly bound
        self.assertTrue(target.value_hook.is_connected_to(source.value_hook))
        self.assertTrue(source.value_hook.is_connected_to(target.value_hook))
    
    def test_initialization_with_carries_bindable_set_performance(self):
        """Test performance of initialization with CarriesBindableSet"""
        import time
        
        # Create source
        source = ObservableSet({100})
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableSet(source.value_hook)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 6 seconds)
        self.assertLess(end_time - start_time, 6.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableSet(source.value_hook)
        source.add(200)
        self.assertEqual(target.value, {100, 200})
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = ObservableSet({10})
        obs2 = ObservableSet({20})
        
        # Bind obs1 to obs2
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        
        # Change obs1, obs2 should update to include obs1's elements
        obs1.add(30)
        self.assertEqual(obs2.value, {10, 30})
        
        # Change obs2, obs1 should also update (bidirectional)
        obs2.add(40)
        self.assertEqual(obs1.value, {10, 30, 40})
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = ObservableSet({100})
        obs2 = ObservableSet({200})
        
        # USE_CALLER_VALUE: target (obs2) gets caller's value
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        self.assertEqual(obs2.value, {100})
        
        # Test update_observable_from_self mode
        obs3 = ObservableSet({300})
        obs4 = ObservableSet({400})
        obs3.connect(obs4.value_hook, "value", InitialSyncMode.USE_TARGET_VALUE)
        # USE_TARGET_VALUE means caller gets target's value
        self.assertEqual(obs3.value, {400})
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = ObservableSet({10})
        obs2 = ObservableSet({20})
        
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        obs1.disconnect()
        
        # Changes should no longer propagate
        obs1.add(50)
        self.assertEqual(obs1.value, {10, 50})
        self.assertEqual(obs2.value, {10})
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableSet({10})
        with self.assertRaises(ValueError):
            obs.connect(obs.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = ObservableSet({10})
        obs2 = ObservableSet({20})
        obs3 = ObservableSet({30})
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        obs2.connect(obs3.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        
        # Verify chain works
        obs1.add(100)
        self.assertEqual(obs2.value, {10, 100})
        self.assertEqual(obs3.value, {10, 100})
        
        # Break the chain by unbinding obs2 from obs3
        obs2.disconnect()
        
        # Change obs1, obs2 should NOT update but obs3 should (obs1 and obs3 remain bound)
        obs1.add(200)
        self.assertEqual(obs2.value, {10, 100})  # obs2 is isolated
        self.assertEqual(obs3.value, {10, 100, 200})  # obs3 gets updated since obs1 and obs3 remain bound
        
        # Change obs3, obs1 should update since obs1 and obs3 remain bound after obs2.disconnect()
        obs3.add(300)
        self.assertEqual(obs1.value, {10, 100, 200, 300})
        self.assertEqual(obs2.value, {10, 100})
    
    def test_string_representation(self):
        """Test string and repr methods"""
        self.assertEqual(str(self.observable), "OS(options={1, 2, 3})")
        self.assertEqual(repr(self.observable), "ObservableSet({1, 2, 3})")
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableSet({10})
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = ObservableSet({10})
        obs2 = ObservableSet({20})
        obs3 = ObservableSet({30})
        
        # Bind obs2 and obs3 to obs1
        obs2.connect(obs1.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        obs3.connect(obs1.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        
        # Change obs1, both should update to obs1's value
        obs1.add(100)
        self.assertEqual(obs2.value, {30, 100})
        self.assertEqual(obs3.value, {30, 100})
        
        # Change obs2, obs1 should also update (bidirectional), obs3 should also update
        obs2.add(200)
        self.assertEqual(obs1.value, {30, 100, 200})
        self.assertEqual(obs3.value, {30, 100, 200})
    
    def test_set_methods(self):
        """Test standard set methods"""
        obs = ObservableSet({1, 2, 3})
        
        # Test add
        obs.add(4)
        self.assertEqual(obs.value, {1, 2, 3, 4})
        
        # Test remove
        obs.remove(2)
        self.assertEqual(obs.value, {1, 3, 4})
        
        # Test discard
        obs.discard(5)  # Non-existent item
        self.assertEqual(obs.value, {1, 3, 4})
        
        # Test clear
        obs.clear()
        self.assertEqual(obs.value, set())
    
    def test_set_copy_behavior(self):
        """Test that set_value returns a copy"""
        obs = ObservableSet({1, 2, 3})
        
        # Get the set value
        set_copy = obs.value
        
        # Modify the copy
        set_copy.add(4)
        
        # Original should not change
        self.assertEqual(obs.value, {1, 2, 3})
        
        # The copy should have the modification
        self.assertEqual(set_copy, {1, 2, 3, 4})
    
    def test_set_validation(self):
        """Test set validation"""
        # Test with valid set
        obs = ObservableSet({1, 2, 3})
        self.assertEqual(obs.value, {1, 2, 3})
        
        # Test with None (should create empty set)
        obs_none: ObservableSet[int] = ObservableSet(None)
        self.assertEqual(obs_none.value, set())
        
        # Test with empty set
        obs_empty: ObservableSet[int] = ObservableSet(set())
        self.assertEqual(obs_empty.value, set())
    
    def test_set_binding_edge_cases(self):
        """Test edge cases for set binding"""
        # Test binding empty sets
        obs1: ObservableSet[int] = ObservableSet(set())
        obs2: ObservableSet[int] = ObservableSet(set())
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        
        obs1.add(1)
        self.assertEqual(obs2.value, {1})
        
        # Test binding sets with same initial values
        obs3 = ObservableSet({42})
        obs4 = ObservableSet({42})
        obs3.connect(obs4.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        
        obs3.add(100)
        self.assertEqual(obs4.value, {42, 100})
    
    def test_set_performance(self):
        """Test set performance characteristics"""
        import time
        
        # Test add performance
        obs: ObservableSet[int] = ObservableSet(set())
        start_time = time.time()
        
        for i in range(1000):
            obs.add(i)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Add operations should be fast")
        self.assertEqual(len(obs.value), 1000)
        
        # Test binding performance
        source = ObservableSet({1, 2, 3})
        start_time = time.time()
        
        for _ in range(100):
            ObservableSet(source.value_hook)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Binding operations should be fast")
    
    def test_set_error_handling(self):
        """Test set error handling"""
        obs = ObservableSet({1, 2, 3})
        
        # Test remove non-existent item
        with self.assertRaises(KeyError):
            obs.remove(99)
        
        # Test discard non-existent item (should not raise error)
        obs.discard(99)
        self.assertEqual(obs.value, {1, 2, 3})
    
    def test_set_binding_consistency(self):
        """Test binding system consistency"""
        source = ObservableSet({100})
        target = ObservableSet(source.value_hook)
        
        # Check binding consistency
        
        # Check that they are properly bound
        self.assertTrue(target.value_hook.is_connected_to(source.value_hook))
        self.assertTrue(source.value_hook.is_connected_to(target.value_hook))
    
    def test_set_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = ObservableSet({10})
        with self.assertRaises(ValueError):
            obs.connect(None, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
    
    def test_set_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = ObservableSet({42})
        obs2 = ObservableSet({42})
        
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        # Both should still have the same value
        self.assertEqual(obs1.value, {42})
        self.assertEqual(obs2.value, {42})
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = ObservableSet({10})
        callback = lambda: None
        
        obs.add_listeners(callback, callback)
        self.assertEqual(len(obs.listeners), 1)
        
        obs.add_listeners(callback)
        self.assertEqual(len(obs.listeners), 1)
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = ObservableSet({10})
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listeners(callback)
        self.assertEqual(len(obs.listeners), 0)


if __name__ == '__main__':
    unittest.main()
