import unittest

from observables import ObservableEnum, ObservableSet, SyncMode




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
        obs.set_enum_value(self.Color.BLUE)
        self.assertEqual(obs.enum_value, self.Color.BLUE)
        
        # Create an observable with limited options
        obs_limited = ObservableEnum(self.Color.RED, {self.Color.RED, self.Color.BLUE})
        
        # Change to invalid value should fail
        with self.assertRaises(ValueError):
            obs_limited.set_enum_value(self.Color.GREEN)  # GREEN is not in the limited options

    def test_change_enum_options(self):
        """Test changing the enum options."""
        obs = ObservableEnum(self.Color.RED)
        
        # Change to valid options
        new_options = {self.Color.RED, self.Color.BLUE, self.Color.GREEN}
        obs.set_enum_options(new_options)
        self.assertEqual(obs.enum_options, new_options)
        
        # Change to options that don't contain current value should fail
        with self.assertRaises(ValueError):
            obs.set_enum_options({self.Color.BLUE, self.Color.GREEN})
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
        obs1.bind_enum_value_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
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
        obs1.bind_enum_options_to(options_source, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
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
        obs1.bind_enum_value_to(obs2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        
        # Verify they are bound
        self.assertEqual(obs2.enum_value, self.Color.RED)
        obs1.enum_value = self.Color.GREEN
        self.assertEqual(obs2.enum_value, self.Color.GREEN)
        
        # Unbind them
        obs1.unbind_enum_value_from(obs2)
        
        # Changes should no longer propagate
        obs1.enum_value = self.Color.YELLOW
        self.assertEqual(obs2.enum_value, self.Color.GREEN)  # Should remain unchanged

    def test_binding_chain(self):
        """Test binding multiple observables in a chain."""
        obs1 = ObservableEnum(self.Color.RED)
        obs2 = ObservableEnum(self.Color.BLUE)
        obs3 = ObservableEnum(self.Color.GREEN)
        
        # Create chain: obs1 -> obs2 -> obs3 with explicit sync modes
        obs1.bind_enum_value_to(obs2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        obs2.bind_enum_value_to(obs3, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        
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
        source.bind_enum_value_to(target1, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        source.bind_enum_value_to(target2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        source.bind_enum_value_to(target3, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        
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
        obs.set_enum_options({self.Color.BLUE, self.Color.GREEN})
        self.assertEqual(notifications, ["changed", "changed"])

    def test_binding_system_consistency(self):
        """Test binding system consistency checking."""
        obs1 = ObservableEnum(self.Color.RED)
        obs2 = ObservableEnum(self.Color.BLUE)
        
        # Check consistency before binding
        is_consistent, message = obs1.check_binding_system_consistency()
        self.assertTrue(is_consistent, message)
        
        # Bind them together
        obs1.bind_enum_value_to(obs2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Check consistency after binding
        is_consistent, message = obs1.check_binding_system_consistency()
        self.assertTrue(is_consistent, message)

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        obs = ObservableEnum(self.Color.RED)
        
        # Try to bind to None
        with self.assertRaises(ValueError):
            obs.bind_enum_value_to(None, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Try to bind to self
        with self.assertRaises(ValueError):
            obs.bind_enum_value_to(obs, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)

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
        
        # Should complete in reasonable time (less than 3 seconds)
        self.assertLess(total_time, 3.0)

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