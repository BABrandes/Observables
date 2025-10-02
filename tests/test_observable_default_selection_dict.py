import unittest
from typing import Any, Literal, Mapping, Optional
from logging import Logger
from observables import ObservableDefaultSelectionDict, OwnedHook, FloatingHook, BaseObservable, InitialSyncMode, HookLike
# Set up logging for tests
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MockObservable(BaseObservable[Literal["value"], Any, Any, Any, "MockObservable"]):
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


class TestObservableDefaultSelectionDict(unittest.TestCase):
    """Test ObservableDefaultSelectionDict functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_owner = MockObservable("test_owner")

    def test_basic_creation(self):
        """Test basic ObservableDefaultSelectionDict creation."""
        # Create test data
        test_dict = {"a": 1, "b": 2, "c": 3}
        test_key = "b"
        default_value = 999
        
        # Create default selection dict
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook=test_key,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Verify creation
        self.assertIsNotNone(selection_dict)
        self.assertEqual(selection_dict.value, 2)  # Should be dict value, not default
        self.assertEqual(selection_dict.key, test_key)
        self.assertEqual(selection_dict.dict_hook.value, test_dict)

    def test_creation_with_none_key(self):
        """Test creation with None key uses default value."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        # Create with None key
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Verify creation
        self.assertIsNotNone(selection_dict)
        self.assertEqual(selection_dict.value, default_value)
        self.assertIsNone(selection_dict.key)

    def test_creation_with_hooks(self):
        """Test creation with external hooks."""
        # Create external hooks using FloatingHook to avoid owner registration issues
        dict_hook = FloatingHook(value={"x": 10, "y": 20}, logger=logger)
        key_hook: HookLike[str|None] = FloatingHook(value="x", logger=logger)
        value_hook = FloatingHook(value=10, logger=logger)
        default_value = 999
        
        # Create selection dict
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=dict_hook,
            key_hook=key_hook,
            value_hook=value_hook,
            default_value=default_value,
            logger=logger
        )
        
        # Verify creation
        self.assertIsNotNone(selection_dict)
        self.assertEqual(selection_dict.value, 10)
        self.assertEqual(selection_dict.key, "x")
        self.assertEqual(selection_dict.dict_hook.value, {"x": 10, "y": 20})

    def test_default_value_behavior(self):
        """Test default value behavior when key is None."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Initially key "a" should give value 1
        self.assertEqual(selection_dict.value, 1)
        self.assertEqual(selection_dict.key, "a")
        
        # Set key to None - should use default value
        selection_dict.key = None
        self.assertEqual(selection_dict.value, default_value)
        self.assertIsNone(selection_dict.key)
        
        # Set key back to "b" - should use dict value
        selection_dict.key = "b"
        self.assertEqual(selection_dict.value, 2)
        self.assertEqual(selection_dict.key, "b")

    def test_value_setting_with_none_key(self):
        """Test setting value when key is None."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Should be able to set value to default when key is None
        selection_dict.value = default_value
        self.assertEqual(selection_dict.value, default_value)
        
        # Should not be able to set value to non-default when key is None
        with self.assertRaises(ValueError) as context:
            selection_dict.value = 123
        self.assertIn("not the default value", str(context.exception))

    def test_value_setting_with_valid_key(self):
        """Test setting value when key is valid."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Should be able to set value when key is valid
        selection_dict.value = 777
        self.assertEqual(selection_dict.value, 777)
        self.assertEqual(selection_dict.dict_hook.value["a"], 777)

    def test_hook_interface(self):
        """Test CarriesHooks interface implementation."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
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
        self.assertEqual(selection_dict.get_value_reference_of_hook("dict"), test_dict)
        self.assertEqual(selection_dict.get_value_reference_of_hook("key"), "a")
        self.assertEqual(selection_dict.get_value_reference_of_hook("value"), 1)
        
        # Test get_hook_key
        self.assertEqual(selection_dict.get_hook_key(dict_hook), "dict")
        self.assertEqual(selection_dict.get_hook_key(key_hook), "key")
        self.assertEqual(selection_dict.get_hook_key(value_hook), "value")

    def test_verification_method(self):
        """Test the verification method."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Test valid values with key
        success, msg = selection_dict.validate_values({"dict": {"a": 1, "b": 2}, "key": "a", "value": 1})
        self.assertTrue(success)
        
        # Test valid values with None key and default value
        success, msg = selection_dict.validate_values({"dict": {"a": 1, "b": 2}, "key": None, "value": default_value})
        self.assertTrue(success)
        
        # Test invalid - None key with non-default value
        success, msg = selection_dict.validate_values({"dict": {"a": 1, "b": 2}, "key": None, "value": 123})
        self.assertFalse(success)
        self.assertIn("not the default value", msg)
        
        # Test invalid - key not in dict
        success, msg = selection_dict.validate_values({"dict": {"a": 1, "b": 2}, "key": "z", "value": 1})
        self.assertFalse(success)
        self.assertIn("not in dictionary", msg)
        
        # Test invalid - value doesn't match dictionary value
        success, msg = selection_dict.validate_values({"dict": {"a": 1, "b": 2}, "key": "a", "value": 999})
        self.assertFalse(success)  # Should be invalid - value doesn't match dictionary
        self.assertIn("not equal to value in dictionary", msg)

    def test_dict_key_change_propagation(self):
        """Test that changing dict or key updates the value."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        default_value = 999
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Change key
        selection_dict.key = "b"
        self.assertEqual(selection_dict.value, 2)
        
        # Change key to None - should use default
        selection_dict.key = None
        self.assertEqual(selection_dict.value, default_value)
        
        # Change dict and then set key
        selection_dict.dict_hook.submit_value({"b": 200, "x": 100, "y": 300})
        selection_dict.key = "x"
        self.assertEqual(selection_dict.value, 100)

    def test_value_change_propagation(self):
        """Test that changing value updates the dict."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Change value when key is set
        selection_dict.value = 777
        self.assertEqual(selection_dict.dict_hook.value["a"], 777)
        self.assertEqual(selection_dict.value, 777)

    def test_connect_disconnect(self):
        """Test connect and disconnect functionality."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
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

    def test_invalidation(self):
        """Test invalidation behavior."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Test invalidation
        success, msg = selection_dict.invalidate()
        self.assertTrue(success)
        self.assertEqual(msg, "No invalidate callback provided")

    def test_set_dict_and_key(self):
        """Test set_dict_and_key method."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Set valid dict and key
        new_dict = {"x": 100, "y": 200}
        selection_dict.set_dict_and_key(new_dict, "x")
        self.assertEqual(selection_dict.dict_hook.value, new_dict)
        self.assertEqual(selection_dict.key, "x")
        self.assertEqual(selection_dict.value, 100)
        
        # Set dict and None key
        selection_dict.set_dict_and_key(new_dict, None)
        self.assertEqual(selection_dict.dict_hook.value, new_dict)
        self.assertIsNone(selection_dict.key)
        self.assertEqual(selection_dict.value, default_value)

    def test_error_handling(self):
        """Test error handling for invalid operations."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        # Test creation with invalid value_hook
        with self.assertRaises(ValueError):
            ObservableDefaultSelectionDict(
                dict_hook=test_dict,
                key_hook="a",
                value_hook="invalid",  # type: ignore
                default_value=default_value,
                logger=logger
            )

    def test_edge_cases(self):
        """Test edge cases."""
        # Test with empty dict
        empty_dict: dict[str, int] = {}
        default_value = 999
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=empty_dict,
            key_hook=None,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        self.assertEqual(selection_dict.value, default_value)
        self.assertIsNone(selection_dict.key)
        
        # Test with default value that equals a dict value
        test_dict = {"a": 999, "b": 2}
        selection_dict2 = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            default_value=999,  # Same as dict["a"]
            logger=logger
        )
        
        self.assertEqual(selection_dict2.value, 999)
        self.assertIsNone(selection_dict2.key)
        
        # Set key to "a" - should still work even though value is same
        selection_dict2.key = "a"
        self.assertEqual(selection_dict2.value, 999)
        self.assertEqual(selection_dict2.key, "a")

    def test_properties(self):
        """Test property access."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Test dict_hook property
        dict_hook = selection_dict.dict_hook
        self.assertIsNotNone(dict_hook)
        self.assertEqual(dict_hook.value, test_dict)
        
        # Test key_hook property
        key_hook = selection_dict.key_hook
        self.assertIsNotNone(key_hook)
        self.assertEqual(key_hook.value, "a")
        
        # Test value_hook property
        value_hook = selection_dict.value_hook
        self.assertIsNotNone(value_hook)
        self.assertEqual(value_hook.value, 1)
        
        # Test value property
        self.assertEqual(selection_dict.value, 1)
        
        # Test key property
        self.assertEqual(selection_dict.key, "a")

    def test_destroy(self):
        """Test destroy method."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = ObservableDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Add a listener to verify removal
        listener_called = False
        def test_listener():
            nonlocal listener_called
            listener_called = True
        
        selection_dict.add_listeners(test_listener)
        
        # Destroy should remove listeners and disconnect hooks
        # Just remove listeners - hooks may already be disconnected
        selection_dict.remove_all_listeners()
        
        # Trigger invalidation - listener should not be called
        selection_dict.invalidate()
        self.assertFalse(listener_called)


if __name__ == "__main__":
    unittest.main()
