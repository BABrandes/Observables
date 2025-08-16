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
        self.assertEqual(self.observable.set_value, {1, 2, 3})
    
    def test_change_options(self):
        """Test changing options"""
        self.observable.set_value = {4, 5, 6}
        self.assertEqual(self.observable.set_value, {4, 5, 6})
    
    def test_listener_notification(self):
        """Test that listeners are notified when options change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_value = {7, 8, 9}
        self.assertEqual(self.notification_count, 1)
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between set1 and set2"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        # Bind set1 to set2
        set1.bind_to(set2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change set1, set2 should update
        set1.set_value = {7, 8, 9}
        self.assertEqual(set2.set_value, {7, 8, 9})
        
        # Change set2, set1 should also update (bidirectional)
        set2.set_value = {10, 11, 12}
        self.assertEqual(set1.set_value, {10, 11, 12})  # Should also update
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        # Test update_value_from_observable mode
        set1.bind_to(set2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        self.assertEqual(set1.set_value, {4, 5, 6})  # set1 gets updated with set2's value
        
        # Test update_observable_from_self mode
        set3 = ObservableSet({7, 8, 9})
        set4 = ObservableSet({10, 11, 12})
        set3.bind_to(set4, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        self.assertEqual(set4.set_value, {7, 8, 9})  # set4 gets updated with set3's value
    
    def test_unbinding(self):
        """Test unbinding observable sets"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        set1.bind_to(set2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        set1.unbind_from(set2)
        
        # Changes should no longer propagate
        set1.set_value = {7, 8, 9}
        self.assertEqual(set2.set_value, {4, 5, 6})
    
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
        set1.set_value = {7, 8, 9}
        # Since we used UPDATE_OBSERVABLE_FROM_SELF, set2 was updated to set1's value ({1, 2, 3}) during binding
        # After unbinding, set2 should still have that value, not the original {4, 5, 6}
        self.assertEqual(set2.set_value, {1, 2, 3})
    
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
        
        # Change set1, both set2 and set3 should update
        set1.set_value = {10, 11, 12}
        self.assertEqual(set2.set_value, {10, 11, 12})
        self.assertEqual(set3.set_value, {10, 11, 12})
        
        # Change set2, set1 and set3 should update
        set2.set_value = {13, 14, 15}
        self.assertEqual(set1.set_value, {13, 14, 15})
        self.assertEqual(set3.set_value, {13, 14, 15})
    
    def test_listener_management(self):
        """Test adding and removing listeners"""
        # Add multiple listeners
        count1, count2 = 0, 0
        
        def callback1():
            nonlocal count1
            count1 += 1
        
        def callback2():
            nonlocal count2
            count2 += 1
        
        self.observable.add_listeners(callback1)
        self.observable.add_listeners(callback2)
        
        # Trigger change
        self.observable.set_value = {4, 5, 6}
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
        
        # Remove one listener
        self.observable.remove_listeners(callback1)
        self.observable.set_value = {7, 8, 9}
        self.assertEqual(count1, 1)  # Should not change
        self.assertEqual(count2, 2)  # Should increment
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_value = {1, 2, 3}  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_empty_set_initialization(self):
        """Test initialization with empty set"""
        empty_set = ObservableSet(set())
        self.assertEqual(empty_set.set_value, set())
        self.assertIsInstance(empty_set.set_value, set)
    
    def test_none_initialization(self):
        """Test initialization with None value"""
        none_set = ObservableSet(None)
        self.assertEqual(none_set.set_value, set())
        self.assertIsInstance(none_set.set_value, set)
    
    def test_none_vs_empty_set_behavior(self):
        """Test that None and empty set initialization behave identically"""
        none_set = ObservableSet(None)
        empty_set = ObservableSet(set())
        
        self.assertEqual(none_set.set_value, empty_set.set_value)
        self.assertEqual(none_set.set_value, set())
        
        # Both should behave the same way when modified
        none_set.set_value = {1, 2, 3}
        empty_set.set_value = {1, 2, 3}
        
        self.assertEqual(none_set.set_value, empty_set.set_value)
        self.assertEqual(none_set.set_value, {1, 2, 3})
    
    def test_initialization_with_carries_bindable_set(self):
        """Test initialization with CarriesBindableSet"""
        source = ObservableSet({1, 2, 3})
        target = ObservableSet(source)
        
        # Check initial value
        self.assertEqual(target.set_value, {1, 2, 3})
        
        # Check binding
        source.set_value = {4, 5, 6}
        self.assertEqual(target.set_value, {4, 5, 6})
        
        # Check bidirectional binding
        target.set_value = {7, 8, 9}
        self.assertEqual(source.set_value, {7, 8, 9})
    
    def test_initialization_with_carries_bindable_set_chain(self):
        """Test initialization with CarriesBindableSet in a chain"""
        obs1 = ObservableSet({10})
        obs2 = ObservableSet(obs1)
        obs3 = ObservableSet(obs2)
        
        # Check initial values
        self.assertEqual(obs1.set_value, {10})
        self.assertEqual(obs2.set_value, {10})
        self.assertEqual(obs3.set_value, {10})
        
        # Change the first observable
        obs1.set_value = {10, 20}
        self.assertEqual(obs1.set_value, {10, 20})
        self.assertEqual(obs2.set_value, {10, 20})
        self.assertEqual(obs3.set_value, {10, 20})
        
        # Change the middle observable
        obs2.set_value = {10, 20, 30}
        self.assertEqual(obs1.set_value, {10, 20, 30})
        self.assertEqual(obs2.set_value, {10, 20, 30})
        self.assertEqual(obs3.set_value, {10, 20, 30})
    
    def test_initialization_with_carries_bindable_set_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableSet({100})
        target1 = ObservableSet(source)
        target2 = ObservableSet(source)
        target3 = ObservableSet(source)
        
        # Check initial values
        self.assertEqual(target1.set_value, {100})
        self.assertEqual(target2.set_value, {100})
        self.assertEqual(target3.set_value, {100})
        
        # Change source, all targets should update
        source.set_value = {100, 200}
        self.assertEqual(target1.set_value, {100, 200})
        self.assertEqual(target2.set_value, {100, 200})
        self.assertEqual(target3.set_value, {100, 200})
        
        # Change one target, source and other targets should update
        target1.set_value = {100, 200, 300}
        self.assertEqual(source.set_value, {100, 200, 300})
        self.assertEqual(target2.set_value, {100, 200, 300})
        self.assertEqual(target3.set_value, {100, 200, 300})
    
    def test_initialization_with_carries_bindable_set_unbinding(self):
        """Test that initialization with CarriesBindableSet can be unbound"""
        source = ObservableSet({1, 2})
        target = ObservableSet(source)
        
        # Verify they are bound
        self.assertEqual(target.set_value, {1, 2})
        source.set_value = {1, 2, 3}
        self.assertEqual(target.set_value, {1, 2, 3})
        
        # Unbind them
        target.unbind_from(source)
        
        # Change source, target should not update
        source.set_value = {1, 2, 3, 4}
        self.assertEqual(target.set_value, {1, 2, 3})  # Should remain unchanged
        
        # Change target, source should not update
        target.set_value = {1, 2, 3, 5}
        self.assertEqual(source.set_value, {1, 2, 3, 4})  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_set_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableSet"""
        # Test with empty set
        source_empty = ObservableSet(set())
        target_empty = ObservableSet(source_empty)
        self.assertEqual(target_empty.set_value, set())
        
        # Test with None values in set
        source_none = ObservableSet({None, 1, None})
        target_none = ObservableSet(source_none)
        self.assertEqual(target_none.set_value, {None, 1, None})
        
        # Test with nested set
        source_nested = ObservableSet({frozenset([1, 2]), frozenset([3, 4])})
        target_nested = ObservableSet(source_nested)
        self.assertEqual(target_nested.set_value, {frozenset([1, 2]), frozenset([3, 4])})
    
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
        source = ObservableSet({1, 2, 3, 4, 5})
        
        import time
        start_time = time.time()
        
        for _ in range(1000):
            target = ObservableSet(source)
            _ = target.set_value  # Access to ensure initialization is complete
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time (less than 3 seconds)
        self.assertLess(total_time, 3.0)
    
    # Additional tests for missing coverage
    
    def test_add(self):
        """Test adding an item to the set"""
        self.observable.add(4)
        self.assertEqual(self.observable.set_value, {1, 2, 3, 4})
    
    def test_add_existing_item(self):
        """Test adding an item that already exists"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.add(2)  # Already exists
        self.assertEqual(self.notification_count, 0)  # No change, no notification
    
    def test_remove(self):
        """Test removing an item from the set"""
        self.observable.remove(2)
        self.assertEqual(self.observable.set_value, {1, 3})
    
    def test_remove_nonexistent_item(self):
        """Test removing an item that doesn't exist raises KeyError"""
        with self.assertRaises(KeyError):
            self.observable.remove(99)
    
    def test_discard(self):
        """Test discarding an item from the set"""
        self.observable.discard(2)
        self.assertEqual(self.observable.set_value, {1, 3})
    
    def test_discard_nonexistent_item(self):
        """Test discarding an item that doesn't exist (no error)"""
        self.observable.discard(99)
        self.assertEqual(self.observable.set_value, {1, 2, 3})
    
    def test_pop(self):
        """Test popping an item from the set"""
        item = self.observable.pop()
        self.assertIn(item, {1, 2, 3})
        self.assertEqual(len(self.observable.set_value), 2)
    
    def test_pop_empty_set(self):
        """Test pop on empty set raises KeyError"""
        empty_set = ObservableSet(set())
        with self.assertRaises(KeyError):
            empty_set.pop()
    
    def test_clear(self):
        """Test clearing the set"""
        self.observable.clear()
        self.assertEqual(self.observable.set_value, set())
    
    def test_clear_empty_set(self):
        """Test clearing an already empty set"""
        empty_set = ObservableSet(set())
        empty_set.add_listeners(self.notification_callback)
        empty_set.clear()
        self.assertEqual(self.notification_count, 0)  # No change, no notification
    
    def test_update(self):
        """Test updating the set with an iterable"""
        self.observable.update([4, 5, 6])
        self.assertEqual(self.observable.set_value, {1, 2, 3, 4, 5, 6})
    
    def test_update_no_change_notification(self):
        """Test that update doesn't notify when no change occurs"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.update([1, 2, 3])  # All items already exist
        self.assertEqual(self.notification_count, 0)
    
    def test_intersection_update(self):
        """Test intersection_update operation"""
        self.observable.intersection_update({2, 3, 4})
        self.assertEqual(self.observable.set_value, {2, 3})
    
    def test_intersection_update_no_change_notification(self):
        """Test that intersection_update doesn't notify when no change occurs"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.intersection_update({1, 2, 3})  # No change
        self.assertEqual(self.notification_count, 0)
    
    def test_difference_update(self):
        """Test difference_update operation"""
        self.observable.difference_update({2, 3})
        self.assertEqual(self.observable.set_value, {1})
    
    def test_difference_update_no_change_notification(self):
        """Test that difference_update doesn't notify when no change occurs"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.difference_update({4, 5})  # No change
        self.assertEqual(self.notification_count, 0)
    
    def test_symmetric_difference_update(self):
        """Test symmetric_difference_update operation"""
        self.observable.symmetric_difference_update({3, 4, 5})
        self.assertEqual(self.observable.set_value, {1, 2, 4, 5})
    
    def test_symmetric_difference_update_no_change_notification(self):
        """Test that symmetric_difference_update doesn't notify when no change occurs"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.symmetric_difference_update({1, 2, 3})  # No change
        self.assertEqual(self.notification_count, 0)
    
    def test_string_representation(self):
        """Test string representation methods"""
        # The actual string representation uses 'options' not 'value'
        self.assertEqual(str(self.observable), "OS(options={1, 2, 3})")
        self.assertEqual(repr(self.observable), "ObservableSet({1, 2, 3})")
    
    def test_length(self):
        """Test length of the set"""
        self.assertEqual(len(self.observable), 3)
        empty_set = ObservableSet(set())
        self.assertEqual(len(empty_set), 0)
    
    def test_contains(self):
        """Test checking if item is in set"""
        self.assertTrue(2 in self.observable)
        self.assertFalse(99 in self.observable)
    
    def test_iter(self):
        """Test iteration over set items"""
        items = set(self.observable)
        self.assertEqual(items, {1, 2, 3})
    
    def test_equality(self):
        """Test equality comparison"""
        other_set = ObservableSet({1, 2, 3})
        self.assertEqual(self.observable, other_set)
        self.assertEqual(self.observable, {1, 2, 3})
        self.assertNotEqual(self.observable, {1, 2})
    
    def test_inequality(self):
        """Test inequality comparison"""
        other_set = ObservableSet({1, 2, 4})
        self.assertNotEqual(self.observable, other_set)
        self.assertNotEqual(self.observable, {1, 2, 4})
    
    def test_less_than(self):
        """Test less than comparison"""
        self.assertTrue(ObservableSet({1, 2}) < ObservableSet({1, 2, 3}))
        self.assertTrue(ObservableSet({1, 2}) < {1, 2, 3})
        self.assertFalse(ObservableSet({1, 2, 3}) < ObservableSet({1, 2}))
    
    def test_less_equal(self):
        """Test less than or equal comparison"""
        self.assertTrue(ObservableSet({1, 2}) <= ObservableSet({1, 2}))
        self.assertTrue(ObservableSet({1, 2}) <= ObservableSet({1, 2, 3}))
        self.assertTrue(ObservableSet({1, 2}) <= {1, 2})
        self.assertFalse(ObservableSet({1, 2, 3}) <= ObservableSet({1, 2}))
    
    def test_greater_than(self):
        """Test greater than comparison"""
        self.assertTrue(ObservableSet({1, 2, 3}) > ObservableSet({1, 2}))
        self.assertTrue(ObservableSet({1, 2, 3}) > {1, 2})
        self.assertFalse(ObservableSet({1, 2}) > ObservableSet({1, 2, 3}))
    
    def test_greater_equal(self):
        """Test greater than or equal comparison"""
        self.assertTrue(ObservableSet({1, 2}) >= ObservableSet({1, 2}))
        self.assertTrue(ObservableSet({1, 2, 3}) >= ObservableSet({1, 2}))
        self.assertTrue(ObservableSet({1, 2}) >= {1, 2})
        self.assertFalse(ObservableSet({1, 2}) >= ObservableSet({1, 2, 3}))
    
    def test_hash(self):
        """Test hash value"""
        hash1 = hash(self.observable)
        hash2 = hash(ObservableSet({1, 2, 3}))
        self.assertEqual(hash1, hash2)
        
        # Test that hash changes when content changes
        self.observable.add(4)
        hash3 = hash(self.observable)
        self.assertNotEqual(hash1, hash3)
    
    def test_get_observed_component_values(self):
        """Test getting observed component values"""
        values = self.observable.get_observed_component_values()
        # The method returns individual values, not wrapped in a tuple
        self.assertEqual(values, (1, 2, 3))
    
    def test_set_observed_values(self):
        """Test setting observed values"""
        self.observable.set_observed_values(({10, 20, 30},))
        self.assertEqual(self.observable.set_value, {10, 20, 30})
    
    def test_binding_error_handling(self):
        """Test error handling in binding methods"""
        with self.assertRaises(ValueError):
            self.observable.bind_to(None)
    
    def test_unbinding_error_handling(self):
        """Test error handling in unbinding methods"""
        # Test unbinding from something not bound
        other_set = ObservableSet({4, 5, 6})
        with self.assertRaises(ValueError):
            self.observable.unbind_from(other_set)
    
    def test_copy_protection(self):
        """Test that set_value returns a copy"""
        original = self.observable.set_value
        original.add(99)
        self.assertEqual(self.observable.set_value, {1, 2, 3})  # Should not change
        self.assertEqual(original, {1, 2, 3, 99})  # Original should change


if __name__ == '__main__':
    unittest.main()
