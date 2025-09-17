"""
ObservableTransfer Module

This module provides the ObservableTransfer class, a powerful observable that acts as a 
transformation layer between multiple input and output hooks with automatic invalidation.

The ObservableTransfer is designed for scenarios where you need to:
- Transform values from multiple input sources to multiple output destinations
- Implement complex calculations that depend on multiple observable values
- Create derived values that automatically update when their dependencies change
- Implement bidirectional transformations with optional reverse computation

Key Features:
- Multiple input trigger hooks for dependency management
- Multiple output trigger hooks for result distribution
- Forward transformation (inputs → outputs) via callable
- Optional reverse transformation (outputs → inputs) via callable
- Automatic transformation triggering through hook invalidation system
- Type-safe generic implementation with named components
- Thread-safe operations with RLock protection
- Full CarriesHooks interface with attach/detach support

Architecture:
The class extends BaseListening and CarriesHooks[IHK|OHK] and manages:
- Input trigger hooks: Named hooks that trigger forward transformation when invalidated
- Output trigger hooks: Named hooks that trigger reverse transformation when invalidated
- Forward callable: Function that computes outputs from inputs
- Reverse callable: Optional function that computes inputs from outputs
- Automatic invalidation detection and transformation triggering

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
    >>> # When input hooks are invalidated, output hooks are automatically updated
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
from .._utils.carries_hooks import CarriesHooks
from .._utils.hook_nexus import HookNexus
from .._utils.general import log


# Type variables for input and output hook names
IHK = TypeVar("IHK")  # Input Hook Keys
OHK = TypeVar("OHK")  # Output Hook Keys
IHV = TypeVar("IHV")
OHV = TypeVar("OHV")


class ObservableTransfer(BaseListening, CarriesHooks[IHK|OHK, IHV|OHV], Generic[IHK, OHK, IHV, OHV]):
    """
    An observable that transforms values between input and output hooks with automatic invalidation.
    
    This class acts as a transformation layer that:
    - Manages multiple named input trigger hooks
    - Manages multiple named output trigger hooks  
    - Automatically triggers forward transformation when input hooks are invalidated
    - Automatically triggers reverse transformation when output hooks are invalidated (if reverse callable provided)
    - Ensures atomic updates using HookNexus for consistency
    - Provides thread-safe operations with RLock protection
    
    The transformation is triggered automatically through the hook invalidation system,
    ensuring that dependent values are always consistent without manual intervention.
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
        super().__init__(logger)
        
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
                value=initial_value_input,
                invalidate_callback=lambda _, k=key: self._on_input_invalidated(k),
                logger=logger
            )
            self._input_hooks[key] = internal_hook_input
            if isinstance(external_hook_or_value, HookLike):
                internal_hook_input.connect(external_hook_or_value, InitialSyncMode.USE_CALLER_VALUE) # type: ignore
        
        # Create output hooks for all keys, connecting to external hooks when provided
        for key, external_hook_or_value in output_trigger_hooks.items():
            # Create internal hook with invalidation callback
            initial_value_output: OHV = external_hook_or_value.value if isinstance(external_hook_or_value, HookLike) else external_hook_or_value # type: ignore
            internal_hook_output = OwnedHook[OHV](
                owner=self,
                value=initial_value_output,
                invalidate_callback=lambda _, k=key: self._on_output_invalidated(k),
                logger=logger
            )
            self._output_hooks[key] = internal_hook_output
            
            # Connect our internal hook to external hook if external hook is provided
            if isinstance(external_hook_or_value, HookLike):
                internal_hook_output.connect(external_hook_or_value, InitialSyncMode.USE_CALLER_VALUE) # type: ignore

    #########################################################################
    # CarriesHooks interface
    #########################################################################

    def get_hook(self, key: IHK|OHK) -> "OwnedHookLike[IHV|OHV]":
        """Get a hook by its key (either input or output)."""
        if key in self._input_hooks:
            return self._input_hooks[key] # type: ignore
        elif key in self._output_hooks:
            return self._output_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def get_input_hook(self, key: IHK) -> OwnedHook[IHV]:
        return self._input_hooks[key] # type: ignore
    
    def get_output_hook(self, key: OHK) -> OwnedHook[OHV]:
        return self._output_hooks[key] # type: ignore

    def get_hook_value_as_reference(self, key: IHK|OHK) -> IHV|OHV:
        if key in self._input_hooks:
            return self._input_hooks[key].value # type: ignore
        elif key in self._output_hooks:
            return self._output_hooks[key].value # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def get_hook_keys(self) -> set[IHK|OHK]:
        return set(self._input_hooks.keys()) | set(self._output_hooks.keys())

    def get_hook_key(self, hook_or_nexus: "HookLike[IHV|OHV]|HookNexus[IHV|OHV]") -> IHK|OHK:
        for key, hook in self._input_hooks.items():
            if hook is hook_or_nexus:
                return key
        for key, hook in self._output_hooks.items():
            if hook is hook_or_nexus:
                return key
        raise ValueError(f"Hook {hook_or_nexus} not found in hooks")

    def connect(self, hook: "HookLike[IHV|OHV]", to_key: IHK|OHK, initial_sync_mode: InitialSyncMode) -> None:
        """Connect an external hook to one of this transfer's hooks."""
        if to_key in self._input_hooks:
            self._input_hooks[to_key].connect(hook, initial_sync_mode) # type: ignore
        elif to_key in self._output_hooks:
            self._output_hooks[to_key].connect(hook, initial_sync_mode) # type: ignore
        else:
            raise ValueError(f"Key {to_key} not found in hooks")

    def disconnect(self, key: Optional[IHK|OHK]) -> None:
        """Disconnect a hook from this transfer by its key."""
        if key is None:
            # Disconnect all hooks
            for hook in list(self._input_hooks.values()) + list(self._output_hooks.values()):
                hook.disconnect()
        elif key in self._input_hooks:
            self._input_hooks[key].disconnect() # type: ignore
        elif key in self._output_hooks:
            self._output_hooks[key].disconnect() # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def is_valid_hook_value(self, hook_key: IHK|OHK, value: IHV|OHV) -> tuple[bool, str]:
        """Validate a value for a specific hook. Currently allows all values."""
        return True, "All values are always valid"

    def invalidate_hooks(self) -> tuple[bool, str]:
        """
        Handle hook invalidation (required by CarriesHooks protocol).
        
        This method is called by the hook system when any of our internal hooks are invalidated.
        Since we handle invalidation through our callback methods (_on_input_invalidated, 
        _on_output_invalidated), this method just logs that it was called.
        """
        log(self, "invalidate_hook", self._logger, True, "Successfully invalidated")
        return True, "Successfully invalidated"

    def destroy(self) -> None:
        """
        Destroy the observable by disconnecting all hooks, removing listeners, and invalidating.
        """
        self.disconnect(None)
        self.remove_all_listeners()
        self.invalidate_hooks()

    #########################################################################
    # Other private methods
    #########################################################################

    def _on_input_invalidated(self, key: IHK) -> tuple[bool, str]:
        """Called when an input hook is invalidated. Triggers forward transformation."""
        try:
            log(self, "_on_input_invalidated", self._logger, True, f"Input hook {key} invalidated, triggering forward transformation")
            self._trigger_forward_transformation()
            return True, "Forward transformation triggered successfully"
        except Exception as e:
            log(self, "_on_input_invalidated", self._logger, False, f"Error in forward transformation: {e}")
            return False, f"Error in forward transformation: {e}"
    


    def _on_output_invalidated(self, key: OHK) -> tuple[bool, str]:
        """Called when an output hook is invalidated. Triggers reverse transformation if available."""
        if self._reverse_callable is None:
            log(self, "_on_output_invalidated", self._logger, False, "Output hook invalidated but no reverse callable provided")
            return False, "No reverse callable available"
        
        try:
            log(self, "_on_output_invalidated", self._logger, True, f"Output hook {key} invalidated, triggering reverse transformation")
            self._trigger_reverse_transformation()
            return True, "Reverse transformation triggered successfully"
        except Exception as e:
            log(self, "_on_output_invalidated", self._logger, False, f"Error in reverse transformation: {e}")
            return False, f"Error in reverse transformation: {e}"
    
    def _trigger_transformation(
            self, 
            source_hooks: dict[IHK, OwnedHook[IHV]] | dict[OHK, OwnedHook[OHV]], 
            target_hooks: dict[OHK, OwnedHook[OHV]] | dict[IHK, OwnedHook[IHV]],
            transform_callable: Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]] | Callable[[Mapping[OHK, OHV]], Mapping[IHK, IHV]],
            direction: str) -> None:
        """
        Trigger transformation between source and target hooks.
        
        Args:
            source_hooks: The hooks to read values from
            target_hooks: The hooks to write values to
            transform_callable: The function to transform values
            direction: Description for logging/errors ("forward" or "reverse")
        """
        with self._lock:
            # Get current values from source hooks
            source_values: dict[IHK, IHV] | dict[OHK, OHV] = {key: hook.value for key, hook in source_hooks.items()} # type: ignore
            
            # Call transformation
            target_values: Mapping[OHK, OHV] | Mapping[IHK, IHV] = transform_callable(source_values) # type: ignore
            
            # Validate target keys
            if target_values.keys() != target_hooks.keys():
                raise ValueError(f"{direction.capitalize()} callable returned incompatible keys")
            
            # Update target hooks
            if len(target_values) == 1:
                key: OHK | IHK = next(iter(target_values.keys()))
                target_hooks[key].submit_single_value(target_values[key]) # type: ignore
            else:
                hooks_and_values: list[tuple[OwnedHookLike[IHV|OHV], IHV|OHV]] = []
                for key, value in target_values.items():
                    hooks_and_values.append((target_hooks[key], value)) # type: ignore
                OwnedHookLike[IHV|OHV].submit_multiple_values(*hooks_and_values)
            
            # Notify listeners
            self._notify_listeners()
    
    def _trigger_forward_transformation(self) -> None:
        """Trigger forward transformation (inputs → outputs)."""
        self._trigger_transformation(
            source_hooks=self._input_hooks,
            target_hooks=self._output_hooks, 
            transform_callable=self._forward_callable,
            direction="forward"
        )
    
    def _trigger_reverse_transformation(self) -> None:
        """Trigger reverse transformation (outputs → inputs)."""
        if self._reverse_callable is None:
            raise ValueError("No reverse callable available")
        
        self._trigger_transformation(
            source_hooks=self._output_hooks,
            target_hooks=self._input_hooks,
            transform_callable=self._reverse_callable,
            direction="reverse"
        )

