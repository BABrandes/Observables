import unittest
from observables import ObservableSelectionOption, InitialSyncMode

class TestObservableSelectionOption(unittest.TestCase):
    """Test cases for ObservableSelectionOption"""
    
    def setUp(self):
        self.observable = ObservableSelectionOption("Apple", {"Apple", "Banana", "Cherry"})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.selected_option, "Apple")
        self.assertEqual(self.observable.available_options, {"Apple", "Banana", "Cherry"})
    
    def test_set_selected_option(self):
        """Test setting a new selected option"""
        self.observable.selected_option = "Banana"
        self.assertEqual(self.observable.selected_option, "Banana")
    
    def test_set_available_options(self):
        """Test setting new available options"""
        new_options = {"Apple", "Orange", "Grape"}
        self.observable.available_options = new_options
        self.assertEqual(self.observable.available_options, new_options)
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.selected_option = "Cherry"
        self.assertEqual(self.notification_count, 1)
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.selected_option = "Apple"  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_listeners(self.notification_callback)
        self.observable.selected_option = "Banana"
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
        self.observable.selected_option = "Cherry"
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_initialization_with_carries_bindable_selection_option(self):
        """Test initialization with CarriesBindableSelectionOption"""
        # Create a source observable selection option
        source = ObservableSelectionOption("Red", {"Red", "Green", "Blue"})
        
        # Create a new observable selection option initialized with the source
        target = ObservableSelectionOption(source)
        
        # Check that the target has the same initial value
        self.assertEqual(target.selected_option, "Red")
        self.assertEqual(target.available_options, {"Red", "Green", "Blue"})
        
        # Check that they are bound together
        source.selected_option = "Green"
        self.assertEqual(target.selected_option, "Green")
        
        # Check bidirectional binding
        target.selected_option = "Blue"
        self.assertEqual(source.selected_option, "Blue")
    
    def test_initialization_with_carries_bindable_selection_option_chain(self):
        """Test initialization with CarriesBindableSelectionOption in a chain"""
        # Create a chain of observable selection options
        obs1 = ObservableSelectionOption("Small", {"Small", "Medium"})
        obs2 = ObservableSelectionOption(obs1)
        obs3 = ObservableSelectionOption(obs2)
        
        # Check initial values
        self.assertEqual(obs1.selected_option, "Small")
        self.assertEqual(obs2.selected_option, "Small")
        self.assertEqual(obs3.selected_option, "Small")
        
        # Change the first observable
        obs1.selected_option = "Medium"
        self.assertEqual(obs1.selected_option, "Medium")
        self.assertEqual(obs2.selected_option, "Medium")
        self.assertEqual(obs3.selected_option, "Medium")
        
        # Change the middle observable
        obs2.selected_option = "Small"
        self.assertEqual(obs1.selected_option, "Small")
        self.assertEqual(obs2.selected_option, "Small")
        self.assertEqual(obs3.selected_option, "Small")
    
    def test_initialization_with_carries_bindable_selection_option_unbinding(self):
        """Test that initialization with CarriesBindableSelectionOption can be unbound"""
        source = ObservableSelectionOption("Red", {"Red", "Green"})
        target = ObservableSelectionOption(source)
        
        # Verify they are bound
        self.assertEqual(target.selected_option, "Red")
        source.selected_option = "Green"
        self.assertEqual(target.selected_option, "Green")
        
        # Unbind them
        target.detach()
        
        # Change source, target should not update
        # Note: source can only use its own available options {"Red", "Green"}
        source.selected_option = "Red"  # Use an option that exists in source's options
        self.assertEqual(target.selected_option, "Green")  # Should remain unchanged
        
        # Change target, source should not update
        target.selected_option = "Red"
        self.assertEqual(source.selected_option, "Red")  # Should remain at last set value
    
    def test_initialization_with_carries_bindable_selection_option_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableSelectionOption("Red", {"Red", "Green"})
        target1 = ObservableSelectionOption(source)
        target2 = ObservableSelectionOption(source)
        target3 = ObservableSelectionOption(source)
        
        # Check initial values
        self.assertEqual(target1.selected_option, "Red")
        self.assertEqual(target2.selected_option, "Red")
        self.assertEqual(target3.selected_option, "Red")
        
        # Change source, all targets should update
        source.selected_option = "Green"
        self.assertEqual(target1.selected_option, "Green")
        self.assertEqual(target2.selected_option, "Green")
        self.assertEqual(target3.selected_option, "Green")
        
        # Change one target, source and other targets should update
        target1.selected_option = "Red"
        self.assertEqual(source.selected_option, "Red")
        self.assertEqual(target2.selected_option, "Red")
        self.assertEqual(target3.selected_option, "Red")
    
    def test_initialization_with_carries_bindable_selection_option_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableSelectionOption"""
        # Test with None value in source
        source_none = ObservableSelectionOption(None, {"Red", "Green"})
        target_none = ObservableSelectionOption(source_none)
        self.assertIsNone(target_none.selected_option)
        self.assertEqual(target_none.available_options, {"Red", "Green"})
        
        # Test with single option in source
        source_single = ObservableSelectionOption("Red", {"Red"})
        target_single = ObservableSelectionOption(source_single)
        self.assertEqual(target_single.selected_option, "Red")
        self.assertEqual(target_single.available_options, {"Red"})
    
    def test_initialization_with_carries_bindable_selection_option_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableSelectionOption"""
        source = ObservableSelectionOption("Red", {"Red", "Green"})
        target = ObservableSelectionOption(source)
        
        # Check binding consistency
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        self.assertTrue(target.distinct_single_value_hook.is_attached_to(source.distinct_single_value_hook))
        self.assertTrue(source.distinct_single_value_hook.is_attached_to(target.distinct_single_value_hook))
    
    def test_initialization_with_carries_bindable_selection_option_performance(self):
        """Test performance of initialization with CarriesBindableSelectionOption"""
        import time
        
        # Create source
        source = ObservableSelectionOption("Red", {"Red", "Green"})
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableSelectionOption(source)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 6 seconds)
        self.assertLess(end_time - start_time, 6.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableSelectionOption(source)
        source.selected_option = "Green"
        self.assertEqual(target.selected_option, "Green")
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = ObservableSelectionOption("Red", {"Red", "Green", "Yellow"})
        obs2 = ObservableSelectionOption("Blue", {"Blue", "Green", "Red"})
        
        # Bind obs1 to obs2
        obs1.attach(obs2.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
        obs1.attach(obs2.available_options_hook, "available_options", InitialSyncMode.SELF_UPDATES)
        
        # After binding, obs2 should have obs1's values
        self.assertEqual(obs2.selected_option, "Red")
        self.assertEqual(obs2.available_options, {"Red", "Green", "Yellow"})
        
        # Change obs1, obs2 should update
        obs1.selected_option = "Green"
        self.assertEqual(obs2.selected_option, "Green")
        
        # Change obs2 to a valid option, obs1 should also update (bidirectional)
        obs2.selected_option = "Yellow"
        self.assertEqual(obs1.selected_option, "Yellow")
        
        # Try to set obs2 to an invalid option, should raise ValueError
        with self.assertRaises(ValueError):
            obs2.selected_option = "Blue"  # "Blue" not in {"Red", "Green", "Yellow"}
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = ObservableSelectionOption("Red", {"Red", "Green", "Yellow"})
        obs2 = ObservableSelectionOption("Blue", {"Blue", "Green", "Red"})
        
        # Test update_value_from_observable mode
        obs1.attach(obs2.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
        obs1.attach(obs2.available_options_hook, "available_options", InitialSyncMode.SELF_UPDATES)
        self.assertEqual(obs1.selected_option, "Blue")  # obs1 gets updated with obs2's value
        
        # Test update_observable_from_self mode
        obs3 = ObservableSelectionOption("Small", {"Small", "Medium", "Large"})
        obs4 = ObservableSelectionOption("Large", {"Small", "Medium", "Large"})
        obs3.attach(obs4.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
        obs3.attach(obs4.available_options_hook, "available_options", InitialSyncMode.SELF_UPDATES)
        self.assertEqual(obs4.selected_option, "Small")  # obs4 gets updated with obs3's value
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = ObservableSelectionOption("Red", {"Red", "Green", "Yellow"})
        obs2 = ObservableSelectionOption("Blue", {"Blue", "Green", "Red"})
        
        obs1.attach(obs2.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
        obs1.attach(obs2.available_options_hook, "available_options", InitialSyncMode.SELF_UPDATES)
        
        # After binding, obs2 should have obs1's values
        self.assertEqual(obs2.selected_option, "Red")
        self.assertEqual(obs2.available_options, {"Red", "Green", "Yellow"})
        
        obs1.detach()
        
        # After disconnecting, obs2 keeps its current values but changes no longer propagate
        self.assertEqual(obs2.selected_option, "Red")
        self.assertEqual(obs2.available_options, {"Red", "Green", "Yellow"})
        
        # Changes should no longer propagate
        obs1.selected_option = "Green"
        self.assertEqual(obs2.selected_option, "Red")  # Should remain unchanged
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableSelectionOption("Red", {"Red", "Green"})
        with self.assertRaises(ValueError):
            obs.attach(obs.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = ObservableSelectionOption("Red", {"Red", "Green", "Blue"})
        obs2 = ObservableSelectionOption("Blue", {"Red", "Green", "Blue"})
        obs3 = ObservableSelectionOption("Green", {"Red", "Green", "Blue"})
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.attach(obs2.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
        obs2.attach(obs3.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
        
        # Verify chain works
        obs1.selected_option = "Green"
        self.assertEqual(obs2.selected_option, "Green")
        self.assertEqual(obs3.selected_option, "Green")
        
        # Break the chain by unbinding obs2 from obs3
        obs2.detach()
        
        # Change obs1, obs2 should update since they remain bound after obs2.detach()
        # Note: obs1 can only use its own available options {"Red", "Green", "Blue"}
        obs1.selected_option = "Green"  # Use an option that exists in obs1's options
        self.assertEqual(obs2.selected_option, "Green")  # Should update since obs1 and obs2 remain bound
        self.assertEqual(obs3.selected_option, "Green")  # Should remain unchanged
        
        # Change obs3, obs1 should update since obs1 and obs3 remain bound after obs2.detach()
        obs3.selected_option = "Blue"
        self.assertEqual(obs1.selected_option, "Blue")  # Should update since obs1 and obs3 remain bound
        self.assertEqual(obs2.selected_option, "Green")  # Should remain unchanged (isolated)
    
    def test_string_representation(self):
        """Test string and repr methods"""
        self.assertEqual(str(self.observable), "OSO(selected_option=Apple, available_options={'Apple', 'Banana', 'Cherry'})")
        self.assertEqual(repr(self.observable), "OSO(selected_option=Apple, available_options={'Apple', 'Banana', 'Cherry'})")
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableSelectionOption("Red", {"Red", "Green"})
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = ObservableSelectionOption("Red", {"Red", "Green"})
        obs2 = ObservableSelectionOption("Blue", {"Blue", "Green"})
        obs3 = ObservableSelectionOption("Green", {"Green", "Blue"})
        
        # Bind obs2 and obs3 to obs1
        obs2.attach(obs1.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
        obs3.attach(obs1.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
        
        # After binding, all observables should be synchronized due to transitive binding
        # When multiple observables are bound to the same target, they all become part of the same binding group
        print(f'After binding:')
        print(f'obs1: selected={obs1.selected_option}, options={obs1.available_options}')
        print(f'obs2: selected={obs2.selected_option}, options={obs2.available_options}')
        print(f'obs3: selected={obs3.selected_option}, options={obs3.available_options}')
        
        # All observables should have the same selected option due to transitive binding
        self.assertEqual(obs1.selected_option, obs2.selected_option)
        self.assertEqual(obs2.selected_option, obs3.selected_option)
        
        # Change obs1, both should update
        obs1.selected_option = "Green"
        self.assertEqual(obs2.selected_option, "Green")
        self.assertEqual(obs3.selected_option, "Green")
        
        # Change obs2 to a valid option, obs1 and obs3 should also update (bidirectional)
        # Due to transitive binding, all observables stay synchronized
        valid_option = "Green" if "Green" in obs2.available_options else list(obs2.available_options)[0]
        obs2.selected_option = valid_option
        self.assertEqual(obs1.selected_option, valid_option)
        self.assertEqual(obs3.selected_option, valid_option)
    
    def test_selection_option_methods(self):
        """Test standard selection option methods"""
        obs = ObservableSelectionOption("Red", {"Red", "Green", "Blue"})
        
        # Test set_selected_option_and_available_options
        obs.set_selected_option_and_available_options("Blue", {"Blue", "Green"})
        self.assertEqual(obs.selected_option, "Blue")
        self.assertEqual(obs.available_options, {"Blue", "Green"})
        
        # Test add_available_option
        obs.add_available_option("Red")
        self.assertEqual(obs.available_options, {"Blue", "Green", "Red"})
        
        # Test remove_available_option
        obs.remove_available_option("Green")
        self.assertEqual(obs.available_options, {"Blue", "Red"})
    
    def test_selection_option_copy_behavior(self):
        """Test that available_options returns a copy"""
        obs = ObservableSelectionOption("Red", {"Red", "Green", "Blue"})
        
        # Get the available options
        options_copy = obs.available_options
        
        # Modify the copy
        options_copy.add("Yellow")
        
        # Original should not change
        self.assertEqual(obs.available_options, {"Red", "Green", "Blue"})
        
        # The copy should have the modification
        self.assertEqual(options_copy, {"Red", "Green", "Blue", "Yellow"})
    
    def test_selection_option_validation(self):
        """Test selection option validation"""
        # Test with valid selection option
        obs = ObservableSelectionOption("Red", {"Red", "Green"})
        self.assertEqual(obs.selected_option, "Red")
        self.assertEqual(obs.available_options, {"Red", "Green"})
        
        # Test with None value
        obs_none = ObservableSelectionOption(None, {"Red", "Green"})
        self.assertIsNone(obs_none.selected_option)
        self.assertEqual(obs_none.available_options, {"Red", "Green"})
    
    def test_selection_option_binding_edge_cases(self):
        """Test edge cases for selection option binding"""
        # Test binding selection options with same initial values
        obs1 = ObservableSelectionOption("Red", {"Red", "Green"})
        obs2 = ObservableSelectionOption("Red", {"Red", "Green"})
        obs1.attach(obs2.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
        
        obs1.selected_option = "Green"
        self.assertEqual(obs2.selected_option, "Green")
        
        # Test binding selection options with different options
        obs3 = ObservableSelectionOption("Red", {"Red", "Blue"})
        obs4 = ObservableSelectionOption("Green", {"Green", "Blue"})
        obs3.attach(obs4.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
        
        obs3.selected_option = "Blue"
        self.assertEqual(obs4.selected_option, "Blue")
    
    def test_selection_option_performance(self):
        """Test selection option performance characteristics"""
        import time
        
        # Test selected_option access performance
        obs = ObservableSelectionOption("Red", {"Red", "Green", "Blue"})
        start_time = time.time()
        
        for _ in range(10000):
            _ = obs.selected_option
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Selected option access should be fast")
        
        # Test binding performance
        source = ObservableSelectionOption("Red", {"Red", "Green"})
        start_time = time.time()
        
        for _ in range(100):
            ObservableSelectionOption(source)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Binding operations should be fast")
    
    def test_selection_option_error_handling(self):
        """Test selection option error handling"""
        obs = ObservableSelectionOption("Red", {"Red", "Green"})
        
        # Test setting invalid selected option
        with self.assertRaises(ValueError):
            obs.selected_option = "Blue"  # Not in available options
        
        # Test setting empty available options
        with self.assertRaises(ValueError):
            obs.available_options = set()
    
    def test_selection_option_binding_consistency(self):
        """Test binding system consistency"""
        source = ObservableSelectionOption("Red", {"Red", "Green"})
        target: ObservableSelectionOption[str] = ObservableSelectionOption(source)
        
        # Check binding consistency
        
        # Check that they are properly bound
        self.assertTrue(target.distinct_single_value_hook.is_attached_to(source.distinct_single_value_hook))
        self.assertTrue(source.distinct_single_value_hook.is_attached_to(target.distinct_single_value_hook))
    
    def test_selection_option_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = ObservableSelectionOption("Red", {"Red", "Green"})
        with self.assertRaises(ValueError):
            obs.attach(None, "selected_option", InitialSyncMode.SELF_UPDATES)  # type: ignore
    
    def test_selection_option_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = ObservableSelectionOption("Red", {"Red", "Green"})
        obs2 = ObservableSelectionOption("Red", {"Red", "Green"})
        
        obs1.attach(obs2.selected_option_hook, "selected_option", InitialSyncMode.SELF_UPDATES)
        # Both should still have the same value
        self.assertEqual(obs1.selected_option, "Red")
        self.assertEqual(obs2.selected_option, "Red")
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = ObservableSelectionOption("Red", {"Red", "Green"})
        callback = lambda: None
        
        obs.add_listeners(callback, callback)
        self.assertEqual(len(obs.listeners), 1)
        
        obs.add_listeners(callback)
        self.assertEqual(len(obs.listeners), 1)
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = ObservableSelectionOption("Red", {"Red", "Green"})
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listeners(callback)
        self.assertEqual(len(obs.listeners), 0)


if __name__ == '__main__':
    unittest.main()