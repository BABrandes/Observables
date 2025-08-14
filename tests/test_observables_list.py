import unittest
from observables import ObservableList

class TestObservableList(unittest.TestCase):
    """Test cases for ObservableList (concrete implementation)"""
    
    def setUp(self):
        self.observable = ObservableList([1, 2, 3])
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_value(self):
        """Test that initial value is set correctly"""
        self.assertEqual(self.observable.list_value, [1, 2, 3])
    
    def test_append(self):
        """Test appending a new value"""
        self.observable.append(4)
        self.assertEqual(self.observable.list_value, [1, 2, 3, 4])
    
    def test_listener_notification(self):
        """Test that listeners are notified when value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.append([7, 8, 9])
        self.assertEqual(self.notification_count, 1)
    
    def test_no_notification_on_same_value(self):
        """Test that listeners are not notified when value doesn't change"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.list_value = [1, 2, 3]  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_remove_listeners(self):
        """Test removing a listener"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove_listeners(self.notification_callback)
        self.observable.append([10, 11, 12])
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
        self.observable.append([13, 14, 15])
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_initialization_with_carries_bindable_list(self):
        """Test initialization with CarriesBindableList"""
        # Create a source observable list
        source = ObservableList([1, 2, 3])
        
        # Create a new observable list initialized with the source
        target = ObservableList(source)
        
        # Check that the target has the same initial value
        self.assertEqual(target.list_value, [1, 2, 3])
        
        # Check that they are bound together
        source.append(4)
        self.assertEqual(target.list_value, [1, 2, 3, 4])
        
        # Check bidirectional binding
        target.append(5)
        self.assertEqual(source.list_value, [1, 2, 3, 4, 5])
    
    def test_initialization_with_carries_bindable_list_chain(self):
        """Test initialization with CarriesBindableList in a chain"""
        # Create a chain of observable lists
        obs1 = ObservableList([10])
        obs2 = ObservableList(obs1)
        obs3 = ObservableList(obs2)
        
        # Check initial values
        self.assertEqual(obs1.list_value, [10])
        self.assertEqual(obs2.list_value, [10])
        self.assertEqual(obs3.list_value, [10])
        
        # Change the first observable
        obs1.append(20)
        self.assertEqual(obs1.list_value, [10, 20])
        self.assertEqual(obs2.list_value, [10, 20])
        self.assertEqual(obs3.list_value, [10, 20])
        
        # Change the middle observable
        obs2.append(30)
        self.assertEqual(obs1.list_value, [10, 20, 30])
        self.assertEqual(obs2.list_value, [10, 20, 30])
        self.assertEqual(obs3.list_value, [10, 20, 30])
    
    def test_initialization_with_carries_bindable_list_multiple_targets(self):
        """Test multiple targets initialized with the same source"""
        source = ObservableList([100])
        target1 = ObservableList(source)
        target2 = ObservableList(source)
        target3 = ObservableList(source)
        
        # Check initial values
        self.assertEqual(target1.list_value, [100])
        self.assertEqual(target2.list_value, [100])
        self.assertEqual(target3.list_value, [100])
        
        # Change source, all targets should update
        source.append(200)
        self.assertEqual(target1.list_value, [100, 200])
        self.assertEqual(target2.list_value, [100, 200])
        self.assertEqual(target3.list_value, [100, 200])
        
        # Change one target, source and other targets should update
        target1.append(300)
        self.assertEqual(source.list_value, [100, 200, 300])
        self.assertEqual(target2.list_value, [100, 200, 300])
        self.assertEqual(target3.list_value, [100, 200, 300])
    
    def test_initialization_with_carries_bindable_list_unbinding(self):
        """Test that initialization with CarriesBindableList can be unbound"""
        source = ObservableList([1, 2])
        target = ObservableList(source)
        
        # Verify they are bound
        self.assertEqual(target.list_value, [1, 2])
        source.append(3)
        self.assertEqual(target.list_value, [1, 2, 3])
        
        # Unbind them
        target.unbind_from(source)
        
        # Change source, target should not update
        source.append(4)
        self.assertEqual(target.list_value, [1, 2, 3])  # Should remain unchanged
        
        # Change target, source should not update
        target.append(5)
        self.assertEqual(source.list_value, [1, 2, 3, 4])  # Should remain unchanged
    
    def test_initialization_with_carries_bindable_list_edge_cases(self):
        """Test edge cases for initialization with CarriesBindableList"""
        # Test with empty list
        source_empty = ObservableList([])
        target_empty = ObservableList(source_empty)
        self.assertEqual(target_empty.list_value, [])
        
        # Test with None values in list
        source_none = ObservableList([None, 1, None])
        target_none = ObservableList(source_none)
        self.assertEqual(target_none.list_value, [None, 1, None])
        
        # Test with nested list
        source_nested = ObservableList([[1, 2], [3, 4]])
        target_nested = ObservableList(source_nested)
        self.assertEqual(target_nested.list_value, [[1, 2], [3, 4]])
    
    def test_initialization_with_carries_bindable_list_binding_consistency(self):
        """Test binding system consistency when initializing with CarriesBindableList"""
        source = ObservableList([1, 2, 3])
        target = ObservableList(source)
        
        # Check binding consistency
        is_consistent, message = target.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
        
        # Check that they are properly bound
        self.assertTrue(target._get_list_hook().is_bound_to(source._get_list_hook()))
        self.assertTrue(source._get_list_hook().is_bound_to(target._get_list_hook()))
    
    def test_initialization_with_carries_bindable_list_performance(self):
        """Test performance of initialization with CarriesBindableList"""
        # Create a source observable list
        source = ObservableList([1, 2, 3, 4, 5])
        
        # Measure time for multiple initializations
        import time
        start_time = time.time()
        
        for _ in range(1000):
            target = ObservableList(source)
            _ = target.list_value  # Access to ensure initialization is complete
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time (less than 3 seconds)
        self.assertLess(total_time, 3.0)
    
    def test_none_initialization(self):
        """Test initialization with None value"""
        # Test initialization with None
        obs = ObservableList(None)
        self.assertEqual(obs.list_value, [])
        
        # Test that it's a proper empty list, not None
        self.assertIsInstance(obs.list_value, list)
        self.assertEqual(len(obs.list_value), 0)
        
        # Test that we can add items to it
        obs.append(1)
        obs.append(2)
        self.assertEqual(obs.list_value, [1, 2])
    
    def test_empty_list_initialization(self):
        """Test initialization with empty list"""
        # Test initialization with empty list
        obs = ObservableList([])
        self.assertEqual(obs.list_value, [])
        
        # Test that it's a proper empty list
        self.assertIsInstance(obs.list_value, list)
        self.assertEqual(len(obs.list_value), 0)
        
        # Test that we can add items to it
        obs.append(10)
        obs.append(20)
        self.assertEqual(obs.list_value, [10, 20])
    
    def test_none_vs_empty_list_behavior(self):
        """Test that None and empty list initialization behave identically"""
        obs_none = ObservableList(None)
        obs_empty = ObservableList([])
        
        # Both should start with empty lists
        self.assertEqual(obs_none.list_value, obs_empty.list_value)
        self.assertEqual(obs_none.list_value, [])
        
        # Both should behave the same way when modified
        obs_none.append(1)
        obs_empty.append(1)
        
        self.assertEqual(obs_none.list_value, obs_empty.list_value)
        self.assertEqual(obs_none.list_value, [1])
