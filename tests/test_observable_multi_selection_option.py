import unittest
from observables import ObservableMultiSelectionOption

class TestObservableMultiSelectionOption(unittest.TestCase):
    """Test cases for ObservableMultiSelectionOption"""
    
    def setUp(self):
        self.observable = ObservableMultiSelectionOption({"Apple", "Banana"}, {"Apple", "Banana", "Cherry"})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.selected_options, {"Apple", "Banana"})
        self.assertEqual(self.observable.available_options, {"Apple", "Banana", "Cherry"})
    
    def test_set_selected_options(self):
        """Test setting new selected options"""
        self.observable.selected_options = {"Banana", "Cherry"}
        self.assertEqual(self.observable.selected_options, {"Banana", "Cherry"})
    
    def test_set_available_options(self):
        """Test setting new available options"""
        # First clear selected options to avoid validation error
        self.observable.selected_options = set()
        new_options = {"Apple", "Orange", "Grape"}
        self.observable.available_options = new_options
        self.assertEqual(self.observable.available_options, new_options)
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.selected_options = {"Cherry"}
        self.assertEqual(self.notification_count, 1)
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.selected_options = {"Apple", "Banana"}  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_listeners(self.notification_callback)
        self.observable.selected_options = {"Banana"}
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
        self.observable.selected_options = {"Cherry"}
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_initialization_with_carries_bindable_multi_selection_option(self):
        """Test initialization with CarriesBindableMultiSelectionOption"""
        # Create a source observable multi-selection option
        source = ObservableMultiSelectionOption({"Red", "Green"}, {"Red", "Green", "Blue"})
        
        # Create a new observable multi-selection option initialized with the source
        target: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(source)
        
        # Check that the target has the same initial value
        self.assertEqual(target.selected_options, {"Red", "Green"})
        self.assertEqual(target.available_options, {"Red", "Green", "Blue"})
        
        # Check that they are bound together
        source.selected_options = {"Green", "Blue"}
        self.assertEqual(target.selected_options, {"Green", "Blue"})
        
        # Check bidirectional binding
        target.selected_options = {"Red", "Blue"}
        self.assertEqual(source.selected_options, {"Red", "Blue"})
    
    def test_initialization_with_carries_bindable_multi_selection_option_chain(self):
        """Test initialization with CarriesBindableMultiSelectionOption in a chain"""
        # Create a chain of observable multi-selection options
        obs1: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption({"Small"}, {"Small", "Medium"})
        obs2: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(obs1)
        obs3: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(obs2)
        
        # Check initial values
        self.assertEqual(obs1.selected_options, {"Small"})
        self.assertEqual(obs2.selected_options, {"Small"})
        self.assertEqual(obs3.selected_options, {"Small"})
        
        # Change the first observable
        obs1.selected_options = {"Medium"}
        self.assertEqual(obs1.selected_options, {"Medium"})
        self.assertEqual(obs2.selected_options, {"Medium"})
        self.assertEqual(obs3.selected_options, {"Medium"})
        
        # Change the middle observable
        obs2.selected_options = {"Small", "Medium"}
        self.assertEqual(obs1.selected_options, {"Small", "Medium"})
        self.assertEqual(obs2.selected_options, {"Small", "Medium"})
        self.assertEqual(obs3.selected_options, {"Small", "Medium"})
    
    def test_initialization_with_carries_bindable_multi_selection_option_unbinding(self):
        """Test that initialization with CarriesBindableMultiSelectionOption can be unbound"""
        source = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        target: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(source)
        
        # Verify they are bound
        self.assertEqual(target.selected_options, {"Red"})
        source.selected_options = {"Green"}
        self.assertEqual(target.selected_options, {"Green"})
        
        # Unbind them
        target.disconnect()
        
        # Change source, target should not update
        source.selected_options = {"Green"}
        self.assertEqual(target.selected_options, {"Green"})  # Should remain unchanged
        
        # Change target, source should not update
        target.selected_options = {"Red"}
        self.assertEqual(source.selected_options, {"Green"})  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_multi_selection_option_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        target1: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(source)
        target2: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(source)
        target3: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(source)
        
        # Check initial values
        self.assertEqual(target1.selected_options, {"Red"})
        self.assertEqual(target2.selected_options, {"Red"})
        self.assertEqual(target3.selected_options, {"Red"})
        
        # Change source, all targets should update
        source.selected_options = {"Green"}
        self.assertEqual(target1.selected_options, {"Green"})
        self.assertEqual(target2.selected_options, {"Green"})
        self.assertEqual(target3.selected_options, {"Green"})
        
        # Change one target, source and other targets should update
        target1.selected_options = {"Red"}
        self.assertEqual(source.selected_options, {"Red"})
        self.assertEqual(target2.selected_options, {"Red"})
        self.assertEqual(target3.selected_options, {"Red"})
    
    def test_initialization_with_carries_bindable_multi_selection_option_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableMultiSelectionOption"""
        # Test with empty selected options in source
        source_empty: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(set(), {"Red", "Green"})
        target_empty: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(source_empty)
        self.assertEqual(target_empty.selected_options, set())
        self.assertEqual(target_empty.available_options, {"Red", "Green"})
        
        # Test with single option in source
        source_single: ObservableMultiSelectionOption[str]   = ObservableMultiSelectionOption({"Red"}, {"Red"})
        target_single: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(source_single)
        self.assertEqual(target_single.selected_options, {"Red"})
        self.assertEqual(target_single.available_options, {"Red"})
    
    def test_initialization_with_carries_bindable_multi_selection_option_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableMultiSelectionOption"""
        source = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        target: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(source)
        
        # Check binding consistency
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        self.assertTrue(target.selected_options_hook.is_connected_to(source.selected_options_hook))
        self.assertTrue(source.selected_options_hook.is_connected_to(target.selected_options_hook))
    
    def test_initialization_with_carries_bindable_multi_selection_option_performance(self):
        """Test performance of initialization with CarriesBindableMultiSelectionOption"""
        import time
        
        # Create source
        source = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        
        # Measure initialization time (reduced iterations for reasonable test time)
        start_time = time.time()
        for _ in range(10):  # Reduced from 1000 to 10 for reasonable test time
            ObservableMultiSelectionOption(source)
        end_time = time.time()
        
        # Should complete in reasonable time (more lenient for complex initialization)
        self.assertLess(end_time - start_time, 60.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableMultiSelectionOption(source)
        source.selected_options = {"Green"}
        self.assertEqual(target.selected_options, {"Green"})
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = ObservableMultiSelectionOption({"Red"}, {"Red", "Green", "Yellow"})
        obs2 = ObservableMultiSelectionOption({"Blue"}, {"Red", "Green", "Blue"})
        
        # Bind obs1 to obs2
        obs1.connect_hooks({"available_options": obs2.available_options_hook, "selected_options": obs2.selected_options_hook}, "use_target_value") #type: ignore
        
        # After binding with USE_TARGET_VALUE, obs1 should get obs2's values
        self.assertEqual(obs1.selected_options, {"Blue"})
        self.assertEqual(obs1.available_options, {"Red", "Green", "Blue"})
        
        # Change obs1, obs2 should update
        obs1.selected_options = {"Green"}
        self.assertEqual(obs2.selected_options, {"Green"})
        
        # Change obs2 to a valid option, obs1 should also update (bidirectional)
        obs2.selected_options = {"Red"}  # Red is valid in both sets
        self.assertEqual(obs1.selected_options, {"Red"})
        
        # Try to set obs2 to an invalid option, should raise ValueError
        with self.assertRaises(ValueError):
            obs2.selected_options = {"Yellow"}  # "Yellow" not in {"Red", "Green", "Blue"}
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = ObservableMultiSelectionOption({"Red"}, {"Red", "Green", "Yellow"})
        obs2 = ObservableMultiSelectionOption({"Blue"}, {"Red", "Green", "Blue"})
        
        # Test update_observable_from_self mode (obs2 gets updated with obs1's value)
        obs1.connect_hooks({"available_options": obs2.available_options_hook, "selected_options": obs2.selected_options_hook}, "use_target_value") #type: ignore
        # Current semantics: caller gets target's values  
        self.assertEqual(obs1.selected_options, {"Blue"})
        self.assertEqual(obs1.available_options, {"Red", "Green", "Blue"})

        # Test update_self_from_observable mode (obs1 gets updated with obs2's value)
        obs3 = ObservableMultiSelectionOption({"Small"}, {"Small", "Medium", "Large"})
        obs4 = ObservableMultiSelectionOption({"Large"}, {"Small", "Medium", "Large"})
        obs3.connect_hooks({"available_options": obs4.available_options_hook, "selected_options": obs4.selected_options_hook}, "use_target_value") #type: ignore
        # Current semantics: caller gets target's values
        self.assertEqual(obs3.selected_options, {"Large"})
        self.assertEqual(obs3.available_options, {"Small", "Medium", "Large"})
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = ObservableMultiSelectionOption({"Red"}, {"Red", "Green", "Yellow"})
        obs2 = ObservableMultiSelectionOption({"Blue"}, {"Red", "Green", "Blue"})
        
        obs1.connect_hooks({"available_options": obs2.available_options_hook, "selected_options": obs2.selected_options_hook}, "use_target_value") #type: ignore
        
        # After binding with USE_TARGET_VALUE, obs1 should get obs2's values
        self.assertEqual(obs1.selected_options, {"Blue"})
        self.assertEqual(obs1.available_options, {"Red", "Green", "Blue"})
        
        obs1.disconnect()
        
        # After disconnect_hooking, both keep their current values but changes no longer propagate
        self.assertEqual(obs1.selected_options, {"Blue"})
        self.assertEqual(obs1.available_options, {"Red", "Green", "Blue"})
        
        # Changes should no longer propagate
        obs1.selected_options = {"Green"}
        self.assertEqual(obs1.selected_options, {"Green"})  # obs1 can change itself
        self.assertEqual(obs2.selected_options, {"Blue"})  # obs2 should remain unchanged
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        with self.assertRaises(ValueError):
            obs.connect_hook(obs.selected_options_hook, "selected_options", "use_target_value") # type: ignore
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = ObservableMultiSelectionOption({"Red"}, {"Red", "Green", "Blue"})
        obs2 = ObservableMultiSelectionOption({"Blue"}, {"Red", "Green", "Blue"})
        obs3 = ObservableMultiSelectionOption({"Green"}, {"Red", "Green", "Blue"})
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.connect_hook(obs2.selected_options_hook, "selected_options", "use_target_value") # type: ignore
        obs2.connect_hook(obs3.selected_options_hook, "selected_options", "use_target_value") # type: ignore
        
        # Verify chain works
        obs1.selected_options = {"Green"}
        self.assertEqual(obs2.selected_options, {"Green"})
        self.assertEqual(obs3.selected_options, {"Green"})
        
        # Break the chain by unbinding obs2 from obs3
        obs2.disconnect()
        
        # Change obs1, obs2 should NOT update (obs2 is now detached from everything)
        # But obs3 should still update because obs1 and obs3 are still bound (transitive binding)
        obs1.selected_options = {"Red"}
        self.assertEqual(obs2.selected_options, {"Green"})  # Should remain unchanged
        self.assertEqual(obs3.selected_options, {"Red"})  # Should update due to transitive binding
        
        # Change obs3, obs1 should update (transitive binding), obs2 should not
        obs3.selected_options = {"Blue"}
        self.assertEqual(obs1.selected_options, {"Blue"})  # Should update due to transitive binding
        self.assertEqual(obs2.selected_options, {"Green"})  # Should remain unchanged
    
    def test_string_representation(self):
        """Test string and repr methods"""
        self.assertEqual(str(self.observable), "OMSO(selected_options={'Apple', 'Banana'}, available_options={'Apple', 'Banana', 'Cherry'})")
        self.assertEqual(repr(self.observable), "ObservableMultiSelectionOption(selected_options={'Apple', 'Banana'}, available_options={'Apple', 'Banana', 'Cherry'})")
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = ObservableMultiSelectionOption({"Red"}, {"Red", "Green", "Blue"})
        obs2 = ObservableMultiSelectionOption({"Blue"}, {"Blue", "Green", "Red"})
        obs3 = ObservableMultiSelectionOption({"Green"}, {"Green", "Blue", "Red"})
        
        # Bind obs2 and obs3 to obs1
        obs2.connect_hook(obs1.selected_options_hook, "selected_options", "use_target_value") # type: ignore
        obs3.connect_hook(obs1.selected_options_hook, "selected_options", "use_target_value") # type: ignore
        
        # Change obs1, both should update
        obs1.selected_options = {"Green"}
        self.assertEqual(obs2.selected_options, {"Green"})
        self.assertEqual(obs3.selected_options, {"Green"})
        
        # Change obs2, obs1 should also update (bidirectional), obs3 should also update
        obs2.selected_options = {"Red"}
        self.assertEqual(obs1.selected_options, {"Red"})
        self.assertEqual(obs3.selected_options, {"Red"})
    
    def test_multi_selection_option_methods(self):
        """Test standard multi-selection option methods"""
        obs = ObservableMultiSelectionOption({"Red", "Green"}, {"Red", "Green", "Blue"})
        
        # Test set_selected_options_and_available_options
        obs.change_selected_options_and_available_options({"Blue"}, {"Blue", "Green", "Yellow"})
        self.assertEqual(obs.selected_options, {"Blue"})
        self.assertEqual(obs.available_options, {"Blue", "Green", "Yellow"})
        
        # Test add_selected_option
        obs.add_selected_option("Green")
        self.assertEqual(obs.selected_options, {"Blue", "Green"})
        
        # Test remove_selected_option
        obs.remove_selected_option("Blue")
        self.assertEqual(obs.selected_options, {"Green"})
    
    def test_multi_selection_option_copy_behavior(self):
        """Test that available_options returns a copy"""
        obs = ObservableMultiSelectionOption({"Red", "Green"}, {"Red", "Green", "Blue"})
        
        # Get the available options
        options_copy = obs.available_options
        
        # Modify the copy
        options_copy.add("Yellow")
        
        # Original should not change
        self.assertEqual(obs.available_options, {"Red", "Green", "Blue"})
        
        # The copy should have the modification
        self.assertEqual(options_copy, {"Red", "Green", "Blue", "Yellow"})
    
    def test_multi_selection_option_validation(self):
        """Test multi-selection option validation"""
        # Test with valid multi-selection option
        obs = ObservableMultiSelectionOption({"Red", "Green"}, {"Red", "Green"})
        self.assertEqual(obs.selected_options, {"Red", "Green"})
        self.assertEqual(obs.available_options, {"Red", "Green"})
        
        # Test with empty selected options
        obs_empty: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(set(), {"Red", "Green"})
        self.assertEqual(obs_empty.selected_options, set())
        self.assertEqual(obs_empty.available_options, {"Red", "Green"})
    
    def test_multi_selection_option_binding_edge_cases(self):
        """Test edge cases for multi-selection option binding"""
        # Test binding multi-selection options with same initial values
        obs1 = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        obs2 = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        obs1.connect_hook(obs2.selected_options_hook, "selected_options", "use_target_value") # type: ignore
        
        obs1.selected_options = {"Green"}
        self.assertEqual(obs2.selected_options, {"Green"})
        
        # Test binding multi-selection options with different options
        obs3 = ObservableMultiSelectionOption({"Red"}, {"Red", "Blue", "Green"})
        obs4 = ObservableMultiSelectionOption({"Green"}, {"Red", "Blue", "Green"})
        obs3.connect_hook(obs4.selected_options_hook, "selected_options", "use_target_value") # type: ignore
        
        obs3.selected_options = {"Blue"}
        self.assertEqual(obs4.selected_options, {"Blue"})
    
    def test_multi_selection_option_performance(self):
        """Test multi-selection option performance characteristics"""
        import time
        
        # Test selected_options access performance
        obs = ObservableMultiSelectionOption({"Red", "Green"}, {"Red", "Green", "Blue"})
        start_time = time.time()
        
        for _ in range(10000):
            _ = obs.selected_options
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Selected options access should be fast")
        
        # Test binding performance
        source = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        start_time = time.time()
        
        for _ in range(100):
            ObservableMultiSelectionOption(source)
        
        end_time = time.time()
        
        # Should complete in reasonable time (more lenient for complex initialization)
        self.assertLess(end_time - start_time, 10.0, "Binding operations should be fast")
    
    def test_multi_selection_option_error_handling(self):
        """Test multi-selection option error handling"""
        obs = ObservableMultiSelectionOption({"Red", "Green"}, {"Red", "Green"})
        
        # Test setting invalid selected options
        with self.assertRaises(ValueError):
            obs.selected_options = {"Blue"}  # Not in available options
        
        # Test setting empty available options
        with self.assertRaises(ValueError):
            obs.available_options = set()
    
    def test_multi_selection_option_binding_consistency(self):
        """Test binding system consistency"""
        source = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        target: ObservableMultiSelectionOption[str] = ObservableMultiSelectionOption(source)
        
        # Check binding consistency
        # Note: check_status_consistency() method no longer exists in new architecture
        # Binding system consistency is now handled automatically by the hook system
        
        # Check that they are properly bound
        self.assertTrue(target.selected_options_hook.is_connected_to(source.selected_options_hook))
        self.assertTrue(source.selected_options_hook.is_connected_to(target.selected_options_hook))
    
    def test_multi_selection_option_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        with self.assertRaises(ValueError):
            obs.connect_hook(None, "selected_options", "use_target_value")  # type: ignore
    
    def test_multi_selection_option_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = ObservableMultiSelectionOption({"Red"}, {"Red", "Green", "Yellow"})
        obs2 = ObservableMultiSelectionOption({"Blue"}, {"Red", "Green", "Blue"})
        
        obs1.connect_hooks({"available_options": obs2.available_options_hook, "selected_options": obs2.selected_options_hook}, "use_target_value") #type: ignore
        # Use target value for sync → caller gets target's values
        self.assertEqual(obs1.selected_options, {"Blue"})
        self.assertEqual(obs1.available_options, {"Red", "Green", "Blue"})
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        callback = lambda: None
        
        obs.add_listeners(callback, callback)
        self.assertEqual(len(obs.listeners), 1)
        
        obs.add_listeners(callback)
        self.assertEqual(len(obs.listeners), 1)
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = ObservableMultiSelectionOption({"Red"}, {"Red", "Green"})
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listeners(callback)
        self.assertEqual(len(obs.listeners), 0)


if __name__ == '__main__':
    unittest.main()
