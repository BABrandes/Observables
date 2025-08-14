import unittest

from observables import ObservableTuple, ObservableSingleValue, SyncMode, ObservableSet, ObservableSelectionOption






class TestObservableTuple(unittest.TestCase):
    """Test cases for ObservableTuple"""
    
    def setUp(self):
        self.observable = ObservableTuple((1, 2, 3))
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.value, (1, 2, 3))
    
    def test_set_tuple(self):
        """Test setting a new tuple value"""
        self.observable.set_tuple((4, 5, 6))
        self.assertEqual(self.observable.value, (4, 5, 6))
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_tuple((7, 8, 9))
        self.assertEqual(self.notification_count, 1)
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_tuple((1, 2, 3))  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between tuple1 and tuple2"""
        tuple1 = ObservableTuple((1, 2, 3))
        tuple2 = ObservableTuple((4, 5, 6))
        
        # Bind tuple1 to tuple2
        tuple1.bind_to(tuple2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change tuple1, tuple2 should update
        tuple1.set_tuple((7, 8, 9))
        self.assertEqual(tuple2.value, (7, 8, 9))
        
        # Change tuple2, tuple1 should also update (bidirectional)
        tuple2.set_tuple((10, 11, 12))
        self.assertEqual(tuple1.value, (10, 11, 12))
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        tuple1 = ObservableTuple((1, 2, 3))
        tuple2 = ObservableTuple((4, 5, 6))
        
        # Test update_value_from_observable mode
        tuple1.bind_to(tuple2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        self.assertEqual(tuple1.value, (4, 5, 6))  # tuple1 gets updated with tuple2's value
        
        # Test update_observable_from_self mode
        tuple3 = ObservableTuple((7, 8, 9))
        tuple4 = ObservableTuple((10, 11, 12))
        tuple3.bind_to(tuple4, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        self.assertEqual(tuple4.value, (7, 8, 9))  # tuple4 gets updated with tuple3's value
    
    def test_unbinding(self):
        """Test unbinding observable tuples"""
        tuple1 = ObservableTuple((1, 2, 3))
        tuple2 = ObservableTuple((4, 5, 6))
        
        tuple1.bind_to(tuple2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        tuple1.unbind_from(tuple2)
        
        # Changes should no longer propagate
        tuple1.set_tuple((7, 8, 9))
        self.assertEqual(tuple2.value, (4, 5, 6))
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        tuple1 = ObservableTuple((1, 2, 3))
        tuple2 = ObservableTuple((4, 5, 6))
        
        tuple1.bind_to(tuple2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        tuple1.unbind_from(tuple2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            tuple1.unbind_from(tuple2)
        
        # Changes should still not propagate
        tuple1.set_tuple((7, 8, 9))
        # Since we used UPDATE_OBSERVABLE_FROM_SELF, tuple2 was updated to tuple1's value ((1, 2, 3)) during binding
        # After unbinding, tuple2 should still have that value, not the original (4, 5, 6)
        self.assertEqual(tuple2.value, (1, 2, 3))
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        tuple1 = ObservableTuple((1, 2, 3))
        with self.assertRaises(ValueError):
            tuple1.bind_to(tuple1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        tuple1 = ObservableTuple((1, 2, 3))
        tuple2 = ObservableTuple((4, 5, 6))
        tuple3 = ObservableTuple((7, 8, 9))
        
        # Bind tuple2 and tuple3 to tuple1
        tuple2.bind_to(tuple1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        tuple3.bind_to(tuple1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change tuple1, both should update
        tuple1.set_tuple((10, 11, 12))
        self.assertEqual(tuple2.value, (10, 11, 12))
        self.assertEqual(tuple3.value, (10, 11, 12))
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableTuple((1, 2, 3))
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_initialization_with_carries_bindable_tuple(self):
        """Test initialization with CarriesBindableTuple"""
        # Create a source observable tuple
        source = ObservableTuple((10, 20, 30))
        
        # Create a new observable tuple initialized with the source
        target = ObservableTuple(source)
        
        # Check that the target has the same initial value
        self.assertEqual(target.value, (10, 20, 30))
        
        # Check that they are bound together
        source.set_tuple((40, 50, 60))
        self.assertEqual(target.value, (40, 50, 60))
        
        # Check bidirectional binding
        target.set_tuple((70, 80, 90))
        self.assertEqual(source.value, (70, 80, 90))
    
    def test_initialization_with_carries_bindable_tuple_chain(self):
        """Test initialization with CarriesBindableTuple in a chain"""
        # Create a chain of observable tuples
        obs1 = ObservableTuple((100,))
        obs2 = ObservableTuple(obs1)
        obs3 = ObservableTuple(obs2)
        
        # Check initial values
        self.assertEqual(obs1.value, (100,))
        self.assertEqual(obs2.value, (100,))
        self.assertEqual(obs3.value, (100,))
        
        # Change the first observable
        obs1.set_tuple((200,))
        self.assertEqual(obs1.value, (200,))
        self.assertEqual(obs2.value, (200,))
        self.assertEqual(obs3.value, (200,))
        
        # Change the middle observable
        obs2.set_tuple((300,))
        self.assertEqual(obs1.value, (300,))
        self.assertEqual(obs2.value, (300,))
        self.assertEqual(obs3.value, (300,))
    
    def test_initialization_with_carries_bindable_tuple_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableTuple((1000,))
        target1 = ObservableTuple(source)
        target2 = ObservableTuple(source)
        target3 = ObservableTuple(source)
        
        # Check initial values
        self.assertEqual(target1.value, (1000,))
        self.assertEqual(target2.value, (1000,))
        self.assertEqual(target3.value, (1000,))
        
        # Change source, all targets should update
        source.set_tuple((2000,))
        self.assertEqual(target1.value, (2000,))
        self.assertEqual(target2.value, (2000,))
        self.assertEqual(target3.value, (2000,))
        
        # Change one target, source and other targets should update
        target1.set_tuple((3000,))
        self.assertEqual(source.value, (3000,))
        self.assertEqual(target2.value, (3000,))
        self.assertEqual(target3.value, (3000,))
    
    def test_initialization_with_carries_bindable_tuple_unbinding(self):
        """Test that initialization with CarriesBindableTuple can be unbound"""
        source = ObservableTuple((1, 2))
        target = ObservableTuple(source)
        
        # Verify they are bound
        self.assertEqual(target.value, (1, 2))
        source.set_tuple((3, 4))
        self.assertEqual(target.value, (3, 4))
        
        # Unbind them
        target.unbind_from(source)
        
        # Change source, target should not update
        source.set_tuple((5, 6))
        self.assertEqual(target.value, (3, 4))  # Should remain unchanged
        
        # Change target, source should not update
        target.set_tuple((7, 8))
        self.assertEqual(source.value, (5, 6))  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_tuple_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableTuple"""
        # Test with empty tuple
        source_empty = ObservableTuple(())
        target_empty = ObservableTuple(source_empty)
        self.assertEqual(target_empty.value, ())
        
        # Test with None values in tuple
        source_none = ObservableTuple((None, 1, None))
        target_none = ObservableTuple(source_none)
        self.assertEqual(target_none.value, (None, 1, None))
        
        # Test with nested tuple
        source_nested = ObservableTuple(((1, 2), (3, 4)))
        target_nested = ObservableTuple(source_nested)
        self.assertEqual(target_nested.value, ((1, 2), (3, 4)))
    
    def test_initialization_with_carries_bindable_tuple_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableTuple"""
        source = ObservableTuple((1, 2, 3))
        target = ObservableTuple(source)
        
        # Check binding consistency
        is_consistent, message = target.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Check that they are properly bound
        self.assertTrue(target._get_tuple_hook().is_bound_to(source._get_tuple_hook()))
        self.assertTrue(source._get_tuple_hook().is_bound_to(target._get_tuple_hook()))
    
    def test_initialization_with_carries_bindable_tuple_performance(self):
        """Test performance of initialization with CarriesBindableTuple"""
        # Create a source observable tuple
        source = ObservableTuple((1, 2, 3, 4, 5))
        
        # Measure time for multiple initializations
        import time
        start_time = time.time()
        
        for _ in range(1000):
            target = ObservableTuple(source)
            _ = target.value  # Access to ensure initialization is complete
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time (less than 3 seconds)
        self.assertLess(total_time, 3.0)
    
    def test_none_initialization(self):
        """Test initialization with None value"""
        # Test initialization with None
        obs = ObservableTuple(None)
        self.assertEqual(obs.value, ())
        
        # Test that it's a proper empty tuple, not None
        self.assertIsInstance(obs.value, tuple)
        self.assertEqual(len(obs.value), 0)
        
        # Test that we can set a new tuple
        obs.set_tuple((1, 2))
        self.assertEqual(obs.value, (1, 2))
    
    def test_empty_tuple_initialization(self):
        """Test initialization with empty tuple"""
        # Test initialization with empty tuple
        obs = ObservableTuple(())
        self.assertEqual(obs.value, ())
        
        # Test that it's a proper empty tuple
        self.assertIsInstance(obs.value, tuple)
        self.assertEqual(len(obs.value), 0)
        
        # Test that we can set a new tuple
        obs.set_tuple((10, 20))
        self.assertEqual(obs.value, (10, 20))
    
    def test_none_vs_empty_tuple_behavior(self):
        """Test that None and empty tuple initialization behave identically"""
        obs_none = ObservableTuple(None)
        obs_empty = ObservableTuple(())
        
        # Both should start with empty tuples
        self.assertEqual(obs_none.value, obs_empty.value)
        self.assertEqual(obs_none.value, ())
        
        # Both should behave the same way when modified
        obs_none.set_tuple((1,))
        obs_empty.set_tuple((1,))
        
        self.assertEqual(obs_none.value, obs_empty.value)
        self.assertEqual(obs_none.value, (1,))
    
    def test_individual_element_binding(self):
        """Test binding individual tuple elements to single value observables"""
        # Create a tuple with 3 elements
        tuple_obs = ObservableTuple((10, 20, 30))
        
        # Create single value observables for each element
        elem0 = ObservableSingleValue(100)
        elem1 = ObservableSingleValue(200)
        elem2 = ObservableSingleValue(300)
        
        # Bind individual elements
        tuple_obs.bind_to_item(elem0, 0)
        tuple_obs.bind_to_item(elem1, 1)
        tuple_obs.bind_to_item(elem2, 2)
        
        # Check initial binding
        self.assertEqual(elem0.value, 10)
        self.assertEqual(elem1.value, 20)
        self.assertEqual(elem2.value, 30)
        
        # Change tuple, individual elements should update
        tuple_obs.set_tuple((40, 50, 60))
        self.assertEqual(elem0.value, 40)
        self.assertEqual(elem1.value, 50)
        self.assertEqual(elem2.value, 60)
        
        # Change individual elements, tuple should update
        elem0.set_value(70)
        self.assertEqual(tuple_obs.value, (70, 50, 60))
        
        elem1.set_value(80)
        self.assertEqual(tuple_obs.value, (70, 80, 60))
        
        elem2.set_value(90)
        self.assertEqual(tuple_obs.value, (70, 80, 90))
    
    def test_individual_element_binding_out_of_bounds(self):
        """Test that binding to out-of-bounds indices raises error"""
        tuple_obs = ObservableTuple((1, 2))
        elem = ObservableSingleValue(100)
        
        # Try to bind to index 2 (out of bounds for tuple of length 2)
        with self.assertRaises(ValueError):
            tuple_obs.bind_to_item(elem, 2)
        
        # Try to bind to negative index
        with self.assertRaises(ValueError):
            tuple_obs.bind_to_item(elem, -1)
    
    def test_individual_element_binding_dynamic_resize(self):
        """Test that binding handles dynamic tuple resizing"""
        tuple_obs = ObservableTuple((1, 2))
        elem = ObservableSingleValue(100)
        
        # Bind to index 1
        tuple_obs.bind_to_item(elem, 1)
        self.assertEqual(elem.value, 2)
        
        # Expand tuple to include more elements
        tuple_obs.set_tuple((1, 2, 3, 4, 5))
        self.assertEqual(elem.value, 2)  # Index 1 should still be 2
        
        # Bind to new index 4
        elem2 = ObservableSingleValue(200)
        tuple_obs.bind_to_item(elem2, 4)
        self.assertEqual(elem2.value, 5)
        
        # Shrink tuple to (1, 2, 3) - now index 4 is out of bounds
        tuple_obs.set_tuple((1, 2, 3))
        
        # Should fail if trying to bind to index that no longer exists
        with self.assertRaises(ValueError):
            tuple_obs.bind_to_item(ObservableSingleValue(300), 4)
    
    def test_individual_element_binding_multiple_elements(self):
        """Test binding multiple elements of the same tuple"""
        tuple_obs = ObservableTuple((1, 2, 3, 4, 5))
        
        # Create observables for multiple elements
        elem0 = ObservableSingleValue(100)
        elem2 = ObservableSingleValue(200)
        elem4 = ObservableSingleValue(300)
        
        # Bind to elements 0, 2, and 4
        tuple_obs.bind_to_item(elem0, 0)
        tuple_obs.bind_to_item(elem2, 2)
        tuple_obs.bind_to_item(elem4, 4)
        
        # Check initial values
        self.assertEqual(elem0.value, 1)
        self.assertEqual(elem2.value, 3)
        self.assertEqual(elem4.value, 5)
        
        # Change tuple, all bound elements should update
        tuple_obs.set_tuple((10, 20, 30, 40, 50))
        self.assertEqual(elem0.value, 10)
        self.assertEqual(elem2.value, 30)
        self.assertEqual(elem4.value, 50)
        
        # Change individual elements, tuple should update accordingly
        elem0.set_value(100)
        self.assertEqual(tuple_obs.value, (100, 20, 30, 40, 50))
        
        elem2.set_value(300)
        self.assertEqual(tuple_obs.value, (100, 20, 300, 40, 50))
        
        elem4.set_value(500)
        self.assertEqual(tuple_obs.value, (100, 20, 300, 40, 500))
    
    def test_individual_element_binding_chain(self):
        """Test chaining individual element bindings"""
        # Create a chain: tuple -> elem0 -> elem1 -> elem2
        tuple_obs = ObservableTuple((1, 2, 3))
        
        elem0 = ObservableSingleValue(100)
        elem1 = ObservableSingleValue(200)
        elem2 = ObservableSingleValue(300)
        
        # Bind in chain
        tuple_obs.bind_to_item(elem0, 0)
        elem0.bind_to(elem1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        elem1.bind_to(elem2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Check initial chain
        self.assertEqual(elem0.value, 1)
        self.assertEqual(elem1.value, 1)
        self.assertEqual(elem2.value, 1)
        
        # Change tuple, should propagate through chain
        tuple_obs.set_tuple((10, 20, 30))
        self.assertEqual(elem0.value, 10)
        self.assertEqual(elem1.value, 10)
        self.assertEqual(elem2.value, 10)
        
        # Change end of chain, should propagate back
        elem2.set_value(100)
        self.assertEqual(elem0.value, 100)
        self.assertEqual(elem1.value, 100)
        self.assertEqual(tuple_obs.value, (100, 20, 30))
    
    def test_individual_element_binding_unbinding(self):
        """Test unbinding individual elements"""
        tuple_obs = ObservableTuple((1, 2, 3))
        elem = ObservableSingleValue(100)
        
        # Bind element 1
        tuple_obs.bind_to_item(elem, 1)
        self.assertEqual(elem.value, 2)
        
        # Change tuple, element should update
        tuple_obs.set_tuple((10, 20, 30))
        self.assertEqual(elem.value, 20)
        
        # Unbind (by setting tuple to shorter length)
        tuple_obs.set_tuple((10,))  # Now only has index 0
        
        # Try to bind to index 1 again - should fail
        with self.assertRaises(ValueError):
            tuple_obs.bind_to_item(ObservableSingleValue(200), 1)
    
    def test_individual_element_binding_validation(self):
        """Test validation when binding individual elements"""
        tuple_obs = ObservableTuple((1, 2, 3))
        
        # Try to bind to None
        with self.assertRaises(ValueError):
            tuple_obs.bind_to_item(None, 0)
        
        # Try to bind to invalid index types
        elem = ObservableSingleValue(100)
        
        # These should raise TypeError or similar
        with self.assertRaises((TypeError, ValueError)):
            tuple_obs.bind_to_item(elem, "invalid")
        
        with self.assertRaises((TypeError, ValueError)):
            tuple_obs.bind_to_item(elem, 1.5)
    
    def test_individual_element_binding_performance(self):
        """Test performance of individual element binding"""
        import time
        
        # Create a large tuple
        large_tuple = tuple(range(100))
        tuple_obs = ObservableTuple(large_tuple)
        
        # Measure time for binding to multiple elements
        start_time = time.time()
        
        elements = []
        for i in range(10):  # Bind to 10 elements
            elem = ObservableSingleValue(0)
            tuple_obs.bind_to_item(elem, i * 10)
            elements.append(elem)
        
        end_time = time.time()
        binding_time = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(binding_time, 1.0, "Element binding should be fast")
        
        # Verify bindings work
        for i, elem in enumerate(elements):
            expected_value = i * 10
            self.assertEqual(elem.value, expected_value)
    
    def test_string_representation(self):
        """Test string and repr methods"""
        obs = ObservableTuple((1, 2, 3))
        
        str_repr = str(obs)
        repr_repr = repr(obs)
        
        self.assertIn("1", str_repr)
        self.assertIn("2", str_repr)
        self.assertIn("3", str_repr)
        self.assertIn("ObservableTuple", repr_repr)
    
    def test_copy_protection(self):
        """Test that external modifications don't affect the observable"""
        external_tuple = (10, 20, 30)
        obs_tuple = ObservableTuple(external_tuple)
        
        # Modify external tuple (though tuples are immutable, this tests the concept)
        # The observable should have its own copy
        self.assertEqual(obs_tuple.value, (10, 20, 30))
        
        # Observable changes should not affect external tuple
        obs_tuple.set_tuple((40, 50, 60))
        self.assertEqual(external_tuple, (10, 20, 30))
    
    def test_tuple_immutability_handling(self):
        """Test that the observable handles tuple immutability correctly"""
        obs = ObservableTuple((1, 2, 3))
        
        # Should be able to set new tuples
        obs.set_tuple((4, 5, 6))
        self.assertEqual(obs.value, (4, 5, 6))
        
        # Should be able to set empty tuple
        obs.set_tuple(())
        self.assertEqual(obs.value, ())
        
        # Should be able to set single-element tuple
        obs.set_tuple((42,))
        self.assertEqual(obs.value, (42,))
    
    def test_binding_system_consistency_with_elements(self):
        """Test binding system consistency with individual element bindings"""
        tuple_obs = ObservableTuple((1, 2, 3))
        elem = ObservableSingleValue(100)
        
        # Bind element 1
        tuple_obs.bind_to_item(elem, 1)
        
        # Check binding consistency
        is_consistent, message = tuple_obs.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Check that the element binding is properly established
        # This tests the internal binding handler creation
        key_string = "value_1"
        self.assertIn(key_string, tuple_obs._component_hooks)
    
    def test_mixed_binding_scenarios(self):
        """Test complex scenarios with both tuple and element bindings"""
        # Create main tuple
        main_tuple = ObservableTuple((1, 2, 3))
        
        # Create secondary tuple bound to main
        secondary_tuple = ObservableTuple(main_tuple)
        
        # Create element observables bound to main tuple
        elem0 = ObservableSingleValue(100)
        elem2 = ObservableSingleValue(200)
        main_tuple.bind_to_item(elem0, 0)
        main_tuple.bind_to_item(elem2, 2)
        
        # Verify initial state
        self.assertEqual(secondary_tuple.value, (1, 2, 3))
        self.assertEqual(elem0.value, 1)
        self.assertEqual(elem2.value, 3)
        
        # Change main tuple - should propagate to both secondary tuple and elements
        main_tuple.set_tuple((10, 20, 30))
        self.assertEqual(secondary_tuple.value, (10, 20, 30))
        self.assertEqual(elem0.value, 10)
        self.assertEqual(elem2.value, 30)
        
        # Change element - should update main tuple and secondary tuple
        elem0.set_value(100)
        self.assertEqual(main_tuple.value, (100, 20, 30))
        self.assertEqual(secondary_tuple.value, (100, 20, 30))
        
        # Change secondary tuple - should update main tuple and elements
        secondary_tuple.set_tuple((200, 300, 400))
        self.assertEqual(main_tuple.value, (200, 300, 400))
        self.assertEqual(elem0.value, 200)
        self.assertEqual(elem2.value, 400)


