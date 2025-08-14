import unittest
from observables import ObservableMultiSelectionOption, ObservableSet, SyncMode

class TestObservableMultiSelectionOption(unittest.TestCase):
    """Test cases for ObservableMultiSelectionOption"""
    
    def setUp(self):
        self.observable = ObservableMultiSelectionOption({2, 3}, {1, 2, 3, 4})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_state(self):
        """Test initial available options and selected options"""
        self.assertEqual(self.observable.available_options, {1, 2, 3, 4})
        self.assertEqual(self.observable.selected_options, {2, 3})
    
    def test_change_available_options(self):
        """Test changing available options"""
        # Change to available options that include the current selected options (2, 3)
        self.observable.set_available_options({2, 3, 5, 6, 7})
        self.assertEqual(self.observable.available_options, {2, 3, 5, 6, 7})
        # Selected options should remain valid
        self.assertEqual(self.observable.selected_options, {2, 3})
    
    def test_change_selected_options(self):
        """Test changing selected options"""
        self.observable.set_selected_options({1, 4})
        self.assertEqual(self.observable.selected_options, {1, 4})
    
    def test_invalid_selected_options(self):
        """Test that changing to invalid options raises error"""
        with self.assertRaises(ValueError):
            self.observable.set_selected_options({999, 1000})
    
    def test_invalid_available_options_with_selected(self):
        """Test that changing available options to exclude selected options raises error"""
        with self.assertRaises(ValueError):
            self.observable.set_available_options({5, 6, 7})  # 2, 3 not in new available options
    
    def test_set_selected_options_and_available_options(self):
        """Test setting both selected options and available options at once"""
        self.observable.set_selected_options_and_available_options({6, 7}, {5, 6, 7, 8})
        self.assertEqual(self.observable.selected_options, {6, 7})
        self.assertEqual(self.observable.available_options, {5, 6, 7, 8})
    
    def test_listener_notification(self):
        """Test that listeners are notified when state changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_selected_options({1, 3})
        self.assertEqual(self.notification_count, 1)
    
    def test_binding_selected_options(self):
        """Test binding selected options between observables"""
        # Create observables with compatible initial states
        obs1 = ObservableMultiSelectionOption({1, 2}, {1, 2, 3, 4, 5, 6})
        obs2 = ObservableMultiSelectionOption({4, 5}, {1, 2, 3, 4, 5, 6})
        
        obs1.bind_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change obs1 selected options, obs2 should update
        obs1.set_selected_options({2, 3})
        self.assertEqual(obs2.selected_options, {2, 3})
        
        # Change obs2 selected options, obs1 should update
        obs2.set_selected_options({5, 6})
        self.assertEqual(obs1.selected_options, {5, 6})
    
    def test_binding_available_options(self):
        """Test binding available options between observables"""
        # Create observables with compatible initial states
        obs1 = ObservableMultiSelectionOption({1, 2}, {1, 2, 3, 4, 5, 6})
        obs2 = ObservableMultiSelectionOption({4, 5}, {1, 2, 3, 4, 5, 6})
        
        obs1.bind_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Test that binding works by verifying they start with the same available options
        self.assertEqual(obs1.available_options, obs2.available_options)
        
        # Test that binding is established by checking binding consistency
        is_consistent, message = obs1.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Test that binding is established by checking binding consistency
        is_consistent, message = obs2.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
    
    def test_unbinding(self):
        """Test unbinding observables"""
        # Create observables with compatible initial states
        obs1 = ObservableMultiSelectionOption({1, 2}, {1, 2, 3, 4, 5, 6})
        obs2 = ObservableMultiSelectionOption({4, 5}, {1, 2, 3, 4, 5, 6})
        
        obs1.bind_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        obs1.unbind_from(obs2)
        
        # Changes should no longer propagate
        obs1.set_selected_options({2, 3})
        self.assertEqual(obs2.selected_options, {4, 5})
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        # Create observables with compatible initial states
        obs1 = ObservableMultiSelectionOption({1, 2}, {1, 2, 3, 4, 5, 6})
        obs2 = ObservableMultiSelectionOption({4, 5}, {1, 2, 3, 4, 5, 6})
        
        obs1.bind_to(obs2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        obs1.unbind_from(obs2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            obs1.unbind_from(obs2)
        
        # Changes should still not propagate
        obs1.set_selected_options({2, 3})
        # Since we used UPDATE_OBSERVABLE_FROM_SELF, obs2 was updated to obs1's value ({1, 2}) during binding
        # After unbinding, obs2 should still have that value, not the original {4, 5}
        self.assertEqual(obs2.selected_options, {1, 2})
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableMultiSelectionOption({1, 2}, {1, 2, 3})
        with self.assertRaises(ValueError):
            obs.bind_to(obs, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        # Create observables with compatible initial states
        obs1 = ObservableMultiSelectionOption({1, 2}, {1, 2, 3, 4, 5, 6, 7, 8, 9})
        obs2 = ObservableMultiSelectionOption({4, 5}, {1, 2, 3, 4, 5, 6, 7, 8, 9})
        obs3 = ObservableMultiSelectionOption({7, 8}, {1, 2, 3, 4, 5, 6, 7, 8, 9})
        
        # Bind obs2 and obs3 selected options to obs1
        obs2.bind_to(obs1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        obs3.bind_to(obs1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change obs1 selected options, both should update
        obs1.set_selected_options({2, 3})
        self.assertEqual(obs2.selected_options, {2, 3})
        self.assertEqual(obs3.selected_options, {2, 3})
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableMultiSelectionOption({1, 2}, {1, 2, 3})
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_initialization_with_carries_bindable_set(self):
        """Test initialization with CarriesBindableSet"""
        # Create source observables
        source_available_options = ObservableSet({1, 2, 3, 4})
        source_selected_options = ObservableSet({2, 3})
        
        # Create a new observable multi-selection option initialized with the sources
        target = ObservableMultiSelectionOption(source_selected_options, source_available_options)
        
        # Check that the target has the same initial values
        self.assertEqual(target.available_options, {1, 2, 3, 4})
        self.assertEqual(target.selected_options, {2, 3})
        
        # Check that they are bound together
        source_available_options.add(5)
        self.assertEqual(target.available_options, {1, 2, 3, 4, 5})
        
        source_selected_options.add(4)
        self.assertEqual(target.selected_options, {2, 3, 4})
        
        # Check bidirectional binding
        target.add_available_option(6)
        self.assertEqual(source_available_options.set_value, {1, 2, 3, 4, 5, 6})
        
        target.selected_options = {1, 5}
        self.assertEqual(source_selected_options.set_value, {1, 5})
    
    def test_initialization_with_carries_bindable_set_only(self):
        """Test initialization with only CarriesBindableSet for available options"""
        # Create source observable set
        source_available_options = ObservableSet({10, 20, 30})
        
        # Create a new observable multi-selection option initialized with the source set
        target = ObservableMultiSelectionOption({20}, source_available_options)
        
        # Check that the target has the same initial available options
        self.assertEqual(target.available_options, {10, 20, 30})
        self.assertEqual(target.selected_options, {20})
        
        # Check that they are bound together
        source_available_options.add(40)
        self.assertEqual(target.available_options, {10, 20, 30, 40})
        
        # Check bidirectional binding
        target.add_available_option(50)
        self.assertEqual(source_available_options.set_value, {10, 20, 30, 40, 50})
    
    def test_initialization_with_carries_bindable_set_only_selected(self):
        """Test initialization with only CarriesBindableSet for selected options"""
        # Create source observable set
        source_selected_options = ObservableSet({100, 200})
        
        # Create a new observable multi-selection option initialized with the source set
        target = ObservableMultiSelectionOption(source_selected_options, {100, 200, 300})
        
        # Check that the target has the same initial selected options
        self.assertEqual(target.available_options, {100, 200, 300})
        self.assertEqual(target.selected_options, {100, 200})
        
        # Check that they are bound together
        source_selected_options.add(300)
        self.assertEqual(target.selected_options, {100, 200, 300})
        
        # Check bidirectional binding
        target.selected_options = {200, 300}
        self.assertEqual(source_selected_options.set_value, {200, 300})
    
    def test_initialization_with_carries_bindable_chain(self):
        """Test initialization with CarriesBindableSet in a chain"""
        # Create a chain of observable multi-selection options
        obs1 = ObservableMultiSelectionOption({1, 2}, {1, 2})
        obs2 = ObservableMultiSelectionOption({3, 4}, {3, 4})
        obs3 = ObservableMultiSelectionOption({5, 6}, {5, 6})
        
        # Bind them in a chain
        obs2.bind_to(obs1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        obs3.bind_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Check initial values after binding
        self.assertEqual(obs1.available_options, {1, 2})
        self.assertEqual(obs1.selected_options, {1, 2})
        self.assertEqual(obs2.available_options, {1, 2})
        self.assertEqual(obs2.selected_options, {1, 2})
        self.assertEqual(obs3.available_options, {1, 2})
        self.assertEqual(obs3.selected_options, {1, 2})
        
        # Test that binding is established by checking binding consistency
        is_consistent, message = obs1.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        is_consistent, message = obs2.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        is_consistent, message = obs3.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
    
    def test_initialization_with_carries_bindable_multiple_targets(self):
        """Test multiple targets initialized with the same sources"""
        source_available_options = ObservableSet({100, 200})
        source_selected_options = ObservableSet({100})
        
        target1 = ObservableMultiSelectionOption(source_selected_options, source_available_options)
        target2 = ObservableMultiSelectionOption(source_selected_options, source_available_options)
        target3 = ObservableMultiSelectionOption(source_selected_options, source_available_options)
        
        # Check initial values
        self.assertEqual(target1.available_options, {100, 200})
        self.assertEqual(target1.selected_options, {100})
        self.assertEqual(target2.available_options, {100, 200})
        self.assertEqual(target2.selected_options, {100})
        self.assertEqual(target3.available_options, {100, 200})
        self.assertEqual(target3.selected_options, {100})
        
        # Change source available options, all targets should update
        source_available_options.add(300)
        self.assertEqual(target1.available_options, {100, 200, 300})
        self.assertEqual(target2.available_options, {100, 200, 300})
        self.assertEqual(target3.available_options, {100, 200, 300})
        
        # Change source selected options, all targets should update
        source_selected_options.add(200)
        self.assertEqual(target1.selected_options, {100, 200})
        self.assertEqual(target2.selected_options, {100, 200})
        self.assertEqual(target3.selected_options, {100, 200})
    
    def test_initialization_with_carries_bindable_unbinding(self):
        """Test that initialization with CarriesBindableSet can be unbound"""
        source_available_options = ObservableSet({1, 2})
        source_selected_options = ObservableSet({1})
        
        target = ObservableMultiSelectionOption(source_selected_options, source_available_options)
        
        # Verify they are bound
        self.assertEqual(target.available_options, {1, 2})
        self.assertEqual(target.selected_options, {1})
        
        source_available_options.add(3)
        source_selected_options.add(2)
        self.assertEqual(target.available_options, {1, 2, 3})
        self.assertEqual(target.selected_options, {1, 2})
        
        # Unbind them
        target.unbind_available_options_from(source_available_options)
        target.unbind_selected_options_from(source_selected_options)
        
        # Change sources, target should not update
        source_available_options.add(4)
        source_selected_options.add(3)
        self.assertEqual(target.available_options, {1, 2, 3})  # Should remain unchanged
        self.assertEqual(target.selected_options, {1, 2})  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableSet"""
        # Test with empty set
        source_empty = ObservableSet(set())
        source_selected_empty = ObservableSet(set())
        target_empty = ObservableMultiSelectionOption(source_selected_empty, source_empty)
        self.assertEqual(target_empty.available_options, set())
        self.assertEqual(target_empty.selected_options, set())
        
        # Test with None values
        source_none = ObservableSet({None, 1, None})
        source_none_selected = ObservableSet({None})
        target_none = ObservableMultiSelectionOption(source_none_selected, source_none)
        self.assertEqual(target_none.available_options, {None, 1})
        self.assertEqual(target_none.selected_options, {None})
    
    def test_initialization_with_carries_bindable_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableSet"""
        source_available_options = ObservableSet({1, 2, 3})
        source_selected_options = ObservableSet({1})
        
        target = ObservableMultiSelectionOption(source_selected_options, source_available_options)
        
        # Check binding consistency
        is_consistent, message = target.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Check that they are properly bound
        self.assertTrue(target._get_available_options_hook().is_bound_to(source_available_options._get_set_hook()))
        self.assertTrue(target._get_selected_options_hook().is_bound_to(source_selected_options._get_set_hook()))
    
    def test_initialization_with_carries_bindable_performance(self):
        """Test performance of initialization with CarriesBindableSet"""
        import time
        
        # Create sources
        source_available_options = ObservableSet({1, 2, 3, 4, 5})
        source_selected_options = ObservableSet({1, 2})
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableMultiSelectionOption(source_selected_options, source_available_options)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(end_time - start_time, 1.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableMultiSelectionOption(source_selected_options, source_available_options)
        source_available_options.add(6)
        source_selected_options.add(3)
        self.assertEqual(target.available_options, {1, 2, 3, 4, 5, 6})
        self.assertEqual(target.selected_options, {1, 2, 3})
    
    def test_empty_selection_initialization(self):
        """Test initialization with empty selected options (default behavior)."""
        # Should work with empty selected options
        obs = ObservableMultiSelectionOption(set(), {1, 2, 3})
        self.assertEqual(obs.selected_options, set())
        self.assertEqual(obs.available_options, {1, 2, 3})
        
        # Should work with empty available options
        obs = ObservableMultiSelectionOption(set(), set())
        self.assertEqual(obs.selected_options, set())
        self.assertEqual(obs.available_options, set())
        
        # Should work with empty selected and empty available options
        obs = ObservableMultiSelectionOption(set(), set())
        self.assertEqual(obs.selected_options, set())
        self.assertEqual(obs.available_options, set())
    
    def test_empty_selection_dynamic_changes(self):
        """Test dynamic changes with empty selections."""
        obs = ObservableMultiSelectionOption({1, 2}, {1, 2, 3})
        
        # Should allow setting selected options to empty
        obs.selected_options = set()
        self.assertEqual(obs.selected_options, set())
        
        # Should allow setting available options to empty set when selected_options is empty
        obs.set_selected_options_and_available_options(set(), set())
        self.assertEqual(obs.available_options, set())
        self.assertEqual(obs.selected_options, set())
        
        # Should allow setting selected options to empty when available options are empty
        obs.selected_options = set()
        self.assertEqual(obs.selected_options, set())
    
    def test_empty_selection_edge_cases(self):
        """Test edge cases with empty selection functionality."""
        # Test with empty selected and non-empty available options
        obs = ObservableMultiSelectionOption(set(), {1, 2, 3})
        self.assertEqual(obs.selected_options, set())
        self.assertEqual(obs.available_options, {1, 2, 3})
        
        # Test changing from empty to valid options
        obs.selected_options = {1, 2}
        self.assertEqual(obs.selected_options, {1, 2})
        
        # Test changing back to empty
        obs.selected_options = set()
        self.assertEqual(obs.selected_options, set())
        
        # Test with empty available options and empty selected
        obs = ObservableMultiSelectionOption(set(), set())
        self.assertEqual(obs.selected_options, set())
        self.assertEqual(obs.available_options, set())
    
    def test_empty_selection_validation_consistency(self):
        """Test that validation is consistent with empty selection support."""
        # Should allow empty selections but still validate non-empty values
        obs = ObservableMultiSelectionOption(set(), {1, 2, 3})
        
        # Should allow empty
        obs.selected_options = set()
        
        # Should still validate non-empty values
        with self.assertRaises(ValueError) as context:
            obs.selected_options = {5, 6}  # Not in available options
        self.assertIn("not in available options", str(context.exception))
        
        # Should allow valid values
        obs.selected_options = {1, 2}
        self.assertEqual(obs.selected_options, {1, 2})
    
    def test_empty_selection_binding_behavior(self):
        """Test that empty selection support affects binding behavior."""
        # Test with empty selections
        obs1 = ObservableMultiSelectionOption(set(), {1, 2, 3, 4})
        obs2 = ObservableMultiSelectionOption({4}, {1, 2, 3, 4})
        
        # Binding should work even with empty selections
        # Use UPDATE_VALUE_FROM_OBSERVABLE so obs1 gets updated to obs2's value
        obs1.bind_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        self.assertEqual(obs1.selected_options, {4})
    
    def test_set_operations(self):
        """Test set operations on selected options."""
        obs = ObservableMultiSelectionOption({1, 2}, {1, 2, 3, 4})
        
        # Test add
        obs.add(3)
        self.assertEqual(obs.selected_options, {1, 2, 3})
        
        # Test remove
        obs.remove(2)
        self.assertEqual(obs.selected_options, {1, 3})
        
        # Test discard
        obs.discard(1)
        self.assertEqual(obs.selected_options, {3})
        
        # Test pop
        item = obs.pop()
        self.assertIn(item, {1, 2, 3, 4})
        self.assertEqual(obs.selected_options, set())
        
        # Test clear
        obs.selected_options = {1, 2, 3}
        obs.clear()
        self.assertEqual(obs.selected_options, set())
    
    def test_available_options_operations(self):
        """Test operations on available options."""
        obs = ObservableMultiSelectionOption({1, 2}, {1, 2, 3, 4})
        
        # Test add_available_option
        obs.add_available_option(5)
        self.assertEqual(obs.available_options, {1, 2, 3, 4, 5})
        
        # Test remove_available_option
        obs.remove_available_option(3)
        self.assertEqual(obs.available_options, {1, 2, 4, 5})
        # Selected options should also be updated if they contained the removed option
        self.assertEqual(obs.selected_options, {1, 2})
    
    def test_magic_methods(self):
        """Test magic methods like __len__, __contains__, __iter__, etc."""
        obs = ObservableMultiSelectionOption({1, 2, 3}, {1, 2, 3, 4, 5})
        
        # Test __len__
        self.assertEqual(len(obs), 3)
        
        # Test __contains__
        self.assertIn(1, obs)
        self.assertNotIn(6, obs)
        
        # Test __iter__
        items = list(obs)
        self.assertEqual(set(items), {1, 2, 3})
        
        # Test __bool__
        self.assertTrue(bool(obs))
        
        # Test empty selection
        obs.selected_options = set()
        self.assertFalse(bool(obs))
    
    def test_equality_and_hash(self):
        """Test equality and hash methods."""
        obs1 = ObservableMultiSelectionOption({1, 2}, {1, 2, 3, 4})
        obs2 = ObservableMultiSelectionOption({1, 2}, {1, 2, 3, 4})
        obs3 = ObservableMultiSelectionOption({2, 3}, {1, 2, 3, 4})
        
        # Test equality
        self.assertEqual(obs1, obs2)
        self.assertNotEqual(obs1, obs3)
        
        # Test hash
        self.assertEqual(hash(obs1), hash(obs2))
        self.assertNotEqual(hash(obs1), hash(obs3))
    
    def test_string_representations(self):
        """Test string and repr methods."""
        obs = ObservableMultiSelectionOption({1, 2}, {1, 2, 3, 4})
        
        str_repr = str(obs)
        repr_repr = repr(obs)
        
        self.assertIn("available_options", str_repr)
        self.assertIn("selected", str_repr)
        self.assertIn("ObservableMultiSelectionOption", repr_repr)
    
    def test_selected_options_not_empty_property(self):
        """Test the selected_options_not_empty property."""
        obs = ObservableMultiSelectionOption({1, 2}, {1, 2, 3, 4})
        
        # Should work with non-empty selection
        self.assertEqual(obs.selected_options_not_empty, {1, 2})
        
        # Should raise error with empty selection
        obs.selected_options = set()
        with self.assertRaises(ValueError):
            _ = obs.selected_options_not_empty
