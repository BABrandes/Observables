import unittest
from typing import Any, Mapping, Optional
from observables import ObservableSync, InitialSyncMode, ObservableSingleValue
from observables._hooks.owned_hook import OwnedHook
from observables._utils.base_carries_hooks import BaseCarriesHooks
# Set up logging for tests
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MockObservable(BaseCarriesHooks[str, int, "MockObservable"]):
    """Mock observable that implements the required interface."""
    
    def __init__(self, name: str):
        self.name = name
        self._hooks: dict[str, OwnedHook[int]] = {}
        
        # Initialize BaseCarriesHooks
        super().__init__()
    
    def _get_hook(self, key: str) -> OwnedHook[int]:
        return self._hooks[key]
    
    def _get_value_reference_of_hook(self, key: str) -> int:
        return self._hooks[key].value
    
    def _get_hook_keys(self) -> set[str]:
        return set(self._hooks.keys())
    
    def _get_hook_key(self, hook_or_nexus: Any) -> str:
        for key, hook in self._hooks.items():
            if hook is hook_or_nexus:
                return key
        raise ValueError(f"Hook {hook_or_nexus} not found")
    
    def add_hook(self, key: str, hook: OwnedHook[int]) -> None:
        """Add a hook to the mock observable."""
        self._hooks[key] = hook


