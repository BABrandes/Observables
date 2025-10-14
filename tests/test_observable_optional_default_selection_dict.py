import unittest
from typing import Any, Literal, Mapping, Optional
from logging import Logger
from observables import ObservableOptionalDefaultSelectionDict
from observables.core import BaseObservable
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


class TestObservableOptionalDefaultSelectionDict(unittest.TestCase):
    """Test ObservableOptionalDefaultSelectionDict functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_owner = MockObservable("test_owner")

    def test_basic_creation(self):
        """Test basic ObservableOptionalDefaultSelectionDict creation."""
        # Create test data
        test_dict = {"a": 1, "b": 2, "c": 3}
        test_key = "b"
        default_value = 999
        
        # Create default selection dict
        selection_dict = ObservableOptionalDefaultSelectionDict(
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
        """Test creation with None key returns None value."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        # Create with None key
        selection_dict = ObservableOptionalDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Verify creation
        self.assertIsNotNone(selection_dict)
        self.assertEqual(selection_dict.value, None)
        self.assertIsNone(selection_dict.key)

    def test_creation_with_missing_key(self):
        """Test creation with key not in dict creates default entry."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        # Create with key not in dict
        selection_dict = ObservableOptionalDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="z",  # Not in dict
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Verify creation - should have added default entry
        self.assertIsNotNone(selection_dict)
        self.assertEqual(selection_dict.value, default_value)
        self.assertEqual(selection_dict.key, "z")
        self.assertEqual(selection_dict.dict_hook.value["z"], default_value)

    def test_none_key_behavior(self):
        """Test that None key gives None value."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = ObservableOptionalDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Initially key "a" should give value 1
        self.assertEqual(selection_dict.value, 1)
        self.assertEqual(selection_dict.key, "a")
        
        # Set key to None - should give None value
        selection_dict.key = None
        self.assertEqual(selection_dict.value, None)
        self.assertIsNone(selection_dict.key)
        
        # Set key back to "b" - should use dict value
        selection_dict.key = "b"
        self.assertEqual(selection_dict.value, 2)
        self.assertEqual(selection_dict.key, "b")

    def test_missing_key_creates_default_entry(self):
        """Test that missing key creates default entry."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = ObservableOptionalDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Set key to one not in dict - should create default entry
        selection_dict.key = "z"
        self.assertEqual(selection_dict.value, default_value)
        self.assertEqual(selection_dict.key, "z")
        self.assertEqual(selection_dict.dict_hook.value["z"], default_value)

    def test_value_setting_with_none_key(self):
        """Test setting value when key is None."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = ObservableOptionalDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Should be able to set value to None when key is None
        selection_dict.value = None
        self.assertEqual(selection_dict.value, None)
        
        # Should not be able to set value to non-None when key is None
        with self.assertRaises(ValueError) as context:
            selection_dict.value = 123
        self.assertIn("not None when key is None", str(context.exception))

    def test_value_setting_with_valid_key(self):
        """Test setting value when key is valid."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        
        selection_dict = ObservableOptionalDefaultSelectionDict(
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

    def test_verification_method(self):
        """Test the verification method."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = ObservableOptionalDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        # Test valid values with key
        success, msg = selection_dict.validate_values({"dict": {"a": 1, "b": 2}, "key": "a", "value": 1})
        self.assertTrue(success)
        
        # Test valid values with None key and None value
        success, msg = selection_dict.validate_values({"dict": {"a": 1, "b": 2}, "key": None, "value": None})
        self.assertTrue(success)
        
        # Test invalid - None key with non-None value
        success, msg = selection_dict.validate_values({"dict": {"a": 1, "b": 2}, "key": None, "value": 123})
        self.assertFalse(success)
        self.assertIn("not None when key is None", msg)
        
        # Test invalid - key not in dict
        success, msg = selection_dict.validate_values({"dict": {"a": 1, "b": 2}, "key": "z", "value": 1})
        self.assertFalse(success)
        self.assertIn("not in dictionary", msg)
        
        # Test invalid - value doesn't match dictionary value
        success, msg = selection_dict.validate_values({"dict": {"a": 1, "b": 2}, "key": "a", "value": 999})
        self.assertFalse(success)
        self.assertIn("not equal to value in dictionary", msg)

    def test_set_dict_and_key(self):
        """Test set_dict_and_key method."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = ObservableOptionalDefaultSelectionDict(
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
        self.assertEqual(selection_dict.value, None)

        # Set dict and missing key - should create default entry
        selection_dict.set_dict_and_key(new_dict, "z")
        self.assertEqual(selection_dict.key, "z")
        self.assertEqual(selection_dict.value, default_value)
        self.assertEqual(selection_dict.dict_hook.value["z"], default_value)

    def test_edge_cases(self):
        """Test edge cases."""
        # Test with empty dict and None key
        empty_dict: dict[str, int] = {}
        default_value = 999
        selection_dict = ObservableOptionalDefaultSelectionDict(
            dict_hook=empty_dict,
            key_hook=None,
            value_hook=None,
            default_value=default_value,
            logger=logger
        )
        
        self.assertEqual(selection_dict.value, None)
        self.assertIsNone(selection_dict.key)
        
        # Test with default value that equals a dict value
        test_dict = {"a": 999, "b": 2}
        selection_dict2 = ObservableOptionalDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook=None,
            value_hook=None,
            default_value=999,  # Same as dict["a"]
            logger=logger
        )
        
        self.assertEqual(selection_dict2.value, None)  # None because key is None
        self.assertIsNone(selection_dict2.key)
        
        # Set key to "a" - should work even though default value equals dict["a"]
        selection_dict2.key = "a"
        self.assertEqual(selection_dict2.value, 999)
        self.assertEqual(selection_dict2.key, "a")

    def test_properties(self):
        """Test property access."""
        test_dict = {"a": 1, "b": 2}
        default_value = 999
        selection_dict = ObservableOptionalDefaultSelectionDict(
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

    def test_callable_default_value(self):
        """Test using a callable as default value."""
        test_dict = {"a": 1, "b": 2}
        
        # Create a callable that returns key-specific defaults
        def default_factory(key: str) -> int:
            return len(key) * 100  # Different value based on key length
        
        selection_dict = ObservableOptionalDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="a",
            value_hook=None,
            default_value=default_factory,
            logger=logger
        )
        
        # Initial key "a" should use dict value
        self.assertEqual(selection_dict.value, 1)
        
        # Set key to None - should give None value
        selection_dict.key = None
        self.assertEqual(selection_dict.value, None)
        
        # Set key to "xyz" (not in dict) - should use callable to create default
        selection_dict.key = "xyz"
        self.assertEqual(selection_dict.value, 300)  # len("xyz") * 100 = 300
        self.assertEqual(selection_dict.dict_hook.value["xyz"], 300)
        
        # Set key to "hello" (not in dict) - should use callable with different result
        selection_dict.key = "hello"
        self.assertEqual(selection_dict.value, 500)  # len("hello") * 100 = 500
        self.assertEqual(selection_dict.dict_hook.value["hello"], 500)

    def test_callable_default_value_in_initialization(self):
        """Test callable default value during initialization."""
        test_dict = {"a": 1}
        
        def default_factory(key: str) -> int:
            return ord(key[0]) if key else 0  # Use ASCII value of first char
        
        # Create with key not in dict
        selection_dict = ObservableOptionalDefaultSelectionDict(
            dict_hook=test_dict,
            key_hook="z",
            value_hook=None,
            default_value=default_factory,
            logger=logger
        )
        
        # Should have created default entry using callable
        self.assertEqual(selection_dict.value, ord("z"))  # 122
        self.assertEqual(selection_dict.dict_hook.value["z"], ord("z"))


if __name__ == "__main__":
    unittest.main()

