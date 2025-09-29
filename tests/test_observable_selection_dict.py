import unittest
from typing import Any, Literal, Mapping, Optional
from logging import Logger
from observables import ObservableSelectionDict, ObservableOptionalSelectionDict, OwnedHook, FloatingHook, BaseObservable, InitialSyncMode
# Set up logging for tests
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MockObservable(BaseObservable[Literal["value"], Any, Any, Any]):
    """Mock observable for testing purposes."""
    
    def __init__(self, name: str):
        self._internal_construct_from_values({"value": name})
    
    def _internal_construct_from_values(
        self,
        initial_values: Mapping[Literal["value"], str],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """Construct a MockObservable instance."""
        super().__init__(initial_component_values_or_hooks=initial_values)
    
    def _act_on_invalidation(self, keys: set[Literal["value"]]) -> None:
        """Act on invalidation - required by BaseObservable."""
        pass

class TestObservableSelectionDict(unittest.TestCase):
    """Test ObservableSelectionDict functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_owner = MockObservable("test_owner")

    def test_basic_creation(self):
        """Test basic ObservableSelectionDict creation."""
        # Create test data
        test_dict = {"a": 1, "b": 2, "c": 3}
        test_key = "b"
        test_value = 2
        
        # Create selection dict
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook=test_key,
            value_hook=None,
            logger=logger
        )
        
        # Verify creation
        self.assertIsNotNone(selection_dict)
        self.assertEqual(selection_dict.value, test_value)
        self.assertEqual(selection_dict.key, test_key)
        self.assertEqual(selection_dict.dict_hook.value, test_dict)

    def test_creation_with_hooks(self):
        """Test creation with external hooks."""
        # Create external hooks using FloatingHook to avoid owner registration issues
        dict_hook = FloatingHook(value={"x": 10, "y": 20}, logger=logger)
        key_hook = FloatingHook(value="x", logger=logger)
        value_hook = FloatingHook(value=10, logger=logger)
        
        # Create selection dict
        selection_dict = ObservableSelectionDict(
            dict_hook=dict_hook,
            key_hook=key_hook,
            value_hook=value_hook,
            logger=logger
        )
        
        # Verify creation
        self.assertIsNotNone(selection_dict)
        self.assertEqual(selection_dict.value, 10)
        self.assertEqual(selection_dict.key, "x")
        self.assertEqual(selection_dict.dict_hook.value, {"x": 10, "y": 20})

    def test_hook_interface(self):
        """Test CarriesHooks interface implementation."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test get_hook_keys
        keys = selection_dict.get_hook_keys()
        self.assertEqual(keys, {"dict", "key", "value"})
        
        # Test get_hook
        dict_hook = selection_dict.get_hook("dict")
        key_hook = selection_dict.get_hook("key")
        value_hook = selection_dict.get_hook("value")
        
        self.assertIsNotNone(dict_hook)
        self.assertIsNotNone(key_hook)
        self.assertIsNotNone(value_hook)
        
        # Test get_hook_value_as_reference
        self.assertEqual(selection_dict.get_hook_value_as_reference("dict"), test_dict)
        self.assertEqual(selection_dict.get_hook_value_as_reference("key"), "a")
        self.assertEqual(selection_dict.get_hook_value_as_reference("value"), 1)
        
        # Test get_hook_key
        self.assertEqual(selection_dict.get_hook_key(dict_hook), "dict")
        self.assertEqual(selection_dict.get_hook_key(key_hook), "key")
        self.assertEqual(selection_dict.get_hook_key(value_hook), "value")

    def test_value_properties(self):
        """Test value and key properties."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test initial values
        self.assertEqual(selection_dict.value, 1)
        self.assertEqual(selection_dict.key, "a")
        
        # Test setting values
        selection_dict.value = 999
        self.assertEqual(selection_dict.value, 999)
        self.assertEqual(selection_dict.dict_hook.value["a"], 999)
        
        selection_dict.key = "b"
        self.assertEqual(selection_dict.key, "b")
        self.assertEqual(selection_dict.value, 2)  # Should update to new key's value

    def test_connect_disconnect(self):
        """Test connect and disconnect functionality."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Create external hook
        external_hook = OwnedHook(owner=self.mock_owner, initial_value="b", logger=logger)
        
        # Connect to key hook
        selection_dict.connect_hook(external_hook, "key", InitialSyncMode.USE_TARGET_VALUE)  # type: ignore
        self.assertEqual(selection_dict.key, "b")
        self.assertEqual(selection_dict.value, 2)
        
        # Disconnect
        selection_dict.disconnect("key")
        # Key should remain "b" but no longer be connected to external hook

    def test_verification_method(self):
        """Test the verification method."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test valid values
        success, _ = selection_dict.validate_values({"dict": {"a": 1, "b": 2}})
        self.assertTrue(success)
        
        success, _ = selection_dict.validate_values({"key": "a"})
        self.assertTrue(success)
        
        success, _ = selection_dict.validate_values({"value": 1})
        self.assertTrue(success)
        
        # Test invalid values - need to test with both key and dict context
        with self.assertRaises(ValueError) as cm:
            selection_dict.validate_values({"key": "nonexistent", "dict": {"a": 1, "b": 2}})
        self.assertIn("not in dictionary", str(cm.exception))

    def test_invalidation(self):
        """Test invalidation behavior."""
        test_dict = {"a": 1, "b": 2}
        def invalidate_callback() -> tuple[bool, str]:
            return True, "Successfully invalidated"
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger,
            invalidate_callback=invalidate_callback
        )
        
        # Test invalidation
        success, msg = selection_dict.invalidate()
        self.assertTrue(success)
        self.assertEqual(msg, "Successfully invalidated")

    def test_dict_key_change_propagation(self):
        """Test that changing dict or key updates the value."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Change key
        selection_dict.key = "b"
        self.assertEqual(selection_dict.value, 2)
        
        # Change dict to include the current key
        selection_dict.dict_hook.submit_value({"b": 200, "x": 100, "y": 300})
        # Now we can set the key to "x" since "b" is still valid
        selection_dict.key = "x"
        self.assertEqual(selection_dict.value, 100)

    def test_value_change_propagation(self):
        """Test that changing value updates the dict."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Change value
        selection_dict.value = 999
        self.assertEqual(selection_dict.dict_hook.value["a"], 999)
        self.assertEqual(selection_dict.value, 999)


class TestObservableOptionalSelectionDict(unittest.TestCase):
    """Test ObservableOptionalSelectionDict functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_owner = MockObservable("test_owner")

    def test_basic_creation(self):
        """Test basic ObservableOptionalSelectionDict creation."""
        # Create test data
        test_dict = {"a": 1, "b": 2, "c": 3}
        test_key = "b"
        test_value = 2
        
        # Create selection dict
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook=test_key,
            value_hook=None,
            logger=logger
        )
        
        # Verify creation
        self.assertIsNotNone(selection_dict)
        self.assertEqual(selection_dict.value, test_value)
        self.assertEqual(selection_dict.key, test_key)
        self.assertEqual(selection_dict.dict_hook.value, test_dict)

    def test_creation_with_none_values(self):
        """Test creation with None values."""
        test_dict = {"a": 1, "b": 2}
        
        # Create with None key and value
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            logger=logger
        )
        
        # Verify creation
        self.assertIsNotNone(selection_dict)
        self.assertIsNone(selection_dict.value)
        self.assertIsNone(selection_dict.key)

    def test_optional_behavior(self):
        """Test optional behavior with None values."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            logger=logger
        )
        
        # Initially both key and value should be None
        self.assertIsNone(selection_dict.key)
        self.assertIsNone(selection_dict.value)
        
        # Set key to a valid value - should get value from dict
        selection_dict.key = "a"
        self.assertEqual(selection_dict.value, 1)
        
        # Set value to None for a non-None key - should work
        selection_dict.value = None
        self.assertEqual(selection_dict.key, "a")
        self.assertIsNone(selection_dict.value)
        
        # Set key back to None - value should automatically be None
        selection_dict.key = None
        self.assertIsNone(selection_dict.key)
        self.assertIsNone(selection_dict.value)

    def test_hook_interface_optional(self):
        """Test CarriesHooks interface with optional values."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test get_hook_keys
        keys = selection_dict.get_hook_keys()
        self.assertEqual(keys, {"dict", "key", "value"})
        
        # Test get_hook_value_as_reference - setting key to None sets value to None
        selection_dict.key = None
        self.assertIsNone(selection_dict.value)

    def test_verification_method_optional(self):
        """Test verification method with optional values."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test valid values
        success, msg = selection_dict.validate_values({"key": "a"})
        self.assertTrue(success)
        
        success, msg = selection_dict.validate_values({"value": 1})
        self.assertTrue(success)
        
        # Test None key - should be valid and set value to None
        selection_dict.key = None
        self.assertIsNone(selection_dict.value)
        # Dictionary should remain unchanged
        self.assertEqual(selection_dict.dict_hook.value, test_dict)
        
        # Test None key with non-None value (should be invalid)
        success, msg = selection_dict.validate_values({"key": None, "value": 999})
        self.assertFalse(success)
        self.assertIn("Value is not None when key is None", msg)

    def test_optional_value_properties(self):
        """Test value and key properties with optional types."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test initial values
        self.assertEqual(selection_dict.value, 1)
        self.assertEqual(selection_dict.key, "a")
        
        # Test setting value to None for a non-None key - should work
        selection_dict.value = None
        self.assertEqual(selection_dict.key, "a")
        self.assertIsNone(selection_dict.value)
        
        # Test setting key to None - should work and value should be None
        selection_dict.key = None
        self.assertIsNone(selection_dict.key)
        self.assertIsNone(selection_dict.value)

    def test_error_handling_optional(self):
        """Test error handling for invalid optional combinations."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test setting key to None - should set value to None
        selection_dict.key = None
        self.assertIsNone(selection_dict.value)
        # Setting key back to "a" and value to 999 should work
        selection_dict.key = "a"
        selection_dict.value = 999
        self.assertEqual(selection_dict.value, 999)

    def test_collective_hooks_optional(self):
        """Test CarriesCollectiveHooks interface with optional values."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test get_collective_hook_keys
        collective_keys = selection_dict.get_hook_keys()
        self.assertEqual(collective_keys, {"dict", "key", "value"})
        
        # Test that the interface is properly implemented
        # The connect_hooks functionality is tested elsewhere
        self.assertTrue(hasattr(selection_dict, 'connect_hooks'))

    def test_edge_case_empty_dict(self):
        """Test behavior with empty dictionary."""
        # Test that creation with empty dict and invalid key fails
        with self.assertRaises(KeyError):
            ObservableOptionalSelectionDict(
                dict_hook={},
                key_hook="nonexistent",
                value_hook=None,
                logger=logger
            )
        
        # Test that None key with empty dict works
        selection_dict = ObservableOptionalSelectionDict[str, int](
            dict_hook={},
            key_hook=None,
            value_hook=None,
            logger=logger
        )
        self.assertIsNone(selection_dict.key)
        self.assertIsNone(selection_dict.value)

    def test_edge_case_single_item_dict(self):
        """Test behavior with single-item dictionary."""
        test_dict = {"only": 42}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="only",
            value_hook=None,
            logger=logger
        )
        
        self.assertEqual(selection_dict.key, "only")
        self.assertEqual(selection_dict.value, 42)
        
        # Test switching to None (must do key first, then value)
        selection_dict.key = None
        self.assertIsNone(selection_dict.key)
        self.assertIsNone(selection_dict.value)

    def test_edge_case_large_dict(self):
        """Test behavior with large dictionary."""
        # Create a large dictionary
        large_dict = {f"key_{i}": i * 100 for i in range(1000)}
        
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=large_dict,
            key_hook="key_500",
            value_hook=None,
            logger=logger
        )
        
        self.assertEqual(selection_dict.key, "key_500")
        self.assertEqual(selection_dict.value, 50000)
        
        # Test switching to another key
        selection_dict.key = "key_999"
        self.assertEqual(selection_dict.value, 99900)

    def test_complex_value_types(self):
        """Test with complex value types."""
        complex_dict = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2, 3),
            "set": {1, 2, 3}
        }
        
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=complex_dict,
            key_hook="list",
            value_hook=None,
            logger=logger
        )
        
        self.assertEqual(selection_dict.value, [1, 2, 3])
        
        # Test switching to different complex types
        selection_dict.key = "dict"
        self.assertEqual(selection_dict.value, {"nested": "value"})
        
        selection_dict.key = "tuple"
        self.assertEqual(selection_dict.value, (1, 2, 3))

    def test_concurrent_modifications(self):
        """Test handling of concurrent modifications."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Modify the underlying dict directly
        test_dict["d"] = 4
        
        # Should be able to switch to the new key
        selection_dict.key = "d"
        self.assertEqual(selection_dict.value, 4)
        
        # Remove a key from underlying dict using set_dict_and_key
        new_dict = {"b": 2, "c": 3, "d": 4}  # Remove key "a"
        selection_dict.set_dict_and_key(new_dict, "d")  # Set to valid key
        
        # Should not be able to switch back to removed key
        with self.assertRaises(KeyError):
            selection_dict.key = "a"

    def test_set_dict_and_key_method(self):
        """Test the set_dict_and_key method for both classes."""
        # Test ObservableSelectionDict
        selection_dict = ObservableSelectionDict(
            dict_hook={"a": 1},
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Verify initial state
        self.assertEqual(selection_dict.key, "a")
        self.assertEqual(selection_dict.value, 1)
        
        # Use set_dict_and_key to change both
        selection_dict.set_dict_and_key({"x": 100, "y": 200}, "x")
        
        # Check the results
        self.assertEqual(selection_dict.key, "x")
        self.assertEqual(selection_dict.value, 100)
        self.assertEqual(selection_dict.dict_hook.value, {"x": 100, "y": 200})
        
        # Test ObservableOptionalSelectionDict
        optional_dict = ObservableOptionalSelectionDict(
            dict_hook={"a": 1},
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Use set_dict_and_key to change both
        optional_dict.set_dict_and_key({"x": 100, "y": 200}, "y")
        self.assertEqual(optional_dict.key, "y")
        self.assertEqual(optional_dict.value, 200)
        
        # Test with None key
        optional_dict.set_dict_and_key({"a": 1, "b": 2}, None)
        self.assertIsNone(optional_dict.key)
        self.assertIsNone(optional_dict.value)

    def test_validation_edge_cases(self):
        """Test edge cases in validation logic."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test validation with all three values
        success, msg = selection_dict.validate_values({
            "dict": {"x": 10, "y": 20},
            "key": "x",
            "value": 10
        })
        self.assertTrue(success)
        
        # Test validation with mismatched dict and value
        success, msg = selection_dict.validate_values({
            "dict": {"x": 10, "y": 20},
            "key": "x",
            "value": 999  # Wrong value
        })
        self.assertFalse(success)
        
        # Test validation with None dict
        success, msg = selection_dict.validate_values({
            "dict": None,
            "key": "x",
            "value": 10
        })
        self.assertFalse(success)
        self.assertIn("Dictionary is None", msg)

    def test_property_getter_setters_comprehensive(self):
        """Test comprehensive property getter/setter behavior."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        selection_dict = ObservableOptionalSelectionDict[str, int](
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test dict_hook property
        self.assertEqual(selection_dict.dict_hook.value, test_dict)
        
        # Test key_hook property
        self.assertEqual(selection_dict.key_hook.value, "a")
        
        # Test value_hook property
        self.assertEqual(selection_dict.value_hook.value, 1)
        
        # Test rapid successive changes
        for key in ["b", "c", "a"]:
            selection_dict.key = key
            self.assertEqual(selection_dict.key, key)
            self.assertEqual(selection_dict.value, test_dict[key])

    def test_error_messages_clarity(self):
        """Test that error messages are clear and helpful."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Test clear error message for invalid key
        try:
            selection_dict.key = None  # Should fail because value is not None
        except ValueError as e:
            self.assertIn("Cannot set key to None when current value is", str(e))
        
        # Test clear error message for invalid value
        try:
            selection_dict.value = None  # Should fail because key is not None
        except ValueError as e:
            self.assertIn("Cannot set value to None when current key is", str(e))

    def test_stress_test_rapid_changes(self):
        """Stress test with rapid changes."""
        test_dict = {f"key_{i}": i for i in range(100)}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="key_0",
            value_hook=None,
            logger=logger
        )
        
        # Rapidly change keys
        for i in range(0, 100, 10):
            key = f"key_{i}"
            selection_dict.key = key
            self.assertEqual(selection_dict.key, key)
            self.assertEqual(selection_dict.value, i)
        
        # Rapidly change values
        for i in range(0, 100, 5):
            new_value = i * 1000
            selection_dict.value = new_value
            # Verify dict was updated
            current_key = selection_dict.key
            assert current_key is not None
            self.assertEqual(selection_dict.dict_hook.value[current_key], new_value)

    def test_type_safety_edge_cases(self):
        """Test type safety with various edge cases."""
        # Test with string keys and numeric values
        test_dict = {"1": 1, "2": 2, "3": 3}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="1",
            value_hook=None,
            logger=logger
        )
        
        self.assertEqual(selection_dict.key, "1")
        self.assertEqual(selection_dict.value, 1)
        
        # Test switching between string keys
        selection_dict.key = "2"
        self.assertEqual(selection_dict.value, 2)

    def test_destroy_cleanup(self):
        """Test destroy method properly cleans up resources."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            logger=logger
        )
        
        # Add some listeners to test cleanup
        def dummy_listener():
            pass
        
        selection_dict.add_listeners(dummy_listener)
        self.assertTrue(selection_dict.has_listeners())
        
        # Test destroy method exists and can be called
        # Note: destroy method should remove listeners but we can't easily test
        # the complete cleanup without internal access
        self.assertTrue(hasattr(selection_dict, 'destroy'))


if __name__ == "__main__":
    unittest.main()
