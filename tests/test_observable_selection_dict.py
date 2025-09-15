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
            value_hook=test_value,
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
            value_hook=1,
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

    def test_collective_hooks_interface(self):
        """Test CarriesCollectiveHooks interface implementation."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=1,
            logger=logger
        )
        
        # Test get_collective_hook_keys
        collective_keys = selection_dict.get_collective_hook_keys()
        self.assertEqual(collective_keys, {"dict", "key", "value"})
        
        # Test that the interface is properly implemented
        # The connect_multiple_hooks functionality is tested elsewhere
        self.assertTrue(hasattr(selection_dict, 'connect_multiple_hooks'))

    def test_value_properties(self):
        """Test value and key properties."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=1,
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
            value_hook=1,
            logger=logger
        )
        
        # Create external hook
        external_hook = OwnedHook(owner=self.mock_owner, value="b", logger=logger)
        
        # Connect to key hook
        selection_dict.connect(external_hook, "key", InitialSyncMode.USE_TARGET_VALUE)  # type: ignore
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
            value_hook=1,
            logger=logger
        )
        
        # Test valid values
        success, msg = selection_dict.is_valid_hook_value("dict", {"a": 1, "b": 2})
        self.assertTrue(success)
        
        success, msg = selection_dict.is_valid_hook_value("key", "a")
        self.assertTrue(success)
        
        success, msg = selection_dict.is_valid_hook_value("value", 1)
        self.assertTrue(success)
        
        # Test invalid values - need to test with both key and dict context
        success, msg = selection_dict.is_valid_hook_values({"key": "nonexistent", "dict": {"a": 1, "b": 2}})
        self.assertFalse(success)
        self.assertIn("not in dictionary", msg)

    def test_invalidation(self):
        """Test invalidation behavior."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=1,
            logger=logger
        )
        
        # Test invalidation
        success, msg = selection_dict.invalidate_hooks()
        self.assertTrue(success)
        self.assertEqual(msg, "Successfully invalidated")

    def test_dict_key_change_propagation(self):
        """Test that changing dict or key updates the value."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=1,
            logger=logger
        )
        
        # Change key
        selection_dict.key = "b"
        self.assertEqual(selection_dict.value, 2)
        
        # Change dict to include the current key
        selection_dict.dict_hook.submit_single_value({"b": 200, "x": 100, "y": 300})
        # Now we can set the key to "x" since "b" is still valid
        selection_dict.key = "x"
        self.assertEqual(selection_dict.value, 100)

    def test_value_change_propagation(self):
        """Test that changing value updates the dict."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=1,
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
            value_hook=test_value,
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
        
        # Set key to None
        selection_dict.key = None
        self.assertIsNone(selection_dict.value)
        
        # Set key to valid value (should fail because value is None)
        with self.assertRaises(ValueError):
            selection_dict.key = "a"
        
        # Set key back to None
        selection_dict.key = None
        self.assertIsNone(selection_dict.value)

    def test_hook_interface_optional(self):
        """Test CarriesHooks interface with optional values."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=1,
            logger=logger
        )
        
        # Test get_hook_keys
        keys = selection_dict.get_hook_keys()
        self.assertEqual(keys, {"dict", "key", "value"})
        
        # Test get_hook_value_as_reference - can't set key to None when value is not None
        with self.assertRaises(ValueError):
            selection_dict.key = None

    def test_verification_method_optional(self):
        """Test verification method with optional values."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=1,
            logger=logger
        )
        
        # Test valid values
        success, msg = selection_dict.is_valid_hook_value("key", "a")
        self.assertTrue(success)
        
        success, msg = selection_dict.is_valid_hook_value("value", 1)
        self.assertTrue(success)
        
        # Test None key with current value 1 (should be invalid)
        success, msg = selection_dict.is_valid_hook_value("key", None)
        self.assertFalse(success)
        
        # Test None key with non-None value (should be invalid)
        with self.assertRaises(ValueError):
            selection_dict.key = None
        # Don't set value directly as it will raise ValueError, just test verification
        success, msg = selection_dict.is_valid_hook_values({"key": None, "value": 999})
        self.assertFalse(success)
        self.assertIn("Key is None but value is not None", msg)

    def test_optional_value_properties(self):
        """Test value and key properties with optional types."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=1,
            logger=logger
        )
        
        # Test initial values
        self.assertEqual(selection_dict.value, 1)
        self.assertEqual(selection_dict.key, "a")
        
        # Test setting to None (should fail because key is not None)
        with self.assertRaises(ValueError):
            selection_dict.value = None
        
        # Test setting key to None (should fail because value is not None)
        with self.assertRaises(ValueError):
            selection_dict.key = None

    def test_error_handling_optional(self):
        """Test error handling for invalid optional combinations."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=1,
            logger=logger
        )
        
        # Test setting value when key is None (should raise error)
        with self.assertRaises(ValueError):
            selection_dict.key = None
        # Setting value to 999 should be valid since key "a" exists in dict
        selection_dict.value = 999
        self.assertEqual(selection_dict.value, 999)

    def test_collective_hooks_optional(self):
        """Test CarriesCollectiveHooks interface with optional values."""
        test_dict = {"a": 1, "b": 2}
        selection_dict = ObservableOptionalSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=1,
            logger=logger
        )
        
        # Test get_collective_hook_keys
        collective_keys = selection_dict.get_collective_hook_keys()
        self.assertEqual(collective_keys, {"dict", "key", "value"})
        
        # Test that the interface is properly implemented
        # The connect_multiple_hooks functionality is tested elsewhere
        self.assertTrue(hasattr(selection_dict, 'connect_multiple_hooks'))


if __name__ == "__main__":
    unittest.main()
