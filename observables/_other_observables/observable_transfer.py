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

from typing import Any, Callable, Generic, Mapping, Optional, TypeVar
from logging import Logger
from threading import RLock

from .._utils.initial_sync_mode import InitialSyncMode

from .._utils.hook import Hook, HookLike
from .._utils.base_listening import BaseListening
from .._utils.carries_hooks import CarriesHooks
from .._utils.hook_nexus import HookNexus
from .._utils.general import log


# Type variables for input and output hook names
IHK = TypeVar("IHK")  # Input Hook Keys
OHK = TypeVar("OHK")  # Output Hook Keys


class ObservableTransfer(BaseListening, CarriesHooks[IHK|OHK], Generic[IHK, OHK]):
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
        input_trigger_hooks: Mapping[IHK, HookLike[Any]],
        output_trigger_hooks: Mapping[OHK, HookLike[Any]],
        forward_callable: Callable[[Mapping[IHK, Any]], Mapping[OHK, Any]],
        reverse_callable: Optional[Callable[[Mapping[OHK, Any]], Mapping[IHK, Any]]] = None,
        logger: Optional[Logger] = None
    ):
        """
        Initialize the ObservableTransfer.

        Args:
            input_trigger_hooks: Dictionary mapping input names to their hooks.
                When any of these hooks are invalidated, forward transformation is triggered.
            output_trigger_hooks: Dictionary mapping output names to their hooks.
                When any of these hooks are invalidated, reverse transformation is triggered (if available).
            forward_callable: Function that transforms input values to output values.
                Expected signature: (input_values: Mapping[IHK, Any]) -> Mapping[OHK, Any]
                Must return a dict with keys matching output_trigger_hooks keys.
            reverse_callable: Optional function that transforms output values to input values.
                Expected signature: (output_values: Mapping[OHK, Any]) -> Mapping[IHK, Any]
                Must return a dict with keys matching input_trigger_hooks keys.
            logger: Optional logger for debugging and monitoring transformations.

        Example:
            >>> # Mathematical transformation
            >>> x_hook = Hook(owner=some_owner, value=5)
            >>> y_hook = Hook(owner=some_owner, value=3)
            >>> sum_hook = Hook(owner=some_owner, value=0)
            >>> product_hook = Hook(owner=some_owner, value=0)
            >>> 
            >>> transfer = ObservableTransfer(
            ...     input_trigger_hooks={"x": x_hook, "y": y_hook},
            ...     output_trigger_hooks={"sum": sum_hook, "product": product_hook},
            ...     forward_callable=lambda inputs: {
            ...         "sum": inputs["x"] + inputs["y"],
            ...         "product": inputs["x"] * inputs["y"]
            ...     }
            ... )
            >>> 
            >>> # When x_hook or y_hook values change, sum_hook and product_hook are automatically updated
        """
        
        # Initialize base classes
        super().__init__(logger)
        
        self._forward_callable: Callable[[Mapping[IHK, Any]], Mapping[OHK, Any]] = forward_callable
        self._reverse_callable: Optional[Callable[[Mapping[OHK, Any]], Mapping[IHK, Any]]] = reverse_callable
        self._lock: RLock = RLock()
        self._logger: Optional[Logger] = logger
        
        # Create internal hooks that mirror the external hooks
        # These internal hooks will have invalidation callbacks that trigger our transformations
        self._input_hooks: dict[IHK, Hook[Any]] = {}
        self._output_hooks: dict[OHK, Hook[Any]] = {}
        
        # Create input hooks and connect them to external hooks
        for key, external_hook in input_trigger_hooks.items():
            # Create internal hook with invalidation callback
            internal_hook: Hook[Any] = Hook(
                owner=self,
                value=external_hook.value,
                invalidate_callback=lambda _, k=key: self._on_input_invalidated(k),
                logger=logger
            )
            self._input_hooks[key] = internal_hook
            # Connect external hook to our internal hook so we get notified of changes
            external_hook.connect_to(internal_hook, InitialSyncMode.PUSH_TO_TARGET)
        
        # Create output hooks and connect them to external hooks  
        for key, external_hook in output_trigger_hooks.items():
            # Create internal hook with invalidation callback
            internal_hook: Hook[Any] = Hook(
                owner=self,
                value=external_hook.value,
                invalidate_callback=lambda _, k=key: self._on_output_invalidated(k),
                logger=logger
            )
            self._output_hooks[key] = internal_hook
            # Connect our internal hook to external hook for pushing results
            internal_hook.connect_to(external_hook, InitialSyncMode.PUSH_TO_TARGET)

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
            source_hooks: dict[IHK, Hook[Any]] | dict[OHK, Hook[Any]], 
            target_hooks: dict[OHK, Hook[Any]] | dict[IHK, Hook[Any]],
            transform_callable: Callable[[Mapping[IHK, Any]], Mapping[OHK, Any]] | Callable[[Mapping[OHK, Any]], Mapping[IHK, Any]],
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
            source_values: dict[IHK, Any] | dict[OHK, Any] = {key: hook.value for key, hook in source_hooks.items()} # type: ignore
            
            # Call transformation
            target_values: Mapping[OHK, Any] | Mapping[IHK, Any] = transform_callable(source_values) # type: ignore
            
            # Validate target keys
            if target_values.keys() != target_hooks.keys():
                raise ValueError(f"{direction.capitalize()} callable returned incompatible keys")
            
            # Update target hooks
            if len(target_values) == 1:
                key: OHK | IHK = next(iter(target_values.keys())) # type: ignore
                value: Any = target_values[key] # type: ignore
                target_hooks[key].value = value # type: ignore
            else:
                nexus_and_values: dict[HookNexus[Any], Any] = {}
                for key, value in target_values.items():
                    nexus: HookNexus[Any] = target_hooks[key].hook_nexus # type: ignore
                    nexus_and_values[nexus] = value
                HookNexus.submit_multiple_values(nexus_and_values)
            
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

    @property
    def hooks(self) -> set["HookLike[Any]"]:
        """Get all hooks (input and output) managed by this transfer."""
        hooks: set["HookLike[Any]"] = set(self._input_hooks.values()) | set(self._output_hooks.values()) # type: ignore
        return hooks

    def get_hook(self, key: IHK|OHK) -> "HookLike[Any]":
        """Get a hook by its key (either input or output)."""
        if key in self._input_hooks:
            return self._input_hooks[key] # type: ignore
        elif key in self._output_hooks:
            return self._output_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def attach(self, hook: "HookLike[Any]", to_key: IHK|OHK, initial_sync_mode: InitialSyncMode) -> None:
        """Attach an external hook to one of this transfer's hooks."""
        if to_key in self._input_hooks:
            self._input_hooks[to_key].connect_to(hook, initial_sync_mode) # type: ignore
        elif to_key in self._output_hooks:
            self._output_hooks[to_key].connect_to(hook, initial_sync_mode) # type: ignore
        else:
            raise ValueError(f"Key {to_key} not found in hooks")

    def detach(self, key: Optional[IHK|OHK]) -> None:
        """Detach a hook from this transfer by its key."""
        if key is None:
            # Detach all hooks
            for hook in list(self._input_hooks.values()) + list(self._output_hooks.values()):
                hook.detach()
        elif key in self._input_hooks:
            self._input_hooks[key].detach() # type: ignore
        elif key in self._output_hooks:
            self._output_hooks[key].detach() # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _is_valid_value(self, hook: "HookLike[Any]", value: Any) -> tuple[bool, str]:
        """Validate a value for a specific hook. Currently allows all values."""
        return True, "All values are always valid"

    def _invalidate_hooks(self, hooks: set["HookLike[Any]"]) -> None:
        """
        Handle hook invalidation (required by CarriesHooks protocol).
        
        This method is called by the hook system when any of our internal hooks are invalidated.
        Since we handle invalidation through our callback methods (_on_input_invalidated, 
        _on_output_invalidated), this method just logs that it was called.
        """
        log(self, "_invalidate_hooks", self._logger, True, f"Invalidated {len(hooks)} hooks (handled by callbacks)")




