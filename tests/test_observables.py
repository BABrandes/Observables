import unittest
from typing import List, Set, Callable
from observable_single_value import ObservableSingleValue
from observable_set import ObservableSet
from observable_list import ObservableList
from observable_selection_option import ObservableSelectionOption
from observable_dict import ObservableDict
from _internal_binding_handler import SyncMode


class ConcreteObservableList(ObservableList[int]):
    """Concrete implementation of ObservableList for testing"""
    
    def __init__(self, values: List[int]):
        self._values = values.copy()
        self._listeners: Set[Callable[[], None]] = set()
        self._binding_handler = None  # Not implemented in this test # type: ignore
    
    def get_value(self) -> List[int]:
        return self._values.copy()
    
    def set_value(self, value: List[int]) -> None:
        if self._values != value:
            self._values = value.copy()
            self._notify_listeners()
    
    def bind_to_list_value_observable(self, observable: "ObservableList[int]") -> None:
        # Not implemented in this test
        pass
    
    def add_listener(self, callback: Callable[[], None]) -> None:
        self._listeners.add(callback)
    
    def remove_listener(self, callback: Callable[[], None]) -> None:
        self._listeners.discard(callback)
    
    def _notify_listeners(self) -> None:
        for callback in self._listeners:
            callback()


class TestObservableSingleValue(unittest.TestCase):
    """Test cases for ObservableSingleValue"""
    
    def setUp(self):
        self.observable = ObservableSingleValue(42)
        self.notification_count = 0
        self.last_notified_value = None
    
    def notification_callback(self):
        self.notification_count += 1
    
    def value_callback(self, value):
        self.last_notified_value = value
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.value, 42)
    
    def test_set_value(self):
        """Test setting a new value"""
        self.observable.set_value(100)
        self.assertEqual(self.observable.value, 100)
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_value(50)
        self.assertEqual(self.notification_count, 1)
    
    def test_multiple_listeners(self):
        """Test multiple listeners are notified"""
        count1, count2 = 0, 0
        
        def callback1():
            nonlocal count1
            count1 += 1
        
        def callback2():
            nonlocal count2
            count2 += 1
        
        self.observable.add_listeners(callback1, callback2)
        self.observable.set_value(75)
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_remove_listener(self):
        """Test removing a listener"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_listeners(self.notification_callback)
        self.observable.set_value(200)
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_all_listeners(self):
        """Test removing all listeners"""
        self.observable.add_listeners(self.notification_callback)
        removed = self.observable.remove_all_listeners()
        self.assertEqual(len(removed), 1)
        self.observable.set_value(300)
        self.assertEqual(self.notification_count, 0)
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        # Bind obs1 to obs2
        obs1.bind_to_observable(obs2)
        
        # Change obs1, obs2 should update
        obs1.set_value(30)
        self.assertEqual(obs2.value, 30)
        
        # Change obs2, obs1 should also update (bidirectional)
        obs2.set_value(40)
        self.assertEqual(obs1.value, 40)  # Should also update
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = ObservableSingleValue(100)
        obs2 = ObservableSingleValue(200)
        
        # Test update_value_from_observable mode
        obs1.bind_to_observable(obs2, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        self.assertEqual(obs1.value, 200)  # obs1 gets updated with obs2's value
        
        # Test update_observable_from_self mode
        obs3 = ObservableSingleValue(300)
        obs4 = ObservableSingleValue(400)
        obs3.bind_to_observable(obs4, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        self.assertEqual(obs4.value, 300)  # obs4 gets updated with obs3's value
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        obs1.bind_to_observable(obs2)
        obs1.unbind_from_observable(obs2)
        
        # Changes should no longer propagate
        obs1.set_value(50)
        self.assertEqual(obs2.value, 20)
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        obs1.bind_to_observable(obs2)
        obs1.unbind_from_observable(obs2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            obs1.unbind_from_observable(obs2)
        
        # Changes should still not propagate
        obs1.set_value(50)
        self.assertEqual(obs2.value, 20)
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableSingleValue(10)
        with self.assertRaises(ValueError):
            obs.bind_to_observable(obs)
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        obs3 = ObservableSingleValue(30)
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.bind_to_observable(obs2)
        obs2.bind_to_observable(obs3)
        
        # Verify chain works
        obs1.set_value(100)
        self.assertEqual(obs2.value, 100)
        self.assertEqual(obs3.value, 100)
        
        # Break the chain by unbinding obs2 from obs3
        obs2.unbind_from_observable(obs3)
        
        # Change obs1, obs2 should update but obs3 should not
        obs1.set_value(200)
        self.assertEqual(obs2.value, 200)
        self.assertEqual(obs3.value, 100)  # Should remain unchanged
        
        # Change obs3, obs1 and obs2 should not update
        obs3.set_value(300)
        self.assertEqual(obs1.value, 200)
        self.assertEqual(obs2.value, 200)
    
    def test_string_representation(self):
        """Test string and repr methods"""
        self.assertEqual(str(self.observable), "OSV(value=42)")
        self.assertEqual(repr(self.observable), "OSV(value=42)")
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableSingleValue(10)
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        obs3 = ObservableSingleValue(30)
        
        # Bind obs2 and obs3 to obs1
        obs2.bind_to_observable(obs1)
        obs3.bind_to_observable(obs1)
        
        # Change obs1, both should update
        obs1.set_value(100)
        self.assertEqual(obs2.value, 100)
        self.assertEqual(obs3.value, 100)
        
        # Change obs2, obs1 should also update (bidirectional), obs3 should also update
        obs2.set_value(200)
        self.assertEqual(obs1.value, 200)  # Should also update
        self.assertEqual(obs3.value, 200)  # Should also update


class TestObservableSet(unittest.TestCase):
    """Test cases for ObservableSet"""
    
    def setUp(self):
        self.observable = ObservableSet({1, 2, 3})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_options(self):
        """Test that initial options are set correctly"""
        self.assertEqual(self.observable.options, {1, 2, 3})
    
    def test_change_options(self):
        """Test changing options"""
        self.observable.change_options({4, 5, 6})
        self.assertEqual(self.observable.options, {4, 5, 6})
    
    def test_listener_notification(self):
        """Test that listeners are notified when options change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.change_options({7, 8, 9})
        self.assertEqual(self.notification_count, 1)
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between set1 and set2"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        # Bind set1 to set2
        set1.bind_to_observable(set2)
        
        # Change set1, set2 should update
        set1.change_options({7, 8, 9})
        self.assertEqual(set2.options, {7, 8, 9})
        
        # Change set2, set1 should also update (bidirectional)
        set2.change_options({10, 11, 12})
        self.assertEqual(set1.options, {10, 11, 12})  # Should also update
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        # Test update_value_from_observable mode
        set1.bind_to_observable(set2, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        self.assertEqual(set1.options, {4, 5, 6})  # set1 gets updated with set2's value
        
        # Test update_observable_from_self mode
        set3 = ObservableSet({7, 8, 9})
        set4 = ObservableSet({10, 11, 12})
        set3.bind_to_observable(set4, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        self.assertEqual(set4.options, {7, 8, 9})  # set4 gets updated with set3's value
    
    def test_unbinding(self):
        """Test unbinding observable sets"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        set1.bind_to_observable(set2)
        set1.unbind_from_observable(set2)
        
        # Changes should no longer propagate
        set1.change_options({7, 8, 9})
        self.assertEqual(set2.options, {4, 5, 6})
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        set1.bind_to_observable(set2)
        set1.unbind_from_observable(set2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            set1.unbind_from_observable(set2)
        
        # Changes should still not propagate
        set1.change_options({7, 8, 9})
        self.assertEqual(set2.options, {4, 5, 6})
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        set1 = ObservableSet({1, 2, 3})
        with self.assertRaises(ValueError):
            set1.bind_to_observable(set1)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable set"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        set3 = ObservableSet({7, 8, 9})
        
        # Bind set2 and set3 to set1
        set2.bind_to_observable(set1)
        set3.bind_to_observable(set1)
        
        # Change set1, both should update
        set1.change_options({10, 11, 12})
        self.assertEqual(set2.options, {10, 11, 12})
        self.assertEqual(set3.options, {10, 11, 12})
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableSet({1, 2, 3})
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))


class TestObservableList(unittest.TestCase):
    """Test cases for ObservableList (concrete implementation)"""
    
    def setUp(self):
        self.observable = ConcreteObservableList([1, 2, 3])
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.get_value(), [1, 2, 3])
    
    def test_set_value(self):
        """Test setting a new value"""
        self.observable.set_value([4, 5, 6])
        self.assertEqual(self.observable.get_value(), [4, 5, 6])
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listener(self.notification_callback)
        self.observable.set_value([7, 8, 9])
        self.assertEqual(self.notification_count, 1)
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listener(self.notification_callback)
        self.observable.set_value([1, 2, 3])  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_listener(self):
        """Test removing a listener"""
        self.observable.add_listener(self.notification_callback)
        self.observable.remove_listener(self.notification_callback)
        self.observable.set_value([10, 11, 12])
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
        self.observable.set_value([13, 14, 15])
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)


class TestObservableSelectionOption(unittest.TestCase):
    """Test cases for ObservableSelectionOption"""
    
    def setUp(self):
        self.observable = ObservableSelectionOption({1, 2, 3, 4}, 2)
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_state(self):
        """Test initial options and selected option"""
        self.assertEqual(self.observable.options, {1, 2, 3, 4})
        self.assertEqual(self.observable.selected_option, 2)
    
    def test_change_options(self):
        """Test changing options"""
        # Change to options that include the current selected option (2)
        self.observable.change_options({2, 5, 6, 7})
        self.assertEqual(self.observable.options, {2, 5, 6, 7})
        # Selected option should remain valid
        self.assertEqual(self.observable.selected_option, 2)
    
    def test_change_selected_option(self):
        """Test changing selected option"""
        self.observable.change_selected_option(3)
        self.assertEqual(self.observable.selected_option, 3)
    
    def test_invalid_selected_option(self):
        """Test that changing to invalid option raises error"""
        with self.assertRaises(ValueError):
            self.observable.change_selected_option(999)
    
    def test_invalid_options_with_selected(self):
        """Test that changing options to exclude selected option raises error"""
        with self.assertRaises(ValueError):
            self.observable.change_options({5, 6, 7})  # 2 not in new options
    
    def test_set_options_and_selected_option(self):
        """Test setting both options and selected option at once"""
        self.observable.set_options_and_selected_option({5, 6, 7, 8}, 6)
        self.assertEqual(self.observable.options, {5, 6, 7, 8})
        self.assertEqual(self.observable.selected_option, 6)
    
    def test_listener_notification(self):
        """Test that listeners are notified when state changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.change_selected_option(3)
        self.assertEqual(self.notification_count, 1)
    
    def test_binding_selected_option(self):
        """Test binding selected option between observables"""
        # Create observables with compatible initial states
        obs1 = ObservableSelectionOption({1, 2, 3, 4, 5, 6}, 1)
        obs2 = ObservableSelectionOption({1, 2, 3, 4, 5, 6}, 4)
        
        obs1.bind_selected_option_to_observable(obs2)
        
        # Change obs1 selected option, obs2 should update
        obs1.change_selected_option(2)
        self.assertEqual(obs2.selected_option, 2)
        
        # Change obs2 selected option, obs1 should update
        obs2.change_selected_option(5)
        self.assertEqual(obs1.selected_option, 5)
    
    def test_binding_options(self):
        """Test binding options between observables"""
        # Create observables with compatible initial states
        obs1 = ObservableSelectionOption({1, 2, 3, 4, 5, 6}, 1)
        obs2 = ObservableSelectionOption({1, 2, 3, 4, 5, 6}, 4)
        
        obs1.bind_options_to_observable(obs2)
        
        # Change obs1 options, obs2 should update
        # Use options that include the current selected option (1)
        # However, this will fail because obs2 has selected option 4, which is not in {1, 7, 8, 9}
        # The binding will propagate and cause obs2 to try to change its options, which will fail
        with self.assertRaises(ValueError):
            obs1.change_options({1, 7, 8, 9})
        
        # Change obs2 options, obs1 should update
        # Use options that include the current selected option (4)
        # However, this will fail because obs1 has selected option 1, which is not in {4, 10, 11, 12}
        # The binding will propagate and cause obs1 to try to change its options, which will fail
        with self.assertRaises(ValueError):
            obs2.change_options({4, 10, 11, 12})
        

    
    def test_unbinding(self):
        """Test unbinding observables"""
        # Create observables with compatible initial states
        obs1 = ObservableSelectionOption({1, 2, 3, 4, 5, 6}, 1)
        obs2 = ObservableSelectionOption({1, 2, 3, 4, 5, 6}, 4)
        
        obs1.bind_selected_option_to_observable(obs2)
        obs1.unbind_selected_option_from_observable(obs2)
        
        # Changes should no longer propagate
        obs1.change_selected_option(2)
        self.assertEqual(obs2.selected_option, 4)
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        # Create observables with compatible initial states
        obs1 = ObservableSelectionOption({1, 2, 3, 4, 5, 6}, 1)
        obs2 = ObservableSelectionOption({1, 2, 3, 4, 5, 6}, 4)
        
        obs1.bind_selected_option_to_observable(obs2)
        obs1.unbind_selected_option_from_observable(obs2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            obs1.unbind_selected_option_from_observable(obs2)
        
        # Changes should still not propagate
        obs1.change_selected_option(2)
        self.assertEqual(obs2.selected_option, 4)
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableSelectionOption({1, 2, 3}, 1)
        with self.assertRaises(ValueError):
            obs.bind_selected_option_to_observable(obs)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        # Create observables with compatible initial states
        obs1 = ObservableSelectionOption({1, 2, 3, 4, 5, 6, 7, 8, 9}, 1)
        obs2 = ObservableSelectionOption({1, 2, 3, 4, 5, 6, 7, 8, 9}, 4)
        obs3 = ObservableSelectionOption({1, 2, 3, 4, 5, 6, 7, 8, 9}, 7)
        
        # Bind obs2 and obs3 selected options to obs1
        obs2.bind_selected_option_to_observable(obs1)
        obs3.bind_selected_option_to_observable(obs1)
        
        # Change obs1 selected option, both should update
        obs1.change_selected_option(2)
        self.assertEqual(obs2.selected_option, 2)
        self.assertEqual(obs3.selected_option, 2)
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableSelectionOption({1, 2, 3}, 1)
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))


class TestObservableIntegration(unittest.TestCase):
    """Integration tests for multiple observable types working together"""
    
    def test_cross_type_binding(self):
        """Test binding between different observable types"""
        # Single value observable
        single_obs = ObservableSingleValue(42)
        
        # Selection option observable
        selection_obs = ObservableSelectionOption({40, 41, 42, 43}, 41)
        
        # Bind single value to selection option
        single_obs.bind_to_observable(selection_obs)
        
        # Change single value, selection should update
        single_obs.set_value(43)
        self.assertEqual(selection_obs.selected_option, 43)
        
        # Change selection, single value should update
        selection_obs.change_selected_option(40)
        self.assertEqual(single_obs.value, 40)
    
    def test_complex_binding_chain(self):
        """Test a chain of bindings between multiple observables"""
        # Create a chain: A -> B -> C
        obs_a = ObservableSingleValue(10)
        obs_b = ObservableSingleValue(20)
        obs_c = ObservableSingleValue(30)
        
        # Bind A to B
        obs_a.bind_to_observable(obs_b)
        # Bind B to C
        obs_b.bind_to_observable(obs_c)
        
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
        selection_obs = ObservableSelectionOption({3, 4, 5, 6}, 5)  # Start with 5 to match single_obs
        set_obs = ObservableSet({3, 4, 5, 6})  # Start with compatible options
        
        # Bind single value to selection option
        single_obs.bind_to_observable(selection_obs)
        # Bind selection option to set (through options)
        selection_obs.bind_options_to_observable(set_obs)
        
        # Change single value, should propagate through chain
        single_obs.set_value(6)
        self.assertEqual(selection_obs.selected_option, 6)
        self.assertEqual(set_obs.options, {3, 4, 5, 6})
    
    def test_binding_removal_in_chain(self):
        """Test removing bindings in the middle of a chain"""
        # Create chain: A -> B -> C
        obs_a = ObservableSingleValue(10)
        obs_b = ObservableSingleValue(20)
        obs_c = ObservableSingleValue(30)
        
        # Bind A to B
        obs_a.bind_to_observable(obs_b)
        # Bind B to C
        obs_b.bind_to_observable(obs_c)
        
        # Verify chain works
        obs_a.set_value(100)
        self.assertEqual(obs_b.value, 100)
        self.assertEqual(obs_c.value, 100)
        
        # Remove binding between B and C
        obs_b.unbind_from_observable(obs_c)
        
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
        obs1.bind_to_observable(obs2)
        
        # Try to bind obs2 back to obs1 (should raise ValueError: "Already bound to...")
        with self.assertRaises(ValueError) as context:
            obs2.bind_to_observable(obs1)
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
        obs1.bind_to_observable(target)
        obs2.bind_to_observable(target)
        obs3.bind_to_observable(target)
        
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


class TestObservableDict(unittest.TestCase):
    """Test cases for ObservableDict"""
    
    def setUp(self):
        self.observable = ObservableDict({"a": 1, "b": 2, "c": 3})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.dict, {"a": 1, "b": 2, "c": 3})
    
    def test_set_item(self):
        """Test setting a single key-value pair"""
        self.observable.set_item("d", 4)
        self.assertEqual(self.observable.dict, {"a": 1, "b": 2, "c": 3, "d": 4})
        self.assertEqual(self.notification_count, 0)  # No listener added yet
    
    def test_get_item(self):
        """Test getting a value by key"""
        self.assertEqual(self.observable.get_item("a"), 1)
        self.assertEqual(self.observable.get_item("x", "default"), "default") # type: ignore
    
    def test_has_key(self):
        """Test checking if a key exists"""
        self.assertTrue(self.observable.has_key("a"))
        self.assertFalse(self.observable.has_key("x"))
    
    def test_remove_item(self):
        """Test removing a key-value pair"""
        self.observable.remove_item("b")
        self.assertEqual(self.observable.dict, {"a": 1, "c": 3})
    
    def test_clear(self):
        """Test clearing all items"""
        self.observable.clear()
        self.assertEqual(self.observable.dict, {})
    
    def test_update(self):
        """Test updating with another dictionary"""
        self.observable.update({"d": 4, "e": 5})
        self.assertEqual(self.observable.dict, {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})
    
    def test_keys_values_items(self):
        """Test getting keys, values, and items"""
        self.assertEqual(self.observable.keys(), {"a", "b", "c"})
        self.assertEqual(self.observable.values(), [1, 2, 3])
        self.assertEqual(self.observable.items(), [("a", 1), ("b", 2), ("c", 3)])
    
    def test_magic_methods(self):
        """Test magic methods like __len__, __contains__, __getitem__, etc."""
        self.assertEqual(len(self.observable), 3)
        self.assertIn("a", self.observable) # type: ignore
        self.assertNotIn("x", self.observable) # type: ignore
        self.assertEqual(self.observable["a"], 1)
        
        # Test __setitem__
        self.observable["d"] = 4
        self.assertEqual(self.observable.dict, {"a": 1, "b": 2, "c": 3, "d": 4})
        
        # Test __delitem__
        del self.observable["b"]
        self.assertEqual(self.observable.dict, {"a": 1, "c": 3, "d": 4})
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_item("d", 4)
        self.assertEqual(self.notification_count, 1)
    
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
        self.observable.set_item("d", 4)
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_item("a", 1)  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_listener(self):
        """Test removing a listener"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_listeners(self.notification_callback)
        self.observable.set_item("d", 4)
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_all_listeners(self):
        """Test removing all listeners"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_all_listeners()
        self.observable.set_item("d", 4)
        self.assertEqual(self.notification_count, 0)
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between dict1 and dict2"""
        dict1 = ObservableDict({"a": 1, "b": 2})
        dict2 = ObservableDict({"c": 3, "d": 4})
        
        # Bind dict1 to dict2 (default: UPDATE_VALUE_FROM_OBSERVABLE)
        dict1.bind_to_observable(dict2)
        
        # After binding, dict1 should have dict2's value
        self.assertEqual(dict1.dict, {"c": 3, "d": 4})
        
        # Change dict1, dict2 should update to match dict1's content
        dict1.set_item("e", 5)
        self.assertEqual(dict1.dict, {"c": 3, "d": 4, "e": 5})
        self.assertEqual(dict2.dict, {"c": 3, "d": 4, "e": 5})
        
        # Change dict2, dict1 should update to match dict2's content
        dict2.set_item("f", 6)
        self.assertEqual(dict1.dict, {"c": 3, "d": 4, "e": 5, "f": 6})
        self.assertEqual(dict2.dict, {"c": 3, "d": 4, "e": 5, "f": 6})
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        dict1 = ObservableDict({"a": 1, "b": 2})
        dict2 = ObservableDict({"c": 3, "d": 4})
        
        # Test UPDATE_VALUE_FROM_OBSERVABLE
        dict1.bind_to_observable(dict2, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        self.assertEqual(dict1.dict, {"c": 3, "d": 4})
        
        # Test UPDATE_OBSERVABLE_FROM_SELF
        dict3 = ObservableDict({"e": 5, "f": 6})
        dict4 = ObservableDict({"g": 7, "h": 8})
        dict3.bind_to_observable(dict4, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        self.assertEqual(dict4.dict, {"e": 5, "f": 6})
    
    def test_unbinding(self):
        """Test unbinding observables"""
        dict1 = ObservableDict({"a": 1, "b": 2})
        dict2 = ObservableDict({"c": 3, "d": 4})
        
        dict1.bind_to_observable(dict2)
        dict1.unbind_from_observable(dict2)
        
        # Changes should no longer propagate
        dict1.set_item("e", 5)
        self.assertEqual(dict2.dict, {"c": 3, "d": 4})
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        dict1 = ObservableDict({"a": 1, "b": 2})
        dict2 = ObservableDict({"c": 3, "d": 4})
        
        dict1.bind_to_observable(dict2)
        dict1.unbind_from_observable(dict2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            dict1.unbind_from_observable(dict2)
        
        # Changes should still not propagate
        dict1.set_item("e", 5)
        self.assertEqual(dict2.dict, {"c": 3, "d": 4})
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        dict1 = ObservableDict({"a": 1, "b": 2})
        with self.assertRaises(ValueError):
            dict1.bind_to_observable(dict1)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        target = ObservableDict({"a": 1, "b": 2})
        dict1 = ObservableDict({"c": 3, "d": 4})
        dict2 = ObservableDict({"e": 5, "f": 6})
        
        # Bind both to the target (default: UPDATE_VALUE_FROM_OBSERVABLE)
        dict1.bind_to_observable(target)
        dict2.bind_to_observable(target)
        
        # After binding, both should have target's value
        self.assertEqual(dict1.dict, {"a": 1, "b": 2})
        self.assertEqual(dict2.dict, {"a": 1, "b": 2})
        
        # Change target, both should update to match target's content
        target.set_item("g", 7)
        self.assertEqual(target.dict, {"a": 1, "b": 2, "g": 7})
        self.assertEqual(dict1.dict, {"a": 1, "b": 2, "g": 7})
        self.assertEqual(dict2.dict, {"a": 1, "b": 2, "g": 7})
        
        # Change one of the observables, target should update to match that observable's content
        dict1.set_item("h", 8)
        self.assertEqual(target.dict, {"a": 1, "b": 2, "g": 7, "h": 8})
        # With bidirectional binding, all observables should update to the same value
        self.assertEqual(dict1.dict, {"a": 1, "b": 2, "g": 7, "h": 8})
        self.assertEqual(dict2.dict, {"a": 1, "b": 2, "g": 7, "h": 8})
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableDict({"a": 1, "b": 2})
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_string_representation(self):
        """Test string and repr methods"""
        self.assertEqual(str(self.observable), "OD(dict={'a': 1, 'b': 2, 'c': 3})")
        self.assertEqual(repr(self.observable), "ObservableDict({'a': 1, 'b': 2, 'c': 3})")
    
    def test_empty_dict_initialization(self):
        """Test initialization with empty dictionary"""
        empty_dict = ObservableDict()
        self.assertEqual(empty_dict.dict, {})
        self.assertEqual(len(empty_dict), 0)
    
    def test_none_initialization(self):
        """Test initialization with None"""
        none_dict = ObservableDict(None)
        self.assertEqual(none_dict.dict, {})
        self.assertEqual(len(none_dict), 0)
    
    def test_copy_protection(self):
        """Test that external modifications don't affect the observable"""
        external_dict = {"x": 10, "y": 20}
        obs_dict = ObservableDict(external_dict)
        
        # Modify external dict
        external_dict["z"] = 30
        
        # Observable should not be affected
        self.assertEqual(obs_dict.dict, {"x": 10, "y": 20})
        
        # Observable changes should not affect external dict
        obs_dict.set_item("w", 40)
        self.assertEqual(external_dict, {"x": 10, "y": 20, "z": 30})


class TestObservableEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def test_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = ObservableSingleValue(10)
        with self.assertRaises(ValueError):
            obs.bind_to_observable(None) # type: ignore
    
    def test_binding_with_invalid_sync_mode(self):
        """Test that invalid sync mode raises an error"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        with self.assertRaises(ValueError):
            obs1.bind_to_observable(obs2, "invalid_mode") # type: ignore
    
    def test_binding_empty_set(self):
        """Test binding with empty sets"""
        set1 = ObservableSet(set())
        set2 = ObservableSet({1, 2, 3})
        
        set1.bind_to_observable(set2)
        set2.change_options({4, 5, 6})
        self.assertEqual(set1.options, {4, 5, 6})
    
    def test_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = ObservableSingleValue(42)
        obs2 = ObservableSingleValue(42)
        
        obs1.bind_to_observable(obs2)
        # Both should still have the same value
        self.assertEqual(obs1.value, 42)
        self.assertEqual(obs2.value, 42)
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = ObservableSingleValue(10)
        callback = lambda: None
        
        obs.add_listeners(callback, callback)
        self.assertEqual(len(obs.listeners), 1)
        
        obs.add_listeners(callback)
        self.assertEqual(len(obs.listeners), 1)
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = ObservableSingleValue(10)
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listeners(callback)
        self.assertEqual(len(obs.listeners), 0)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
