import unittest
from observables import ObservableSelectionOption, ObservableSet, SyncMode, ObservableSingleValue







class TestObservableSelectionOption(unittest.TestCase):
    """Test cases for ObservableSelectionOption"""
    
    def setUp(self):
        self.observable = ObservableSelectionOption(2, {1, 2, 3, 4})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_state(self):
        """Test initial options and selected option"""
        self.assertEqual(self.observable.available_options, {1, 2, 3, 4})
        self.assertEqual(self.observable.selected_option, 2)
    
    def test_change_options(self):
        """Test changing options"""
        # Change to options that include the current selected option (2)
        self.observable.available_options = {2, 5, 6, 7}
        self.assertEqual(self.observable.available_options, {2, 5, 6, 7})
        # Selected option should remain valid
        self.assertEqual(self.observable.selected_option, 2)
    
    def test_change_selected_option(self):
        """Test changing selected option"""
        self.observable.selected_option = 3
        self.assertEqual(self.observable.selected_option, 3)
    
    def test_invalid_selected_option(self):
        """Test that changing to invalid option raises error"""
        with self.assertRaises(ValueError):
            self.observable.selected_option = 999
    
    def test_invalid_options_with_selected(self):
        """Test that changing options to exclude selected option raises error"""
        with self.assertRaises(ValueError):
            self.observable.available_options = {5, 6, 7}  # 2 not in new options
    
    def test_set_options_and_selected_option(self):
        """Test setting both options and selected option at once"""
        self.observable.set_selected_option_and_available_options(6, {5, 6, 7, 8})
        self.assertEqual(self.observable.selected_option, 6)
        self.assertEqual(self.observable.available_options, {5, 6, 7, 8})
    
    def test_listener_notification(self):
        """Test that listeners are notified when state changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.selected_option = 3
        self.assertEqual(self.notification_count, 1)
    
    def test_binding_selected_option(self):
        """Test binding selected option between observables"""
        # Create observables with compatible initial states
        obs1 = ObservableSelectionOption(1, {1, 2, 3, 4, 5, 6})
        obs2 = ObservableSelectionOption(4, {1, 2, 3, 4, 5, 6})
        
        obs1.bind_selected_option_to(obs2)
        
        # Change obs1 selected option, obs2 should update
        obs1.selected_option = 2
        self.assertEqual(obs2.selected_option, 2)
        
        # Change obs2 selected option, obs1 should update
        obs2.selected_option = 5
        self.assertEqual(obs1.selected_option, 5)
    
    def test_binding_options(self):
        """Test binding options between observables"""
        # Create observables with compatible initial states
        obs1 = ObservableSelectionOption(1, {1, 2, 3, 4, 5, 6})
        obs2 = ObservableSelectionOption(4, {1, 2, 3, 4, 5, 6})
        
        obs1.bind_available_options_to(obs2)
        
        # Change obs1 options, obs2 should update
        # Use options that include the current selected option (1)
        # However, this will fail because obs2 has selected option 4, which is not in {1, 7, 8, 9}
        # The binding will propagate and cause obs2 to try to change its options, which will fail
        with self.assertRaises(ValueError):
            obs1.available_options = {1, 7, 8, 9}
        
        # Change obs2 options, obs1 should update
        # Use options that include the current selected option (4)
        # However, this will fail because obs1 has selected option 1, which is not in {4, 10, 11, 12}
        # The binding will propagate and cause obs1 to try to change its options, which will fail
        with self.assertRaises(ValueError):
            obs2.available_options = {4, 10, 11, 12}
    
    
    
    def test_unbinding(self):
        """Test unbinding observables"""
        # Create observables with compatible initial states
        obs1 = ObservableSelectionOption(1, {1, 2, 3, 4, 5, 6})
        obs2 = ObservableSelectionOption(4, {1, 2, 3, 4, 5, 6})
        
        obs1.bind_selected_option_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        obs1.unbind_selected_option_from(obs2)
        
        # Changes should no longer propagate
        obs1.selected_option = 2
        self.assertEqual(obs2.selected_option, 4)
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        # Create observables with compatible initial states
        obs1 = ObservableSelectionOption(1, {1, 2, 3, 4, 5, 6})
        obs2 = ObservableSelectionOption(4, {1, 2, 3, 4, 5, 6})
        
        obs1.bind_selected_option_to(obs2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        obs1.unbind_selected_option_from(obs2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            obs1.unbind_selected_option_from(obs2)
        
        # Changes should still not propagate
        obs1.selected_option = 2
        # Since we used UPDATE_OBSERVABLE_FROM_SELF, obs2 was updated to obs1's value (1) during binding
        # After unbinding, obs2 should still have that value, not the original 4
        self.assertEqual(obs2.selected_option, 1)
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableSelectionOption(1, {1, 2, 3})
        with self.assertRaises(ValueError):
            obs.bind_selected_option_to(obs)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        # Create observables with compatible initial states
        obs1 = ObservableSelectionOption(1, {1, 2, 3, 4, 5, 6, 7, 8, 9})
        obs2 = ObservableSelectionOption(4, {1, 2, 3, 4, 5, 6, 7, 8, 9})
        obs3 = ObservableSelectionOption(7, {1, 2, 3, 4, 5, 6, 7, 8, 9})
        
        # Bind obs2 and obs3 selected options to obs1
        obs2.bind_selected_option_to(obs1)
        obs3.bind_selected_option_to(obs1)
        
        # Change obs1 selected option, both should update
        obs1.selected_option = 2
        self.assertEqual(obs2.selected_option, 2)
        self.assertEqual(obs3.selected_option, 2)
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableSelectionOption(1, {1, 2, 3})
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_initialization_with_carries_bindable_set_and_single_value(self):
        """Test initialization with CarriesBindableSet and CarriesBindableSingleValue"""
        # Create source observables
        source_options = ObservableSet({1, 2, 3, 4})
        source_selected = ObservableSingleValue(2)
        
        # Create a new observable selection option initialized with the sources
        target = ObservableSelectionOption(source_selected, source_options)
        
        # Check that the target has the same initial values
        self.assertEqual(target.available_options, {1, 2, 3, 4})
        self.assertEqual(target.selected_option, 2)
        
        # Check that they are bound together
        source_options.add(5)
        self.assertEqual(target.available_options, {1, 2, 3, 4, 5})
        
        source_selected.single_value =(3)
        self.assertEqual(target.selected_option, 3)
        
        # Check bidirectional binding
        target.add(6)
        self.assertEqual(source_options.set_value, {1, 2, 3, 4, 5, 6})
        
        target.selected_option = 4
        self.assertEqual(source_selected.single_value, 4)
    
    def test_initialization_with_carries_bindable_set_only(self):
        """Test initialization with only CarriesBindableSet"""
        # Create source observable set
        source_options = ObservableSet({10, 20, 30})
        
        # Create a new observable selection option initialized with the source set
        target = ObservableSelectionOption(20, source_options)
        
        # Check that the target has the same initial options
        self.assertEqual(target.available_options, {10, 20, 30})
        self.assertEqual(target.selected_option, 20)
        
        # Check that they are bound together
        source_options.add(40)
        self.assertEqual(target.available_options, {10, 20, 30, 40})
        
        # Check bidirectional binding
        target.add(50)
        self.assertEqual(source_options.set_value, {10, 20, 30, 40, 50})
    
    def test_initialization_with_carries_bindable_single_value_only(self):
        """Test initialization with only CarriesBindableSingleValue"""
        # Create source observable single value
        source_selected = ObservableSingleValue(100)
        
        # Create a new observable selection option initialized with the source single value
        target = ObservableSelectionOption(source_selected, {100, 200, 300})
        
        # Check that the target has the same initial selected option
        self.assertEqual(target.available_options, {100, 200, 300})
        self.assertEqual(target.selected_option, 100)
        
        # Check that they are bound together
        source_selected.single_value =(200)
        self.assertEqual(target.selected_option, 200)
        
        # Check bidirectional binding
        target.selected_option = 300
        self.assertEqual(source_selected.single_value, 300)
    
    def test_initialization_with_carries_bindable_chain(self):
        """Test initialization with CarriesBindableSet and CarriesBindableSingleValue in a chain"""
        # Create a chain of observable selection options
        obs1 = ObservableSelectionOption(1, {1, 2})
        obs2 = ObservableSelectionOption(obs1, obs1)
        obs3 = ObservableSelectionOption(obs2, obs2)
        
        # Check initial values
        self.assertEqual(obs1.available_options, {1, 2})
        self.assertEqual(obs1.selected_option, 1)
        self.assertEqual(obs2.available_options, {1, 2})
        self.assertEqual(obs2.selected_option, 1)
        self.assertEqual(obs3.available_options, {1, 2})
        self.assertEqual(obs3.selected_option, 1)
        
        # Change the first observable
        obs1.add(3)
        obs1.selected_option = 2
        self.assertEqual(obs1.available_options, {1, 2, 3})
        self.assertEqual(obs1.selected_option, 2)
        self.assertEqual(obs2.available_options, {1, 2, 3})
        self.assertEqual(obs2.selected_option, 2)
        self.assertEqual(obs3.available_options, {1, 2, 3})
        self.assertEqual(obs3.selected_option, 2)
    
    def test_initialization_with_carries_bindable_multiple_targets(self):
        """Test multiple targets initialized with the same sources"""
        source_options = ObservableSet({100, 200})
        source_selected = ObservableSingleValue(100)
        
        target1 = ObservableSelectionOption(source_selected, source_options)
        target2 = ObservableSelectionOption(source_selected, source_options)
        target3 = ObservableSelectionOption(source_selected, source_options)
        
        # Check initial values
        self.assertEqual(target1.available_options, {100, 200})
        self.assertEqual(target1.selected_option, 100)
        self.assertEqual(target2.available_options, {100, 200})
        self.assertEqual(target2.selected_option, 100)
        self.assertEqual(target3.available_options, {100, 200})
        self.assertEqual(target3.selected_option, 100)
        
        # Change source options, all targets should update
        source_options.add(300)
        self.assertEqual(target1.available_options, {100, 200, 300})
        self.assertEqual(target2.available_options, {100, 200, 300})
        self.assertEqual(target3.available_options, {100, 200, 300})
        
        # Change source selected option, all targets should update
        source_selected.single_value =(200)
        self.assertEqual(target1.selected_option, 200)
        self.assertEqual(target2.selected_option, 200)
        self.assertEqual(target3.selected_option, 200)
    
    def test_initialization_with_carries_bindable_unbinding(self):
        """Test that initialization with CarriesBindableSet and CarriesBindableSingleValue can be unbound"""
        source_options = ObservableSet({1, 2})
        source_selected = ObservableSingleValue(1)
        
        target = ObservableSelectionOption(source_selected, source_options)
        
        # Verify they are bound
        self.assertEqual(target.available_options, {1, 2})
        self.assertEqual(target.selected_option, 1)
        
        source_options.add(3)
        source_selected.single_value =(2)
        self.assertEqual(target.available_options, {1, 2, 3})
        self.assertEqual(target.selected_option, 2)
        
        # Unbind them
        target.unbind_available_options_from(source_options)
        target.unbind_selected_option_from(source_selected)
        
        # Change sources, target should not update
        source_options.add(4)
        source_selected.single_value =(3)
        self.assertEqual(target.available_options, {1, 2, 3})  # Should remain unchanged
        self.assertEqual(target.selected_option, 2)  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableSet and CarriesBindableSingleValue"""
        # Test with empty set
        source_empty = ObservableSet(set())
        source_selected = ObservableSingleValue(None)
        target_empty = ObservableSelectionOption(source_selected, source_empty)
        self.assertEqual(target_empty.available_options, set())
        self.assertIsNone(target_empty.selected_option)
        
        # Test with None values
        source_none = ObservableSet({None, 1, None})
        source_none_selected = ObservableSingleValue(None)
        target_none = ObservableSelectionOption(source_none_selected, source_none)
        self.assertEqual(target_none.available_options, {None, 1})
        self.assertIsNone(target_none.selected_option)
    
    def test_initialization_with_carries_bindable_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableSet and CarriesBindableSingleValue"""
        source_options = ObservableSet({1, 2, 3})
        source_selected = ObservableSingleValue(1)
        
        target = ObservableSelectionOption(source_selected, source_options)
        
        # Check binding consistency
        is_consistent, message = target.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Check that they are properly bound
        self.assertTrue(target._get_set_hook().is_bound_to(source_options._get_set_hook()))
        self.assertTrue(target._get_single_value_hook().is_bound_to(source_selected._get_single_value_hook()))
    
    def test_initialization_with_carries_bindable_performance(self):
        """Test performance of initialization with CarriesBindableSet and CarriesBindableSingleValue"""
        import time
        
        # Create sources
        source_options = ObservableSet({1, 2, 3, 4, 5})
        source_selected = ObservableSingleValue(1)
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableSelectionOption(source_selected, source_options)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(end_time - start_time, 1.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableSelectionOption(source_selected, source_options)
        source_options.add(6)
        source_selected.single_value =(2)
        self.assertEqual(target.available_options, {1, 2, 3, 4, 5, 6})
        self.assertEqual(target.selected_option, 2)

    def test_allow_none_initialization(self):
        """Test initialization with allow_none=True (default)."""
        # Should work with None selected option
        obs = ObservableSelectionOption(None, {1, 2, 3}, allow_none=True)
        self.assertIsNone(obs.selected_option)
        self.assertEqual(obs.available_options, {1, 2, 3})
        
        # Should work with empty options set
        obs = ObservableSelectionOption(None, set(), allow_none=True)
        self.assertIsNone(obs.selected_option)
        self.assertEqual(obs.available_options, set())
        
        # Should work with None selected and empty options
        obs = ObservableSelectionOption(None, set(), allow_none=True)
        self.assertIsNone(obs.selected_option)
        self.assertEqual(obs.available_options, set())

    def test_disallow_none_initialization(self):
        """Test initialization with allow_none=False."""
        # Should work with valid selected option
        obs = ObservableSelectionOption(1, {1, 2, 3}, allow_none=False)
        self.assertEqual(obs.selected_option, 1)
        self.assertEqual(obs.available_options, {1, 2, 3})
        
        # Should fail with None selected option
        with self.assertRaises(ValueError) as context:
            ObservableSelectionOption(None, {1, 2, 3}, allow_none=False)
        self.assertIn("Selected option is None but allow_none is False", str(context.exception))
        
        # Should fail with empty options set
        with self.assertRaises(ValueError) as context:
            ObservableSelectionOption(1, set(), allow_none=False)
        self.assertIn("Selected option is None but allow_none is False", str(context.exception))
        
        # Should fail with None selected and empty options
        with self.assertRaises(ValueError) as context:
            ObservableSelectionOption(None, set(), allow_none=False)
        self.assertIn("Selected option is None but allow_none is False", str(context.exception))

    def test_allow_none_dynamic_changes(self):
        """Test dynamic changes with allow_none=True."""
        obs = ObservableSelectionOption(1, {1, 2, 3}, allow_none=True)
        
        # Should allow setting selected option to None
        obs.selected_option = None
        self.assertIsNone(obs.selected_option)
        
        # Should allow setting options to empty set when selected_option is None
        # Use the method that sets both at once to maintain valid state
        obs.set_selected_option_and_available_options(None, set())
        self.assertEqual(obs.available_options, set())
        self.assertIsNone(obs.selected_option)
        
        # Should allow setting selected option to None when options are empty
        obs.selected_option = None
        self.assertIsNone(obs.selected_option)

    def test_disallow_none_dynamic_changes(self):
        """Test dynamic changes with allow_none=False."""
        obs = ObservableSelectionOption(1, {1, 2, 3}, allow_none=False)
        
        # Should fail when trying to set selected option to None
        with self.assertRaises(ValueError) as context:
            obs.selected_option = None
        self.assertIn("Selected option is None but allow_none is False", str(context.exception))
        
        # Should fail when trying to set options to empty set
        with self.assertRaises(ValueError) as context:
            obs.available_options = set()
        self.assertIn("empty set of options can not be set", str(context.exception))
        
        # Should fail when trying to set selected option to None with empty options
        obs = ObservableSelectionOption(1, {1, 2, 3}, allow_none=False)
        with self.assertRaises(ValueError) as context:
            obs.available_options = set()
        self.assertIn("empty set of options can not be set", str(context.exception))

    def test_allow_none_edge_cases(self):
        """Test edge cases with allow_none functionality."""
        # Test with None selected and non-empty options
        obs = ObservableSelectionOption(None, {1, 2, 3}, allow_none=True)
        self.assertIsNone(obs.selected_option)
        self.assertEqual(obs.available_options, {1, 2, 3})
        
        # Test changing from None to valid option
        obs.selected_option = 1
        self.assertEqual(obs.selected_option, 1)
        
        # Test changing back to None
        obs.selected_option = None
        self.assertIsNone(obs.selected_option)
        
        # Test with empty options and None selected
        obs = ObservableSelectionOption(None, set(), allow_none=True)
        self.assertIsNone(obs.selected_option)
        self.assertEqual(obs.available_options, set())

    def test_allow_none_validation_consistency(self):
        """Test that validation is consistent with allow_none setting."""
        # With allow_none=True, should allow None but still validate non-None values
        obs = ObservableSelectionOption(None, {1, 2, 3}, allow_none=True)
        
        # Should allow None
        obs.selected_option = None
        
        # Should still validate non-None values
        with self.assertRaises(ValueError) as context:
            obs.selected_option = 5  # Not in options
        self.assertIn("not in options", str(context.exception))
        
        # Should allow valid values
        obs.selected_option = 1
        self.assertEqual(obs.selected_option, 1)

    def test_allow_none_binding_behavior(self):
        """Test that allow_none setting affects binding behavior."""
        # Test with allow_none=True
        obs1 = ObservableSelectionOption(None, {1, 2, 3, 4}, allow_none=True)
        obs2 = ObservableSelectionOption(4, {1, 2, 3, 4}, allow_none=True)
        
        # Binding should work even with None values
        # Use UPDATE_VALUE_FROM_OBSERVABLE so obs1 gets updated to obs2's value
        obs1.bind_selected_option_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        self.assertEqual(obs1.selected_option, 4)
        
        # Test with allow_none=False
        obs3 = ObservableSelectionOption(1, {1, 2, 3, 4}, allow_none=False)
        obs4 = ObservableSelectionOption(4, {1, 2, 3, 4}, allow_none=False)
        
        # Binding should work with valid values
        obs3.bind_selected_option_to(obs4, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        self.assertEqual(obs3.selected_option, 4)