class TestObservableSync(unittest.TestCase):
    """Test ObservableSync functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_owner = MockObservable("test_owner")

    def test_basic_creation_with_values(self):
        """Test basic ObservableSync creation with initial values."""
        def sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            """Simple sync callback that ensures all values are positive."""
            result: dict[str, int] = {}
            for key, value in submitted_values.items():
                result[key] = abs(value) if value is not None else 0 # type: ignore
            return result

        sync = ObservableSync[str, str, int, str](
            sync_values_initially_valid={"a": 5, "b": -3, "c": 0},
            sync_values_callback=sync_callback,
            logger=logger
        )

        # Check that sync hooks were created correctly
        # Note: The sync callback is NOT applied during initialization, only during validation
        self.assertEqual(sync.get_sync_hook("a").value, 5)  # Original value
        self.assertEqual(sync.get_sync_hook("b").value, -3)  # Original value
        self.assertEqual(sync.get_sync_hook("c").value, 0)   # Original value

        # Check hook keys
        self.assertEqual(sync.get_hook_keys(), {"a", "b", "c"})

    def test_basic_creation_with_hooks(self):
        """Test basic ObservableSync creation with initial values (no longer supports hooks)."""
        def sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            """Sync callback that doubles all values."""
            return {key: value * 2 for key, value in submitted_values.items()}

        sync = ObservableSync[str, str, int, str](
            sync_values_initially_valid={"a": 10, "b": 20},
            sync_values_callback=sync_callback,
            logger=logger
        )

        # Check that sync hooks were created and values are NOT doubled during initialization
        # Note: The sync callback is NOT applied during initialization, only during validation
        self.assertEqual(sync.get_sync_hook("a").value, 10)  # Original value
        self.assertEqual(sync.get_sync_hook("b").value, 20)  # Original value

    def test_sync_callback_validation(self):
        """Test that sync callback must return all required keys."""
        def invalid_sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            """Invalid callback that doesn't return all keys."""
            return {"a": 5}  # Missing "b" and "c"

        with self.assertRaises(ValueError) as context:
            ObservableSync[str, str, int, str](
                sync_values_initially_valid={"a": 5, "b": 3, "c": 1},
                sync_values_callback=invalid_sync_callback,
                logger=logger
            )
        
        self.assertIn("Sync callback validation failed", str(context.exception))

    def test_output_callback_basic(self):
        """Test basic output callback functionality."""
        def sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            """Simple sync callback."""
            return submitted_values

        def output_callback(values: Mapping[str, int]) -> Mapping[str, str]:
            """Output callback that creates string representations."""
            return {
                "sum_str": f"Sum: {sum(values.values())}",
                "count_str": f"Count: {len(values)}"
            }

        sync = ObservableSync[str, str, int, str](
            sync_values_initially_valid={"a": 5, "b": 3},
            sync_values_callback=sync_callback,
            output_values_callback=output_callback,
            logger=logger
        )

        # Check that output hooks were created
        self.assertEqual(sync.get_output_hook("sum_str").value, "Sum: 8")
        self.assertEqual(sync.get_output_hook("count_str").value, "Count: 2")

        # Check all hook keys include both sync and output
        self.assertEqual(sync.get_hook_keys(), {"a", "b", "sum_str", "count_str"})

    def test_output_callback_validation(self):
        """Test that output callback must return all required keys."""
        def sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            return submitted_values

        def invalid_output_callback(values: Mapping[str, int]) -> Mapping[str, str]:
            """Invalid callback that raises an error."""
            raise ValueError("Output callback error")

        with self.assertRaises(ValueError) as context:
            ObservableSync[str, str, int, str](
                sync_values_initially_valid={"a": 5, "b": 3},
                sync_values_callback=sync_callback,
                output_values_callback=invalid_output_callback,
                logger=logger
            )
        
        self.assertIn("Output callback validation failed", str(context.exception))

    def test_hook_access_methods(self):
        """Test hook access methods."""
        def sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            return submitted_values

        sync = ObservableSync[str, str, int, str](
            sync_values_initially_valid={"a": 5, "b": 10},
            sync_values_callback=sync_callback,
            logger=logger
        )

        # Test _get_hook
        hook_a = sync.get_hook("a")
        self.assertEqual(hook_a.value, 5)

        # Test _get_value_reference_of_hook
        value_a = sync.get_value_reference_of_hook("a")
        self.assertEqual(value_a, 5)

        # Test _get_hook_key
        hook_key = sync.get_hook_key(hook_a)
        self.assertEqual(hook_key, "a")

        # Test error cases
        with self.assertRaises(ValueError):
            sync.get_hook("nonexistent")

        with self.assertRaises(ValueError):
            sync.get_value_reference_of_hook("nonexistent")

    def test_no_output_callback(self):
        """Test ObservableSync without output callback."""
        def sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            return submitted_values

        sync = ObservableSync[str, str, int, str](
            sync_values_initially_valid={"a": 5, "b": 10},
            sync_values_callback=sync_callback,
            logger=logger
        )

        # Should only have sync hooks, no output hooks
        self.assertEqual(sync.get_hook_keys(), {"a", "b"})
        self.assertEqual(len(sync.get_output_hooks()), 0)

    def test_error_handling_in_callbacks(self):
        """Test error handling when callbacks raise exceptions."""
        def error_sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            """Sync callback that raises an error."""
            raise ValueError("Sync callback error")

        with self.assertRaises(ValueError) as context:
            ObservableSync[str, str, int, str](
                sync_values_initially_valid={"a": 5},
                sync_values_callback=error_sync_callback,
                logger=logger
            )
        
        self.assertIn("Sync callback validation failed", str(context.exception))

    def test_edge_cases(self):
        """Test edge cases."""
        # Empty sync hooks
        def sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            return submitted_values

        sync = ObservableSync[str, str, int, str](
            sync_values_initially_valid={},
            sync_values_callback=sync_callback,
            logger=logger
        )

        self.assertEqual(sync.get_hook_keys(), set())

        # None values
        def sync_callback_with_none(current_values: Mapping[str, Optional[int]], submitted_values: Mapping[str, Optional[int]]) -> Mapping[str, Optional[int]]:
            return submitted_values

        sync_with_none = ObservableSync[str, str, Optional[int], str](
            sync_values_initially_valid={"a": None, "b": 5},
            sync_values_callback=sync_callback_with_none,
            logger=logger
        )

        self.assertIsNone(sync_with_none.get_sync_hook("a").value)
        self.assertEqual(sync_with_none.get_sync_hook("b").value, 5)

    def test_complex_output_transformation(self):
        """Test complex output transformation with multiple outputs."""
        def sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            return submitted_values

        def output_callback(values: Mapping[str, int]) -> Mapping[str, str]:
            """Complex output callback with multiple outputs."""
            total = sum(values.values())
            count = len(values)
            avg = total / count if count > 0 else 0
            max_val = max(values.values()) if values else 0
            min_val = min(values.values()) if values else 0
            
            return {
                "total": f"Total: {total}",
                "count": f"Count: {count}",
                "average": f"Average: {avg:.2f}",
                "range": f"Range: {min_val}-{max_val}"
            }

        sync = ObservableSync[str, str, int, str](
            sync_values_initially_valid={"a": 10, "b": 20, "c": 30},
            sync_values_callback=sync_callback,
            output_values_callback=output_callback,
            logger=logger
        )

        # Check all output values
        self.assertEqual(sync.get_output_hook("total").value, "Total: 60")
        self.assertEqual(sync.get_output_hook("count").value, "Count: 3")
        self.assertEqual(sync.get_output_hook("average").value, "Average: 20.00")
        self.assertEqual(sync.get_output_hook("range").value, "Range: 10-30")

    def test_listener_notification(self):
        """Test that listeners are notified when values change."""
        def sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            return submitted_values

        sync = ObservableSync[str, str, int, str](
            sync_values_initially_valid={"a": 5},
            sync_values_callback=sync_callback,
            logger=logger
        )

        # Add a listener
        notifications: list[str] = []
        def listener():
            notifications.append("notified")

        sync.add_listeners(listener)

        # Change a value
        sync.get_sync_hook("a").submit_value(10)

        # Check that listener was notified
        self.assertGreater(len(notifications), 0)

    def test_integration_with_observable_single_value(self):
        """Test integration with ObservableSingleValue by connecting after initialization."""
        # Create external observables
        external_a = ObservableSingleValue[int](5, logger=logger)
        external_b = ObservableSingleValue[int](10, logger=logger)

        def sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            """Sync callback that ensures sum is always 20."""
            if not submitted_values:
                return submitted_values  # Handle empty case
            current_sum = sum(submitted_values.values())
            if current_sum != 20:
                # Adjust first value to make sum 20
                first_key = next(iter(submitted_values.keys()))
                return {**submitted_values, first_key: 20 - sum(v for k, v in submitted_values.items() if k != first_key)}
            return submitted_values

        sync = ObservableSync[str, str, int, str](
            sync_values_initially_valid={"a": 5, "b": 10},
            sync_values_callback=sync_callback,
            logger=logger
        )

        # Check initial state
        # Note: The sync callback is NOT applied during initialization, only during validation
        # Values remain as originally provided
        self.assertEqual(sync.get_sync_hook("a").value, 5)  # Original value
        self.assertEqual(sync.get_sync_hook("b").value, 10)  # Original value

        # Now connect to external observables after initialization
        sync.get_sync_hook("a").connect_hook(external_a.hook, InitialSyncMode.USE_CALLER_VALUE)
        sync.get_sync_hook("b").connect_hook(external_b.hook, InitialSyncMode.USE_CALLER_VALUE)

        # Check that external values are updated to match sync values
        self.assertEqual(external_a.value, 5)  # Matches sync value
        self.assertEqual(external_b.value, 10)  # Matches sync value

    def test_combination_validation(self):
        """Test that sync callback is validated with every combination of given values."""
        def valid_sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            """Valid callback that returns all input keys."""
            return {key: value * 2 for key, value in submitted_values.items()}

        # This should work - callback handles all combinations correctly
        sync = ObservableSync[str, str, int, str](
            sync_values_initially_valid={"a": 1, "b": 2, "c": 3},
            sync_values_callback=valid_sync_callback,
            logger=logger
        )

        # Check that values are NOT doubled during initialization
        # Note: The sync callback is NOT applied during initialization, only during validation
        self.assertEqual(sync.get_sync_hook("a").value, 1)  # Original value
        self.assertEqual(sync.get_sync_hook("b").value, 2)  # Original value
        self.assertEqual(sync.get_sync_hook("c").value, 3)  # Original value

    def test_combination_validation_failure(self):
        """Test that sync callback validation fails when callback doesn't handle all combinations."""
        def invalid_sync_callback(current_values: Mapping[str, int], submitted_values: Mapping[str, int]) -> Mapping[str, int]:
            """Invalid callback that only handles certain combinations."""
            if len(submitted_values) == 3:
                # Only handle full combination
                return {key: value * 2 for key, value in submitted_values.items()}
            else:
                # Fail for partial combinations
                raise ValueError("Cannot handle partial combinations")

        # This should fail during validation
        with self.assertRaises(ValueError) as context:
            ObservableSync[str, str, int, str](
                sync_values_initially_valid={"a": 1, "b": 2, "c": 3},
                sync_values_callback=invalid_sync_callback,
                logger=logger
            )
        
        self.assertIn("Sync callback validation failed for combination", str(context.exception))


if __name__ == "__main__":
    unittest.main()