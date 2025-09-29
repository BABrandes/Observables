import unittest

from observables import ObservableTuple, ObservableSingleValue, ObservableSet, ObservableSelectionOption, InitialSyncMode
from tests.test_base import ObservableTestCase

class TestObservableTuple(ObservableTestCase):
    """Test cases for ObservableTuple"""
    
    def setUp(self):
        super().setUp()
        self.observable = ObservableTuple((1, 2, 3))
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.value, (1, 2, 3))
    
    def test_set_value(self):
        """Test setting a new value"""
        self.observable.value = (4, 5, 6)
        self.assertEqual(self.observable.value, (4, 5, 6))
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.value = (7, 8, 9)
        self.assertEqual(self.notification_count, 1)
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.value = (1, 2, 3)  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_listeners(self.notification_callback)
        self.observable.value = (10, 11, 12)
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
        self.observable.value = (13, 14, 15)
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_initialization_with_carries_bindable_tuple(self):
        """Test initialization with CarriesBindableTuple"""
        # Create a source observable tuple
        source = ObservableTuple((1, 2, 3))
        
        # Create a new observable tuple initialized with the source
        target = ObservableTuple(source.value_hook)
        
        # Check that the target has the same initial value
        self.assertEqual(target.value, (1, 2, 3))
        
        # Check that they are bound together
        source.value = (4, 5, 6)
        self.assertEqual(target.value, (4, 5, 6))
        
        # Check bidirectional binding
        target.value = (7, 8, 9)
        self.assertEqual(source.value, (7, 8, 9))
    
    def test_initialization_with_carries_bindable_tuple_chain(self):
        """Test initialization with CarriesBindableTuple in a chain"""
        # Create a chain of observable tuples
        obs1 = ObservableTuple((10,))
        obs2 = ObservableTuple(obs1.value_hook)
        obs3 = ObservableTuple(obs2.value_hook)
        
        # Check initial values
        self.assertEqual(obs1.value, (10,))
        self.assertEqual(obs2.value, (10,))
        self.assertEqual(obs3.value, (10,))
        
        # Change the first observable
        obs1.value = (20, 30)
        self.assertEqual(obs1.value, (20, 30))
        self.assertEqual(obs2.value, (20, 30))
        self.assertEqual(obs3.value, (20, 30))
        
        # Change the middle observable
        obs2.value = (40, 50, 60)
        self.assertEqual(obs1.value, (40, 50, 60))
        self.assertEqual(obs2.value, (40, 50, 60))
        self.assertEqual(obs3.value, (40, 50, 60))
    
    def test_initialization_with_carries_bindable_tuple_unbinding(self):
        """Test that initialization with CarriesBindableTuple can be unbound"""
        source = ObservableTuple((100,))
        target = ObservableTuple(source.value_hook)
        
        # Verify they are bound
        self.assertEqual(target.value, (100,))
        source.value = (200, 300)
        self.assertEqual(target.value, (200, 300))
        
        # Unbind them
        target.disconnect()
        
        # Change source, target should not update
        source.value = (400, 500)
        self.assertEqual(target.value, (200, 300))  # Should remain unchanged
        
        # Change target, source should not update
        target.value = (600, 700)
        self.assertEqual(source.value, (400, 500))  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_tuple_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableTuple((100,))
        target1 = ObservableTuple(source.value_hook)
        target2 = ObservableTuple(source.value_hook)
        target3 = ObservableTuple(source.value_hook)
        
        # Check initial values
        self.assertEqual(target1.value, (100,))
        self.assertEqual(target2.value, (100,))
        self.assertEqual(target3.value, (100,))
        
        # Change source, all targets should update
        source.value = (200, 300)
        self.assertEqual(target1.value, (200, 300))
        self.assertEqual(target2.value, (200, 300))
        self.assertEqual(target3.value, (200, 300))
        
        # Change one target, source and other targets should update
        target1.value = (400, 500, 600)
        self.assertEqual(source.value, (400, 500, 600))
        self.assertEqual(target2.value, (400, 500, 600))
        self.assertEqual(target3.value, (400, 500, 600))
    
    def test_initialization_with_carries_bindable_tuple_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableTuple"""
        # Test with empty tuple in source
        source_empty = ObservableTuple(())
        target_empty = ObservableTuple(source_empty.value_hook)
        self.assertEqual(target_empty.value, ())
        
        # Test with None in source
        source_none: ObservableTuple[int] = ObservableTuple(None)
        target_none = ObservableTuple(source_none.value_hook)
        self.assertEqual(target_none.value, ())
        
        # Test with single item
        source_single = ObservableTuple((42,))
        target_single = ObservableTuple(source_single.value_hook)
        self.assertEqual(target_single.value, (42,))
    
    def test_initialization_with_carries_bindable_tuple_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableTuple"""
        source = ObservableTuple((100,))
        target = ObservableTuple(source.value_hook)
        
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        self.assertTrue(target.value_hook.is_connected_to(source.value_hook))
        self.assertTrue(source.value_hook.is_connected_to(target.value_hook))
    
    def test_initialization_with_carries_bindable_tuple_performance(self):
        """Test performance of initialization with CarriesBindableTuple"""
        import time
        
        # Create source
        source = ObservableTuple((100,))
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableTuple(source.value_hook)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 6 seconds)
        self.assertLess(end_time - start_time, 6.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableTuple(source.value_hook)
        source.value = (200, 300)
        self.assertEqual(target.value, (200, 300))
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = ObservableTuple((10,))
        obs2 = ObservableTuple((20,))
        
        # Bind obs1 to obs2
        obs1.connect_hook(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        # Change obs1, obs2 should update
        obs1.value = (30, 40)
        self.assertEqual(obs2.value, (30, 40))  # obs2 took obs1's value
        
        # Change obs2, obs1 should also update (bidirectional)
        obs2.value = (50, 60, 70)
        self.assertEqual(obs1.value, (50, 60, 70))
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = ObservableTuple((100,))
        obs2 = ObservableTuple((200,))
        
        # USE_CALLER_VALUE: target (obs2) gets caller's value
        obs1.connect_hook(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        self.assertEqual(obs2.value, (100,))
        
        # Test update_observable_from_self mode
        obs3 = ObservableTuple((300,))
        obs4 = ObservableTuple((400,))
        obs3.connect_hook(obs4.value_hook, "value", InitialSyncMode.USE_TARGET_VALUE)  # type: ignore
        # USE_TARGET_VALUE means caller gets target's value
        self.assertEqual(obs3.value, (400,))
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = ObservableTuple((10,))
        obs2 = ObservableTuple((20,))
        
        obs1.connect_hook(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        obs1.disconnect()
        
        # Changes should no longer propagate
        obs1.value = (50, 60)
        self.assertEqual(obs2.value, (10,))
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableTuple((10,))
        with self.assertRaises(ValueError):
            obs.connect_hook(obs.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = ObservableTuple((10,))
        obs2 = ObservableTuple((20,))
        obs3 = ObservableTuple((30,))
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.connect_hook(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        obs2.connect_hook(obs3.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        # Verify chain works
        obs1.value = (100, 200)
        self.assertEqual(obs2.value, (100, 200))  # obs2 took obs1's value
        self.assertEqual(obs3.value, (100, 200))  # obs3 also gets updated since all three are bound
        
        # Break the chain by unbinding obs2 from obs3
        obs2.disconnect()
        
        # Change obs1, obs2 should NOT update but obs3 should (obs1 and obs3 remain bound)
        obs1.value = (300, 400)
        self.assertEqual(obs2.value, (100, 200))  # obs2 is isolated
        self.assertEqual(obs3.value, (300, 400))  # obs3 gets updated since obs1 and obs3 remain bound
        
        # Change obs3, obs1 should update since obs1 and obs3 remain bound after obs2.disconnect_hook()
        obs3.value = (500, 600)
        self.assertEqual(obs1.value, (500, 600))  # obs1 gets updated since obs1 and obs3 remain bound
        self.assertEqual(obs2.value, (100, 200))  # obs2 is isolated
    
    def test_string_representation(self):
        """Test string and repr methods"""
        self.assertEqual(str(self.observable), "OT(tuple=(1, 2, 3))")
        self.assertEqual(repr(self.observable), "ObservableTuple((1, 2, 3))")
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableTuple((10,))
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = ObservableTuple((10,))
        obs2 = ObservableTuple((20,))
        obs3 = ObservableTuple((30,))
        
        # Bind obs2 and obs3 to obs1
        obs2.connect_hook(obs1.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        obs3.connect_hook(obs1.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        # Change obs1, both should update
        obs1.value = (100, 200)
        self.assertEqual(obs2.value, (100, 200))
        self.assertEqual(obs3.value, (100, 200))
        
        # Change obs2, obs1 should also update (bidirectional), obs3 should also update
        obs2.value = (300, 400, 500)
        self.assertEqual(obs1.value, (300, 400, 500))
        self.assertEqual(obs3.value, (300, 400, 500))
    
    def test_tuple_methods(self):
        """Test standard tuple methods"""
        obs = ObservableTuple((1, 2, 3))
        
        # Test length
        self.assertEqual(len(obs), 3)
        
        # Test indexing
        self.assertEqual(obs[0], 1)
        self.assertEqual(obs[1], 2)
        self.assertEqual(obs[2], 3)
        self.assertEqual(obs[-1], 3)
        
        # Test contains
        self.assertIn(2, obs)
        self.assertNotIn(5, obs)
        
        # Test iteration
        items = list(obs)
        self.assertEqual(items, [1, 2, 3])
    
    def test_tuple_validation(self):
        """Test tuple validation"""
        # Test with valid tuple
        obs = ObservableTuple((1, 2, 3))
        self.assertEqual(obs.value, (1, 2, 3))
        
        # Test with None (should create empty tuple)
        obs_none: ObservableTuple[int] = ObservableTuple(None)
        self.assertEqual(obs_none.value, ())
        
        # Test with empty tuple
        obs_empty: ObservableTuple[int] = ObservableTuple(())
        self.assertEqual(obs_empty.value, ())
    
    def test_tuple_binding_edge_cases(self):
        """Test edge cases for tuple binding"""
        # Test binding empty tuples
        obs1 = ObservableTuple(())
        obs2 = ObservableTuple(())
        obs1.connect_hook(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        obs1.value = (1,)
        self.assertEqual(obs2.value, (1,))
        
        # Test binding tuples with same initial values
        obs3 = ObservableTuple((42,))
        obs4 = ObservableTuple((42,))
        obs3.connect_hook(obs4.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        obs3.value = (100, 200)
        self.assertEqual(obs4.value, (100, 200))
    
    def test_tuple_performance(self):
        """Test tuple performance characteristics"""
        import time
        
        # Test tuple_value performance
        obs = ObservableTuple((1, 2, 3))
        start_time = time.time()
        
        for _ in range(10000):
            _ = obs.value
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Tuple value access should be fast")
        
        # Test binding performance
        source = ObservableTuple((1, 2, 3))
        start_time = time.time()
        
        for _ in range(100):
            ObservableTuple(source.value_hook)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Binding operations should be fast")
    
    def test_tuple_error_handling(self):
        """Test tuple error handling"""
        obs = ObservableTuple((1, 2, 3))
        
        # Test index out of range
        with self.assertRaises(IndexError):
            _ = obs[10]
        
        # Test negative index out of range
        with self.assertRaises(IndexError):
            _ = obs[-10]
    
    def test_tuple_binding_consistency(self):
        """Test binding system consistency"""
        source = ObservableTuple((100,))
        target = ObservableTuple(source.value_hook)
        
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        self.assertTrue(target.value_hook.is_connected_to(source.value_hook))
        self.assertTrue(source.value_hook.is_connected_to(target.value_hook))
    
    def test_tuple_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = ObservableTuple((10,))
        with self.assertRaises(ValueError):
            obs.connect_hook(None, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
    
    def test_tuple_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = ObservableTuple((42,))
        obs2 = ObservableTuple((42,))
        
        obs1.connect_hook(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        # Both should still have the same value
        self.assertEqual(obs1.value, (42,))
        self.assertEqual(obs2.value, (42,))
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = ObservableTuple((10,))
        callback = lambda: None
        
        obs.add_listeners(callback, callback)
        self.assertEqual(len(obs.listeners), 1)
        
        obs.add_listeners(callback)
        self.assertEqual(len(obs.listeners), 1)
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = ObservableTuple((10,))
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listeners(callback)
        self.assertEqual(len(obs.listeners), 0)

if __name__ == '__main__':
    unittest.main()

class TestObservableIntegration(unittest.TestCase):
    """Integration tests for multiple observable types working together"""
    
    def test_cross_type_binding(self):
        """Test binding between different observable types"""
        # Single value observable
        single_obs: ObservableSingleValue[int|None] = ObservableSingleValue(42)

        # Selection option observable
        selection_obs: ObservableSelectionOption[int|None] = ObservableSelectionOption(41, {40, 41, 42, 43})
        
        # Bind single value to selection option
        single_obs.connect_hook(selection_obs.selected_option_hook, "value", InitialSyncMode.USE_CALLER_VALUE) # type: ignore
        
        # Change single value, selection should update
        single_obs.value = 43
        self.assertEqual(selection_obs.selected_option, 43)
        
        # Change selection, single value should update
        selection_obs.selected_option = 40
        self.assertEqual(single_obs.value, 40)
    
    def test_complex_binding_chain(self):
        """Test a chain of bindings between multiple observables"""
        # Create a chain: A -> B -> C
        obs_a = ObservableSingleValue(10)
        obs_b = ObservableSingleValue(20)
        obs_c = ObservableSingleValue(30)
        
        # Bind A to B
        obs_a.connect_hook(obs_b.hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        # Bind B to C
        obs_b.connect_hook(obs_c.hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        # Change A, should propagate to B and C
        obs_a.value = 100
        self.assertEqual(obs_b.value, 100)
        self.assertEqual(obs_c.value, 100)
        
        # Change C, should propagate to B and A
        obs_c.value = 200
        self.assertEqual(obs_b.value, 200)
        self.assertEqual(obs_a.value, 200)
    
    def test_mixed_type_binding_chain(self):
        """Test binding chain with mixed observable types"""
        # Create a mixed chain: SingleValue -> SelectionOption -> Set
        # Ensure all values are compatible across the chain
        single_obs: ObservableSingleValue[int|None] = ObservableSingleValue(5)
        selection_obs: ObservableSelectionOption[int|None] = ObservableSelectionOption(5, {3, 4, 5, 6})  # Start with 5 to match single_obs
        set_obs: ObservableSet[int|None] = ObservableSet({3, 4, 5, 6})  # Start with compatible options
        
        # Bind single value to selection option
        single_obs.connect_hook(selection_obs.selected_option_hook, "value", InitialSyncMode.USE_CALLER_VALUE) # type: ignore
        # Bind selection option to set (through options)
        selection_obs.connect_hook(set_obs.value_hook, "available_options", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        # Change single value, should propagate through chain
        single_obs.value = (6)
        self.assertEqual(selection_obs.selected_option, 6)
        self.assertEqual(set_obs.value, {3, 4, 5, 6})
    
    def test_binding_removal_in_chain(self):
        """Test removing bindings in the middle of a chain"""
        # Create chain: A -> B -> C
        obs_a = ObservableSingleValue(10)
        obs_b = ObservableSingleValue(20)
        obs_c = ObservableSingleValue(30)
        
        # Bind A to B
        obs_a.connect_hook(obs_b.hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        # Bind B to C
        obs_b.connect_hook(obs_c.hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        # Verify chain works
        obs_a.value = 100
        self.assertEqual(obs_b.value, 100)
        self.assertEqual(obs_c.value, 100)
        
        # Remove binding between B and C
        obs_b.disconnect()
        
        # Change A, B should NOT update (obs_b is now detached from everything)
        # But obs_c should update because obs_a and obs_c are still bound (transitive binding)
        obs_a.value = 200
        self.assertEqual(obs_b.value, 100)  # Should remain unchanged
        self.assertEqual(obs_c.value, 200)  # Should update due to transitive binding
        
        # Change C, obs_a should update (transitive binding), obs_b should not
        obs_c.value = 300
        self.assertEqual(obs_a.value, 300)  # Should update due to transitive binding
        self.assertEqual(obs_b.value, 100)  # Should remain unchanged
    
    def test_circular_binding_prevention(self):
        """Test that circular bindings are prevented"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        # Bind obs1 to obs2
        obs1.connect_hook(obs2.hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        # Try to bind obs2 back to obs1 (should raise ValueError about hook groups not being disjoint)
        with self.assertRaises(ValueError) as context:
            obs2.connect_hook(obs1.hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        self.assertIn("hook groups must be disjoint", str(context.exception))
        
        # The first binding still exists and is bidirectional, so changing obs1 should affect obs2
        obs1.value = 100
        self.assertEqual(obs2.value, 100)  # Should be updated due to existing binding
        
        # Since the first binding is still active and bidirectional, changing obs2 should affect obs1
        obs2.value = 200
        self.assertEqual(obs1.value, 200)  # Should be updated due to existing bidirectional binding
    
    def test_multiple_bindings_to_same_target(self):
        """Test multiple observables binding to the same target"""
        target = ObservableSingleValue(50)
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        obs3 = ObservableSingleValue(30)
        
        # Bind all three to the target
        obs1.connect_hook(target.hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        obs2.connect_hook(target.hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        obs3.connect_hook(target.hook, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        # Change target, all should update
        target.value = 100
        self.assertEqual(obs1.value, 100)
        self.assertEqual(obs2.value, 100)
        self.assertEqual(obs3.value, 100)
        
        # Change one of the observables, target should update
        obs1.value = 200
        self.assertEqual(target.value, 200)  
        # With bidirectional binding, all observables should update to the same value
        self.assertEqual(obs2.value, 200)
        self.assertEqual(obs3.value, 200)
    

    

    

    
    


    

    
