import unittest
from observables import ObservableSet, SyncMode


class TestObservableSet(unittest.TestCase):
    """Test cases for ObservableSet"""
    
    def setUp(self):
        self.observable = ObservableSet({1, 2, 3})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_options(self):
        """Test that initial options are set correctly"""
        self.assertEqual(self.observable.value, {1, 2, 3})
    
    def test_change_options(self):
        """Test changing options"""
        self.observable.set_set({4, 5, 6})
        self.assertEqual(self.observable.value, {4, 5, 6})
    
    def test_listener_notification(self):
        """Test that listeners are notified when options change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_set({7, 8, 9})
        self.assertEqual(self.notification_count, 1)
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between set1 and set2"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        # Bind set1 to set2
        set1.bind_to(set2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change set1, set2 should update
        set1.set_set({7, 8, 9})
        self.assertEqual(set2.value, {7, 8, 9})
        
        # Change set2, set1 should also update (bidirectional)
        set2.set_set({10, 11, 12})
        self.assertEqual(set1.value, {10, 11, 12})  # Should also update
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        # Test update_value_from_observable mode
        set1.bind_to(set2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        self.assertEqual(set1.value, {4, 5, 6})  # set1 gets updated with set2's value
        
        # Test update_observable_from_self mode
        set3 = ObservableSet({7, 8, 9})
        set4 = ObservableSet({10, 11, 12})
        set3.bind_to(set4, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        self.assertEqual(set4.value, {7, 8, 9})  # set4 gets updated with set3's value
    
    def test_unbinding(self):
        """Test unbinding observable sets"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        set1.bind_to(set2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        set1.unbind_from(set2)
        
        # Changes should no longer propagate
        set1.set_set({7, 8, 9})
        self.assertEqual(set2.value, {4, 5, 6})
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        set1.bind_to(set2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        set1.unbind_from(set2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            set1.unbind_from(set2)
        
        # Changes should still not propagate
        set1.set_set({7, 8, 9})
        # Since we used UPDATE_OBSERVABLE_FROM_SELF, set2 was updated to set1's value ({1, 2, 3}) during binding
        # After unbinding, set2 should still have that value, not the original {4, 5, 6}
        self.assertEqual(set2.value, {1, 2, 3})
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        set1 = ObservableSet({1, 2, 3})
        with self.assertRaises(ValueError):
            set1.bind_to(set1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable set"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        set3 = ObservableSet({7, 8, 9})
        
        # Bind set2 and set3 to set1
        set2.bind_to(set1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        set3.bind_to(set1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change set1, both should update
        set1.set_set({10, 11, 12})
        self.assertEqual(set2.value, {10, 11, 12})
        self.assertEqual(set3.value, {10, 11, 12})
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableSet({1, 2, 3})
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_initialization_with_carries_bindable_set(self):
        """Test initialization with CarriesBindableSet"""
        # Create a source observable set
        source = ObservableSet({1, 2, 3})
        
        # Create a new observable set initialized with the source
        target = ObservableSet(source)
        
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
        obs2 = ObservableSet(obs1)
        obs3 = ObservableSet(obs2)
        
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
    
    def test_initialization_with_carries_bindable_set_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableSet({100})
        target1 = ObservableSet(source)
        target2 = ObservableSet(source)
        target3 = ObservableSet(source)
        
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
    
    def test_initialization_with_carries_bindable_set_unbinding(self):
        """Test that initialization with CarriesBindableSet can be unbound"""
        source = ObservableSet({1, 2})
        target = ObservableSet(source)
        
        # Verify they are bound
        self.assertEqual(target.value, {1, 2})
        source.add(3)
        self.assertEqual(target.value, {1, 2, 3})
        
        # Unbind them
        target.unbind_from(source)
        
        # Change source, target should not update
        source.add(4)
        self.assertEqual(target.value, {1, 2, 3})  # Should remain unchanged
        
        # Change target, source should not update
        target.add(5)
        self.assertEqual(source.value, {1, 2, 3, 4})  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_set_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableSet"""
        # Test with empty set
        source_empty = ObservableSet(set())
        target_empty = ObservableSet(source_empty)
        self.assertEqual(target_empty.value, set())
        
        # Test with None values in set
        source_none = ObservableSet({None, 1, None})
        target_none = ObservableSet(source_none)
        self.assertEqual(target_none.value, {None, 1})
        
        # Test with nested set
        source_nested = ObservableSet({frozenset([1, 2]), frozenset([3, 4])})
        target_nested = ObservableSet(source_nested)
        self.assertEqual(target_nested.value, {frozenset([1, 2]), frozenset([3, 4])})
    
    def test_initialization_with_carries_bindable_set_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableSet"""
        source = ObservableSet({1, 2, 3})
        target = ObservableSet(source)
        
        # Check binding consistency
        is_consistent, message = target.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Check that they are properly bound
        self.assertTrue(target._get_set_hook().is_bound_to(source._get_set_hook()))
        self.assertTrue(source._get_set_hook().is_bound_to(target._get_set_hook()))
    
    def test_initialization_with_carries_bindable_set_performance(self):
        """Test performance of initialization with CarriesBindableSet"""
        # Create a source observable set
        source = ObservableSet({1, 2, 3, 4, 5})
        
        # Measure time for multiple initializations
        import time
        start_time = time.time()
        
        for _ in range(1000):
            target = ObservableSet(source)
            _ = target.value  # Access to ensure initialization is complete
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time (less than 3 seconds)
        self.assertLess(total_time, 3.0)
    
    def test_none_initialization(self):
        """Test initialization with None value"""
        # Test initialization with None
        obs = ObservableSet(None)
        self.assertEqual(obs.value, set())
        
        # Test that it's a proper empty set, not None
        self.assertIsInstance(obs.value, set)
        self.assertEqual(len(obs.value), 0)
        
        # Test that we can add items to it
        obs.add(1)
        obs.add(2)
        self.assertEqual(obs.value, {1, 2})
    
    def test_empty_set_initialization(self):
        """Test initialization with empty set"""
        # Test initialization with empty set
        obs = ObservableSet(set())
        self.assertEqual(obs.value, set())
        
        # Test that it's a proper empty set
        self.assertIsInstance(obs.value, set)
        self.assertEqual(len(obs.value), 0)
        
        # Test that we can add items to it
        obs.add(10)
        obs.add(20)
        self.assertEqual(obs.value, {10, 20})
    
    def test_none_vs_empty_set_behavior(self):
        """Test that None and empty set initialization behave identically"""
        obs_none = ObservableSet(None)
        obs_empty = ObservableSet(set())
        
        # Both should start with empty sets
        self.assertEqual(obs_none.value, obs_empty.value)
        self.assertEqual(obs_none.value, set())
        
        # Both should behave the same way when modified
        obs_none.add(1)
        obs_empty.add(1)
        
        self.assertEqual(obs_none.value, obs_empty.value)
        self.assertEqual(obs_none.value, {1})

    def test_binding_empty_set(self):
        """Test binding with empty sets"""
        set1 = ObservableSet(set())
        set2 = ObservableSet({1, 2, 3})
        
        set1.bind_to(set2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        set2.set_set({4, 5, 6})
        self.assertEqual(set1.value, {4, 5, 6})


if __name__ == '__main__':
    unittest.main()
