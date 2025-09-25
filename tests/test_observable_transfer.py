import unittest
import threading
import time
from typing import Any, Literal, Mapping, Optional, cast
from logging import Logger
from observables import ObservableTransfer, BaseObservable, InitialSyncMode, ObservableSingleValue, HookLike
from observables._hooks.owned_hook import OwnedHook
# Set up logging for tests
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MockObservable(BaseObservable[Any, Any, Any, Any]):
    """Mock observable for testing purposes that can handle arbitrary hooks."""
    
    def __init__(self, name: str):
        self._internal_construct_from_values({"value": name})
        # Store hooks that are created with this owner
        self._registered_hooks: dict[Any, Any] = {}
    
    def _internal_construct_from_values(
        self,
        initial_values: Mapping[Any, Any],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """Construct a MockObservable instance."""
        super().__init__(initial_component_values_or_hooks=initial_values)
    
    def _act_on_invalidation(self, keys: set[Any]) -> None:
        """Act on invalidation - required by BaseObservable."""
        pass
    
    def get_hook_key(self, hook_or_nexus: Any) -> Any:
        """Get the key for a hook - return a dummy key for any hook."""
        # For testing purposes, return a dummy key
        return "dummy_key"
    
    def is_valid_hook_value(self, hook_key: Any, value: Any) -> tuple[bool, str]:
        """Check if the value is valid - always return True for testing."""
        return True, "Mock validation always passes"


class TestObservableTransfer(unittest.TestCase):
    """Test ObservableTransfer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_owner = MockObservable("test_owner")

    def test_basic_creation(self):
        """Test basic ObservableTransfer creation."""
        # Create input hooks
        x_hook = OwnedHook(owner=self.mock_owner, initial_value=5, logger=logger)
        y_hook = OwnedHook(owner=self.mock_owner, initial_value=3, logger=logger)
        
        # Create output hooks
        sum_hook = OwnedHook(owner=self.mock_owner, initial_value=0, logger=logger)
        product_hook = OwnedHook(owner=self.mock_owner, initial_value=0, logger=logger)
        
        # Create transfer
        transfer = ObservableTransfer(
            input_trigger_hooks={"x": x_hook, "y": y_hook},
            output_trigger_hooks={"sum": sum_hook, "product": product_hook},
            forward_callable=lambda inputs: {
                "sum": inputs["x"] + inputs["y"],
                "product": inputs["x"] * inputs["y"]
            },
            logger=logger
        )
        
        # Verify creation
        self.assertIsNotNone(transfer)
        self.assertEqual(len(transfer.get_hook_keys()), 4)  # 2 inputs + 2 outputs
        
        # The transfer should have its own internal hooks, not the external ones
        # This is correct architecture - the transfer manages its own hooks
        transfer_hooks = transfer.get_hook_dict().values()
        self.assertEqual(len(transfer_hooks), 4)
        
        # Verify we can access the hooks by key
        x_internal_hook = transfer.get_hook("x")
        y_internal_hook = transfer.get_hook("y")
        sum_internal_hook = transfer.get_hook("sum")
        product_internal_hook = transfer.get_hook("product")
        
        # These should be the transfer's internal hooks, not the external ones
        self.assertNotEqual(x_internal_hook, x_hook)  # Different objects
        self.assertNotEqual(y_internal_hook, y_hook)  # Different objects
        self.assertNotEqual(sum_internal_hook, sum_hook)  # Different objects
        self.assertNotEqual(product_internal_hook, product_hook)  # Different objects
        
        # But the values should be synchronized
        self.assertEqual(x_internal_hook.value, x_hook.value)
        self.assertEqual(y_internal_hook.value, y_hook.value)

    def test_hook_access(self):
        """Test hook access methods."""
        x_hook = OwnedHook(owner=self.mock_owner, initial_value=5, logger=logger)
        y_hook = OwnedHook(owner=self.mock_owner, initial_value=3, logger=logger)
        sum_hook = OwnedHook(owner=self.mock_owner, initial_value=0, logger=logger)
        
        transfer = ObservableTransfer(
            input_trigger_hooks={"x": x_hook, "y": y_hook},
            output_trigger_hooks={"sum": sum_hook},
            forward_callable=lambda inputs: {"sum": inputs["x"] + inputs["y"]},
            logger=logger
        )
        
        # Test get_hook - should return transfer's internal hooks, not external ones
        x_internal_hook = transfer.get_hook("x")
        y_internal_hook = transfer.get_hook("y")
        sum_internal_hook = transfer.get_hook("sum")
        
        # These should be different objects (internal vs external hooks)
        self.assertNotEqual(x_internal_hook, x_hook)
        self.assertNotEqual(y_internal_hook, y_hook)
        self.assertNotEqual(sum_internal_hook, sum_hook)
        
        # But values should be synchronized
        self.assertEqual(x_internal_hook.value, x_hook.value)
        self.assertEqual(y_internal_hook.value, y_hook.value)
        self.assertEqual(sum_internal_hook.value, sum_hook.value)
        
        # Test that we can get all the hooks we expect
        self.assertIsNotNone(x_internal_hook)
        self.assertIsNotNone(y_internal_hook)
        self.assertIsNotNone(sum_internal_hook)
        
        # Test invalid key
        with self.assertRaises(ValueError):
            transfer.get_hook("invalid")

    def test_forward_transformation_single_output(self):
        """Test forward transformation with single output."""
        # Track transformation calls
        transform_called: list[bool] = []
        
        def forward_transform(inputs: Mapping[Literal["x", "y"], Any]) -> Mapping[Literal["sum"], Any]:
            transform_called.append(True)
            return {"sum": inputs["x"] + inputs["y"]}
        
        # Create observables for easier testing
        x_obs = ObservableSingleValue(5, logger=logger)
        y_obs = ObservableSingleValue(3, logger=logger)
        sum_obs = ObservableSingleValue(0, logger=logger)
        
        ObservableTransfer[Literal["x", "y"], Literal["sum"], int, int](
            input_trigger_hooks={"x": x_obs.hook, "y": y_obs.hook},
            output_trigger_hooks={"sum": sum_obs.hook},
            forward_callable=forward_transform,
            logger=logger
        )
        
        # Initially, sum should be 0
        self.assertEqual(sum_obs.value, 0)
        
        # Trigger transformation by changing input value
        transform_called.clear()
        x_obs.value = 10  # This should trigger the transfer
        
        # Should have triggered transformation
        self.assertTrue(transform_called)
        self.assertEqual(sum_obs.value, 13)  # 10 + 3

    def test_forward_transformation_multiple_outputs(self):
        """Test forward transformation with multiple outputs."""
        # Track transformation calls
        transform_called: list[bool] = []
        
        def forward_transform(inputs: Mapping[Literal["x", "y"], Any]) -> Mapping[Literal["sum", "product", "difference"], Any]:
            transform_called.append(True)
            return {
                "sum": inputs["x"] + inputs["y"],
                "product": inputs["x"] * inputs["y"],
                "difference": inputs["x"] - inputs["y"]
            }
        
        # Create observables for easier testing
        x_obs = ObservableSingleValue(10, logger=logger)
        y_obs = ObservableSingleValue(4, logger=logger)
        sum_obs = ObservableSingleValue(0, logger=logger)
        product_obs = ObservableSingleValue(0, logger=logger)
        diff_obs = ObservableSingleValue(0, logger=logger)
        
        ObservableTransfer[Literal["x", "y"], Literal["sum"]|Literal["product"]|Literal["difference"], int, int](
            input_trigger_hooks={"x": x_obs.hook, "y": y_obs.hook},
            output_trigger_hooks={"sum": sum_obs.hook, "product": product_obs.hook, "difference": diff_obs.hook},
            forward_callable=forward_transform,
            logger=logger
        )
        
        # Initially, outputs should be 0
        self.assertEqual(sum_obs.value, 0)
        self.assertEqual(product_obs.value, 0)
        self.assertEqual(diff_obs.value, 0)
        
        # Trigger transformation by changing input
        transform_called.clear()
        y_obs.value = 5  # Change from 4 to 5
        
        # Should have triggered transformation and updated all outputs
        self.assertTrue(transform_called)
        self.assertEqual(sum_obs.value, 15)    # 10 + 5
        self.assertEqual(product_obs.value, 50)  # 10 * 5
        self.assertEqual(diff_obs.value, 5)     # 10 - 5

    def test_reverse_transformation(self):
        """Test reverse transformation (outputs → inputs)."""
        # Track transformation calls
        forward_called: list[bool] = []
        reverse_called: list[bool] = []
        
        def forward_transform(inputs: Mapping[Literal["x"], Any]) -> Mapping[Literal["result"], Any]:
            forward_called.append(True)
            return {"result": inputs["x"] * 2}
        
        def reverse_transform(outputs: Mapping[Literal["result"], Any]) -> Mapping[Literal["x"], Any]:
            reverse_called.append(True)
            return {"x": outputs["result"] // 2}
        
        # Create observables
        x_obs = ObservableSingleValue(5, logger=logger)
        result_obs = ObservableSingleValue(0, logger=logger)
        
        ObservableTransfer[Literal["x"], Literal["result"], int, int](
            input_trigger_hooks={"x": x_obs.hook},
            output_trigger_hooks={"result": result_obs.hook},
            forward_callable=forward_transform,
            reverse_callable=reverse_transform,
            logger=logger
        )
        
        # Test forward transformation
        forward_called.clear()
        x_obs.value = 7  # This should trigger forward transformation
        self.assertTrue(forward_called)
        self.assertEqual(result_obs.value, 14)  # 7 * 2
        
        # Test reverse transformation
        reverse_called.clear()
        result_obs.value = 20  # This should trigger reverse transformation
        self.assertTrue(reverse_called)
        self.assertEqual(x_obs.value, 10)  # 20 // 2

    def test_bidirectional_temperature_conversion(self):
        """Test bidirectional transformation with temperature conversion."""
        # Create observables
        celsius_obs = ObservableSingleValue(20.0, logger=logger)
        fahrenheit_obs = ObservableSingleValue(68.0, logger=logger)
        
        def celsius_to_fahrenheit(inputs: Mapping[Literal["celsius"], Any]) -> Mapping[Literal["fahrenheit"], Any]:
            return {"fahrenheit": inputs["celsius"] * 9/5 + 32}
        
        def fahrenheit_to_celsius(outputs: Mapping[Literal["fahrenheit"], Any]) -> Mapping[Literal["celsius"], Any]:
            return {"celsius": (outputs["fahrenheit"] - 32) * 5/9}
        
        ObservableTransfer[Literal["celsius"], Literal["fahrenheit"], float, float](
            input_trigger_hooks={"celsius": celsius_obs.hook},
            output_trigger_hooks={"fahrenheit": fahrenheit_obs.hook},
            forward_callable=celsius_to_fahrenheit,
            reverse_callable=fahrenheit_to_celsius,
            logger=logger
        )
        
        # Test forward: Change Celsius, check Fahrenheit
        celsius_obs.value = 0.0  # Freezing point
        self.assertAlmostEqual(fahrenheit_obs.value, 32.0, places=1)
        
        # Test reverse: Change Fahrenheit, check Celsius  
        fahrenheit_obs.value = 100.0
        self.assertAlmostEqual(celsius_obs.value, 37.777777777777786, places=5)

    def test_attach_detach_hooks(self):
        """Test attach and detach functionality."""
        x_hook = OwnedHook(owner=self.mock_owner, initial_value=5, logger=logger)
        result_hook = OwnedHook(owner=self.mock_owner, initial_value=0, logger=logger)
        external_hook = OwnedHook(owner=self.mock_owner, initial_value=999, logger=logger)
        
        transfer = ObservableTransfer(
            input_trigger_hooks={"x": x_hook},
            output_trigger_hooks={"result": result_hook},
            forward_callable=lambda inputs: {"result": inputs["x"] * 2},
            logger=logger
        )
        
        # Test attach
        transfer.connect(external_hook, "x", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        # Test detach
        transfer.disconnect("x")
        
        # Test invalid key for attach/detach
        with self.assertRaises(ValueError):
            transfer.connect(external_hook, "invalid", InitialSyncMode.USE_CALLER_VALUE)  # type: ignore
        
        with self.assertRaises(ValueError):
            transfer.disconnect("invalid")

    def test_dictionary_access_scenario(self):
        """Test dictionary access transformation scenario."""
        # Create observables for dictionary access pattern
        dict_obs = ObservableSingleValue[dict[str, int]]({"a": 1, "b": 2, "c": 3}, logger=logger)
        key_obs: ObservableSingleValue[str] = ObservableSingleValue("a", logger=logger)
        value_obs = ObservableSingleValue[Optional[int]](None, logger=logger)
        exists_obs = ObservableSingleValue[bool](False, logger=logger)
        
        def dict_access_transform(inputs: Mapping[Literal["dict", "key"], Any]) -> Mapping[Literal["value", "exists"], Any]:
            d = inputs["dict"]
            k = inputs["key"]
            return {
                "value": d.get(k),
                "exists": k in d
            }
        
        ObservableTransfer[Literal["dict", "key"], Literal["value", "exists"], dict[str, int] | str | int | bool | None, dict[str, int] | str | int | bool | None](
            input_trigger_hooks={
                "dict": cast(HookLike[dict[str, int] | str | int | bool | None], dict_obs.hook),
                "key": cast(HookLike[dict[str, int] | str | int | bool | None], key_obs.hook)
            },
            output_trigger_hooks={
                "value": cast(HookLike[dict[str, int] | str | int | bool | None], value_obs.hook),
                "exists": cast(HookLike[dict[str, int] | str | int | bool | None], exists_obs.hook)
            },
            forward_callable=dict_access_transform,
            logger=logger
        )
        
        # Test initial state
        self.assertIsNone(value_obs.value)
        self.assertFalse(exists_obs.value)
        
        # Trigger transformation by changing key
        key_obs.value = "b"
        self.assertEqual(value_obs.value, 2)      # dict["b"] = 2
        self.assertTrue(exists_obs.value)         # "b" exists in dict
        
        # Change key to non-existent value
        key_obs.value = "z"
        self.assertIsNone(value_obs.value)        # dict["z"] = None
        self.assertFalse(exists_obs.value)        # "z" doesn't exist
        
        # Change dictionary
        dict_obs.value = {"x": 10, "y": 20, "z": 30}
        self.assertEqual(value_obs.value, 30)     # dict["z"] = 30 now
        self.assertTrue(exists_obs.value)         # "z" exists now

    def test_thread_safety(self):
        """Test thread safety of transformations."""
        # Create observables
        x_obs = ObservableSingleValue(0, logger=logger)
        y_obs = ObservableSingleValue(0, logger=logger)
        sum_obs = ObservableSingleValue(0, logger=logger)
        
        # Track transformation calls
        transform_count: list[int] = []
        
        def slow_transform(inputs: Mapping[Literal["x", "y"], Any]) -> Mapping[Literal["sum"], Any]:
            time.sleep(0.01)  # Simulate slow transformation
            transform_count.append(1)
            return {"sum": inputs["x"] + inputs["y"]}
        
        ObservableTransfer[Literal["x", "y"], Literal["sum"], int, int](
            input_trigger_hooks={"x": x_obs.hook, "y": y_obs.hook},
            output_trigger_hooks={"sum": sum_obs.hook},
            forward_callable=slow_transform,
            logger=logger
        )
        
        def worker_thread(thread_id: int) -> None:
            """Worker thread that triggers transformations."""
            for i in range(3):  # Reduced for faster testing
                x_obs.value = thread_id * 10 + i
                time.sleep(0.005)
        
        # Start multiple threads
        threads: list[threading.Thread] = []
        for i in range(2):  # Reduced number of threads
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have completed without errors
        self.assertTrue(len(transform_count) > 0)

    def test_listener_notifications(self):
        """Test that listeners are notified when transformations occur."""
        # Create observables
        x_obs = ObservableSingleValue(5, logger=logger)
        result_obs = ObservableSingleValue(0, logger=logger)
        
        transfer = ObservableTransfer(
            input_trigger_hooks={"x": x_obs.hook},
            output_trigger_hooks={"result": result_obs.hook},
            forward_callable=lambda inputs: {"result": inputs["x"] * 2},
            logger=logger
        )
        
        # Add listener to transfer
        notifications: list[str] = []
        transfer.add_listeners(lambda: notifications.append("transfer_notified"))
        
        # Trigger transformation by changing input
        x_obs.value = 10
        
        # Should have notified listeners
        self.assertIn("transfer_notified", notifications)

    def test_string_formatting_use_case(self):
        """Test string formatting use case."""
        # Create observables
        template_obs = ObservableSingleValue("Hello, {name}!", logger=logger)
        name_obs = ObservableSingleValue("World", logger=logger)
        result_obs = ObservableSingleValue("", logger=logger)
        
        def format_string(inputs: Mapping[Literal["template", "name"], Any]) -> Mapping[Literal["result"], Any]:
            return {"result": inputs["template"].format(name=inputs["name"])}
        
        ObservableTransfer[Literal["template", "name"], Literal["result"], str, str](
            input_trigger_hooks={"template": template_obs.hook, "name": name_obs.hook},
            output_trigger_hooks={"result": result_obs.hook},
            forward_callable=format_string,
            logger=logger
        )
        
        # Test initial transformation
        name_obs.value = "Alice"  # Trigger transformation
        self.assertEqual(result_obs.value, "Hello, Alice!")
        
        # Change template
        template_obs.value = "Hi {name}, how are you?"
        self.assertEqual(result_obs.value, "Hi Alice, how are you?")

    def test_mathematical_operations_use_case(self):
        """Test mathematical operations use case."""
        # Create observables
        x_obs = ObservableSingleValue(10.0, logger=logger)
        y_obs = ObservableSingleValue(3.0, logger=logger)
        
        sum_obs = ObservableSingleValue(0.0, logger=logger)
        product_obs = ObservableSingleValue(0.0, logger=logger)
        quotient_obs = ObservableSingleValue(0.0, logger=logger)
        
        def math_operations(inputs: Mapping[Literal["x", "y"], Any]) -> Mapping[Literal["sum", "product", "quotient"], Any]:
            x, y = inputs["x"], inputs["y"]
            return {
                "sum": x + y,
                "product": x * y,
                "quotient": x / y if y != 0 else float('inf')
            }
        
        ObservableTransfer[Literal["x", "y"], Literal["sum", "product", "quotient"], int|float, int|float](
            input_trigger_hooks={"x": x_obs.hook, "y": y_obs.hook},
            output_trigger_hooks={"sum": sum_obs.hook, "product": product_obs.hook, "quotient": quotient_obs.hook},
            forward_callable=math_operations,
            logger=logger
        )
        
        # Test calculation by changing input
        x_obs.value = 12.0  # Trigger transformation
        self.assertEqual(sum_obs.value, 15.0)      # 12 + 3
        self.assertEqual(product_obs.value, 36.0)  # 12 * 3
        self.assertEqual(quotient_obs.value, 4.0)  # 12 / 3
        
        # Test division by zero
        y_obs.value = 0.0
        self.assertEqual(sum_obs.value, 12.0)      # 12 + 0
        self.assertEqual(product_obs.value, 0.0)   # 12 * 0
        self.assertEqual(quotient_obs.value, float('inf'))  # 12 / 0


if __name__ == '__main__':
    unittest.main()
