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

from typing import Callable, Generic, Mapping, Optional, TypeVar
from logging import Logger
from threading import RLock

from .._utils.initial_sync_mode import InitialSyncMode

from .._hooks.owned_hook import OwnedHook
from .._hooks.hook_like import HookLike
from .._hooks.owned_hook_like import OwnedHookLike
from .._utils.base_listening import BaseListening
from .._utils.base_carries_hooks import BaseCarriesHooks
from .._utils.hook_nexus import HookNexus
from .._utils.general import log


# Type variables for input and output hook names
IHK = TypeVar("IHK")  # Input Hook Keys
OHK = TypeVar("OHK")  # Output Hook Keys
IHV = TypeVar("IHV")
OHV = TypeVar("OHV")


class ObservableTransfer(BaseListening, BaseCarriesHooks[IHK|OHK, IHV|OHV], Generic[IHK, OHK, IHV, OHV]):
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
    
    **New Architecture Integration:**
    The transformation is triggered automatically through the add_values_to_be_updated_callback,
    which is called by the NexusManager during value submission. This replaces the old
    invalidation-based system with a more flexible hook-based approach.
    """

    def __init__(
        self,
        input_trigger_hooks: Mapping[IHK, HookLike[IHV]|IHV],
        forward_callable: Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]],
        output_trigger_hooks: Mapping[OHK, HookLike[OHV]|OHV] = {},
        reverse_callable: Optional[Callable[[Mapping[OHK, OHV]], Mapping[IHK, IHV]]] = None,
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
                Must return a dict with keys matching output_trigger_hooks keys.
            output_trigger_hooks: Dictionary mapping output names to their hooks or None.
                When any of these hooks are invalidated, reverse transformation is triggered (if available).
                Use value as value for keys that should be managed internally without external connection.
                All keys that the forward_callable returns must be present in this dict.
            reverse_callable: Optional function that transforms output values to input values.
                Expected signature: (output_values: Mapping[OHK, OHV]) -> Mapping[IHK, IHV]
                If None, reverse transformation is not triggered.
                Must return a dict with keys matching input_trigger_hooks keys.
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
            >>> sum_hook = Hook(owner=some_owner, value=0)
            >>> product_value = 0
            >>> 
            >>> transfer = ObservableTransfer(
            ...     input_trigger_hooks={"x": x_hook, "y": y_hook},
            ...     output_trigger_hooks={"sum": sum_hook, "product": product_value},  # product is internal-only
            ...     forward_callable=lambda inputs: {
            ...         "sum": inputs["x"] + inputs["y"],
            ...         "product": inputs["x"] * inputs["y"]
            ...     }
            ... )
            >>> 
            >>> # x_hook and y_hook changes trigger automatic updates
            >>> # sum_hook gets external updates, product_hook remains internal
        """
        
        # Initialize base classes
        BaseListening.__init__(self, logger)
        
        def add_values_to_be_updated_callback(
            current_values: Mapping[IHK|OHK, IHV|OHV],
            submitted_values: Mapping[IHK|OHK, IHV|OHV]
        ) -> Mapping[IHK|OHK, IHV|OHV]:
            """
            Add values to be updated by triggering transformations.
            This callback is called when any hook value changes.
            """
            # Check if any input values changed - if so, trigger forward transformation
            input_keys = set(input_trigger_hooks.keys())
            if any(key in submitted_values for key in input_keys):
                # Trigger forward transformation
                try:
                    # Use submitted values for changed keys, current values for unchanged keys
                    input_values: Mapping[IHK, IHV] = {}
                    for key in input_keys:
                        if key in submitted_values:
                            input_values[key] = submitted_values[key] # type: ignore
                        else:
                            input_values[key] = current_values[key] # type: ignore
                    output_values: Mapping[OHK, OHV] = forward_callable(input_values)
                    return output_values # type: ignore
                except Exception as e:
                    log(self, "add_values_to_be_updated_callback", logger, False, f"Forward transformation failed: {e}")
                    return {}
            
            # Check if any output values changed - if so, trigger reverse transformation
            if reverse_callable is not None:
                output_keys = set(output_trigger_hooks.keys())
                if any(key in submitted_values for key in output_keys):
                    try:
                        # Use submitted values for changed keys, current values for unchanged keys
                        output_values = {}
                        for key in output_keys:
                            if key in submitted_values:
                                output_values[key] = submitted_values[key] # type: ignore
                            else:
                                output_values[key] = current_values[key] # type: ignore
                        input_values = reverse_callable(output_values)
                        return input_values # type: ignore
                    except Exception as e:
                        log(self, "add_values_to_be_updated_callback", logger, False, f"Reverse transformation failed: {e}")
                        return {}
            
            return {}
        
        BaseCarriesHooks.__init__( # type: ignore
            self,
            logger=logger,
            invalidate_callback=None,
            validate_complete_values_in_isolation_callback=None,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback
        )
        
        self._forward_callable: Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]] = forward_callable
        self._reverse_callable: Optional[Callable[[Mapping[OHK, OHV]], Mapping[IHK, IHV]]] = reverse_callable
        self._lock: RLock = RLock()
        self._logger: Optional[Logger] = logger
        
        # Create internal hooks for all keys that will be used in transformations
        # These internal hooks will have invalidation callbacks that trigger our transformations
        self._input_hooks: dict[IHK, OwnedHook[IHV]] = {}
        self._output_hooks: dict[OHK, OwnedHook[OHV]] = {}
        
        # We need to determine all possible keys by analyzing the callable signatures
        # For now, we'll create hooks for the provided external hooks and connect them
        
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
            if isinstance(external_hook_or_value, HookLike):
                internal_hook_input.connect_hook(external_hook_or_value, InitialSyncMode.USE_CALLER_VALUE) # type: ignore
        
        # Create output hooks for all keys, connecting to external hooks when provided
        for key, external_hook_or_value in output_trigger_hooks.items():
            # Create internal hook with invalidation callback
            initial_value_output: OHV = external_hook_or_value.value if isinstance(external_hook_or_value, HookLike) else external_hook_or_value # type: ignore
            internal_hook_output = OwnedHook[OHV](
                owner=self,
                initial_value=initial_value_output,
                logger=logger
            )
            self._output_hooks[key] = internal_hook_output
            
            # Connect our internal hook to external hook if external hook is provided
            if isinstance(external_hook_or_value, HookLike):
                internal_hook_output.connect_hook(external_hook_or_value, InitialSyncMode.USE_CALLER_VALUE) # type: ignore

    #########################################################################
    # CarriesHooks interface
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