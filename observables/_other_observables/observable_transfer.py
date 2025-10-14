"""
ObservableTransfer Module - New Hook-Based Architecture

This module provides the ObservableTransfer class, a powerful observable that acts as a 
transformation layer between multiple input and output hooks using the new hook-based
sync system.

The ObservableTransfer is designed for scenarios where you need to:
- Transform values from multiple input sources to multiple output destinations
- Implement complex calculations that depend on multiple observable values
- Create derived values that automatically update when their dependencies change
- Implement bidirectional transformations with optional reverse computation

**New Architecture Features:**
- Uses add_values_to_be_updated_callback instead of listeners for transformation triggering
- Integrates with NexusManager for value submission and synchronization
- Supports custom validation and completion logic
- Replaces old invalidation-based system with more flexible hook-based approach

Key Features:
- Multiple input trigger hooks for dependency management
- Multiple output trigger hooks for result distribution
- Forward transformation (inputs → outputs) via callable
- Optional reverse transformation (outputs → inputs) via callable
- **Both callables always receive COMPLETE sets of values** (mixing submitted and current values)
- Automatic transformation triggering through add_values_to_be_updated_callback
- Type-safe generic implementation with named components
- Thread-safe operations with RLock protection
- Full BaseCarriesHooks interface with hook management support

Architecture:
The class extends BaseListening and BaseCarriesHooks[IHK|OHK] and manages:
- Input trigger hooks: Named hooks that trigger forward transformation when changed
- Output trigger hooks: Named hooks that trigger reverse transformation when changed
- Forward callable: Function that computes outputs from inputs
- Reverse callable: Optional function that computes inputs from outputs
- add_values_to_be_updated_callback: Handles transformation logic in the new architecture

Use Cases:
1. **Dictionary Access**: dict + key → value transformation
2. **Mathematical Operations**: multiple numbers → calculated result
3. **String Formatting**: template + variables → formatted string
4. **Data Conversion**: raw data → processed/validated data
5. **Complex Business Logic**: multiple business values → derived state

Example Usage:
    >>> # Dictionary access example
    >>> data_dict = ObservableDict({"a": 1, "b": 2, "c": 3})
    >>> key_obs = ObservableSingleValue("a")
    >>> value_hook = Hook(owner=some_owner, value=0)
    >>> 
    >>> transfer = ObservableTransfer(
    ...     input_trigger_hooks={"dict": data_dict.dict_hook, "key": key_obs.single_value_hook},
    ...     output_trigger_hooks={"value": value_hook},
    ...     forward_callable=lambda inputs: {"value": inputs["dict"].get(inputs["key"], 0)}
    ... )
    >>> 
    >>> # When input hooks change, output hooks are automatically updated via the new sync system
    >>> key_obs.single_value = "b"  # Triggers forward transformation automatically

Performance Characteristics:
- O(1) for hook access operations
- Transformation performance depends on the provided callables
- Automatic invalidation detection with minimal overhead
- Thread-safe operations for concurrent access
- Atomic updates using HookNexus.submit_multiple_values()
"""

from typing import Callable, Generic, Mapping, Optional, TypeVar, Literal
from logging import Logger

from .._hooks.owned_hook import OwnedHook
from .._hooks.hook_like import HookLike
from .._hooks.owned_hook_like import OwnedHookLike
from .._utils.base_listening import BaseListening
from .._utils.base_carries_hooks import BaseCarriesHooks
from .._utils.hook_nexus import HookNexus

# Type variables for input and output hook names
IHK = TypeVar("IHK")  # Input Hook Keys
OHK = TypeVar("OHK")  # Output Hook Keys
IHV = TypeVar("IHV")
OHV = TypeVar("OHV")


