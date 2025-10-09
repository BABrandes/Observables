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
        def sync_callback(submitted_values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
            """Simple sync callback that passes through valid values."""
            # Just return the submitted values as-is
            return (True, dict(submitted_values))

        sync = ObservableSync[str, int](
            sync_values_initially_valid={"a": 5, "b": 3, "c": 0},
            sync_values_callback=sync_callback,
            logger=logger
        )

        # Check that sync hooks were created correctly
        self.assertEqual(sync.get_sync_hook("a").value, 5)  # Original value
        self.assertEqual(sync.get_sync_hook("b").value, 3)  # Original value
        self.assertEqual(sync.get_sync_hook("c").value, 0)   # Original value

        # Check hook keys
        self.assertEqual(sync.get_hook_keys(), {"a", "b", "c"})

    def test_basic_creation_with_hooks(self):
        """Test basic ObservableSync creation with initial values (no longer supports hooks)."""
        def sync_callback(submitted_values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
            """Simple sync callback that passes through values."""
            return (True, dict(submitted_values))

        sync = ObservableSync[str, int](
            sync_values_initially_valid={"a": 10, "b": 20},
            sync_values_callback=sync_callback,
            logger=logger
        )

        # Check that sync hooks were created with initial values
        self.assertEqual(sync.get_sync_hook("a").value, 10)  # Original value
        self.assertEqual(sync.get_sync_hook("b").value, 20)  # Original value

    def test_sync_callback_validation(self):
        """Test that sync callback validation fails when callback returns different values."""
        def invalid_sync_callback(submitted_values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
            """Invalid callback that returns different values that don't match when completed."""
            # This will fail because when we submit just "a", it returns a different value
            # When completed, it becomes {"a": 999, "b": 3, "c": 1} which != initial {"a": 5, "b": 3, "c": 1}
            return (True, {key: 999 for key in submitted_values.keys()})

        with self.assertRaises(ValueError) as context:
            ObservableSync[str, int](
                sync_values_initially_valid={"a": 5, "b": 3, "c": 1},
                sync_values_callback=invalid_sync_callback,
                logger=logger
            )
        
        self.assertIn("Sync callback validation failed", str(context.exception))


    def test_hook_access_methods(self):
        """Test hook access methods."""
        def sync_callback(submitted_values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
            return (True, dict(submitted_values))

        sync = ObservableSync[str, int](
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

    def test_basic_sync(self):
        """Test basic ObservableSync with simple pass-through callback."""
        def sync_callback(submitted_values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
            return (True, dict(submitted_values))

        sync = ObservableSync[str, int](
            sync_values_initially_valid={"a": 5, "b": 10},
            sync_values_callback=sync_callback,
            logger=logger
        )

        # Should have sync hooks
        self.assertEqual(sync.get_hook_keys(), {"a", "b"})
        self.assertEqual(len(sync.get_sync_hooks()), 2)

    def test_error_handling_in_callbacks(self):
        """Test error handling when callbacks raise exceptions."""
        def error_sync_callback(submitted_values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
            """Sync callback that raises an error."""
            raise ValueError("Sync callback error")

        with self.assertRaises(ValueError) as context:
            ObservableSync[str, int](
                sync_values_initially_valid={"a": 5},
                sync_values_callback=error_sync_callback,
                logger=logger
            )
        
        self.assertIn("Sync callback validation failed", str(context.exception))

    def test_edge_cases(self):
        """Test edge cases."""
        # Empty sync hooks
        def sync_callback(submitted_values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
            return (True, dict(submitted_values))

        sync = ObservableSync[str, int](
            sync_values_initially_valid={},
            sync_values_callback=sync_callback,
            logger=logger
        )

        self.assertEqual(sync.get_hook_keys(), set())

        # None values
        def sync_callback_with_none(submitted_values: Mapping[str, Optional[int]]) -> tuple[bool, dict[str, Optional[int]]]:
            return (True, dict(submitted_values))

        sync_with_none = ObservableSync[str, Optional[int]](
            sync_values_initially_valid={"a": None, "b": 5},
            sync_values_callback=sync_callback_with_none,
            logger=logger
        )

        self.assertIsNone(sync_with_none.get_sync_hook("a").value)
        self.assertEqual(sync_with_none.get_sync_hook("b").value, 5)


    def test_listener_notification(self):
        """Test that listeners are notified when values change."""
        def sync_callback(submitted_values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
            return (True, dict(submitted_values))

        sync = ObservableSync[str, int](
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

        def sync_callback(submitted_values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
            """Simple sync callback that passes through values."""
            return (True, dict(submitted_values))

        sync = ObservableSync[str, int](
            sync_values_initially_valid={"a": 5, "b": 10},
            sync_values_callback=sync_callback,
            logger=logger
        )

        # Check initial state
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
        def valid_sync_callback(submitted_values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
            """Valid callback that passes through submitted values."""
            return (True, dict(submitted_values))

        # This should work - callback handles all combinations correctly
        sync = ObservableSync[str, int](
            sync_values_initially_valid={"a": 1, "b": 2, "c": 3},
            sync_values_callback=valid_sync_callback,
            logger=logger
        )

        # Check that values are preserved during initialization
        self.assertEqual(sync.get_sync_hook("a").value, 1)  # Original value
        self.assertEqual(sync.get_sync_hook("b").value, 2)  # Original value
        self.assertEqual(sync.get_sync_hook("c").value, 3)  # Original value

    def test_combination_validation_failure(self):
        """Test that sync callback validation fails when callback doesn't handle all combinations."""
        def invalid_sync_callback(submitted_values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
            """Invalid callback that only handles certain combinations."""
            if len(submitted_values) == 3:
                # Only handle full combination
                return (True, {key: value * 2 for key, value in submitted_values.items()})
            else:
                # Fail for partial combinations
                raise ValueError("Cannot handle partial combinations")

        # This should fail during validation
        with self.assertRaises(ValueError) as context:
            ObservableSync[str, int](
                sync_values_initially_valid={"a": 1, "b": 2, "c": 3},
                sync_values_callback=invalid_sync_callback,
                logger=logger
            )
        
        self.assertIn("Sync callback validation failed for combination", str(context.exception))

    def test_square_root_constraint(self):
        """Test square root constraint - showcases the power of ObservableSync.
        
        This test demonstrates a mathematical constraint where:
        - square_value = root_value²
        - domain selects between positive and negative root solutions
        
        Any of the three values can be changed, and the others sync automatically.
        """
        def sync_callback(submitted_values: Mapping[str, float | str]) -> tuple[bool, dict[str, float | str]]:
            """Sync callback that maintains the constraint: square_value = root_value²."""
            result: dict[str, float | str] = {}
            
            # Extract submitted values
            root = submitted_values.get("root_value")
            square = submitted_values.get("square_value")
            domain = submitted_values.get("domain")
            
            # When all three values are present (validation mode), check consistency
            if all(k in submitted_values for k in ["root_value", "square_value", "domain"]):
                # Validate that the values are consistent
                if not isinstance(root, (int, float)) or not isinstance(square, (int, float)):
                    return (False, {})
                
                # Check: square = root²
                if abs(square - root * root) > 1e-10:
                    return (False, {})
                
                # Check: domain matches sign of root
                expected_domain = "positive" if root >= 0 else "negative"
                if domain != expected_domain:
                    return (False, {})
                
                # All consistent, no changes needed
                return (True, {})
            
            # Case 1: root_value was submitted (primary value)
            if "root_value" in submitted_values and isinstance(root, (int, float)):
                # Calculate square from root
                result["square_value"] = root * root
                # Update domain to match the sign of the root
                result["domain"] = "positive" if root >= 0 else "negative"
            
            # Case 2: square_value and domain were submitted together
            elif "square_value" in submitted_values and "domain" in submitted_values:
                if not isinstance(square, (int, float)):
                    return (False, {})
                if square < 0:
                    return (False, {})  # Invalid: can't take square root of negative number
                
                sqrt_val = square ** 0.5
                # Use domain to determine the sign of the root
                result["root_value"] = -sqrt_val if domain == "negative" else sqrt_val
            
            # Case 3: Only square_value (use positive domain by default)
            elif "square_value" in submitted_values:
                if not isinstance(square, (int, float)):
                    return (False, {})
                if square < 0:
                    return (False, {})
                result["root_value"] = square ** 0.5
            
            # Case 4: Only domain was submitted
            elif "domain" in submitted_values:
                # Can't change domain without knowing current root
                # Return no changes; this will be checked during validation
                pass
            
            return (True, result)

        # Create ObservableSync with initial valid state
        # Initial state: √4 = 2 (positive domain)
        sync = ObservableSync[str, float | str](
            sync_values_initially_valid={
                "square_value": 4.0,
                "root_value": 2.0,
                "domain": "positive"
            },
            sync_values_callback=sync_callback,
            logger=logger
        )

        # Verify initial state
        self.assertEqual(sync.get_sync_hook("square_value").value, 4.0)
        self.assertEqual(sync.get_sync_hook("root_value").value, 2.0)
        self.assertEqual(sync.get_sync_hook("domain").value, "positive")

        # Test 1: Change root_value → square_value should update
        sync.get_sync_hook("root_value").submit_value(3.0)
        self.assertEqual(sync.get_sync_hook("square_value").value, 9.0)  # 3² = 9
        self.assertEqual(sync.get_sync_hook("root_value").value, 3.0)
        self.assertEqual(sync.get_sync_hook("domain").value, "positive")  # Still positive

        # Test 2: Change root_value to negative → domain should update
        sync.get_sync_hook("root_value").submit_value(-4.0)
        self.assertEqual(sync.get_sync_hook("square_value").value, 16.0)  # (-4)² = 16
        self.assertEqual(sync.get_sync_hook("root_value").value, -4.0)
        self.assertEqual(sync.get_sync_hook("domain").value, "negative")  # Now negative

        # Test 3: Change to a positive root → square_value and domain should update
        sync.get_sync_hook("root_value").submit_value(5.0)
        self.assertEqual(sync.get_sync_hook("square_value").value, 25.0)  # 5² = 25
        self.assertEqual(sync.get_sync_hook("root_value").value, 5.0)
        self.assertEqual(sync.get_sync_hook("domain").value, "positive")  # Positive root

        # Test 4: Change square_value alone → root_value should be positive (default)
        sync.get_sync_hook("square_value").submit_value(36.0)
        self.assertEqual(sync.get_sync_hook("square_value").value, 36.0)
        self.assertEqual(sync.get_sync_hook("root_value").value, 6.0)  # √36 = 6 (positive default)
        self.assertEqual(sync.get_sync_hook("domain").value, "positive")

        # Test 5: Change back to negative root → demonstrates both solutions
        sync.get_sync_hook("root_value").submit_value(-6.0)
        self.assertEqual(sync.get_sync_hook("square_value").value, 36.0)  # (-6)² = 36
        self.assertEqual(sync.get_sync_hook("root_value").value, -6.0)
        self.assertEqual(sync.get_sync_hook("domain").value, "negative")  # Negative root

        # Test 6: Edge case - square root of 0
        sync.get_sync_hook("root_value").submit_value(0.0)
        self.assertEqual(sync.get_sync_hook("square_value").value, 0.0)
        self.assertEqual(sync.get_sync_hook("root_value").value, 0.0)
        self.assertEqual(sync.get_sync_hook("domain").value, "positive")  # 0 is considered positive
        
        # Test 7: Large values
        sync.get_sync_hook("root_value").submit_value(-10.0)
        self.assertEqual(sync.get_sync_hook("square_value").value, 100.0)
        self.assertEqual(sync.get_sync_hook("root_value").value, -10.0)
        self.assertEqual(sync.get_sync_hook("domain").value, "negative")

        # Test 8: Submit multiple values at once - square_value and domain together
        # This demonstrates the power of coordinated updates!
        sync.submit_values({
            "square_value": 49.0,
            "domain": "negative"
        })
        self.assertEqual(sync.get_sync_hook("square_value").value, 49.0)
        self.assertEqual(sync.get_sync_hook("root_value").value, -7.0)  # √49 = -7 (negative domain)
        self.assertEqual(sync.get_sync_hook("domain").value, "negative")

        # Test 9: Submit square_value and domain (positive) together
        sync.submit_values({
            "square_value": 64.0,
            "domain": "positive"
        })
        self.assertEqual(sync.get_sync_hook("square_value").value, 64.0)
        self.assertEqual(sync.get_sync_hook("root_value").value, 8.0)  # √64 = 8 (positive domain)
        self.assertEqual(sync.get_sync_hook("domain").value, "positive")

        # Test 10: Submit all three values at once (they must be consistent)
        sync.submit_values({
            "square_value": 81.0,
            "root_value": 9.0,
            "domain": "positive"
        })
        self.assertEqual(sync.get_sync_hook("square_value").value, 81.0)
        self.assertEqual(sync.get_sync_hook("root_value").value, 9.0)
        self.assertEqual(sync.get_sync_hook("domain").value, "positive")

        # Test 11: Submit all three values with negative root
        sync.submit_values({
            "square_value": 121.0,
            "root_value": -11.0,
            "domain": "negative"
        })
        self.assertEqual(sync.get_sync_hook("square_value").value, 121.0)
        self.assertEqual(sync.get_sync_hook("root_value").value, -11.0)
        self.assertEqual(sync.get_sync_hook("domain").value, "negative")

        # Test 12: Try to submit inconsistent values - should fail
        with self.assertRaises(ValueError):
            sync.submit_values({
                "square_value": 100.0,
                "root_value": 5.0,  # Inconsistent! 5² ≠ 100
                "domain": "positive"
            })


if __name__ == "__main__":
    unittest.main()