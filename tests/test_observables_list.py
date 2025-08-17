import unittest
from observables import ObservableList
from observables._utils.initial_sync_mode import InitialSyncMode

class TestObservableList(unittest.TestCase):
    """Test cases for ObservableList (concrete implementation)"""
    
    def setUp(self):
        self.observable = ObservableList([1, 2, 3])
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.list_value, [1, 2, 3])
    
    def test_append(self):
        """Test appending a new value"""
        self.observable.append(4)
        self.assertEqual(self.observable.list_value, [1, 2, 3, 4])
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.append(7)
        self.assertEqual(self.notification_count, 1)
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.list_value = [1, 2, 3]  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_listeners(self.notification_callback)
        self.observable.append(10)
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
        self.observable.append(13)
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_initialization_with_carries_bindable_list(self):
        """Test initialization with CarriesBindableList"""
        # Create a source observable list
        source = ObservableList([1, 2, 3])
        
        # Create a new observable list initialized with the source
        target = ObservableList(source)
        
        # Check that the target has the same initial value
        self.assertEqual(target.list_value, [1, 2, 3])
        
        # Check that they are bound together
        source.append(4)
        self.assertEqual(target.list_value, [1, 2, 3, 4])
        
        # Check bidirectional binding
        target.append(5)
        self.assertEqual(source.list_value, [1, 2, 3, 4, 5])
    
    def test_initialization_with_carries_bindable_list_chain(self):
        """Test initialization with CarriesBindableList in a chain"""
        # Create a chain of observable lists
        obs1 = ObservableList([10])
        obs2 = ObservableList(obs1)
        obs3 = ObservableList(obs2)
        
        # Check initial values
        self.assertEqual(obs1.list_value, [10])
        self.assertEqual(obs2.list_value, [10])
        self.assertEqual(obs3.list_value, [10])
        
        # Change the first observable
        obs1.append(20)
        self.assertEqual(obs1.list_value, [10, 20])
        self.assertEqual(obs2.list_value, [10, 20])
        self.assertEqual(obs3.list_value, [10, 20])
        
        # Change the middle observable
        obs2.append(30)
        self.assertEqual(obs1.list_value, [10, 20, 30])
        self.assertEqual(obs2.list_value, [10, 20, 30])
        self.assertEqual(obs3.list_value, [10, 20, 30])
    
    def test_initialization_with_carries_bindable_list_unbinding(self):
        """Test that initialization with CarriesBindableList can be unbound"""
        source = ObservableList([100])
        target = ObservableList(source)
        
        # Verify they are bound
        self.assertEqual(target.list_value, [100])
        source.append(200)
        self.assertEqual(target.list_value, [100, 200])
        
        # Unbind them
        target.detach()
        
        # Change source, target should not update
        source.append(300)
        self.assertEqual(target.list_value, [100, 200])  # Should remain unchanged
        
        # Change target, source should not update
        target.append(400)
        self.assertEqual(source.list_value, [100, 200, 300])  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_list_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableList([100])
        target1 = ObservableList(source)
        target2 = ObservableList(source)
        target3 = ObservableList(source)
        
        # Check initial values
        self.assertEqual(target1.list_value, [100])
        self.assertEqual(target2.list_value, [100])
        self.assertEqual(target3.list_value, [100])
        
        # Change source, all targets should update
        source.append(200)
        self.assertEqual(target1.list_value, [100, 200])
        self.assertEqual(target2.list_value, [100, 200])
        self.assertEqual(target3.list_value, [100, 200])
        
        # Change one target, source and other targets should update
        target1.append(300)
        self.assertEqual(source.list_value, [100, 200, 300])
        self.assertEqual(target2.list_value, [100, 200, 300])
        self.assertEqual(target3.list_value, [100, 200, 300])
    
    def test_initialization_with_carries_bindable_list_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableList"""
        # Test with empty list in source
        source_empty: ObservableList[int] = ObservableList([])
        target_empty = ObservableList(source_empty)
        self.assertEqual(target_empty.list_value, [])
        
        # Test with None in source
        source_none: ObservableList[int] = ObservableList(None)
        target_none = ObservableList(source_none)
        self.assertEqual(target_none.list_value, [])
        
        # Test with single item
        source_single = ObservableList([42])
        target_single = ObservableList(source_single)
        self.assertEqual(target_single.list_value, [42])
    
    def test_initialization_with_carries_bindable_list_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableList"""
        source = ObservableList([100])
        target = ObservableList(source)
        
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        self.assertTrue(target.distinct_list_hook.is_attached_to(source.distinct_list_hook))
        self.assertTrue(source.distinct_list_hook.is_attached_to(target.distinct_list_hook))
    
    def test_initialization_with_carries_bindable_list_performance(self):
        """Test performance of initialization with CarriesBindableList"""
        import time
        
        # Create source
        source = ObservableList([100])
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableList(source)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 6 seconds)
        self.assertLess(end_time - start_time, 6.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableList(source)
        source.append(200)
        self.assertEqual(target.list_value, [100, 200])
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = ObservableList([10])
        obs2 = ObservableList([20])
        
        # Bind obs1 to obs2
        obs1.bind_to(obs2)
        
        # Change obs1, obs2 should update
        obs1.append(30)
        self.assertEqual(obs2.list_value, [20, 30])  # obs1 took obs2's initial value [20]
        
        # Change obs2, obs1 should also update (bidirectional)
        obs2.append(40)
        self.assertEqual(obs1.list_value, [20, 30, 40])  # obs1 took obs2's initial value [20]
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = ObservableList([100])
        obs2 = ObservableList([200])
        
        # Test update_value_from_observable mode
        obs1.bind_to(obs2)
        self.assertEqual(obs1.list_value, [200])  # obs1 gets updated with obs2's value
        
        # Test update_observable_from_self mode
        obs3 = ObservableList([300])
        obs4 = ObservableList([400])
        obs3.bind_to(obs4, InitialSyncMode.SELF_UPDATES)
        self.assertEqual(obs4.list_value, [300])  # obs4 gets updated with obs3's value
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = ObservableList([10])
        obs2 = ObservableList([20])
        
        obs1.bind_to(obs2)
        obs1.detach()
        
        # Changes should no longer propagate
        obs1.append(50)
        self.assertEqual(obs2.list_value, [20])
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableList([10])
        with self.assertRaises(ValueError):
            obs.bind_to(obs)
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = ObservableList([10])
        obs2 = ObservableList([20])
        obs3 = ObservableList([30])
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.bind_to(obs2)
        obs2.bind_to(obs3)
        
        # Verify chain works
        obs1.append(100)
        self.assertEqual(obs2.list_value, [30, 100])  # obs2 took obs3's initial value [30]
        self.assertEqual(obs3.list_value, [30, 100])  # obs3 also gets updated since all three are bound
        
        # Break the chain by unbinding obs2 from obs3
        obs2.detach()
        
        # Change obs1, obs2 should NOT update but obs3 should (obs1 and obs3 remain bound)
        obs1.append(200)
        self.assertEqual(obs2.list_value, [30, 100])  # obs2 is isolated, should not update
        self.assertEqual(obs3.list_value, [30, 100, 200])  # obs3 gets updated since obs1 and obs3 remain bound
        
        # Change obs3, obs1 should update since obs1 and obs3 remain bound after obs2.detach()
        obs3.append(300)
        self.assertEqual(obs1.list_value, [30, 100, 200, 300])  # obs1 took obs3's initial value [30] and remains bound
        self.assertEqual(obs2.list_value, [30, 100])  # obs2 is isolated
    
    def test_string_representation(self):
        """Test string and repr methods"""
        self.assertEqual(str(self.observable), "OL(value=[1, 2, 3])")
        self.assertEqual(repr(self.observable), "ObservableList([1, 2, 3])")
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableList([10])
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = ObservableList([10])
        obs2 = ObservableList([20])
        obs3 = ObservableList([30])
        
        # Bind obs2 and obs3 to obs1
        obs2.bind_to(obs1)
        obs3.bind_to(obs1)
        
        # Change obs1, both should update
        obs1.append(100)
        self.assertEqual(obs2.list_value, [10, 100])
        self.assertEqual(obs3.list_value, [10, 100])
        
        # Change obs2, obs1 should also update (bidirectional), obs3 should also update
        obs2.append(200)
        self.assertEqual(obs1.list_value, [10, 100, 200])  # obs1 keeps its original value [10]
        self.assertEqual(obs3.list_value, [10, 100, 200])  # obs3 also gets updated
    
    def test_list_methods(self):
        """Test standard list methods"""
        obs = ObservableList([1, 2, 3])
        
        # Test append
        obs.append(4)
        self.assertEqual(obs.list_value, [1, 2, 3, 4])
        
        # Test extend
        obs.extend([5, 6])
        self.assertEqual(obs.list_value, [1, 2, 3, 4, 5, 6])
        
        # Test insert
        obs.insert(0, 0)
        self.assertEqual(obs.list_value, [0, 1, 2, 3, 4, 5, 6])
        
        # Test remove
        obs.remove(3)
        self.assertEqual(obs.list_value, [0, 1, 2, 4, 5, 6])
        
        # Test pop
        popped = obs.pop()
        self.assertEqual(popped, 6)
        self.assertEqual(obs.list_value, [0, 1, 2, 4, 5])
        
        # Test clear
        obs.clear()
        self.assertEqual(obs.list_value, [])
    
    def test_list_indexing(self):
        """Test list indexing operations"""
        obs = ObservableList([10, 20, 30, 40, 50])
        
        # Test getitem
        self.assertEqual(obs[0], 10)
        self.assertEqual(obs[-1], 50)
        
        # Test setitem
        obs[2] = 35
        self.assertEqual(obs.list_value, [10, 20, 35, 40, 50])
        
        # Test delitem
        del obs[1]
        self.assertEqual(obs.list_value, [10, 35, 40, 50])
        
        # Test slice operations
        obs[1:3] = [25, 30] # type: ignore
        self.assertEqual(obs.list_value, [10, 25, 30, 50])
    
    def test_list_comparison(self):
        """Test list comparison operations"""
        obs1 = ObservableList([1, 2, 3])
        obs2 = ObservableList([1, 2, 3])
        obs3 = ObservableList([1, 2, 4])
        
        # Test equality
        self.assertEqual(obs1, obs2)
        self.assertNotEqual(obs1, obs3)
        
        # Test comparison with regular lists
        self.assertEqual(obs1, [1, 2, 3])
        self.assertNotEqual(obs1, [1, 2, 4])
    
    def test_list_iteration(self):
        """Test list iteration"""
        obs = ObservableList([1, 2, 3, 4, 5])
        
        # Test iteration
        items = list(obs)
        self.assertEqual(items, [1, 2, 3, 4, 5])
        
        # Test length
        self.assertEqual(len(obs), 5)
        
        # Test contains
        self.assertIn(3, obs)
        self.assertNotIn(6, obs)
    
    def test_list_copy_behavior(self):
        """Test that list_value returns a copy"""
        obs = ObservableList([1, 2, 3])
        
        # Get the list value
        list_copy = obs.list_value
        
        # Modify the copy
        list_copy.append(4)
        
        # Original should not change
        self.assertEqual(obs.list_value, [1, 2, 3])
        
        # The copy should have the modification
        self.assertEqual(list_copy, [1, 2, 3, 4])
    
    def test_list_validation(self):
        """Test list validation"""
        # Test with valid list
        obs = ObservableList([1, 2, 3])
        self.assertEqual(obs.list_value, [1, 2, 3])
        
        # Test with None (should create empty list)
        obs_none: ObservableList[int] = ObservableList(None)
        self.assertEqual(obs_none.list_value, [])
        
        # Test with empty list
        obs_empty: ObservableList[int] = ObservableList([])
        self.assertEqual(obs_empty.list_value, [])
    
    def test_list_binding_edge_cases(self):
        """Test edge cases for list binding"""
        # Test binding empty lists
        obs1: ObservableList[int] = ObservableList([])
        obs2: ObservableList[int] = ObservableList([])
        obs1.bind_to(obs2)
        
        obs1.append(1)
        self.assertEqual(obs2.list_value, [1])
        
        # Test binding lists with same initial values
        obs3 = ObservableList([42])
        obs4 = ObservableList([42])
        obs3.bind_to(obs4)
        
        obs3.append(100)
        self.assertEqual(obs4.list_value, [42, 100])
    
    def test_list_performance(self):
        """Test list performance characteristics"""
        import time
        
        # Test append performance
        obs: ObservableList[int] = ObservableList([])
        start_time = time.time()
        
        for i in range(1000):
            obs.append(i)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Append operations should be fast")
        self.assertEqual(len(obs.list_value), 1000)
        
        # Test binding performance
        source = ObservableList([1, 2, 3])
        start_time = time.time()
        
        for _ in range(100):
            ObservableList(source)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Binding operations should be fast")
    
    def test_list_error_handling(self):
        """Test list error handling"""
        obs = ObservableList([1, 2, 3])
        
        # Test index out of range
        with self.assertRaises(IndexError):
            _ = obs[10]
        
        # Test remove non-existent item (should not raise error, just do nothing)
        obs.remove(99)
        self.assertEqual(obs.list_value, [1, 2, 3])  # Should remain unchanged
        
        # Test pop from empty list
        empty_obs: ObservableList[int] = ObservableList([])
        with self.assertRaises(IndexError):
            empty_obs.pop()
    
    def test_list_binding_consistency(self):
        """Test binding system consistency"""
        source = ObservableList([100])
        target = ObservableList(source)
        
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        self.assertTrue(target.distinct_list_hook.is_attached_to(source.distinct_list_hook))
        self.assertTrue(source.distinct_list_hook.is_attached_to(target.distinct_list_hook))
    
    def test_list_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = ObservableList([10])
        with self.assertRaises(ValueError):
            obs.bind_to(None)  # type: ignore
    
    def test_list_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = ObservableList([42])
        obs2 = ObservableList([42])
        
        obs1.bind_to(obs2)
        # Both should still have the same value
        self.assertEqual(obs1.list_value, [42])
        self.assertEqual(obs2.list_value, [42])
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = ObservableList([10])
        callback = lambda: None
        
        obs.add_listeners(callback, callback)
        self.assertEqual(len(obs.listeners), 1)
        
        obs.add_listeners(callback)
        self.assertEqual(len(obs.listeners), 1)
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = ObservableList([10])
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listeners(callback)
        self.assertEqual(len(obs.listeners), 0)


if __name__ == '__main__':
    unittest.main()
