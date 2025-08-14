import unittest
from observables import ObservableDict, SyncMode




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
        dict1.bind_to(dict2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
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
        dict1.bind_to(dict2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        self.assertEqual(dict1.value, {"c": 3, "d": 4})
        
        # Test UPDATE_OBSERVABLE_FROM_SELF
        dict3 = ObservableDict({"e": 5, "f": 6})
        dict4 = ObservableDict({"g": 7, "h": 8})
        dict3.bind_to(dict4, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        self.assertEqual(dict4.value, {"e": 5, "f": 6})
    
    def test_unbinding(self):
        """Test unbinding observables"""
        dict1 = ObservableDict({"a": 1, "b": 2})
        dict2 = ObservableDict({"c": 3, "d": 4})
        
        dict1.bind_to(dict2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        dict1.unbind_from(dict2)
        
        # Changes should no longer propagate
        dict1.set_item("e", 5)
        self.assertEqual(dict2.value, {"c": 3, "d": 4})
    
    def test_unbinding_multiple_times(self):
        """Test that unbinding multiple times raises ValueError"""
        dict1 = ObservableDict({"a": 1, "b": 2})
        dict2 = ObservableDict({"c": 3, "d": 4})
        
        dict1.bind_to(dict2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        dict1.unbind_from(dict2)
        
        # Second unbind should raise ValueError since there's nothing to unbind
        with self.assertRaises(ValueError):
            dict1.unbind_from(dict2)
        
        # Changes should still not propagate
        dict1.set_item("e", 5)
        # Since we used UPDATE_OBSERVABLE_FROM_SELF, dict2 was updated to dict1's value ({"a": 1, "b": 2}) during binding
        # After unbinding, dict2 should still have that value, not the original {"c": 3, "d": 4}
        self.assertEqual(dict2.value, {"a": 1, "b": 2})
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        dict1 = ObservableDict({"a": 1, "b": 2})
        with self.assertRaises(ValueError):
            dict1.bind_to(dict1, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        target = ObservableDict({"a": 1, "b": 2})
        dict1 = ObservableDict({"c": 3, "d": 4})
        dict2 = ObservableDict({"e": 5, "f": 6})
        
        # Bind both to the target with explicit sync mode
        dict1.bind_to(target, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        dict2.bind_to(target, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
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
        target.unbind_from(source)
        
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
        self.assertTrue(target._get_dict_hook().is_bound_to(source._get_dict_hook()))
        self.assertTrue(source._get_dict_hook().is_bound_to(target._get_dict_hook()))
    
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