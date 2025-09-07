import unittest
from observables import ObservableDict, InitialSyncMode

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
        """Test setting a new key-value pair"""
        self.observable.set_item("d", 4)
        self.assertEqual(self.observable.value, {"a": 1, "b": 2, "c": 3, "d": 4})
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_item("e", 5)
        self.assertEqual(self.notification_count, 1)
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.set_item("a", 1)  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_listeners(self.notification_callback)
        self.observable.set_item("f", 6)
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
        self.observable.set_item("g", 7)
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_initialization_with_carries_bindable_dict(self):
        """Test initialization with CarriesBindableDict"""
        # Create a source observable dict
        source = ObservableDict({"x": 100, "y": 200})
        
        # Create a new observable dict initialized with the source
        target: ObservableDict[str, int] = ObservableDict(source.value_hook)
        
        # Check that the target has the same initial value
        self.assertEqual(target.value, {"x": 100, "y": 200})
        
        # Check that they are bound together
        source.set_item("z", 300)
        self.assertEqual(target.value, {"x": 100, "y": 200, "z": 300})
        
        # Check bidirectional binding
        target.set_item("w", 400)
        self.assertEqual(source.value, {"x": 100, "y": 200, "z": 300, "w": 400})
    
    def test_initialization_with_carries_bindable_dict_chain(self):
        """Test initialization with CarriesBindableDict in a chain"""
        # Create a chain of observable dicts
        obs1 = ObservableDict({"key1": 10})
        obs2 = ObservableDict(obs1.value_hook)
        obs3 = ObservableDict(obs2.value_hook)
        
        # Check initial values
        self.assertEqual(obs1.value, {"key1": 10})
        self.assertEqual(obs2.value, {"key1": 10})
        self.assertEqual(obs3.value, {"key1": 10})
        
        # Change the first observable
        obs1.set_item("key2", 20)
        self.assertEqual(obs1.value, {"key1": 10, "key2": 20})
        self.assertEqual(obs2.value, {"key1": 10, "key2": 20})
        self.assertEqual(obs3.value, {"key1": 10, "key2": 20})
        
        # Change the middle observable
        obs2.set_item("key3", 30)
        self.assertEqual(obs1.value, {"key1": 10, "key2": 20, "key3": 30})
        self.assertEqual(obs2.value, {"key1": 10, "key2": 20, "key3": 30})
        self.assertEqual(obs3.value, {"key1": 10, "key2": 20, "key3": 30})
    
    def test_initialization_with_carries_bindable_dict_unbinding(self):
        """Test that initialization with CarriesBindableDict can be unbound"""
        source = ObservableDict({"key1": 100})
        target = ObservableDict(source.value_hook)
        
        # Verify they are bound
        self.assertEqual(target.value, {"key1": 100})
        source.set_item("key2", 200)
        self.assertEqual(target.value, {"key1": 100, "key2": 200})
        
        # Unbind them
        target.disconnect()
        
        # Change source, target should not update
        source.set_item("key3", 300)
        self.assertEqual(target.value, {"key1": 100, "key2": 200})  # Should remain unchanged
        
        # Change target, source should not update
        target.set_item("key4", 400)
        self.assertEqual(source.value, {"key1": 100, "key2": 200, "key3": 300})  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_dict_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableDict({"key1": 100})
        target1 = ObservableDict(source.value_hook)
        target2 = ObservableDict(source.value_hook)
        target3 = ObservableDict(source.value_hook)
        
        # Check initial values
        self.assertEqual(target1.value, {"key1": 100})
        self.assertEqual(target2.value, {"key1": 100})
        self.assertEqual(target3.value, {"key1": 100})
        
        # Change source, all targets should update
        source.set_item("key2", 200)
        self.assertEqual(target1.value, {"key1": 100, "key2": 200})
        self.assertEqual(target2.value, {"key1": 100, "key2": 200})
        self.assertEqual(target3.value, {"key1": 100, "key2": 200})
        
        # Change one target, source and other targets should update
        target1.set_item("key3", 300)
        self.assertEqual(source.value, {"key1": 100, "key2": 200, "key3": 300})
        self.assertEqual(target2.value, {"key1": 100, "key2": 200, "key3": 300})
        self.assertEqual(target3.value, {"key1": 100, "key2": 200, "key3": 300})
    
    def test_initialization_with_carries_bindable_dict_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableDict"""
        # Test with empty dict in source
        source_empty: ObservableDict[str, int] = ObservableDict({})
        target_empty = ObservableDict(source_empty.value_hook)
        self.assertEqual(target_empty.value, {})
        
        # Test with None in source
        source_none: ObservableDict[str, int] = ObservableDict(None)
        target_none = ObservableDict(source_none.value_hook)
        self.assertEqual(target_none.value, {})
        
        # Test with single item
        source_single = ObservableDict({"single": 42})
        target_single = ObservableDict(source_single.value_hook)
        self.assertEqual(target_single.value, {"single": 42})
    
    def test_initialization_with_carries_bindable_dict_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableDict"""
        source = ObservableDict({"key1": 100})
        target = ObservableDict(source.value_hook)
        
        # Check binding consistency
        
        # Check that they are properly bound
        self.assertTrue(target.value_hook.is_connected_to(source.value_hook))
        self.assertTrue(source.value_hook.is_connected_to(target.value_hook))
    
    def test_initialization_with_carries_bindable_dict_performance(self):
        """Test performance of initialization with CarriesBindableDict"""
        import time
        
        # Create source
        source = ObservableDict({"key1": 100})
        
        # Measure initialization time
        start_time = time.time()
        for _ in range(1000):
            target = ObservableDict(source.value_hook)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 6 seconds)
        self.assertLess(end_time - start_time, 6.0, "Initialization should be fast")
        
        # Verify the last target is properly bound
        target = ObservableDict(source.value_hook)
        source.set_item("key2", 200)
        self.assertEqual(target.value, {"key1": 100, "key2": 200})
    
    def test_binding_bidirectional(self):
        """Test bidirectional binding between obs1 and obs2"""
        obs1 = ObservableDict({"key1": 10})
        obs2 = ObservableDict({"key2": 20})
        
        # Bind obs1 to obs2
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        
        # Change obs1, obs2 should update
        obs1.set_item("key3", 30)
        self.assertEqual(obs2.value, {"key1": 10, "key3": 30})  # obs2 gets obs1's value and updates
        
        # Change obs2, obs1 should also update (bidirectional)
        obs2.set_item("key4", 40)
        self.assertEqual(obs1.value, {"key1": 10, "key3": 30, "key4": 40})  # obs1 gets updated since they're bound
    
    def test_binding_initial_sync_modes(self):
        """Test different initial sync modes"""
        obs1 = ObservableDict({"key1": 100})
        obs2 = ObservableDict({"key2": 200})
        
        # Test USE_CALLER_VALUE mode (obs1 pushes its value to obs2)
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        self.assertEqual(obs2.value, {"key1": 100})  # obs2 gets obs1's value
        
        # Test USE_CALLER_VALUE mode (obs3 pushes its value to obs4)
        obs3 = ObservableDict({"key3": 300})
        obs4 = ObservableDict({"key4": 400})
        obs3.connect(obs4.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        self.assertEqual(obs4.value, {"key3": 300})  # obs4 gets obs3's value
    
    def test_unbinding(self):
        """Test unbinding observables"""
        obs1 = ObservableDict({"key1": 10})
        obs2 = ObservableDict({"key2": 20})
        
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        obs1.disconnect()
        
        # Changes should no longer propagate
        obs1.set_item("key3", 50)
        self.assertEqual(obs2.value, {"key1": 10})  # obs2 keeps its current bound value
    
    def test_binding_to_self(self):
        """Test that binding to self raises an error"""
        obs = ObservableDict({"key1": 10})
        with self.assertRaises(ValueError):
            obs.connect(obs.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
    
    def test_binding_chain_unbinding(self):
        """Test unbinding in a chain of bindings"""
        obs1 = ObservableDict({"key1": 10})
        obs2 = ObservableDict({"key2": 20})
        obs3 = ObservableDict({"key3": 30})
        
        # Create chain: obs1 -> obs2 -> obs3
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        obs2.connect(obs3.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        
        # Verify chain works
        obs1.set_item("key4", 100)
        self.assertEqual(obs2.value, {"key1": 10, "key4": 100})  # obs2 gets obs1's value and updates
        self.assertEqual(obs3.value, {"key1": 10, "key4": 100})  # obs3 also gets updated since all three are bound
        
        # Break the chain by unbinding obs2 from obs3
        obs2.disconnect()
        
        # Change obs1, obs2 should NOT update but obs3 should (obs1 and obs3 remain bound)
        obs1.set_item("key5", 200)
        self.assertEqual(obs2.value, {"key1": 10, "key4": 100})  # obs2 keeps its current bound value
        self.assertEqual(obs3.value, {"key1": 10, "key4": 100, "key5": 200})  # obs3 gets updated since obs1 and obs3 remain bound
        
        # Change obs3, obs1 should update since obs1 and obs3 remain bound after obs2.disconnect()
        obs3.set_item("key6", 300)
        self.assertEqual(obs1.value, {"key1": 10, "key4": 100, "key5": 200, "key6": 300})  # obs1 gets updated
        self.assertEqual(obs2.value, {"key1": 10, "key4": 100})  # obs2 is isolated
    
    def test_string_representation(self):
        """Test string and repr methods"""
        self.assertEqual(str(self.observable), "OD(dict={'a': 1, 'b': 2, 'c': 3})")
        self.assertEqual(repr(self.observable), "ObservableDict({'a': 1, 'b': 2, 'c': 3})")
    
    def test_listener_management(self):
        """Test listener management methods"""
        obs = ObservableDict({"key1": 10})
        
        # Test is_listening_to
        self.assertFalse(obs.is_listening_to(self.notification_callback))
        
        obs.add_listeners(self.notification_callback)
        self.assertTrue(obs.is_listening_to(self.notification_callback))
        
        obs.remove_listeners(self.notification_callback)
        self.assertFalse(obs.is_listening_to(self.notification_callback))
    
    def test_multiple_bindings(self):
        """Test multiple bindings to the same observable"""
        obs1 = ObservableDict({"key1": 10})
        obs2 = ObservableDict({"key2": 20})
        obs3 = ObservableDict({"key3": 30})
        
        # Bind obs2 and obs3 to obs1
        obs2.connect(obs1.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        obs3.connect(obs1.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        
        # Change obs1, both should update
        obs1.set_item("key4", 100)
        self.assertEqual(obs2.value, {"key3": 30, "key4": 100})  # obs2 gets obs3's value (last to bind)
        self.assertEqual(obs3.value, {"key3": 30, "key4": 100})  # obs3 also gets obs3's value (last to bind)
        
        # Change obs2, obs1 should also update (bidirectional), obs3 should also update
        obs2.set_item("key5", 200)
        self.assertEqual(obs1.value, {"key3": 30, "key4": 100, "key5": 200})
        self.assertEqual(obs3.value, {"key3": 30, "key4": 100, "key5": 200})  # obs3 also gets obs3's value (last to bind)
    
    def test_dict_methods(self):
        """Test standard dict methods"""
        obs = ObservableDict({"a": 1, "b": 2})
        
        # Test set_item
        obs.set_item("c", 3)
        self.assertEqual(obs.value, {"a": 1, "b": 2, "c": 3})
        
        # Test get_item
        self.assertEqual(obs.get_item("a"), 1)
        self.assertEqual(obs.get_item("d", 999), 999)  # Use compatible default type
        
        # Test has_key
        self.assertTrue(obs.has_key("a"))
        self.assertFalse(obs.has_key("d"))
        
        # Test change_value
        obs.change_value({"x": 10, "y": 20})
        self.assertEqual(obs.value, {"x": 10, "y": 20})
    
    def test_dict_copy_behavior(self):
        """Test that dict_value returns a copy"""
        obs = ObservableDict({"a": 1, "b": 2})
        
        # Get the dict value
        dict_copy = obs.value
        
        # Modify the copy
        dict_copy["c"] = 3
        
        # Original should not change
        self.assertEqual(obs.value, {"a": 1, "b": 2})
        
        # The copy should have the modification
        self.assertEqual(dict_copy, {"a": 1, "b": 2, "c": 3})
    
    def test_dict_validation(self):
        """Test dict validation"""
        # Test with valid dict
        obs = ObservableDict({"key1": "value1"})
        self.assertEqual(obs.value, {"key1": "value1"})
        
        # Test with None (should create empty dict)
        obs_none: ObservableDict[str, int] = ObservableDict(None)
        self.assertEqual(obs_none.value, {})
        
        # Test with empty dict
        obs_empty: ObservableDict[str, int] = ObservableDict({})
        self.assertEqual(obs_empty.value, {})
    
    def test_dict_binding_edge_cases(self):
        """Test edge cases for dict binding"""
        # Test binding empty dicts
        obs1: ObservableDict[str, str] = ObservableDict({})
        obs2: ObservableDict[str, str] = ObservableDict({})
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        
        obs1.set_item("key1", "value1")
        self.assertEqual(obs2.value, {"key1": "value1"})
        
        # Test binding dicts with same initial values
        obs3 = ObservableDict({"key1": "value1"})
        obs4 = ObservableDict({"key1": "value1"})
        obs3.connect(obs4.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        
        obs3.set_item("key2", "value2")
        self.assertEqual(obs4.value, {"key1": "value1", "key2": "value2"})
    
    def test_dict_performance(self):
        """Test dict performance characteristics"""
        import time
        
        # Test set_item performance
        obs: ObservableDict[str, int] = ObservableDict({})
        start_time = time.time()
        
        for i in range(1000):
            obs.set_item(f"key{i}", i)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Set item operations should be fast")
        self.assertEqual(len(obs.value), 1000)
        
        # Test binding performance
        source = ObservableDict({"key1": "value1"})
        start_time = time.time()
        
        for _ in range(100):
            ObservableDict(source.value_hook)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Binding operations should be fast")
    
    def test_dict_error_handling(self):
        """Test dict error handling"""
        obs = ObservableDict({"a": 1, "b": 2})
        
        # Test get_item with non-existent key
        self.assertIsNone(obs.get_item("c"))
        self.assertEqual(obs.get_item("c", 999), 999)  # Use compatible default type
    
    def test_dict_binding_consistency(self):
        """Test binding system consistency"""
        source = ObservableDict({"key1": "value1"})
        target = ObservableDict(source.value_hook)
        
        # Check binding consistency
        
        # Check that they are properly bound
        self.assertTrue(target.value_hook.is_connected_to(source.value_hook))
        self.assertTrue(source.value_hook.is_connected_to(target.value_hook))
    
    def test_dict_binding_none_observable(self):
        """Test that binding to None raises an error"""
        obs = ObservableDict({"key1": "value1"})
        with self.assertRaises(ValueError):
            obs.connect(None, "value", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
    
    def test_dict_binding_with_same_values(self):
        """Test binding when observables already have the same value"""
        obs1 = ObservableDict({"key1": "value1"})
        obs2 = ObservableDict({"key1": "value1"})
        
        obs1.connect(obs2.value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        # Both should still have the same value
        self.assertEqual(obs1.value, {"key1": "value1"})
        self.assertEqual(obs2.value, {"key1": "value1"})
    
    def test_listener_duplicates(self):
        """Test that duplicate listeners are not added"""
        obs = ObservableDict({"key1": "value1"})
        callback = lambda: None
        
        obs.add_listeners(callback, callback)
        self.assertEqual(len(obs.listeners), 1)
        
        obs.add_listeners(callback)
        self.assertEqual(len(obs.listeners), 1)
    
    def test_remove_nonexistent_listener(self):
        """Test removing a listener that doesn't exist"""
        obs = ObservableDict({"key1": "value1"})
        callback = lambda: None
        
        # Should not raise an error
        obs.remove_listeners(callback)
        self.assertEqual(len(obs.listeners), 0)


if __name__ == '__main__':
    unittest.main()