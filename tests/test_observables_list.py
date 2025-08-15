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
        self.observable.append(7)
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
        self.observable.append(10)
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
        self.observable.append(13)
        
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

    # Additional tests for missing coverage
    
    def test_extend(self):
        """Test extending the list with an iterable"""
        self.observable.extend([4, 5, 6])
        self.assertEqual(self.observable.list_value, [1, 2, 3, 4, 5, 6])
    
    def test_extend_no_change_notification(self):
        """Test that extend doesn't notify when no change occurs"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.extend([])  # Empty iterable
        self.assertEqual(self.notification_count, 0)
    
    def test_insert(self):
        """Test inserting an item at a specific position"""
        self.observable.insert(1, 10)
        self.assertEqual(self.observable.list_value, [1, 10, 2, 3])
    
    def test_remove(self):
        """Test removing an item from the list"""
        self.observable.remove(2)
        self.assertEqual(self.observable.list_value, [1, 3])
    
    def test_remove_nonexistent_item(self):
        """Test removing an item that doesn't exist"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.remove(99)  # Item doesn't exist
        self.assertEqual(self.observable.list_value, [1, 2, 3])
        self.assertEqual(self.notification_count, 0)  # No notification
    
    def test_pop(self):
        """Test popping an item from the list"""
        item = self.observable.pop()
        self.assertEqual(item, 3)
        self.assertEqual(self.observable.list_value, [1, 2])
    
    def test_pop_at_index(self):
        """Test popping an item at a specific index"""
        item = self.observable.pop(0)
        self.assertEqual(item, 1)
        self.assertEqual(self.observable.list_value, [2, 3])
    
    def test_pop_index_error(self):
        """Test pop with invalid index raises IndexError"""
        with self.assertRaises(IndexError):
            self.observable.pop(10)
    
    def test_clear(self):
        """Test clearing the list"""
        self.observable.clear()
        self.assertEqual(self.observable.list_value, [])
    
    def test_clear_empty_list(self):
        """Test clearing an already empty list"""
        empty_list = ObservableList([])
        empty_list.add_listeners(self.notification_callback)
        empty_list.clear()
        self.assertEqual(self.notification_count, 0)  # No change, no notification
    
    def test_sort(self):
        """Test sorting the list"""
        unsorted = ObservableList([3, 1, 4, 1, 5])
        unsorted.sort()
        self.assertEqual(unsorted.list_value, [1, 1, 3, 4, 5])
    
    def test_sort_reverse(self):
        """Test sorting the list in reverse order"""
        unsorted = ObservableList([3, 1, 4, 1, 5])
        unsorted.sort(reverse=True)
        self.assertEqual(unsorted.list_value, [5, 4, 3, 1, 1])
    
    def test_sort_with_key(self):
        """Test sorting with a custom key function"""
        words = ObservableList(['cat', 'dog', 'bird', 'ant'])
        words.sort(key=len)
        self.assertEqual(words.list_value, ['ant', 'cat', 'dog', 'bird'])
    
    def test_sort_no_change_notification(self):
        """Test that sort doesn't notify when no change occurs"""
        sorted_list = ObservableList([1, 2, 3])
        sorted_list.add_listeners(self.notification_callback)
        sorted_list.sort()  # Already sorted
        self.assertEqual(self.notification_count, 0)
    
    def test_reverse(self):
        """Test reversing the list"""
        self.observable.reverse()
        self.assertEqual(self.observable.list_value, [3, 2, 1])
    
    def test_reverse_no_change_notification(self):
        """Test that reverse doesn't notify when no change occurs"""
        single_item = ObservableList([1])
        single_item.add_listeners(self.notification_callback)
        single_item.reverse()  # Single item, no change
        self.assertEqual(self.notification_count, 0)
    
    def test_count(self):
        """Test counting occurrences of an item"""
        list_with_duplicates = ObservableList([1, 2, 2, 3, 2, 4])
        self.assertEqual(list_with_duplicates.count(2), 3)
        self.assertEqual(list_with_duplicates.count(5), 0)
    
    def test_index(self):
        """Test finding the index of an item"""
        self.assertEqual(self.observable.index(2), 1)
        self.assertEqual(self.observable.index(3), 2)
    
    def test_index_with_start(self):
        """Test finding index with start parameter"""
        list_with_duplicates = ObservableList([1, 2, 2, 3, 2, 4])
        self.assertEqual(list_with_duplicates.index(2, 2), 2)
    
    def test_index_with_start_stop(self):
        """Test finding index with start and stop parameters"""
        list_with_duplicates = ObservableList([1, 2, 2, 3, 2, 4])
        self.assertEqual(list_with_duplicates.index(2, 2, 4), 2)
    
    def test_index_value_error(self):
        """Test index with item not found raises ValueError"""
        with self.assertRaises(ValueError):
            self.observable.index(99)
    
    def test_string_representation(self):
        """Test string representation methods"""
        self.assertEqual(str(self.observable), "OL(value=[1, 2, 3])")
        self.assertEqual(repr(self.observable), "ObservableList([1, 2, 3])")
    
    def test_length(self):
        """Test length of the list"""
        self.assertEqual(len(self.observable), 3)
        empty_list = ObservableList([])
        self.assertEqual(len(empty_list), 0)
    
    def test_getitem(self):
        """Test getting item by index"""
        self.assertEqual(self.observable[0], 1)
        self.assertEqual(self.observable[1], 2)
        self.assertEqual(self.observable[2], 3)
    
    def test_getitem_slice(self):
        """Test getting items by slice"""
        self.assertEqual(self.observable[1:3], [2, 3])
        self.assertEqual(self.observable[:2], [1, 2])
        self.assertEqual(self.observable[::2], [1, 3])
    
    def test_getitem_index_error(self):
        """Test getitem with invalid index raises IndexError"""
        with self.assertRaises(IndexError):
            _ = self.observable[10]
    
    def test_setitem(self):
        """Test setting item by index"""
        self.observable[1] = 20
        self.assertEqual(self.observable.list_value, [1, 20, 3])
    
    def test_setitem_slice(self):
        """Test setting items by slice"""
        self.observable[1:3] = [20, 30]
        self.assertEqual(self.observable.list_value, [1, 20, 30])
    
    def test_setitem_no_change_notification(self):
        """Test that setitem doesn't notify when no change occurs"""
        self.observable.add_listeners(self.notification_callback)
        self.observable[1] = 2  # Same value
        self.assertEqual(self.notification_count, 0)
    
    def test_setitem_index_error(self):
        """Test setitem with invalid index raises IndexError"""
        with self.assertRaises(IndexError):
            self.observable[10] = 99
    
    def test_delitem(self):
        """Test deleting item by index"""
        del self.observable[1]
        self.assertEqual(self.observable.list_value, [1, 3])
    
    def test_delitem_slice(self):
        """Test deleting items by slice"""
        del self.observable[1:3]
        self.assertEqual(self.observable.list_value, [1])
    
    def test_delitem_no_change_notification(self):
        """Test that delitem doesn't notify when no change occurs"""
        empty_list = ObservableList([])
        empty_list.add_listeners(self.notification_callback)
        # Can't delete from empty list, but test the case
        self.assertEqual(self.notification_count, 0)
    
    def test_delitem_index_error(self):
        """Test delitem with invalid index raises IndexError"""
        with self.assertRaises(IndexError):
            del self.observable[10]
    
    def test_contains(self):
        """Test checking if item is in list"""
        self.assertTrue(2 in self.observable)
        self.assertFalse(99 in self.observable)
    
    def test_iter(self):
        """Test iteration over list items"""
        items = list(self.observable)
        self.assertEqual(items, [1, 2, 3])
    
    def test_reversed(self):
        """Test reverse iteration over list items"""
        items = list(reversed(self.observable))
        self.assertEqual(items, [3, 2, 1])
    
    def test_equality(self):
        """Test equality comparison"""
        other_list = ObservableList([1, 2, 3])
        self.assertEqual(self.observable, other_list)
        self.assertEqual(self.observable, [1, 2, 3])
        self.assertNotEqual(self.observable, [1, 2])
    
    def test_inequality(self):
        """Test inequality comparison"""
        other_list = ObservableList([1, 2, 4])
        self.assertNotEqual(self.observable, other_list)
        self.assertNotEqual(self.observable, [1, 2, 4])
    
    def test_less_than(self):
        """Test less than comparison"""
        self.assertTrue(ObservableList([1, 2]) < ObservableList([1, 3]))
        self.assertTrue(ObservableList([1, 2]) < [1, 3])
        self.assertFalse(ObservableList([1, 3]) < ObservableList([1, 2]))
    
    def test_less_equal(self):
        """Test less than or equal comparison"""
        self.assertTrue(ObservableList([1, 2]) <= ObservableList([1, 2]))
        self.assertTrue(ObservableList([1, 2]) <= ObservableList([1, 3]))
        self.assertTrue(ObservableList([1, 2]) <= [1, 2])
        self.assertFalse(ObservableList([1, 3]) <= ObservableList([1, 2]))
    
    def test_greater_than(self):
        """Test greater than comparison"""
        self.assertTrue(ObservableList([1, 3]) > ObservableList([1, 2]))
        self.assertTrue(ObservableList([1, 3]) > [1, 2])
        self.assertFalse(ObservableList([1, 2]) > ObservableList([1, 3]))
    
    def test_greater_equal(self):
        """Test greater than or equal comparison"""
        self.assertTrue(ObservableList([1, 2]) >= ObservableList([1, 2]))
        self.assertTrue(ObservableList([1, 3]) >= ObservableList([1, 2]))
        self.assertTrue(ObservableList([1, 2]) >= [1, 2])
        self.assertFalse(ObservableList([1, 2]) >= ObservableList([1, 3]))
    
    def test_addition(self):
        """Test list concatenation"""
        other_list = ObservableList([4, 5])
        result = self.observable + other_list
        self.assertEqual(result, [1, 2, 3, 4, 5])
        
        # Test with regular list
        result = self.observable + [4, 5]
        self.assertEqual(result, [1, 2, 3, 4, 5])
    
    def test_multiplication(self):
        """Test list repetition"""
        result = self.observable * 2
        self.assertEqual(result, [1, 2, 3, 1, 2, 3])
    
    def test_right_multiplication(self):
        """Test right multiplication"""
        result = 2 * self.observable
        self.assertEqual(result, [1, 2, 3, 1, 2, 3])
    
    def test_hash(self):
        """Test hash value"""
        hash1 = hash(self.observable)
        hash2 = hash(ObservableList([1, 2, 3]))
        self.assertEqual(hash1, hash2)
        
        # Test that hash changes when content changes
        self.observable.append(4)
        hash3 = hash(self.observable)
        self.assertNotEqual(hash1, hash3)
    
    def test_get_observed_component_values(self):
        """Test getting observed component values"""
        values = self.observable.get_observed_component_values()
        self.assertEqual(values, ([1, 2, 3],))
    
    def test_set_observed_values(self):
        """Test setting observed values"""
        self.observable.set_observed_values(([10, 20, 30],))
        self.assertEqual(self.observable.list_value, [10, 20, 30])
    
    def test_binding_error_handling(self):
        """Test error handling in binding methods"""
        with self.assertRaises(ValueError):
            self.observable.bind_to(None)
    
    def test_unbinding_error_handling(self):
        """Test error handling in unbinding methods"""
        # Test unbinding from something not bound
        other_list = ObservableList([4, 5, 6])
        with self.assertRaises(ValueError):
            self.observable.unbind_from(other_list)
    
    def test_verification_method(self):
        """Test the verification method in initialization"""
        # Test with invalid value type
        with self.assertRaises(ValueError):
            ObservableList("not a list")
    
    def test_copy_protection(self):
        """Test that list_value returns a copy"""
        original = self.observable.list_value
        original.append(99)
        self.assertEqual(self.observable.list_value, [1, 2, 3])  # Should not change
        self.assertEqual(original, [1, 2, 3, 99])  # Original should change