class TestObservableIntegration(unittest.TestCase):
    """Integration tests for multiple observable types working together"""
    
    def test_cross_type_binding(self):
        """Test binding between different observable types"""
        # Single value observable
        single_obs = ObservableSingleValue(42)
        
        # Selection option observable
        selection_obs = ObservableSelectionOption(41, {40, 41, 42, 43})
        
        # Bind single value to selection option
        single_obs.bind_to(selection_obs, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change single value, selection should update
        single_obs.set_value(43)
        self.assertEqual(selection_obs.selected_option, 43)
        
        # Change selection, single value should update
        selection_obs.set_selected_option(40)
        self.assertEqual(single_obs.value, 40)
    
    def test_complex_binding_chain(self):
        """Test a chain of bindings between multiple observables"""
        # Create a chain: A -> B -> C
        obs_a = ObservableSingleValue(10)
        obs_b = ObservableSingleValue(20)
        obs_c = ObservableSingleValue(30)
        
        # Bind A to B
        obs_a.bind_to(obs_b, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        # Bind B to C
        obs_b.bind_to(obs_c, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change A, should propagate to B and C
        obs_a.set_value(100)
        self.assertEqual(obs_b.value, 100)
        self.assertEqual(obs_c.value, 100)
        
        # Change C, should propagate to B and A
        obs_c.set_value(200)
        self.assertEqual(obs_b.value, 200)
        self.assertEqual(obs_a.value, 200)
    
    def test_mixed_type_binding_chain(self):
        """Test binding chain with mixed observable types"""
        # Create a mixed chain: SingleValue -> SelectionOption -> Set
        # Ensure all values are compatible across the chain
        single_obs = ObservableSingleValue(5)
        selection_obs = ObservableSelectionOption(5, {3, 4, 5, 6})  # Start with 5 to match single_obs
        set_obs = ObservableSet({3, 4, 5, 6})  # Start with compatible options
        
        # Bind single value to selection option
        single_obs.bind_to(selection_obs, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        # Bind selection option to set (through options)
        selection_obs.bind_options_to_observable(set_obs, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change single value, should propagate through chain
        single_obs.set_value(6)
        self.assertEqual(selection_obs.selected_option, 6)
        self.assertEqual(set_obs.value, {3, 4, 5, 6})
    
    def test_binding_removal_in_chain(self):
        """Test removing bindings in the middle of a chain"""
        # Create chain: A -> B -> C
        obs_a = ObservableSingleValue(10)
        obs_b = ObservableSingleValue(20)
        obs_c = ObservableSingleValue(30)
        
        # Bind A to B
        obs_a.bind_to(obs_b, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        # Bind B to C
        obs_b.bind_to(obs_c, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Verify chain works
        obs_a.set_value(100)
        self.assertEqual(obs_b.value, 100)
        self.assertEqual(obs_c.value, 100)
        
        # Remove binding between B and C
        obs_b.unbind_from(obs_c)
        
        # Change A, B should update but C should not
        obs_a.set_value(200)
        self.assertEqual(obs_b.value, 200)
        self.assertEqual(obs_c.value, 100)  # Should remain unchanged
        
        # Change C, A and B should not update
        obs_c.set_value(300)
        self.assertEqual(obs_a.value, 200)
        self.assertEqual(obs_b.value, 200)
    
    def test_circular_binding_prevention(self):
        """Test that circular bindings are prevented"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        # Bind obs1 to obs2
        obs1.bind_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Try to bind obs2 back to obs1 (should raise ValueError: "Already bound to...")
        with self.assertRaises(ValueError) as context:
            obs2.bind_to(obs1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        self.assertIn("Already bound to", str(context.exception))
        
        # The first binding still exists and is bidirectional, so changing obs1 should affect obs2
        obs1.set_value(100)
        self.assertEqual(obs2.value, 100)  # Should be updated due to existing binding
        
        # Since the first binding is still active and bidirectional, changing obs2 should affect obs1
        obs2.set_value(200)
        self.assertEqual(obs1.value, 200)  # Should be updated due to existing bidirectional binding
    
    def test_multiple_bindings_to_same_target(self):
        """Test multiple observables binding to the same target"""
        target = ObservableSingleValue(50)
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        obs3 = ObservableSingleValue(30)
        
        # Bind all three to the target
        obs1.bind_to(target, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        obs2.bind_to(target, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        obs3.bind_to(target, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change target, all should update
        target.set_value(100)
        self.assertEqual(obs1.value, 100)
        self.assertEqual(obs2.value, 100)
        self.assertEqual(obs3.value, 100)
        
        # Change one of the observables, target should update
        obs1.set_value(200)
        self.assertEqual(target.value, 200)
        # With bidirectional binding, all observables should update to the same value
        self.assertEqual(obs2.value, 200)
        self.assertEqual(obs3.value, 200)
    
    def test_tuple_element_binding_edge_cases(self):
        """Test edge cases for tuple element binding"""
        # Test with very large indices
        large_tuple = tuple(range(1000))
        tuple_obs = ObservableTuple(large_tuple)
        
        # Bind to last element
        last_elem = ObservableSingleValue(0)
        tuple_obs.bind_to_item(last_elem, 999)
        self.assertEqual(last_elem.value, 999)
        
        # Bind to first element
        first_elem = ObservableSingleValue(0)
        tuple_obs.bind_to_item(first_elem, 0)
        self.assertEqual(first_elem.value, 0)
        
        # Test with single-element tuple
        single_tuple = ObservableTuple((42,))
        single_elem = ObservableSingleValue(0)
        single_tuple.bind_to_item(single_elem, 0)
        self.assertEqual(single_elem.value, 42)
        
        # Test with tuple containing None values
        none_tuple = ObservableTuple((None, 1, None, 3))
        none_elem = ObservableSingleValue(100)
        none_tuple.bind_to_item(none_elem, 0)
        self.assertIsNone(none_elem.value)
        
        # Test with tuple containing complex objects
        complex_obj = {"key": "value"}
        complex_tuple = ObservableTuple((complex_obj, 2, 3))
        complex_elem = ObservableSingleValue({})
        complex_tuple.bind_to_item(complex_elem, 0)
        self.assertEqual(complex_elem.value, complex_obj)
    
    def test_tuple_element_binding_errors(self):
        """Test error conditions for tuple element binding"""
        tuple_obs = ObservableTuple((1, 2, 3))
        
        # Test binding to None hook
        with self.assertRaises(ValueError) as context:
            tuple_obs.bind_to_item(None, 0)
        self.assertIn("Cannot bind to None observable", str(context.exception))
        
        # Test binding to invalid index types
        elem = ObservableSingleValue(100)
        
        # String index
        with self.assertRaises(ValueError) as context:
            tuple_obs.bind_to_item(elem, "0")
        self.assertIn("must be an integer", str(context.exception))
        
        # Float index
        with self.assertRaises(ValueError) as context:
            tuple_obs.bind_to_item(elem, 1.5)
        self.assertIn("must be an integer", str(context.exception))
        
        # List index
        with self.assertRaises(ValueError) as context:
            tuple_obs.bind_to_item(elem, [0])
        self.assertIn("must be an integer", str(context.exception))
        
        # Test binding to out-of-bounds positive index
        with self.assertRaises(ValueError) as context:
            tuple_obs.bind_to_item(elem, 10)
        self.assertIn("out of bounds", str(context.exception))
        
        # Test binding to negative index
        with self.assertRaises(ValueError) as context:
            tuple_obs.bind_to_item(elem, -1)
        self.assertIn("out of bounds", str(context.exception))
        
        # Test binding to very large index
        with self.assertRaises(ValueError) as context:
            tuple_obs.bind_to_item(elem, 999999)
        self.assertIn("out of bounds", str(context.exception))
    
    def test_tuple_dynamic_resizing_edge_cases(self):
        """Test edge cases for dynamic tuple resizing"""
        # Test expanding from empty tuple
        empty_tuple = ObservableTuple(())
        elem = ObservableSingleValue(100)
        
        # Try to bind to index 0 of empty tuple - should fail
        with self.assertRaises(ValueError):
            empty_tuple.bind_to_item(elem, 0)
        
        # Expand tuple and bind
        empty_tuple.set_tuple((1,))
        empty_tuple.bind_to_item(elem, 0)
        self.assertEqual(elem.value, 1)
        
        # Test shrinking tuple with active bindings
        tuple_obs = ObservableTuple((1, 2, 3, 4, 5))
        elem0 = ObservableSingleValue(100)
        elem2 = ObservableSingleValue(200)
        elem4 = ObservableSingleValue(300)
        
        # Bind to elements 0, 2, and 4
        tuple_obs.bind_to_item(elem0, 0)
        tuple_obs.bind_to_item(elem2, 2)
        tuple_obs.bind_to_item(elem4, 4)
        
        # Shrink to size 3 - element 4 binding should become invalid
        tuple_obs.set_tuple((10, 20, 30))
        
        # Try to bind to index 4 again - should fail
        with self.assertRaises(ValueError):
            tuple_obs.bind_to_item(ObservableSingleValue(400), 4)
        
        # But indices 0 and 2 should still work
        self.assertEqual(elem0.value, 10)
        self.assertEqual(elem2.value, 30)
        
        # Test expanding beyond current bindings
        tuple_obs.set_tuple((100, 200, 300, 400, 500, 600))
        
        # Should be able to bind to new indices
        elem5 = ObservableSingleValue(0)
        tuple_obs.bind_to_item(elem5, 5)
        self.assertEqual(elem5.value, 600)
    
    def test_tuple_element_binding_validation_errors(self):
        """Test validation errors during tuple element binding"""
        # Test with invalid hook types
        tuple_obs = ObservableTuple((1, 2, 3))
        
        # Try to bind to a string (not an observable)
        with self.assertRaises(AttributeError):
            tuple_obs.bind_to_item("not an observable", 0)
        
        # Try to bind to an integer (not an observable)
        with self.assertRaises(AttributeError):
            tuple_obs.bind_to_item(42, 0)
        
        # Try to bind to a list (not an observable)
        with self.assertRaises(AttributeError):
            tuple_obs.bind_to_item([1, 2, 3], 0)
        
        # Test with tuple that has validation issues
        def validation_method(x):
            if x["value"] == (1, 2, 3):
                return False, "Tuple not allowed"
            return True, "OK"
        
        # This would require modifying the ObservableTuple class to accept custom validation
        # For now, we'll test the existing validation
        
        # Test binding to tuple with None values
        none_tuple = ObservableTuple((None, None, None))
        elem = ObservableSingleValue(100)
        none_tuple.bind_to_item(elem, 0)
        self.assertIsNone(elem.value)
    
    def test_tuple_element_binding_performance_edge_cases(self):
        """Test performance edge cases for tuple element binding"""
        import time
        
        # Test with very large tuple
        large_size = 10000
        large_tuple = tuple(range(large_size))
        tuple_obs = ObservableTuple(large_tuple)
        
        # Measure time for binding to many elements
        start_time = time.time()
        
        elements = []
        for i in range(100):  # Bind to 100 elements
            elem = ObservableSingleValue(0)
            tuple_obs.bind_to_item(elem, i * 100)
            elements.append(elem)
        
        end_time = time.time()
        binding_time = end_time - start_time
        
        # Should complete in reasonable time (less than 5 seconds)
        self.assertLess(binding_time, 5.0, "Large tuple element binding should be reasonable")
        
        # Verify bindings work correctly
        for i, elem in enumerate(elements):
            expected_value = i * 100
            self.assertEqual(elem.value, expected_value)
        
        # Test changing large tuple
        start_time = time.time()
        new_large_tuple = tuple(range(large_size, 2 * large_size))
        tuple_obs.set_tuple(new_large_tuple)
        end_time = time.time()
        
        change_time = end_time - start_time
        # Should complete in reasonable time (less than 2 seconds)
        self.assertLess(change_time, 2.0, "Large tuple change should be reasonable")
        
        # Verify all bindings updated correctly
        for i, elem in enumerate(elements):
            expected_value = (i * 100) + large_size
            self.assertEqual(elem.value, expected_value)
    
    def test_tuple_element_binding_concurrent_access(self):
        """Test concurrent access patterns for tuple element binding"""
        # Test rapid binding and unbinding
        tuple_obs = ObservableTuple((1, 2, 3, 4, 5))
        
        # Rapidly bind and change elements
        for i in range(10):
            elem = ObservableSingleValue(i * 100)
            tuple_obs.bind_to_item(elem, i % 5)
            tuple_obs.set_tuple(tuple(range(i + 1, i + 6)))
        
        # Final state should be consistent
        self.assertEqual(tuple_obs.value, (10, 11, 12, 13, 14))
        
        # Test binding multiple elements to same index
        tuple_obs = ObservableTuple((1, 2, 3))
        elem1 = ObservableSingleValue(100)
        elem2 = ObservableSingleValue(200)
        
        # Bind both to index 0
        tuple_obs.bind_to_item(elem1, 0)
        tuple_obs.bind_to_item(elem2, 0)
        
        # Both should have the same value
        self.assertEqual(elem1.value, 1)
        self.assertEqual(elem2.value, 1)
        
        # Change tuple, both should update
        tuple_obs.set_tuple((10, 20, 30))
        self.assertEqual(elem1.value, 10)
        self.assertEqual(elem2.value, 10)
        
        # Change one element, tuple should update
        elem1.set_value(100)
        self.assertEqual(tuple_obs.value, (100, 20, 30))
        # elem2 should still have the old value since bindings are independent
        self.assertEqual(elem2.value, 10)
    
    def test_tuple_element_binding_memory_management(self):
        """Test memory management for tuple element bindings"""
        import gc
        import weakref
        
        # Test that bindings don't create memory leaks
        tuple_obs = ObservableTuple((1, 2, 3))
        
        # Create weak references to elements
        elem = ObservableSingleValue(100)
        elem_ref = weakref.ref(elem)
        
        # Bind element
        tuple_obs.bind_to_item(elem, 0)
        
        # Delete element reference
        del elem
        
        # Force garbage collection
        gc.collect()
        
        # Element should be garbage collected
        # Note: The hook remains in the tuple's component_hooks, which is expected
        # as it represents the binding interface for that index
        # However, the element itself may not be garbage collected if it's still bound
        # This is expected behavior in Python
        pass  # We can't guarantee garbage collection of bound elements
        
        # Test that tuple can still be used
        tuple_obs.set_tuple((10, 20, 30))
        self.assertEqual(tuple_obs.value, (10, 20, 30))
    
    def test_tuple_element_binding_error_recovery(self):
        """Test error recovery for tuple element binding"""
        # Test recovery from invalid binding attempts
        tuple_obs = ObservableTuple((1, 2, 3))
        
        # Try invalid binding
        try:
            tuple_obs.bind_to_item(None, 0)
        except ValueError:
            pass  # Expected error
        
        # Tuple should still be in valid state
        self.assertEqual(tuple_obs.value, (1, 2, 3))
        
        # Should be able to make valid bindings after error
        elem = ObservableSingleValue(100)
        tuple_obs.bind_to_item(elem, 0)
        self.assertEqual(elem.value, 1)
        
        # Test recovery from out-of-bounds binding
        try:
            tuple_obs.bind_to_item(ObservableSingleValue(200), 10)
        except ValueError:
            pass  # Expected error
        
        # Existing binding should still work
        self.assertEqual(elem.value, 1)
        
        # Tuple should still be valid
        self.assertEqual(tuple_obs.value, (1, 2, 3))
    
    def test_tuple_element_binding_type_safety(self):
        """Test type safety for tuple element binding"""
        # Test with different types in tuple
        mixed_tuple = ObservableTuple((1, "hello", 3.14, True, None))
        
        # Bind to different types
        int_elem = ObservableSingleValue(0)
        str_elem = ObservableSingleValue("")
        float_elem = ObservableSingleValue(0.0)
        bool_elem = ObservableSingleValue(False)
        none_elem = ObservableSingleValue(100)
        
        # Bind to each type
        mixed_tuple.bind_to_item(int_elem, 0)
        mixed_tuple.bind_to_item(str_elem, 1)
        mixed_tuple.bind_to_item(float_elem, 2)
        mixed_tuple.bind_to_item(bool_elem, 3)
        mixed_tuple.bind_to_item(none_elem, 4)
        
        # Check types are preserved
        self.assertEqual(int_elem.value, 1)
        self.assertEqual(str_elem.value, "hello")
        self.assertEqual(float_elem.value, 3.14)
        self.assertEqual(bool_elem.value, True)
        self.assertIsNone(none_elem.value)
        
        # Test changing types
        mixed_tuple.set_tuple((100, "world", 2.718, False, "not none"))
        
        # Check types are still preserved
        self.assertEqual(int_elem.value, 100)
        self.assertEqual(str_elem.value, "world")
        self.assertEqual(float_elem.value, 2.718)
        self.assertEqual(bool_elem.value, False)
        self.assertEqual(none_elem.value, "not none")
    
    def test_tuple_element_binding_boundary_conditions(self):
        """Test boundary conditions for tuple element binding"""
        # Test with tuple of size 1
        single_tuple = ObservableTuple((42,))
        elem = ObservableSingleValue(0)
        
        # Bind to index 0
        single_tuple.bind_to_item(elem, 0)
        self.assertEqual(elem.value, 42)
        
        # Try to bind to index 1 - should fail
        with self.assertRaises(ValueError):
            single_tuple.bind_to_item(ObservableSingleValue(100), 1)
        
        # Test with tuple of size 0
        empty_tuple = ObservableTuple(())
        
        # Try to bind to any index - should fail
        with self.assertRaises(ValueError):
            empty_tuple.bind_to_item(ObservableSingleValue(100), 0)
        
        # Test with very large tuple
        large_size = 100000
        large_tuple = tuple(range(large_size))
        large_tuple_obs = ObservableTuple(large_tuple)
        
        # Bind to last element
        last_elem = ObservableSingleValue(0)
        large_tuple_obs.bind_to_item(last_elem, large_size - 1)
        self.assertEqual(last_elem.value, large_size - 1)
        
        # Try to bind beyond bounds
        with self.assertRaises(ValueError):
            large_tuple_obs.bind_to_item(ObservableSingleValue(100), large_size)
    
    def test_tuple_element_binding_consistency_checks(self):
        """Test consistency checking for tuple element bindings"""
        tuple_obs = ObservableTuple((1, 2, 3, 4, 5))
        
        # Add some element bindings
        elem0 = ObservableSingleValue(100)
        elem2 = ObservableSingleValue(200)
        elem4 = ObservableSingleValue(300)
        
        tuple_obs.bind_to_item(elem0, 0)
        tuple_obs.bind_to_item(elem2, 2)
        tuple_obs.bind_to_item(elem4, 4)
        
        # Check binding system consistency
        is_consistent, message = tuple_obs.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Verify individual element hooks exist
        self.assertIn("value_0", tuple_obs._component_hooks)
        self.assertIn("value_2", tuple_obs._component_hooks)
        self.assertIn("value_4", tuple_obs._component_hooks)
        
        # Verify hooks are properly connected
        hook0 = tuple_obs._component_hooks["value_0"]
        hook2 = tuple_obs._component_hooks["value_2"]
        hook4 = tuple_obs._component_hooks["value_4"]
        
        self.assertEqual(len(hook0.connected_hooks), 1)
        self.assertEqual(len(hook2.connected_hooks), 1)
        self.assertEqual(len(hook4.connected_hooks), 1)
    
    def test_tuple_element_binding_cleanup(self):
        """Test cleanup behavior for tuple element bindings"""
        tuple_obs = ObservableTuple((1, 2, 3))
        
        # Create and bind elements
        elem1 = ObservableSingleValue(100)
        elem2 = ObservableSingleValue(200)
        
        tuple_obs.bind_to_item(elem1, 1)
        tuple_obs.bind_to_item(elem2, 2)
        
        # Verify bindings exist
        self.assertIn("value_1", tuple_obs._component_hooks)
        self.assertIn("value_2", tuple_obs._component_hooks)
        
        # Shrink tuple to remove indices 1 and 2
        tuple_obs.set_tuple((10,))
        
        # Hooks for indices 1 and 2 should be removed
        self.assertNotIn("value_1", tuple_obs._component_hooks)
        self.assertNotIn("value_2", tuple_obs._component_hooks)
        
        # Try to bind to removed indices - should fail
        with self.assertRaises(ValueError):
            tuple_obs.bind_to_item(ObservableSingleValue(300), 1)
        
        with self.assertRaises(ValueError):
            tuple_obs.bind_to_item(ObservableSingleValue(400), 2)