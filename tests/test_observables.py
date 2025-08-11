import unittest
from typing import List, Set, Callable
from observables import (
    ObservableSingleValue,
    ObservableSet,
    ObservableList,
    ObservableSelectionOption,
    ObservableDict,
    SyncMode,
    ObservableEnum,
)


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
        
        obs1.bind_to_observable(obs2, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        obs1.unbind_from_observable(obs2)
        
        # Changes should no longer propagate
        obs1.set_value(50)
        self.assertEqual(obs2.value, 20)
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(20)
        
        obs1.bind_to_observable(obs2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        obs1.unbind_from_observable(obs2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            obs1.unbind_from_observable(obs2)
        
        # Changes should still not propagate
        obs1.set_value(50)
        # Since we used UPDATE_OBSERVABLE_FROM_SELF, obs2 was updated to obs1's value (10) during binding
        # After unbinding, obs2 should still have that value, not the original 20
        self.assertEqual(obs2.value, 10)
    
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
    
    def test_initialization_with_carries_bindable_single_value(self):
        """Test initialization with CarriesBindableSingleValue"""
        # Create a source observable
        source = ObservableSingleValue(100)
        
        # Create a new observable initialized with the source
        target = ObservableSingleValue(source)
        
        # Check that the target has the same initial value
        self.assertEqual(target.value, 100)
        
        # Check that they are bound together
        source.set_value(200)
        self.assertEqual(target.value, 200)
        
        # Check bidirectional binding
        target.set_value(300)
        self.assertEqual(source.value, 300)
    
    def test_initialization_with_carries_bindable_single_value_with_validator(self):
        """Test initialization with CarriesBindableSingleValue and validator"""
        def validate_positive(value):
            return value > 0
        
        # Create a source observable with validator
        source = ObservableSingleValue(50, validator=validate_positive)
        
        # Create a target observable initialized with the source and validator
        target = ObservableSingleValue(source, validator=validate_positive)
        
        # Check that the target has the same initial value
        self.assertEqual(target.value, 50)
        
        # Check that they are bound together
        source.set_value(75)
        self.assertEqual(target.value, 75)
        
        # Check that validation still works
        with self.assertRaises(ValueError):
            source.set_value(-10)
        
        # Target should still have the previous valid value
        self.assertEqual(target.value, 75)
    
    def test_initialization_with_carries_bindable_single_value_different_types(self):
        """Test initialization with CarriesBindableSingleValue of different types"""
        # Test with string type
        source_str = ObservableSingleValue("hello")
        target_str = ObservableSingleValue(source_str)
        self.assertEqual(target_str.value, "hello")
        
        # Test with float type
        source_float = ObservableSingleValue(3.14)
        target_float = ObservableSingleValue(source_float)
        self.assertEqual(target_float.value, 3.14)
        
        # Test with list type
        source_list = ObservableSingleValue([1, 2, 3])
        target_list = ObservableSingleValue(source_list)
        self.assertEqual(target_list.value, [1, 2, 3])
    
    def test_initialization_with_carries_bindable_single_value_chain(self):
        """Test initialization with CarriesBindableSingleValue in a chain"""
        # Create a chain of observables
        obs1 = ObservableSingleValue(10)
        obs2 = ObservableSingleValue(obs1)
        obs3 = ObservableSingleValue(obs2)
        
        # Check initial values
        self.assertEqual(obs1.value, 10)
        self.assertEqual(obs2.value, 10)
        self.assertEqual(obs3.value, 10)
        
        # Change the first observable
        obs1.set_value(20)
        self.assertEqual(obs1.value, 20)
        self.assertEqual(obs2.value, 20)
        self.assertEqual(obs3.value, 20)
        
        # Change the middle observable
        obs2.set_value(30)
        self.assertEqual(obs1.value, 30)
        self.assertEqual(obs2.value, 30)
        self.assertEqual(obs3.value, 30)
    
    def test_initialization_with_carries_bindable_single_value_unbinding(self):
        """Test that initialization with CarriesBindableSingleValue can be unbound"""
        source = ObservableSingleValue(100)
        target = ObservableSingleValue(source)
        
        # Verify they are bound
        self.assertEqual(target.value, 100)
        source.set_value(200)
        self.assertEqual(target.value, 200)
        
        # Unbind them
        target.unbind_from_observable(source)
        
        # Change source, target should not update
        source.set_value(300)
        self.assertEqual(target.value, 200)  # Should remain unchanged
        
        # Change target, source should not update
        target.set_value(400)
        self.assertEqual(source.value, 300)  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_single_value_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableSingleValue(100)
        target1 = ObservableSingleValue(source)
        target2 = ObservableSingleValue(source)
        target3 = ObservableSingleValue(source)
        
        # Check initial values
        self.assertEqual(target1.value, 100)
        self.assertEqual(target2.value, 100)
        self.assertEqual(target3.value, 100)
        
        # Change source, all targets should update
        source.set_value(200)
        self.assertEqual(target1.value, 200)
        self.assertEqual(target2.value, 200)
        self.assertEqual(target3.value, 200)
        
        # Change one target, source and other targets should update
        target1.set_value(300)
        self.assertEqual(source.value, 300)
        self.assertEqual(target2.value, 300)
        self.assertEqual(target3.value, 300)
    
    def test_initialization_with_carries_bindable_single_value_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableSingleValue"""
        # Test with None value in source
        source_none = ObservableSingleValue(None)
        target_none = ObservableSingleValue(source_none)
        self.assertIsNone(target_none.value)
        
        # Test with zero value
        source_zero = ObservableSingleValue(0)
        target_zero = ObservableSingleValue(source_zero)
        self.assertEqual(target_zero.value, 0)
        
        # Test with empty string
        source_empty = ObservableSingleValue("")
        target_empty = ObservableSingleValue(source_empty)
        self.assertEqual(target_empty.value, "")
    
    def test_initialization_with_carries_bindable_single_value_validation_errors(self):
        """Test validation errors when initializing with CarriesBindableSingleValue"""
        def validate_even(value):
            return value % 2 == 0
        
        # Create source with even value
        source = ObservableSingleValue(10, validator=validate_even)
        
        # Target should initialize successfully with even value
        target = ObservableSingleValue(source, validator=validate_even)
        self.assertEqual(target.value, 10)
        
        # Try to set odd value in source, should fail
        with self.assertRaises(ValueError):
            source.set_value(11)
        
        # Target should still have the previous valid value
        self.assertEqual(target.value, 10)
        
        # Set valid even value
        source.set_value(12)
        self.assertEqual(target.value, 12)
    
    def test_initialization_with_carries_bindable_single_value_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableSingleValue"""
        source = ObservableSingleValue(100)
        target = ObservableSingleValue(source)
        
        # Check binding consistency
        is_consistent, message = target.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Check that they are properly bound
        self.assertTrue(target._binding_handler.is_bound_to(source._binding_handler))
        self.assertTrue(source._binding_handler.is_bound_to(target._binding_handler))
    
    def test_initialization_with_carries_bindable_single_value_performance(self):
        """Test performance of initialization with CarriesBindableSingleValue"""
        import time
        
        # Create source
        source = ObservableSingleValue(100)
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableSingleValue(source)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(end_time - start_time, 1.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableSingleValue(source)
        source.set_value(200)
        self.assertEqual(target.value, 200)


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
        set1.bind_to_observable(set2)
        
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
        set1.bind_to_observable(set2, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        self.assertEqual(set1.value, {4, 5, 6})  # set1 gets updated with set2's value
        
        # Test update_observable_from_self mode
        set3 = ObservableSet({7, 8, 9})
        set4 = ObservableSet({10, 11, 12})
        set3.bind_to_observable(set4, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        self.assertEqual(set4.value, {7, 8, 9})  # set4 gets updated with set3's value
    
    def test_unbinding(self):
        """Test unbinding observable sets"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        set1.bind_to_observable(set2, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        set1.unbind_from_observable(set2)
        
        # Changes should no longer propagate
        set1.set_set({7, 8, 9})
        self.assertEqual(set2.value, {4, 5, 6})
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        set1 = ObservableSet({1, 2, 3})
        set2 = ObservableSet({4, 5, 6})
        
        set1.bind_to_observable(set2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        set1.unbind_from_observable(set2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            set1.unbind_from_observable(set2)
        
        # Changes should still not propagate
        set1.set_set({7, 8, 9})
        # Since we used UPDATE_OBSERVABLE_FROM_SELF, set2 was updated to set1's value ({1, 2, 3}) during binding
        # After unbinding, set2 should still have that value, not the original {4, 5, 6}
        self.assertEqual(set2.value, {1, 2, 3})
    
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
        target.unbind_from_observable(source)
        
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
        self.assertTrue(target._binding_handler.is_bound_to(source._binding_handler))
        self.assertTrue(source._binding_handler.is_bound_to(target._binding_handler))
    
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
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(total_time, 1.0)
    
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
    
    def test_initialization_with_carries_bindable_list(self):
        """Test initialization with CarriesBindableList"""
        # Create a source observable list
        source = ObservableList([1, 2, 3])
        
        # Create a new observable list initialized with the source
        target = ObservableList(source)
        
        # Check that the target has the same initial value
        self.assertEqual(target.value, [1, 2, 3])
        
        # Check that they are bound together
        source.append(4)
        self.assertEqual(target.value, [1, 2, 3, 4])
        
        # Check bidirectional binding
        target.append(5)
        self.assertEqual(source.value, [1, 2, 3, 4, 5])
    
    def test_initialization_with_carries_bindable_list_chain(self):
        """Test initialization with CarriesBindableList in a chain"""
        # Create a chain of observable lists
        obs1 = ObservableList([10])
        obs2 = ObservableList(obs1)
        obs3 = ObservableList(obs2)
        
        # Check initial values
        self.assertEqual(obs1.value, [10])
        self.assertEqual(obs2.value, [10])
        self.assertEqual(obs3.value, [10])
        
        # Change the first observable
        obs1.append(20)
        self.assertEqual(obs1.value, [10, 20])
        self.assertEqual(obs2.value, [10, 20])
        self.assertEqual(obs3.value, [10, 20])
        
        # Change the middle observable
        obs2.append(30)
        self.assertEqual(obs1.value, [10, 20, 30])
        self.assertEqual(obs2.value, [10, 20, 30])
        self.assertEqual(obs3.value, [10, 20, 30])
    
    def test_initialization_with_carries_bindable_list_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableList([100])
        target1 = ObservableList(source)
        target2 = ObservableList(source)
        target3 = ObservableList(source)
        
        # Check initial values
        self.assertEqual(target1.value, [100])
        self.assertEqual(target2.value, [100])
        self.assertEqual(target3.value, [100])
        
        # Change source, all targets should update
        source.append(200)
        self.assertEqual(target1.value, [100, 200])
        self.assertEqual(target2.value, [100, 200])
        self.assertEqual(target3.value, [100, 200])
        
        # Change one target, source and other targets should update
        target1.append(300)
        self.assertEqual(source.value, [100, 200, 300])
        self.assertEqual(target2.value, [100, 200, 300])
        self.assertEqual(target3.value, [100, 200, 300])
    
    def test_initialization_with_carries_bindable_list_unbinding(self):
        """Test that initialization with CarriesBindableList can be unbound"""
        source = ObservableList([1, 2])
        target = ObservableList(source)
        
        # Verify they are bound
        self.assertEqual(target.value, [1, 2])
        source.append(3)
        self.assertEqual(target.value, [1, 2, 3])
        
        # Unbind them
        target.unbind_from_observable(source)
        
        # Change source, target should not update
        source.append(4)
        self.assertEqual(target.value, [1, 2, 3])  # Should remain unchanged
        
        # Change target, source should not update
        target.append(5)
        self.assertEqual(source.value, [1, 2, 3, 4])  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_list_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableList"""
        # Test with empty list
        source_empty = ObservableList([])
        target_empty = ObservableList(source_empty)
        self.assertEqual(target_empty.value, [])
        
        # Test with None values in list
        source_none = ObservableList([None, 1, None])
        target_none = ObservableList(source_none)
        self.assertEqual(target_none.value, [None, 1, None])
        
        # Test with nested list
        source_nested = ObservableList([[1, 2], [3, 4]])
        target_nested = ObservableList(source_nested)
        self.assertEqual(target_nested.value, [[1, 2], [3, 4]])
    
    def test_initialization_with_carries_bindable_list_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableList"""
        source = ObservableList([1, 2, 3])
        target = ObservableList(source)
        
        # Check binding consistency
        is_consistent, message = target.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Check that they are properly bound
        self.assertTrue(target._binding_handler.is_bound_to(source._binding_handler))
        self.assertTrue(source._binding_handler.is_bound_to(target._binding_handler))
    
    def test_initialization_with_carries_bindable_list_performance(self):
        """Test performance of initialization with CarriesBindableList"""
        # Create a source observable list
        source = ObservableList([1, 2, 3, 4, 5])
        
        # Measure time for multiple initializations
        import time
        start_time = time.time()
        
        for _ in range(1000):
            target = ObservableList(source)
            _ = target.value  # Access to ensure initialization is complete
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(total_time, 1.0)
    
    def test_none_initialization(self):
        """Test initialization with None value"""
        # Test initialization with None
        obs = ObservableList(None)
        self.assertEqual(obs.value, [])
        
        # Test that it's a proper empty list, not None
        self.assertIsInstance(obs.value, list)
        self.assertEqual(len(obs.value), 0)
        
        # Test that we can add items to it
        obs.append(1)
        obs.append(2)
        self.assertEqual(obs.value, [1, 2])
    
    def test_empty_list_initialization(self):
        """Test initialization with empty list"""
        # Test initialization with empty list
        obs = ObservableList([])
        self.assertEqual(obs.value, [])
        
        # Test that it's a proper empty list
        self.assertIsInstance(obs.value, list)
        self.assertEqual(len(obs.value), 0)
        
        # Test that we can add items to it
        obs.append(10)
        obs.append(20)
        self.assertEqual(obs.value, [10, 20])
    
    def test_none_vs_empty_list_behavior(self):
        """Test that None and empty list initialization behave identically"""
        obs_none = ObservableList(None)
        obs_empty = ObservableList([])
        
        # Both should start with empty lists
        self.assertEqual(obs_none.value, obs_empty.value)
        self.assertEqual(obs_none.value, [])
        
        # Both should behave the same way when modified
        obs_none.append(1)
        obs_empty.append(1)
        
        self.assertEqual(obs_none.value, obs_empty.value)
        self.assertEqual(obs_none.value, [1])


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
        self.observable.set_selected_option_and_available_options(6, {5, 6, 7, 8})
        self.assertEqual(self.observable.selected_option, 6)
        self.assertEqual(self.observable.options, {5, 6, 7, 8})
    
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
        
        obs1.bind_selected_option_to_observable(obs2, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        obs1.unbind_selected_option_from_observable(obs2)
        
        # Changes should no longer propagate
        obs1.change_selected_option(2)
        self.assertEqual(obs2.selected_option, 4)
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        # Create observables with compatible initial states
        obs1 = ObservableSelectionOption({1, 2, 3, 4, 5, 6}, 1)
        obs2 = ObservableSelectionOption({1, 2, 3, 4, 5, 6}, 4)
        
        obs1.bind_selected_option_to_observable(obs2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        obs1.unbind_selected_option_from_observable(obs2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            obs1.unbind_selected_option_from_observable(obs2)
        
        # Changes should still not propagate
        obs1.change_selected_option(2)
        # Since we used UPDATE_OBSERVABLE_FROM_SELF, obs2 was updated to obs1's value (1) during binding
        # After unbinding, obs2 should still have that value, not the original 4
        self.assertEqual(obs2.selected_option, 1)
    
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
    
    def test_initialization_with_carries_bindable_set_and_single_value(self):
        """Test initialization with CarriesBindableSet and CarriesBindableSingleValue"""
        # Create source observables
        source_options = ObservableSet({1, 2, 3, 4})
        source_selected = ObservableSingleValue(2)
        
        # Create a new observable selection option initialized with the sources
        target = ObservableSelectionOption(source_options, source_selected)
        
        # Check that the target has the same initial values
        self.assertEqual(target.options, {1, 2, 3, 4})
        self.assertEqual(target.selected_option, 2)
        
        # Check that they are bound together
        source_options.add(5)
        self.assertEqual(target.options, {1, 2, 3, 4, 5})
        
        source_selected.set_value(3)
        self.assertEqual(target.selected_option, 3)
        
        # Check bidirectional binding
        target.add(6)
        self.assertEqual(source_options.value, {1, 2, 3, 4, 5, 6})
        
        target.selected_option = 4
        self.assertEqual(source_selected.value, 4)
    
    def test_initialization_with_carries_bindable_set_only(self):
        """Test initialization with only CarriesBindableSet"""
        # Create source observable set
        source_options = ObservableSet({10, 20, 30})
        
        # Create a new observable selection option initialized with the source set
        target = ObservableSelectionOption(source_options, 20)
        
        # Check that the target has the same initial options
        self.assertEqual(target.options, {10, 20, 30})
        self.assertEqual(target.selected_option, 20)
        
        # Check that they are bound together
        source_options.add(40)
        self.assertEqual(target.options, {10, 20, 30, 40})
        
        # Check bidirectional binding
        target.add(50)
        self.assertEqual(source_options.value, {10, 20, 30, 40, 50})
    
    def test_initialization_with_carries_bindable_single_value_only(self):
        """Test initialization with only CarriesBindableSingleValue"""
        # Create source observable single value
        source_selected = ObservableSingleValue(100)
        
        # Create a new observable selection option initialized with the source single value
        target = ObservableSelectionOption({100, 200, 300}, source_selected)
        
        # Check that the target has the same initial selected option
        self.assertEqual(target.options, {100, 200, 300})
        self.assertEqual(target.selected_option, 100)
        
        # Check that they are bound together
        source_selected.set_value(200)
        self.assertEqual(target.selected_option, 200)
        
        # Check bidirectional binding
        target.selected_option = 300
        self.assertEqual(source_selected.value, 300)
    
    def test_initialization_with_carries_bindable_chain(self):
        """Test initialization with CarriesBindableSet and CarriesBindableSingleValue in a chain"""
        # Create a chain of observable selection options
        obs1 = ObservableSelectionOption({1, 2}, 1)
        obs2 = ObservableSelectionOption(obs1, obs1)
        obs3 = ObservableSelectionOption(obs2, obs2)
        
        # Check initial values
        self.assertEqual(obs1.options, {1, 2})
        self.assertEqual(obs1.selected_option, 1)
        self.assertEqual(obs2.options, {1, 2})
        self.assertEqual(obs2.selected_option, 1)
        self.assertEqual(obs3.options, {1, 2})
        self.assertEqual(obs3.selected_option, 1)
        
        # Change the first observable
        obs1.add(3)
        obs1.selected_option = 2
        self.assertEqual(obs1.options, {1, 2, 3})
        self.assertEqual(obs1.selected_option, 2)
        self.assertEqual(obs2.options, {1, 2, 3})
        self.assertEqual(obs2.selected_option, 2)
        self.assertEqual(obs3.options, {1, 2, 3})
        self.assertEqual(obs3.selected_option, 2)
    
    def test_initialization_with_carries_bindable_multiple_targets(self):
        """Test multiple targets initialized with the same sources"""
        source_options = ObservableSet({100, 200})
        source_selected = ObservableSingleValue(100)
        
        target1 = ObservableSelectionOption(source_options, source_selected)
        target2 = ObservableSelectionOption(source_options, source_selected)
        target3 = ObservableSelectionOption(source_options, source_selected)
        
        # Check initial values
        self.assertEqual(target1.options, {100, 200})
        self.assertEqual(target1.selected_option, 100)
        self.assertEqual(target2.options, {100, 200})
        self.assertEqual(target2.selected_option, 100)
        self.assertEqual(target3.options, {100, 200})
        self.assertEqual(target3.selected_option, 100)
        
        # Change source options, all targets should update
        source_options.add(300)
        self.assertEqual(target1.options, {100, 200, 300})
        self.assertEqual(target2.options, {100, 200, 300})
        self.assertEqual(target3.options, {100, 200, 300})
        
        # Change source selected option, all targets should update
        source_selected.set_value(200)
        self.assertEqual(target1.selected_option, 200)
        self.assertEqual(target2.selected_option, 200)
        self.assertEqual(target3.selected_option, 200)
    
    def test_initialization_with_carries_bindable_unbinding(self):
        """Test that initialization with CarriesBindableSet and CarriesBindableSingleValue can be unbound"""
        source_options = ObservableSet({1, 2})
        source_selected = ObservableSingleValue(1)
        
        target = ObservableSelectionOption(source_options, source_selected)
        
        # Verify they are bound
        self.assertEqual(target.options, {1, 2})
        self.assertEqual(target.selected_option, 1)
        
        source_options.add(3)
        source_selected.set_value(2)
        self.assertEqual(target.options, {1, 2, 3})
        self.assertEqual(target.selected_option, 2)
        
        # Unbind them
        target.unbind_options_from_observable(source_options)
        target.unbind_selected_option_from_observable(source_selected)
        
        # Change sources, target should not update
        source_options.add(4)
        source_selected.set_value(3)
        self.assertEqual(target.options, {1, 2, 3})  # Should remain unchanged
        self.assertEqual(target.selected_option, 2)  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableSet and CarriesBindableSingleValue"""
        # Test with empty set
        source_empty = ObservableSet(set())
        source_selected = ObservableSingleValue(None)
        target_empty = ObservableSelectionOption(source_empty, source_selected)
        self.assertEqual(target_empty.options, set())
        self.assertIsNone(target_empty.selected_option)
        
        # Test with None values
        source_none = ObservableSet({None, 1, None})
        source_none_selected = ObservableSingleValue(None)
        target_none = ObservableSelectionOption(source_none, source_none_selected)
        self.assertEqual(target_none.options, {None, 1})
        self.assertIsNone(target_none.selected_option)
    
    def test_initialization_with_carries_bindable_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableSet and CarriesBindableSingleValue"""
        source_options = ObservableSet({1, 2, 3})
        source_selected = ObservableSingleValue(1)
        
        target = ObservableSelectionOption(source_options, source_selected)
        
        # Check binding consistency
        is_consistent, message = target.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Check that they are properly bound
        self.assertTrue(target._options_binding_handler.is_bound_to(source_options._binding_handler))
        self.assertTrue(target._selected_option_binding_handler.is_bound_to(source_selected._binding_handler))
    
    def test_initialization_with_carries_bindable_performance(self):
        """Test performance of initialization with CarriesBindableSet and CarriesBindableSingleValue"""
        import time
        
        # Create sources
        source_options = ObservableSet({1, 2, 3, 4, 5})
        source_selected = ObservableSingleValue(1)
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableSelectionOption(source_options, source_selected)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(end_time - start_time, 1.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableSelectionOption(source_options, source_selected)
        source_options.add(6)
        source_selected.set_value(2)
        self.assertEqual(target.options, {1, 2, 3, 4, 5, 6})
        self.assertEqual(target.selected_option, 2)


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
        self.assertEqual(set_obs.value, {3, 4, 5, 6})
    
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
        self.assertEqual(self.observable.value, {"a": 1, "b": 2, "c": 3})
    
    def test_set_item(self):
        """Test setting a single key-value pair"""
        self.observable.set_item("d", 4)
        self.assertEqual(self.observable.value, {"a": 1, "b": 2, "c": 3, "d": 4})
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
        self.assertEqual(self.observable.value, {"a": 1, "c": 3})
    
    def test_clear(self):
        """Test clearing all items"""
        self.observable.clear()
        self.assertEqual(self.observable.value, {})
    
    def test_update(self):
        """Test updating with another dictionary"""
        self.observable.update({"d": 4, "e": 5})
        self.assertEqual(self.observable.value, {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})
    
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
        self.assertEqual(self.observable.value, {"a": 1, "b": 2, "c": 3, "d": 4})
        
        # Test __delitem__
        del self.observable["b"]
        self.assertEqual(self.observable.value, {"a": 1, "c": 3, "d": 4})
    
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
        
        # Bind dict1 to dict2 with explicit sync mode
        dict1.bind_to_observable(dict2, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        
        # After binding, dict1 should have dict2's value
        self.assertEqual(dict1.value, {"c": 3, "d": 4})
        
        # Change dict1, dict2 should update to match dict1's content
        dict1.set_item("e", 5)
        self.assertEqual(dict1.value, {"c": 3, "d": 4, "e": 5})
        self.assertEqual(dict2.value, {"c": 3, "d": 4, "e": 5})
        
        # Change dict2, dict1 should update to match dict2's content
        dict2.set_item("f", 6)
        self.assertEqual(dict1.value, {"c": 3, "d": 4, "e": 5, "f": 6})
        self.assertEqual(dict2.value, {"c": 3, "d": 4, "e": 5, "f": 6})
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        dict1 = ObservableDict({"a": 1, "b": 2})
        dict2 = ObservableDict({"c": 3, "d": 4})
        
        # Test UPDATE_VALUE_FROM_OBSERVABLE
        dict1.bind_to_observable(dict2, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        self.assertEqual(dict1.value, {"c": 3, "d": 4})
        
        # Test UPDATE_OBSERVABLE_FROM_SELF
        dict3 = ObservableDict({"e": 5, "f": 6})
        dict4 = ObservableDict({"g": 7, "h": 8})
        dict3.bind_to_observable(dict4, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        self.assertEqual(dict4.value, {"e": 5, "f": 6})
    
    def test_unbinding(self):
        """Test unbinding observables"""
        dict1 = ObservableDict({"a": 1, "b": 2})
        dict2 = ObservableDict({"c": 3, "d": 4})
        
        dict1.bind_to_observable(dict2, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        dict1.unbind_from_observable(dict2)
        
        # Changes should no longer propagate
        dict1.set_item("e", 5)
        self.assertEqual(dict2.value, {"c": 3, "d": 4})
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        dict1 = ObservableDict({"a": 1, "b": 2})
        dict2 = ObservableDict({"c": 3, "d": 4})
        
        dict1.bind_to_observable(dict2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        dict1.unbind_from_observable(dict2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            dict1.unbind_from_observable(dict2)
        
        # Changes should still not propagate
        dict1.set_item("e", 5)
        # Since we used UPDATE_OBSERVABLE_FROM_SELF, dict2 was updated to dict1's value ({"a": 1, "b": 2}) during binding
        # After unbinding, dict2 should still have that value, not the original {"c": 3, "d": 4}
        self.assertEqual(dict2.value, {"a": 1, "b": 2})
    
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
        
        # Bind both to the target with explicit sync mode
        dict1.bind_to_observable(target, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        dict2.bind_to_observable(target, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        
        # After binding, both should have target's value
        self.assertEqual(dict1.value, {"a": 1, "b": 2})
        self.assertEqual(dict2.value, {"a": 1, "b": 2})
        
        # Change target, both should update to match target's content
        target.set_item("g", 7)
        self.assertEqual(target.value, {"a": 1, "b": 2, "g": 7})
        self.assertEqual(dict1.value, {"a": 1, "b": 2, "g": 7})
        self.assertEqual(dict2.value, {"a": 1, "b": 2, "g": 7})
        
        # Change one of the observables, target should update to match that observable's content
        dict1.set_item("h", 8)
        self.assertEqual(target.value, {"a": 1, "b": 2, "g": 7, "h": 8})
        # With bidirectional binding, all observables should update to the same value
        self.assertEqual(dict1.value, {"a": 1, "b": 2, "g": 7, "h": 8})
        self.assertEqual(dict2.value, {"a": 1, "b": 2, "g": 7, "h": 8})
    
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
        self.assertEqual(empty_dict.value, {})
        self.assertEqual(len(empty_dict), 0)
    
    def test_none_initialization(self):
        """Test initialization with None"""
        none_dict = ObservableDict(None)
        self.assertEqual(none_dict.value, {})
        self.assertEqual(len(none_dict), 0)
    
    def test_copy_protection(self):
        """Test that external modifications don't affect the observable"""
        external_dict = {"x": 10, "y": 20}
        obs_dict = ObservableDict(external_dict)
        
        # Modify external dict
        external_dict["z"] = 30
        
        # Observable should not be affected
        self.assertEqual(obs_dict.value, {"x": 10, "y": 20})
        
        # Observable changes should not affect external dict
        obs_dict.set_item("w", 40)
        self.assertEqual(external_dict, {"x": 10, "y": 20, "z": 30})
    
    def test_initialization_with_carries_bindable_dict(self):
        """Test initialization with CarriesBindableDict"""
        # Create a source observable dict
        source = ObservableDict({"a": 1, "b": 2})
        
        # Create a new observable dict initialized with the source
        target = ObservableDict(source)
        
        # Check that the target has the same initial value
        self.assertEqual(target.value, {"a": 1, "b": 2})
        
        # Check that they are bound together
        source.set_item("c", 3)
        self.assertEqual(target.value, {"a": 1, "b": 2, "c": 3})
        
        # Check bidirectional binding
        target.set_item("d", 4)
        self.assertEqual(source.value, {"a": 1, "b": 2, "c": 3, "d": 4})
    
    def test_initialization_with_carries_bindable_dict_chain(self):
        """Test initialization with CarriesBindableDict in a chain"""
        # Create a chain of observable dicts
        obs1 = ObservableDict({"x": 10})
        obs2 = ObservableDict(obs1)
        obs3 = ObservableDict(obs2)
        
        # Check initial values
        self.assertEqual(obs1.value, {"x": 10})
        self.assertEqual(obs2.value, {"x": 10})
        self.assertEqual(obs3.value, {"x": 10})
        
        # Change the first observable
        obs1.set_item("y", 20)
        self.assertEqual(obs1.value, {"x": 10, "y": 20})
        self.assertEqual(obs2.value, {"x": 10, "y": 20})
        self.assertEqual(obs3.value, {"x": 10, "y": 20})
    
    def test_initialization_with_carries_bindable_dict_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableDict({"key1": "value1"})
        target1 = ObservableDict(source)
        target2 = ObservableDict(source)
        target3 = ObservableDict(source)
        
        # Check initial values
        self.assertEqual(target1.value, {"key1": "value1"})
        self.assertEqual(target2.value, {"key1": "value1"})
        self.assertEqual(target3.value, {"key1": "value1"})
        
        # Change source, all targets should update
        source.set_item("key2", "value2")
        self.assertEqual(target1.value, {"key1": "value1", "key2": "value2"})
        self.assertEqual(target2.value, {"key1": "value1", "key2": "value2"})
        self.assertEqual(target3.value, {"key1": "value1", "key2": "value2"})
    
    def test_initialization_with_carries_bindable_dict_unbinding(self):
        """Test that initialization with CarriesBindableDict can be unbound"""
        source = ObservableDict({"a": 1})
        target = ObservableDict(source)
        
        # Verify they are bound
        self.assertEqual(target.value, {"a": 1})
        source.set_item("b", 2)
        self.assertEqual(target.value, {"a": 1, "b": 2})
        
        # Unbind them
        target.unbind_from_observable(source)
        
        # Change source, target should not update
        source.set_item("c", 3)
        self.assertEqual(target.value, {"a": 1, "b": 2})  # Should remain unchanged
        
        # Change target, source should not update
        target.set_item("d", 4)
        self.assertEqual(source.value, {"a": 1, "b": 2, "c": 3})  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_dict_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableDict"""
        # Test with empty dict
        source_empty = ObservableDict({})
        target_empty = ObservableDict(source_empty)
        self.assertEqual(target_empty.value, {})
        
        # Test with None values in dict
        source_none = ObservableDict({"key": None})
        target_none = ObservableDict(source_none)
        self.assertIsNone(target_none.value["key"])
        
        # Test with nested dict
        source_nested = ObservableDict({"nested": {"inner": "value"}})
        target_nested = ObservableDict(source_nested)
        self.assertEqual(target_nested.value, {"nested": {"inner": "value"}})
    
    def test_initialization_with_carries_bindable_dict_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableDict"""
        source = ObservableDict({"a": 1})
        target = ObservableDict(source)
        
        # Check binding consistency
        is_consistent, message = target.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Check that they are properly bound
        self.assertTrue(target._binding_handler.is_bound_to(source._binding_handler))
        self.assertTrue(source._binding_handler.is_bound_to(target._binding_handler))
    
    def test_initialization_with_carries_bindable_dict_performance(self):
        """Test performance of initialization with CarriesBindableDict"""
        import time
        
        # Create source
        source = ObservableDict({"a": 1, "b": 2, "c": 3})
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableDict(source)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(end_time - start_time, 1.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableDict(source)
        source.set_item("d", 4)
        self.assertEqual(target.value, {"a": 1, "b": 2, "c": 3, "d": 4})


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
        set2.set_set({4, 5, 6})
        self.assertEqual(set1.value, {4, 5, 6})
    
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


class TestObservableEnum(unittest.TestCase):
    """Test cases for ObservableEnum class."""
    
    def setUp(self):
        """Set up test fixtures."""
        from enum import Enum
        
        class TestColor(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"
            YELLOW = "yellow"
        
        class TestSize(Enum):
            SMALL = "small"
            MEDIUM = "medium"
            LARGE = "large"
        
        self.Color = TestColor
        self.Size = TestSize
        # Don't create a bound observable in setUp to avoid side effects
        # self.observable = ObservableEnum(self.Color.RED)

    def test_initialization_with_enum_value(self):
        """Test initialization with a direct enum value."""
        obs = ObservableEnum(self.Color.BLUE)
        self.assertEqual(obs.enum_value, self.Color.BLUE)
        self.assertEqual(obs.enum_options, {self.Color.RED, self.Color.GREEN, self.Color.BLUE, self.Color.YELLOW})

    def test_initialization_with_custom_options(self):
        """Test initialization with custom enum options."""
        custom_options = {self.Color.RED, self.Color.BLUE}
        obs = ObservableEnum(self.Color.RED, custom_options)
        self.assertEqual(obs.enum_value, self.Color.RED)
        self.assertEqual(obs.enum_options, custom_options)

    def test_initialization_with_observable_enum(self):
        """Test initialization with another ObservableEnum."""
        source = ObservableEnum(self.Color.GREEN)
        target = ObservableEnum(source)
        
        # Check that the target has the same initial value
        self.assertEqual(target.enum_value, self.Color.GREEN)
        self.assertEqual(target.enum_options, {self.Color.RED, self.Color.GREEN, self.Color.BLUE, self.Color.YELLOW})
        
        # Check that they are bound together
        source.enum_value = self.Color.BLUE
        self.assertEqual(target.enum_value, self.Color.BLUE)
        
        # Check bidirectional binding
        target.enum_value = self.Color.YELLOW
        self.assertEqual(source.enum_value, self.Color.YELLOW)

    def test_initialization_with_observable_options(self):
        """Test initialization with observable options set."""
        options_source = ObservableSet({self.Color.RED, self.Color.BLUE})
        obs = ObservableEnum(self.Color.RED, options_source)
        
        # Check initial state
        self.assertEqual(obs.enum_value, self.Color.RED)
        self.assertEqual(obs.enum_options, {self.Color.RED, self.Color.BLUE})
        
        # Check that options binding works
        options_source.add(self.Color.GREEN)
        self.assertEqual(obs.enum_options, {self.Color.RED, self.Color.BLUE, self.Color.GREEN})

    def test_validation_on_initialization(self):
        """Test that invalid enum values are rejected during initialization."""
        custom_options = {self.Color.RED, self.Color.BLUE}
        
        # This should work
        obs1 = ObservableEnum(self.Color.RED, custom_options)
        self.assertEqual(obs1.enum_value, self.Color.RED)
        
        # This should fail
        with self.assertRaises(ValueError):
            ObservableEnum(self.Color.GREEN, custom_options)

    def test_change_enum_value(self):
        """Test changing the enum value."""
        obs = ObservableEnum(self.Color.RED)
        
        # Change to valid value
        obs.change_enum_value(self.Color.BLUE)
        self.assertEqual(obs.enum_value, self.Color.BLUE)
        
        # Create an observable with limited options
        obs_limited = ObservableEnum(self.Color.RED, {self.Color.RED, self.Color.BLUE})
        
        # Change to invalid value should fail
        with self.assertRaises(ValueError):
            obs_limited.change_enum_value(self.Color.GREEN)  # GREEN is not in the limited options

    def test_change_enum_options(self):
        """Test changing the enum options."""
        obs = ObservableEnum(self.Color.RED)
        
        # Change to valid options
        new_options = {self.Color.RED, self.Color.BLUE, self.Color.GREEN}
        obs.change_enum_options(new_options)
        self.assertEqual(obs.enum_options, new_options)
        
        # Change to options that don't contain current value should fail
        with self.assertRaises(ValueError):
            obs.change_enum_options({self.Color.BLUE, self.Color.GREEN})
        # The enum value and options should remain unchanged
        self.assertEqual(obs.enum_value, self.Color.RED)
        self.assertEqual(obs.enum_options, {self.Color.RED, self.Color.BLUE, self.Color.GREEN})

    def test_set_enum_value_and_options(self):
        """Test setting both enum value and options simultaneously."""
        obs = ObservableEnum(self.Color.RED)
        
        # Set both values atomically
        obs.set_enum_value_and_options(self.Color.BLUE, {self.Color.BLUE, self.Color.GREEN})
        self.assertEqual(obs.enum_value, self.Color.BLUE)
        self.assertEqual(obs.enum_options, {self.Color.BLUE, self.Color.GREEN})
        
        # Invalid combination should fail
        with self.assertRaises(ValueError):
            obs.set_enum_value_and_options(self.Color.RED, {self.Color.BLUE, self.Color.GREEN})

    def test_add_enum_option(self):
        """Test adding a new enum option."""
        obs = ObservableEnum(self.Color.RED, {self.Color.RED, self.Color.BLUE})
        
        # Add new option
        obs.add_enum_option(self.Color.GREEN)
        self.assertEqual(obs.enum_options, {self.Color.RED, self.Color.BLUE, self.Color.GREEN})
        
        # Add existing option should not change anything
        obs.add_enum_option(self.Color.RED)
        self.assertEqual(obs.enum_options, {self.Color.RED, self.Color.BLUE, self.Color.GREEN})

    def test_remove_enum_option(self):
        """Test removing an enum option."""
        obs = ObservableEnum(self.Color.RED, {self.Color.RED, self.Color.BLUE, self.Color.GREEN})
        
        # Remove option
        obs.remove_enum_option(self.Color.BLUE)
        self.assertEqual(obs.enum_options, {self.Color.RED, self.Color.GREEN})
        
        # Remove currently selected option should fail
        with self.assertRaises(ValueError):
            obs.remove_enum_option(self.Color.RED)

    def test_binding_enum_value(self):
        """Test binding enum values between observables."""
        obs1 = ObservableEnum(self.Color.RED)
        obs2 = ObservableEnum(self.Color.BLUE)
        
        # Bind them together
        obs1.bind_enum_value_to_observable(obs2)
        
        # Check that changes propagate
        obs1.enum_value = self.Color.GREEN
        self.assertEqual(obs2.enum_value, self.Color.GREEN)
        
        obs2.enum_value = self.Color.YELLOW
        self.assertEqual(obs1.enum_value, self.Color.YELLOW)

    def test_binding_enum_options(self):
        """Test binding enum options between observables."""
        # Start with an enum value that will be valid in the target options
        obs1 = ObservableEnum(self.Color.GREEN, {self.Color.RED, self.Color.BLUE, self.Color.GREEN})
        options_source = ObservableSet({self.Color.GREEN, self.Color.YELLOW})
        
        # Bind options together with explicit sync mode
        obs1.bind_enum_options_to_observable(options_source, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        
        # Check that options binding works - obs1 should get options from source
        self.assertEqual(obs1.enum_options, {self.Color.GREEN, self.Color.YELLOW})
        # The enum value should remain valid (GREEN is in both old and new options)
        self.assertEqual(obs1.enum_value, self.Color.GREEN)
        
        # Check that options changes propagate
        options_source.add(self.Color.BLUE)
        self.assertEqual(obs1.enum_options, {self.Color.GREEN, self.Color.YELLOW, self.Color.BLUE})

    def test_unbinding(self):
        """Test unbinding observables."""
        obs1 = ObservableEnum(self.Color.RED)
        obs2 = ObservableEnum(self.Color.BLUE)
        
        # Bind them together with explicit sync mode
        obs1.bind_enum_value_to_observable(obs2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        
        # Verify they are bound
        self.assertEqual(obs2.enum_value, self.Color.RED)
        obs1.enum_value = self.Color.GREEN
        self.assertEqual(obs2.enum_value, self.Color.GREEN)
        
        # Unbind them
        obs1.unbind_enum_value_from_observable(obs2)
        
        # Changes should no longer propagate
        obs1.enum_value = self.Color.YELLOW
        self.assertEqual(obs2.enum_value, self.Color.GREEN)  # Should remain unchanged

    def test_binding_chain(self):
        """Test binding multiple observables in a chain."""
        obs1 = ObservableEnum(self.Color.RED)
        obs2 = ObservableEnum(self.Color.BLUE)
        obs3 = ObservableEnum(self.Color.GREEN)
        
        # Create chain: obs1 -> obs2 -> obs3 with explicit sync modes
        obs1.bind_enum_value_to_observable(obs2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        obs2.bind_enum_value_to_observable(obs3, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        
        # Check initial values
        self.assertEqual(obs1.enum_value, self.Color.RED)
        self.assertEqual(obs2.enum_value, self.Color.RED)
        self.assertEqual(obs3.enum_value, self.Color.RED)
        
        # Change the first observable
        obs1.enum_value = self.Color.BLUE
        self.assertEqual(obs1.enum_value, self.Color.BLUE)
        self.assertEqual(obs2.enum_value, self.Color.BLUE)
        self.assertEqual(obs3.enum_value, self.Color.BLUE)
        
        # Change the middle observable
        obs2.enum_value = self.Color.GREEN
        self.assertEqual(obs1.enum_value, self.Color.GREEN)
        self.assertEqual(obs2.enum_value, self.Color.GREEN)
        self.assertEqual(obs3.enum_value, self.Color.GREEN)

    def test_multiple_targets(self):
        """Test binding one source to multiple targets."""
        source = ObservableEnum(self.Color.RED)
        target1 = ObservableEnum(self.Color.BLUE)
        target2 = ObservableEnum(self.Color.GREEN)
        target3 = ObservableEnum(self.Color.YELLOW)
        
        # Bind source to all targets with explicit sync mode
        source.bind_enum_value_to_observable(target1, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        source.bind_enum_value_to_observable(target2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        source.bind_enum_value_to_observable(target3, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        
        # Check initial values
        self.assertEqual(target1.enum_value, self.Color.RED)
        self.assertEqual(target2.enum_value, self.Color.RED)
        self.assertEqual(target3.enum_value, self.Color.RED)
        
        # Change source, all targets should update
        source.enum_value = self.Color.BLUE
        self.assertEqual(target1.enum_value, self.Color.BLUE)
        self.assertEqual(target2.enum_value, self.Color.BLUE)
        self.assertEqual(target3.enum_value, self.Color.BLUE)
        
        # Change one target, source and other targets should update
        target1.enum_value = self.Color.GREEN
        self.assertEqual(source.enum_value, self.Color.GREEN)
        self.assertEqual(target2.enum_value, self.Color.GREEN)
        self.assertEqual(target3.enum_value, self.Color.GREEN)

    def test_listener_notifications(self):
        """Test that listeners are notified of changes."""
        obs = ObservableEnum(self.Color.RED)
        notifications = []
        
        # Add listener
        obs.add_listeners(lambda: notifications.append("changed"))
        
        # Change value
        obs.enum_value = self.Color.BLUE
        self.assertEqual(notifications, ["changed"])
        
        # Change options
        obs.change_enum_options({self.Color.BLUE, self.Color.GREEN})
        self.assertEqual(notifications, ["changed", "changed"])

    def test_binding_system_consistency(self):
        """Test binding system consistency checking."""
        obs1 = ObservableEnum(self.Color.RED)
        obs2 = ObservableEnum(self.Color.BLUE)
        
        # Check consistency before binding
        is_consistent, message = obs1.check_binding_system_consistency()
        self.assertTrue(is_consistent, message)
        
        # Bind them together
        obs1.bind_enum_value_to_observable(obs2)
        
        # Check consistency after binding
        is_consistent, message = obs1.check_binding_system_consistency()
        self.assertTrue(is_consistent, message)

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        obs = ObservableEnum(self.Color.RED)
        
        # Try to bind to None
        with self.assertRaises(ValueError):
            obs.bind_enum_value_to_observable(None)
        
        # Try to bind to self
        with self.assertRaises(ValueError):
            obs.bind_enum_value_to_observable(obs)

    def test_comparison_operators(self):
        """Test comparison operators."""
        obs1 = ObservableEnum(self.Color.RED)
        obs2 = ObservableEnum(self.Color.RED)
        obs3 = ObservableEnum(self.Color.BLUE)
        
        # Test equality
        self.assertEqual(obs1, obs2)
        self.assertNotEqual(obs1, obs3)
        self.assertEqual(obs1, self.Color.RED)
        self.assertNotEqual(obs1, self.Color.BLUE)
        
        # Test hash
        self.assertEqual(hash(obs1), hash(obs2))
        self.assertNotEqual(hash(obs1), hash(obs3))

    def test_string_representations(self):
        """Test string representations."""
        obs = ObservableEnum(self.Color.RED, {self.Color.RED, self.Color.BLUE})
        
        str_repr = str(obs)
        repr_repr = repr(obs)
        
        self.assertIn("RED", str_repr)
        self.assertIn("BLUE", str_repr)
        self.assertIn("ObservableEnum", repr_repr)

    def test_boolean_conversion(self):
        """Test boolean conversion."""
        obs = ObservableEnum(self.Color.RED)
        
        # Should be truthy
        self.assertTrue(bool(obs))
        
        # Test with different enum types
        from enum import Enum
        class EmptyEnum(Enum):
            pass
        
        # This should work but might be implementation dependent
        # We'll just test that it doesn't crash
        try:
            empty_obs = ObservableEnum(list(EmptyEnum)[0] if EmptyEnum else None)
            if empty_obs:
                _ = bool(empty_obs)
        except (IndexError, TypeError):
            pass  # Expected for empty enum

    def test_initialization_with_carries_enum_performance(self):
        """Test performance of initialization with CarriesEnum"""
        # Create a source observable enum
        source = ObservableEnum(self.Color.RED)
        
        # Measure time for multiple initializations
        import time
        start_time = time.time()
        
        for _ in range(1000):
            target = ObservableEnum(source)
            _ = target.enum_value  # Access to ensure initialization is complete
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(total_time, 1.0)

    def test_initialization_with_carries_bindable_set_performance(self):
        """Test performance of initialization with CarriesBindableSet"""
        # Create a source observable set
        source = ObservableSet({self.Color.RED, self.Color.BLUE})
        
        # Measure time for multiple initializations
        import time
        start_time = time.time()
        
        for _ in range(1000):
            target = ObservableEnum(self.Color.RED, source)
            _ = target.enum_options  # Access to ensure initialization is complete
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(total_time, 1.0)


if __name__ == '__main__':
    unittest.main()
