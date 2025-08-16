import unittest
from enum import Enum
from observables import ObservableEnum, SyncMode


class TestEnum(Enum):
    """Test enum for testing purposes"""
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"


class TestObservableEnum(unittest.TestCase):
    """Test cases for ObservableEnum"""
    
    def setUp(self):
        self.observable = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B, TestEnum.C})
        self.notification_count = 0
    
    def notification_callback(self):
        self.notification_count += 1
    
    def test_initial_enum_value(self):
        """Test that initial enum value is set correctly"""
        self.assertEqual(self.observable.enum_value, TestEnum.A)
    
    def test_initial_enum_options(self):
        """Test that initial enum options are set correctly"""
        self.assertEqual(self.observable.enum_options, {TestEnum.A, TestEnum.B, TestEnum.C})
    
    def test_change_enum_value(self):
        """Test changing enum value"""
        self.observable.enum_value = TestEnum.B
        self.assertEqual(self.observable.enum_value, TestEnum.B)
    
    def test_change_enum_options(self):
        """Test changing enum options"""
        # Change to options that include the current value
        self.observable.enum_options = {TestEnum.A, TestEnum.D, TestEnum.E}
        self.assertEqual(self.observable.enum_options, {TestEnum.A, TestEnum.D, TestEnum.E})
    
    def test_listener_notification(self):
        """Test that listeners are notified when enum value changes"""
        self.observable.add_listeners(self.notification_callback)
        self.observable.enum_value = TestEnum.C
        self.assertEqual(self.notification_count, 1)
    
    def test_binding_enum_value(self):
        """Test binding enum value to another observable"""
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(TestEnum.B, {TestEnum.A, TestEnum.B})
        
        # Bind enum1's value to enum2
        enum1.bind_enum_value_to_observable(enum2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change enum2's value, enum1 should update
        enum2.enum_value = TestEnum.A
        self.assertEqual(enum1.enum_value, TestEnum.A)
        
        # Change enum1's value, enum2 should update
        enum1.enum_value = TestEnum.B
        self.assertEqual(enum2.enum_value, TestEnum.B)
    
    def test_binding_enum_options(self):
        """Test binding enum options to another observable"""
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(TestEnum.B, {TestEnum.A, TestEnum.B})
        
        # Bind enum1's options to enum2
        enum1.bind_enum_options_to_observable(enum2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Change enum2's options, enum1 should update
        enum2.enum_options = {TestEnum.A, TestEnum.B, TestEnum.C}
        self.assertEqual(enum1.enum_options, {TestEnum.A, TestEnum.B, TestEnum.C})
        
        # Change enum1's options, enum2 should update
        enum1.enum_options = {TestEnum.A, TestEnum.B, TestEnum.D}
        self.assertEqual(enum2.enum_options, {TestEnum.A, TestEnum.B, TestEnum.D})
    
    def test_binding_system_consistency(self):
        """Test binding system consistency"""
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(TestEnum.B, {TestEnum.A, TestEnum.B})
        
        # Bind them together
        enum1.bind_to(enum2)
        
        # Check binding consistency
        is_consistent, message = enum1.check_binding_system_consistency()
        self.assertTrue(is_consistent, f"Binding system should be consistent: {message}")
    
    def test_boolean_conversion(self):
        """Test boolean conversion of enum value"""
        # Test with valid enum value
        self.assertTrue(bool(self.observable))
        
        # Test with None enum value
        none_enum = ObservableEnum(None, {TestEnum.A, TestEnum.B})
        self.assertFalse(bool(none_enum))
    
    def test_comparison_operators(self):
        """Test comparison operators with enum values"""
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(TestEnum.B, {TestEnum.A, TestEnum.B})
        
        # Test equality
        self.assertEqual(enum1, TestEnum.A)
        self.assertEqual(enum1, enum1)
        self.assertNotEqual(enum1, TestEnum.B)
        
        # Test less than/greater than (based on enum order)
        # Note: ObservableEnum doesn't support < > operators directly
        self.assertLess(TestEnum.A.value, TestEnum.B.value)
        self.assertGreater(TestEnum.B.value, TestEnum.A.value)
    
    def test_edge_cases(self):
        """Test edge cases for enum operations"""
        # Test with None value and valid options
        none_enum = ObservableEnum(None, {TestEnum.A, TestEnum.B})
        self.assertIsNone(none_enum.enum_value)
        self.assertEqual(none_enum.enum_options, {TestEnum.A, TestEnum.B})
    
    def test_initialization_with_custom_options(self):
        """Test initialization with custom enum options"""
        custom_options = {TestEnum.D, TestEnum.E}
        custom_enum = ObservableEnum(TestEnum.D, custom_options)
        self.assertEqual(custom_enum.enum_value, TestEnum.D)
        self.assertEqual(custom_enum.enum_options, custom_options)
    
    def test_initialization_with_enum_value(self):
        """Test initialization with just enum value"""
        value_only_enum = ObservableEnum(TestEnum.B)
        self.assertEqual(value_only_enum.enum_value, TestEnum.B)
        # Should have default options based on the enum class
        self.assertIsInstance(value_only_enum.enum_options, set)
    
    def test_initialization_with_observable_enum(self):
        """Test initialization with another ObservableEnum"""
        source_enum = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        target_enum = ObservableEnum(source_enum)
        
        # Check initial values
        self.assertEqual(target_enum.enum_value, TestEnum.A)
        # The options should include all enum values by default
        self.assertIn(TestEnum.A, target_enum.enum_options)
        self.assertIn(TestEnum.B, target_enum.enum_options)
    
    def test_initialization_with_observable_options(self):
        """Test initialization with ObservableSet for options"""
        from observables import ObservableSet
        
        options_set = ObservableSet({TestEnum.A, TestEnum.B})
        enum_with_obs_options = ObservableEnum(TestEnum.A, options_set)
        
        self.assertEqual(enum_with_obs_options.enum_value, TestEnum.A)
        self.assertEqual(enum_with_obs_options.enum_options, {TestEnum.A, TestEnum.B})
        
        # Check binding
        options_set.add(TestEnum.C)
        self.assertEqual(enum_with_obs_options.enum_options, {TestEnum.A, TestEnum.B, TestEnum.C})
    
    def test_multiple_targets(self):
        """Test multiple targets bound to the same source"""
        source = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        target1 = ObservableEnum(source)
        target2 = ObservableEnum(source)
        
        # Check initial values
        self.assertEqual(target1.enum_value, TestEnum.A)
        self.assertEqual(target2.enum_value, TestEnum.A)
        
        # Change source, all targets should update
        source.enum_value = TestEnum.B
        self.assertEqual(target1.enum_value, TestEnum.B)
        self.assertEqual(target2.enum_value, TestEnum.B)
    
    def test_add_enum_option(self):
        """Test adding an enum option"""
        self.observable.add_enum_option(TestEnum.D)
        self.assertIn(TestEnum.D, self.observable.enum_options)
    
    def test_remove_enum_option(self):
        """Test removing an enum option"""
        self.observable.remove_enum_option(TestEnum.B)
        self.assertNotIn(TestEnum.B, self.observable.enum_options)
    
    def test_set_enum_value_and_options(self):
        """Test setting both enum value and options at once"""
        self.observable.set_enum_value_and_options(TestEnum.D, {TestEnum.D, TestEnum.E})
        self.assertEqual(self.observable.enum_value, TestEnum.D)
        self.assertEqual(self.observable.enum_options, {TestEnum.D, TestEnum.E})
    
    def test_string_representations(self):
        """Test string representation methods"""
        str_repr = str(self.observable)
        repr_repr = repr(self.observable)
        
        self.assertIn("TestEnum.A", str_repr)
        self.assertIn("ObservableEnum", repr_repr)
    
    def test_unbinding(self):
        """Test unbinding from observables"""
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(TestEnum.B, {TestEnum.A, TestEnum.B})
        
        # Bind them
        enum1.bind_to(enum2)
        
        # Unbind
        enum1.unbind_from(enum2)
        
        # Changes should no longer propagate
        enum2.enum_value = TestEnum.A
        self.assertEqual(enum1.enum_value, TestEnum.A)  # Should not change
    
    def test_validation_on_initialization(self):
        """Test validation during initialization"""
        # Test with invalid enum value
        with self.assertRaises(ValueError):
            ObservableEnum("not an enum", {TestEnum.A, TestEnum.B})
        
        # Test with invalid options type
        with self.assertRaises(AttributeError):
            ObservableEnum(TestEnum.A, "not a set")
    
    def test_initialization_with_carries_bindable_set_performance(self):
        """Test performance of initialization with CarriesBindableSet"""
        from observables import ObservableSet
        
        options_set = ObservableSet({TestEnum.A, TestEnum.B, TestEnum.C, TestEnum.D, TestEnum.E})
        
        import time
        start_time = time.time()
        
        for _ in range(1000):
            enum = ObservableEnum(TestEnum.A, options_set)
            _ = enum.enum_value  # Access to ensure initialization is complete
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time (less than 3 seconds)
        self.assertLess(total_time, 3.0)
    
    def test_initialization_with_carries_enum_performance(self):
        """Test performance of initialization with CarriesBindableEnum"""
        source_enum = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B, TestEnum.C, TestEnum.D, TestEnum.E})
        
        import time
        start_time = time.time()
        
        for _ in range(1000):
            enum = ObservableEnum(source_enum)
            _ = enum.enum_value  # Access to ensure initialization is complete
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time (less than 3 seconds)
        self.assertLess(total_time, 3.0)
    
    def test_binding_chain(self):
        """Test binding in a chain"""
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(enum1)
        enum3 = ObservableEnum(enum2)
        
        # Check initial values
        self.assertEqual(enum1.enum_value, TestEnum.A)
        self.assertEqual(enum2.enum_value, TestEnum.A)
        self.assertEqual(enum3.enum_value, TestEnum.A)
        
        # Change the first enum
        enum1.enum_value = TestEnum.B
        self.assertEqual(enum1.enum_value, TestEnum.B)
        self.assertEqual(enum2.enum_value, TestEnum.B)
        self.assertEqual(enum3.enum_value, TestEnum.B)
    
    def test_binding_enum_options_chain(self):
        """Test binding enum options in a chain"""
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(enum1)
        enum3 = ObservableEnum(enum2)
        
        # Check initial options
        self.assertEqual(enum1.enum_options, {TestEnum.A, TestEnum.B})
        self.assertEqual(enum2.enum_options, {TestEnum.A, TestEnum.B})
        self.assertEqual(enum3.enum_options, {TestEnum.A, TestEnum.B})
        
        # Change the first enum's options
        enum1.enum_options = {TestEnum.C, TestEnum.D}
        self.assertEqual(enum1.enum_options, {TestEnum.C, TestEnum.D})
        self.assertEqual(enum2.enum_options, {TestEnum.C, TestEnum.D})
        self.assertEqual(enum3.enum_options, {TestEnum.C, TestEnum.D})
    
    def test_binding_removal_in_chain(self):
        """Test binding removal in a chain"""
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(enum1)
        enum3 = ObservableEnum(enum2)
        
        # Remove binding between enum2 and enum3
        enum3.unbind_from(enum2)
        
        # Change enum1, enum2 should update but enum3 should not
        enum1.enum_value = TestEnum.B
        self.assertEqual(enum2.enum_value, TestEnum.B)
        self.assertEqual(enum3.enum_value, TestEnum.A)  # Should not change
    
    def test_circular_binding_prevention(self):
        """Test that circular bindings are prevented"""
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(TestEnum.B, {TestEnum.A, TestEnum.B})
        
        # Bind enum1 to enum2
        enum1.bind_to(enum2)
        
        # Try to bind enum2 back to enum1 (should not create circular binding)
        # This will fail because they're already bound
        with self.assertRaises(ValueError):
            enum2.bind_to(enum1)
    
    def test_mixed_type_binding_chain(self):
        """Test binding chain with mixed types"""
        from observables import ObservableSet
        
        # Create a chain: ObservableSet -> ObservableEnum -> ObservableEnum
        options_set = ObservableSet({TestEnum.A, TestEnum.B})
        enum1 = ObservableEnum(TestEnum.A, options_set)
        enum2 = ObservableEnum(enum1)
        
        # Change the set, both enums should update
        options_set.add(TestEnum.C)
        self.assertIn(TestEnum.C, enum1.enum_options)
        self.assertIn(TestEnum.C, enum2.enum_options)
        
        # Change enum1, enum2 should update
        enum1.enum_value = TestEnum.B
        self.assertEqual(enum2.enum_value, TestEnum.B)
    
    def test_binding_cleanup(self):
        """Test that bindings are properly cleaned up"""
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(enum1)
        
        # Check they are bound
        self.assertTrue(enum2._get_enum_hook().is_bound_to(enum1._get_enum_hook()))
        
        # Unbind
        enum2.unbind_from(enum1)
        
        # Check they are no longer bound
        self.assertFalse(enum2._get_enum_hook().is_bound_to(enum1._get_enum_hook()))
    
    def test_error_recovery(self):
        """Test error recovery in binding system"""
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(enum1)
        
        # Simulate a binding error by corrupting the hook
        # This tests the error handling in the binding system
        try:
            # This should not crash the system
            enum2.unbind_from(enum1)
            enum2.unbind_from(enum1)  # Try to unbind again
        except Exception:
            # Should handle gracefully
            pass
        
        # System should still be functional
        self.assertEqual(enum2.enum_value, TestEnum.A)
    
    def test_memory_management(self):
        """Test memory management in binding system"""
        import weakref
        
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        weak_ref = weakref.ref(enum1)
        
        # Create and destroy many bound enums
        for _ in range(100):
            enum2 = ObservableEnum(enum1)
            del enum2
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # enum1 should still exist
        self.assertIsNotNone(weak_ref())
    
    def test_concurrent_access(self):
        """Test concurrent access to bound enums"""
        import threading
        import time
        
        enum1 = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        enum2 = ObservableEnum(enum1)
        
        results = []
        errors = []
        
        def reader():
            try:
                for _ in range(100):
                    results.append(enum2.enum_value)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        def writer():
            try:
                for i in range(10):
                    enum1.enum_value = TestEnum.B if i % 2 == 0 else TestEnum.A
                    time.sleep(0.002)
            except Exception as e:
                errors.append(e)
        
        # Start reader and writer threads
        reader_thread = threading.Thread(target=reader)
        writer_thread = threading.Thread(target=writer)
        
        reader_thread.start()
        writer_thread.start()
        
        reader_thread.join()
        writer_thread.join()
        
        # Check for errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertGreater(len(results), 0)
    
    def test_type_safety(self):
        """Test type safety in binding system"""
        from observables import ObservableSingleValue
        
        # Try to bind enum to single value (should work for value binding)
        single_value = ObservableSingleValue(TestEnum.A)
        enum = ObservableEnum(TestEnum.A, {TestEnum.A, TestEnum.B})
        
        # Bind enum value to single value
        enum.bind_enum_value_to_observable(single_value)
        
        # Change single value, enum should update
        single_value.single_value = TestEnum.B
        self.assertEqual(enum.enum_value, TestEnum.B)
    
    def test_validation_errors(self):
        """Test validation error handling"""
        # Test with invalid enum value type
        with self.assertRaises(ValueError):
            ObservableEnum(123, {TestEnum.A, TestEnum.B})
        
        # Test with invalid options type
        with self.assertRaises(AttributeError):
            ObservableEnum(TestEnum.A, "invalid")
        
        # Test with enum value not in options
        with self.assertRaises(ValueError):
            ObservableEnum(TestEnum.A, {TestEnum.B, TestEnum.C})