class ObservableTransfer(BaseListening, BaseCarriesHooks[IHK|OHK, IHV|OHV, "ObservableTransfer"], Generic[IHK, OHK, IHV, OHV]):
    """
    An observable that transforms values between input and output hooks using the new hook-based architecture.
    
    This class acts as a transformation layer that:
    - Manages multiple named input trigger hooks
    - Manages multiple named output trigger hooks  
    - Automatically triggers forward transformation when input hooks change
    - Automatically triggers reverse transformation when output hooks change (if reverse callable provided)
    - Uses add_values_to_be_updated_callback for transformation logic
    - Integrates with NexusManager for value submission and synchronization
    - Provides thread-safe operations with RLock protection
    
    **IMPORTANT - Complete Value Sets:**
    Both forward_callable and reverse_callable are ALWAYS called with complete sets of values.
    When a hook value changes, the callable receives:
    - The new (submitted) value for changed keys
    - The current (existing) value for unchanged keys
    This ensures transformations always have all required inputs available.
    
    **New Architecture Integration:**
    The transformation is triggered automatically through the add_values_to_be_updated_callback,
    which is called by the NexusManager during value submission. This replaces the old
    invalidation-based system with a more flexible hook-based approach.
    """

    def __init__(
        self,
        input_trigger_hooks: Mapping[IHK, HookLike[IHV]|IHV],
        forward_callable: Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]],
        output_trigger_hook_keys: set[OHK],
        reverse_callable: Optional[Callable[[Mapping[OHK, OHV]], Mapping[IHK, IHV]]] = None,
        assume_inverse_callable_is_always_valid: bool = False,
        precision_threshold_for_inverse_callable_validation: float = 1e-6,
        logger: Optional[Logger] = None
    ):
        """
        Initialize the ObservableTransfer.

        Args:
            input_trigger_hooks: Dictionary mapping input names to their hooks or None.
                When any of these hooks are invalidated, forward transformation is triggered.
                Use value as value for keys that should be managed internally without external connection.
                All keys that the forward_callable expects must be present in this dict.
            forward_callable: Function that transforms input values to output values.
                Expected signature: (input_values: Mapping[IHK, IHV]) -> Mapping[OHK, OHV]
                Must return a dict with keys matching output_trigger_hook_keys.
                **IMPORTANT**: This callable is ALWAYS called with a COMPLETE set of input values,
                combining submitted (changed) values with current (unchanged) values.
            output_trigger_hook_keys: Set of output hook keys.
                When any of these hooks are invalidated, reverse transformation is triggered (if available).
                All keys that the forward_callable returns must be present in this set.
            reverse_callable: Optional function that transforms output values to input values.
                Expected signature: (output_values: Mapping[OHK, OHV]) -> Mapping[IHK, IHV]
                If None, reverse transformation is not triggered.
                Must return a dict with keys matching input_trigger_hooks keys.
                It must be the inverse function of the forward callable.
                **IMPORTANT**: This callable is ALWAYS called with a COMPLETE set of output values,
                combining submitted (changed) values with current (unchanged) values.
            logger: Optional logger for debugging and monitoring transformations.
        
        Note:
            For each key in the dictionaries, an internal hook is created:
            - If the value is a HookLike object, it's connected to the internal hook
            - If the value is a value, the internal hook remains standalone
            This ensures all transformation keys have corresponding hooks for the CarriesHooks interface.

        Example:
            >>> # Mathematical transformation with mixed external/internal hooks
            >>> x_hook = Hook(owner=some_owner, value=5)
            >>> y_hook = Hook(owner=some_owner, value=3)
            >>> 
            >>> transfer = ObservableTransfer(
            ...     input_trigger_hooks={"x": x_hook, "y": y_hook},
            ...     output_trigger_hook_keys={"sum", "product"},
            ...     forward_callable=lambda inputs: {
            ...         "sum": inputs["x"] + inputs["y"],
            ...         "product": inputs["x"] * inputs["y"]
            ...     }
            ... )
            >>> 
            >>> # x_hook and y_hook changes trigger automatic updates
            >>> # sum_hook and product_hook get updated automatically when x_hook or y_hook changes
            >>> # NOTE: forward_callable will ALWAYS receive BOTH "x" and "y" values,
            >>> # even if only one of them changed (it gets the new value for the changed
            >>> # one and the current value for the unchanged one)
        """

        self._forward_callable: Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]] = forward_callable
        self._reverse_callable: Optional[Callable[[Mapping[OHK, OHV]], Mapping[IHK, IHV]]] = reverse_callable

        self._input_hooks: dict[IHK, HookLike[IHV]|IHV] = {}
        self._output_hooks: dict[OHK, HookLike[OHV]|OHV] = {}

        self._assume_inverse_callable_is_always_valid: bool = assume_inverse_callable_is_always_valid
        self._precision_threshold_for_inverse_callable_validation: float = precision_threshold_for_inverse_callable_validation

        # Create input hooks for all keys, connecting to external hooks when provided
        for key, external_hook_or_value in input_trigger_hooks.items():
            # Create internal hook with invalidation callback
            initial_value_input: IHV = external_hook_or_value.value if isinstance(external_hook_or_value, HookLike) else external_hook_or_value # type: ignore
            internal_hook_input: OwnedHook[IHV] = OwnedHook(
                owner=self,
                initial_value=initial_value_input,
                logger=logger
            )
            self._input_hooks[key] = internal_hook_input
            # Connect the internal hook to the external hook later (after the object is initialized)

        # Create output hooks for all keys, connecting to external hooks when provided
        if isinstance(output_trigger_hook_keys, set): # type: ignore
            output_values: dict[OHK, OHV] = self._forward_callable(self.get_input_values()) # type: ignore
        else:
            raise ValueError(f"Invalid output trigger hooks: {output_trigger_hooks}")
        for key in output_trigger_hook_keys:
            internal_hook_output: OwnedHook[OHV] = OwnedHook(
                owner=self,
                initial_value=output_values[key],
                logger=logger
            )
            self._output_hooks[key] = internal_hook_output

        BaseListening.__init__(self, logger)

        def add_values_to_be_updated_callback(
            self_ref: "ObservableTransfer[IHK, OHK, IHV, OHV]",
            current_values: Mapping[IHK|OHK, IHV|OHV],
            submitted_values: Mapping[IHK|OHK, IHV|OHV]
        ) -> Mapping[IHK|OHK, IHV|OHV]:
            """
            Add values to be updated by triggering transformations.
            This callback is called when any hook value changes.
            
            NOTE: Both forward_callable and reverse_callable are ALWAYS called with
            COMPLETE sets of values by merging submitted_values (changed keys) with
            current_values (unchanged keys). This ensures transformations always have
            all required inputs available.
            """

            if reverse_callable is not None and not self_ref._assume_inverse_callable_is_always_valid:
                is_inverse, msg = self_ref.check_if_reverse_callable_is_the_inverse_of_the_forward_callable()
                if not is_inverse:
                    raise ValueError(f"Reverse callable validation failed: {msg}")

            values_to_be_added: dict[IHK|OHK, IHV|OHV] = {}

            # Check if any input values changed - if so, trigger forward transformation
            input_keys = set(input_trigger_hooks.keys())
            if any(key in submitted_values for key in input_keys):
                # Trigger forward transformation

                # Use submitted values for changed keys, current values for unchanged keys
                input_values: Mapping[IHK, IHV] = {}
                for key in input_keys:
                    if key in submitted_values:
                        input_values[key] = submitted_values[key] # type: ignore
                    else:
                        input_values[key] = current_values[key] # type: ignore
                output_values: Mapping[OHK, OHV] = forward_callable(input_values)
                values_to_be_added.update(output_values) # type: ignore
            
            # Check if any output values changed - if so, trigger reverse transformation
            if reverse_callable is not None:
                output_keys = set(output_trigger_hook_keys)
                if any(key in submitted_values for key in output_keys):
                    # Use submitted values for changed keys, current values for unchanged keys
                    output_values = {}
                    for key in output_keys:
                        if key in submitted_values:
                            output_values[key] = submitted_values[key] # type: ignore
                        else:
                            output_values[key] = current_values[key] # type: ignore
                    input_values = reverse_callable(output_values)
                    # For reverse transformation, we need to return the input values
                    # but they should be applied to the input hooks, not output hooks
                    values_to_be_added.update(input_values) # type: ignore

            # Remove values that are already in the submitted values
            for key in submitted_values:
                values_to_be_added.pop(key, None)

            return values_to_be_added

        BaseCarriesHooks.__init__( # type: ignore
            self,
            logger=logger,
            invalidate_callback=None,
            validate_complete_values_in_isolation_callback=None,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback
        )
        
        # Check if the reverse callable is valid (after initialization)
        if reverse_callable is not None:
            is_inverse, msg = self.check_if_reverse_callable_is_the_inverse_of_the_forward_callable()
            if not is_inverse:
                raise ValueError(f"Reverse callable validation failed: {msg}")

        # Connect the internal hook to the external hook if provided
        for key, external_hook_or_value in input_trigger_hooks.items():
            internal_hook_input = self._input_hooks[key] # type: ignore
            if isinstance(external_hook_or_value, HookLike):
                internal_hook_input.connect_hook(external_hook_or_value, "use_caller_value") # type: ignore

    #########################################################################
    # BaseCarriesHooks abstract methods
    #########################################################################

    def _get_hook(self, key: IHK|OHK) -> "OwnedHookLike[IHV|OHV]":
        """Get a hook by its key (either input or output)."""
        if key in self._input_hooks:
            return self._input_hooks[key] # type: ignore
        elif key in self._output_hooks:
            return self._output_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_value_reference_of_hook(self, key: IHK|OHK) -> IHV|OHV:
        if key in self._input_hooks:
            return self._input_hooks[key].value # type: ignore
        elif key in self._output_hooks:
            return self._output_hooks[key].value # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_hook_keys(self) -> set[IHK|OHK]:
        return set(self._input_hooks.keys()) | set(self._output_hooks.keys())

    def _get_hook_key(self, hook_or_nexus: "HookLike[IHV|OHV]|HookNexus[IHV|OHV]") -> IHK|OHK:
        for key, hook in self._input_hooks.items():
            if hook is hook_or_nexus:
                return key
        for key, hook in self._output_hooks.items():
            if hook is hook_or_nexus:
                return key
        raise ValueError(f"Hook {hook_or_nexus} not found in hooks")

    #########################################################################
    # Other private methods
    #########################################################################

    def _get_input_hook(self, key: IHK) -> OwnedHook[IHV]:
        return self._input_hooks[key] # type: ignore
    
    def _get_output_hook(self, key: OHK) -> OwnedHook[OHV]:
        return self._output_hooks[key] # type: ignore

    #########################################################################
    # Other public methods
    #########################################################################

    @property
    def forward_callable(self) -> Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]]:
        """
        Get the forward callable.
        """
        return self._forward_callable
    
    @property
    def reverse_callable(self) -> Optional[Callable[[Mapping[OHK, OHV]], Mapping[IHK, IHV]]]:
        """
        Get the reverse callable.
        """
        return self._reverse_callable

    def get_input_hooks(self) -> dict[IHK, OwnedHook[IHV]]:
        """
        Get the input hooks as a copied dictionary.
        """
        return self._input_hooks.copy() # type: ignore
    
    def get_output_hooks(self) -> dict[OHK, OwnedHook[OHV]]:
        """
        Get the output hooks as a copied dictionary.
        """
        return self._output_hooks.copy() # type: ignore

    def get_input_hook(self, key: IHK) -> OwnedHook[IHV]:
        """
        Get the input hook by its key.
        """
        return self._input_hooks[key] # type: ignore
    
    def get_output_hook(self, key: OHK) -> OwnedHook[OHV]:
        """
        Get the output hook by its key.
        """
        return self._output_hooks[key] # type: ignore

    def get_input_values(self) -> Mapping[IHK, IHV]:
        """
        Get the input values as a dictionary.
        """
        input_values: dict[IHK, IHV] = {}
        for key, hook in self._input_hooks.items():
            value: IHV = hook.value # type: ignore
            input_values[key] = value

        return input_values
    
    def get_output_values(self) -> Mapping[OHK, OHV]:
        """
        Get the output values as a dictionary.
        """

        output_values: dict[OHK, OHV] = {}
        for key, hook in self._output_hooks.items():
            value: OHV = hook.value # type: ignore
            output_values[key] = value

        return output_values

    def submit_input_values(self, values: Mapping[IHK, IHV]) -> None:
        """
        Submit input values to the transfer.

        Args:
            values: Mapping of input hook keys to their new values
        """

        values_to_submit: dict[IHK, IHV] = {}
        for key, value in values.items():
            if key not in self._input_hooks:
                raise ValueError(f"Key {key} not found in input hooks")
            values_to_submit[key] = value # type: ignore
        success, msg = self.submit_values(values_to_submit) # type: ignore
        if not success:
            raise ValueError(msg)

    def submit_output_values(self, values: Mapping[OHK, OHV]) -> None:
        """
        Submit output values to the transfer.

        Args:
            values: Mapping of output hook keys to their new values
        """
        
        values_to_submit: dict[OHK, OHV] = {}
        for key, value in values.items():
            if key not in self._output_hooks:
                raise ValueError(f"Key {key} not found in output hooks")
            values_to_submit[key] = value # type: ignore
        success, msg = self.submit_values(values_to_submit) # type: ignore
        if not success:
            raise ValueError(msg)

    def validate_input_values(self, values: Mapping[IHK, IHV]) -> None:
        """
        Submit input values to the transfer.

        Args:
            values: Mapping of input hook keys to their new values
        """

        values_to_validate: dict[IHK, IHV] = {}
        for key, value in values.items():
            if key not in self._input_hooks:
                raise ValueError(f"Key {key} not found in input hooks")
            values_to_validate[key] = value # type: ignore
        success, msg = self.validate_values(values_to_validate) # type: ignore
        if not success:
            raise ValueError(msg)

    def validate_output_values(self, values: Mapping[OHK, OHV]) -> None:
        """
        Submit output values to the transfer.

        Args:
            values: Mapping of output hook keys to their new values
        """
        
        values_to_validate: dict[OHK, OHV] = {}
        for key, value in values.items():
            if key not in self._output_hooks:
                raise ValueError(f"Key {key} not found in output hooks")
            values_to_validate[key] = value # type: ignore
        success, msg = self.validate_values(values_to_validate) # type: ignore
        if not success:
            raise ValueError(msg)

    def check_if_reverse_callable_is_the_inverse_of_the_forward_callable(self, check_for: Literal["input_values", "output_values"] = "input_values") -> tuple[bool, str]:
        """
        Check both callables are inverses of each other.

        Args:
            check_for: Whether to check if the reverse callable is the inverse of the forward callable or the forward callable is the inverse of the reverse callable.

        Returns:
            A tuple containing a boolean indicating if the callables are inverses of each other and a string describing the result.
        """

        if self._reverse_callable is None:
            raise ValueError("Reverse callable is not set")

        if check_for == "input_values":
            start_values = self.get_input_values()
            callable_1 = self._forward_callable
            callable_2 = self._reverse_callable
        else:
            start_values = self.get_output_values()
            callable_1 = self._reverse_callable
            callable_2 = self._forward_callable
        
        # Test with current values to ensure reverse callable returns all input keys
        try:
            intermediate_result = callable_1(start_values) # type: ignore
        except Exception as e:
            if check_for == "input_values":
                return False, f"Error when calling forward callable: {e}"
            else:
                return False, f"Error when calling reverse callable: {e}"

        if not isinstance(intermediate_result, dict):
            if check_for == "input_values":
                return False, "Forward callable does not return a dictionary"
            else:
                return False, "Reverse callable does not return a dictionary"

        try:
            reverse_result = callable_2(intermediate_result) # type: ignore
        except Exception as e:
            if check_for == "input_values":
                return False, f"Error when calling reverse callable: {e}"
            else:
                return False, f"Error when calling forward callable: {e}"
        
        # Check if it returns a dictionary
        if not isinstance(reverse_result, dict):
            if check_for == "input_values":
                return False, "Reverse callable does not return a dictionary"
            else:
                return False, "Forward callable does not return a dictionary"
        
        # Check if the reverse result is equal to the original input values (with precision threshold for numeric types)
        for key in reverse_result:

            # Skip keys that are not in the start values (e.g. if reverse callable returns more keys than the forward callable)
            if key not in start_values:
                continue

            start_values_value = start_values[key] # type: ignore
            reverse_result_value = reverse_result[key] # type: ignore

            # Check if the reverse result is equal to the original input values (with precision threshold for numeric types)
            if hasattr(reverse_result_value, "__sub__") and hasattr(start_values_value, "__sub__"):
                if abs(reverse_result_value - start_values_value) > self._precision_threshold_for_inverse_callable_validation: # type: ignore
                    return False, f"Reverse callable is not the inverse of the forward callable for key {key}"
            else:
                if not reverse_result_value == start_values_value:
                    return False, f"Reverse callable is not the inverse of the forward callable for key {key}"

        return True, "Inverse callable is valid on the present input values"
