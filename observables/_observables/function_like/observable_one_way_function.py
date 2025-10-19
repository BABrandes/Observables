"""
ObservableOneWayFunction Module - Simplified One-Way Transformation

This module provides the ObservableOneWayFunction class, a simplified observable that acts as a 
one-way transformation layer from multiple input hooks to multiple output hooks.

The ObservableOneWayFunction is designed for scenarios where you need to:
- Transform values from multiple input sources to multiple output destinations
- Implement complex calculations that depend on multiple observable values
- Create derived values that automatically update when their dependencies change
- One-way data flow only (no reverse transformation)

Key Features:
- Multiple input trigger hooks for dependency management
- Multiple output hooks for result distribution
- Forward transformation only (inputs → outputs) via callable
- Automatic transformation triggering through add_values_to_be_updated_callback
- Type-safe generic implementation with named components
- Thread-safe operations with RLock protection
- Full BaseCarriesHooks interface with hook management support

Architecture:
The class extends BaseListening and BaseCarriesHooks[IHK|OHK] and manages:
- Input trigger hooks: Named hooks that trigger forward transformation when changed
- Output hooks: Named hooks that receive transformed values (read-only from external perspective)
- Forward callable: Function that computes outputs from inputs
- add_values_to_be_updated_callback: Handles transformation logic

Use Cases:
1. **Computed Properties**: Calculate derived values from base observables
2. **Data Formatting**: Transform raw data to display format
3. **Validation Results**: Compute validation state from input fields
4. **Mathematical Operations**: Calculate results from multiple inputs
5. **Business Logic**: Derive business state from multiple values

Example Usage:
    >>> from observables import XValue, XOneWayFunction
    >>> 
    >>> # Temperature conversion example
    >>> celsius = XValue(0.0)
    >>> 
    >>> temp_converter = XOneWayFunction(
    ...     function_input_hooks={"celsius": celsius.hook},
    ...     function_output_hook_keys={"fahrenheit", "kelvin"},
    ...     function_callable=lambda inputs: {
    ...         "fahrenheit": inputs["celsius"] * 9/5 + 32,
    ...         "kelvin": inputs["celsius"] + 273.15
    ...     }
    ... )
    >>> 
    >>> # When celsius changes, fahrenheit and kelvin update automatically
    >>> celsius.value = 100.0
    >>> print(temp_converter.get_output_hook("fahrenheit").value)  # 212.0
    >>> print(temp_converter.get_output_hook("kelvin").value)     # 373.15

Performance Characteristics:
- O(1) for hook access operations
- Transformation performance depends on the provided callable
- Thread-safe operations for concurrent access
- Atomic updates using the hook system
"""

from typing import Callable, Generic, Mapping, Optional, TypeVar
from logging import Logger

from ..._hooks.owned_hook import OwnedHook
from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._hooks.hook_protocols.managed_hook import ManagedHookProtocol
from ..._auxiliary.listening_base import ListeningBase
from ..._carries_hooks.carries_hooks_base import CarriesHooksBase
from ..._nexus_system.nexus import Nexus
from ..._nexus_system.update_function_values import UpdateFunctionValues

# Type variables for input and output hook names and values
IHK = TypeVar("IHK")  # Input Hook Keys
OHK = TypeVar("OHK")  # Output Hook Keys
IHV = TypeVar("IHV")  # Input Hook Values
OHV = TypeVar("OHV")  # Output Hook Values


class ObservableOneWayFunction(ListeningBase, CarriesHooksBase[IHK|OHK, IHV|OHV, "ObservableOneWayFunction"], Generic[IHK, OHK, IHV, OHV]):
    """
    An observable that transforms values from input hooks to output hooks (one-way only).
    
    This class acts as a one-way transformation layer that:
    - Manages multiple named input hooks
    - Manages multiple named output hooks  
    - Automatically triggers function transformation when input hooks change
    - Uses add_values_to_be_updated_callback for transformation logic
    - Provides thread-safe operations with RLock protection
    
    **IMPORTANT - Complete Value Sets:**
    The function_callable is ALWAYS called with complete sets of values.
    When a hook value changes, the callable receives:
    - The new (submitted) value for changed keys
    - The current (existing) value for unchanged keys
    This ensures transformations always have all required inputs available.
    
    **One-Way Flow:**
    Unlike ObservableTransfer, this class does NOT support reverse transformations.
    Output hooks are managed internally and should not be modified externally
    (though they can be read or connected to other observables).
    """

    def __init__(
        self,
        input_variables_per_key: Mapping[IHK, Hook[IHV]|ReadOnlyHook[IHV]],
        one_way_function_callable: Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]],
        function_output_hook_keys: set[OHK],
        logger: Optional[Logger] = None
    ):
        """
        Initialize the ObservableOneWayFunction.

        Args:
            function_input_hooks: Dictionary mapping input names to their hooks.
                When any of these hooks change, the function transformation is triggered.
                All keys that the function_callable expects must be present in this dict.
            function_callable: Function that transforms input values to output values.
                Expected signature: (input_values: Mapping[IHK, IHV]) -> Mapping[OHK, OHV]
                Must return a dict with keys matching function_output_hook_keys.
                **IMPORTANT**: This callable is ALWAYS called with a COMPLETE set of input values,
                combining submitted (changed) values with current (unchanged) values.
            function_output_hook_keys: Set of output hook keys.
                All keys that the function_callable returns must be present in this set.
            logger: Optional logger for debugging and monitoring transformations.
        
        Note:
            Internal hooks are created for both inputs and outputs:
            - Input hooks are connected to external hooks if provided
            - Output hooks are managed internally and updated by the function_callable
            This ensures all keys have corresponding hooks for the CarriesHooks interface.

        Example:
            >>> from observables import XValue, XOneWayFunction
            >>> 
            >>> # Calculate area and perimeter from width and height
            >>> width = XValue(5.0)
            >>> height = XValue(3.0)
            >>> 
            >>> rectangle = XOneWayFunction(
            ...     function_input_hooks={"width": width.hook, "height": height.hook},
            ...     function_output_hook_keys={"area", "perimeter"},
            ...     function_callable=lambda inputs: {
            ...         "area": inputs["width"] * inputs["height"],
            ...         "perimeter": 2 * (inputs["width"] + inputs["height"])
            ...     }
            ... )
            >>> 
            >>> # width and height changes trigger automatic updates to area and perimeter
            >>> width.value = 10.0
            >>> # area and perimeter are automatically recalculated
        """

        self._one_way_function_callable: Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]] = one_way_function_callable

        self._input_hooks: dict[IHK, OwnedHook[IHV]] = {}
        self._output_hooks: dict[OHK, OwnedHook[OHV]] = {}

        # Create input hooks for all keys, connecting to external hooks when provided
        for key, external_hook_or_value in input_variables_per_key.items():
            # Create internal hook
            initial_value_input: IHV = external_hook_or_value.value if isinstance(external_hook_or_value, ManagedHookProtocol) else external_hook_or_value # type: ignore
            internal_hook_input: OwnedHook[IHV] = OwnedHook(
                owner=self,
                initial_value=initial_value_input,
                logger=logger
            )
            self._input_hooks[key] = internal_hook_input

        # Create output hooks for all keys
        output_values: dict[OHK, OHV] = self._one_way_function_callable(self.get_input_values()) # type: ignore
        for key in function_output_hook_keys:
            if key not in output_values:
                raise ValueError(f"Function callable must return all output keys. Missing key: {key}")
            internal_hook_output: OwnedHook[OHV] = OwnedHook(
                owner=self,
                initial_value=output_values[key],
                logger=logger
            )
            self._output_hooks[key] = internal_hook_output

        ListeningBase.__init__(self, logger)

        def add_values_to_be_updated_callback(
            self_ref: "ObservableOneWayFunction[IHK, OHK, IHV, OHV]",
            update_values: UpdateFunctionValues[IHK|OHK, IHV|OHV]
        ) -> Mapping[IHK|OHK, IHV|OHV]:
            """
            Add values to be updated by triggering the function transformation.
            This callback is called when any hook value changes.
            
            NOTE: The function_callable is ALWAYS called with COMPLETE sets of values
            by merging update_values.submitted (changed keys) with update_values.current (unchanged keys).
            This ensures transformations always have all required inputs available.
            """

            values_to_be_added: dict[IHK|OHK, IHV|OHV] = {}

            # Check if any input values changed - if so, trigger function transformation
            input_keys = set(input_variables_per_key.keys())
            if any(key in update_values.submitted for key in input_keys):
                # Trigger function transformation

                # Use submitted values for changed keys, current values for unchanged keys
                input_values: dict[IHK, IHV] = {}
                for key in input_keys:
                    if key in update_values.submitted:
                        input_values[key] = update_values.submitted[key] # type: ignore
                    else:
                        input_values[key] = update_values.current[key] # type: ignore
                
                # Call function callable with complete input values
                output_values: Mapping[OHK, OHV] = one_way_function_callable(input_values)
                
                # Add all output values to be updated
                values_to_be_added.update(output_values) # type: ignore

            # Remove values that are already in the submitted values
            for key in update_values.submitted:
                values_to_be_added.pop(key, None)

            return values_to_be_added

        CarriesHooksBase.__init__( # type: ignore
            self,
            logger=logger,
            invalidate_callback=None,
            validate_complete_values_in_isolation_callback=None,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback
        )

        # Connect internal input hooks to external hooks if provided
        for key, external_hook_or_value in input_variables_per_key.items():
            internal_hook_input = self._input_hooks[key]
            if isinstance(external_hook_or_value, ManagedHookProtocol): # type: ignore
                internal_hook_input.connect_hook(external_hook_or_value, "use_caller_value") # type: ignore

    #########################################################################
    # CarriesHooksBase abstract methods
    #########################################################################

    def _get_hook_by_key(self, key: IHK|OHK) -> OwnedHook[IHV|OHV]:
        """
        Get a hook by its key.

        ** This method is not thread-safe and should only be called by the get_hook method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Args:
            key: The key of the hook to get

        Returns:
            The hook associated with the key
        """

        if key in self._input_hooks:
            return self._input_hooks[key] # type: ignore
        elif key in self._output_hooks:
            return self._output_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_value_by_key(self, key: IHK|OHK) -> IHV|OHV:
        """
        Get a value as a copy by its key.

        ** This method is not thread-safe and should only be called by the get_value_of_hook method.

        ** Must be implemented by subclasses to provide efficient lookup for values.

        Args:
            key: The key of the hook to get the value of
        """

        if key in self._input_hooks:
            return self._input_hooks[key].value # type: ignore
        elif key in self._output_hooks:
            return self._output_hooks[key].value # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_hook_keys(self) -> set[IHK|OHK]:
        """
        Get all keys of the hooks.

        ** This method is not thread-safe and should only be called by the get_hook_keys method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Returns:
            The set of keys for the hooks
        """

        return set(self._input_hooks.keys()) | set(self._output_hooks.keys())

    def _get_key_by_hook_or_nexus(self, hook_or_nexus: Hook[IHV|OHV]|Nexus[IHV|OHV]) -> IHK|OHK:
        """
        Get the key for a hook or nexus.

        ** This method is not thread-safe and should only be called by the get_hook_key method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Args:
            hook_or_nexus: The hook or nexus to get the key for

        Returns:
            The key for the hook or nexus
        """

        for key, hook in self._input_hooks.items():
            if hook is hook_or_nexus:
                return key
        for key, hook in self._output_hooks.items():
            if hook is hook_or_nexus:
                return key
        raise ValueError(f"Hook {hook_or_nexus} not found in hooks")


    #########################################################################
    # Public API
    #########################################################################

    #-------------------------------- Hooks, values, and keys --------------------------------

    def hook(self, key: IHK|OHK) -> Hook[IHV|OHV]:
        """
        Get a hook by its key.

        ** Thread-safe **

        Returns:
            The hook associated with the key.
        """
        with self._lock:
            return self._get_hook_by_key(key)

    def keys(self) -> set[IHK|OHK]:
        """
        Get all hook keys.

        ** Thread-safe **

        Returns:
            The set of all hook keys.
        """
        with self._lock:
            return set(self._get_hook_keys())

    def hooks(self) -> dict[IHK|OHK, Hook[IHV|OHV]]:
        """
        Get all hooks.

        ** Thread-safe **

        Returns:
            The dictionary of hooks.
        """
        with self._lock:
            return self._get_dict_of_hooks() # type: ignore

    def value(self, key: IHK|OHK) -> IHV|OHV:
        """
        Get a value by its key.

        ** Thread-safe **

        Returns:
            The value of the hook.
        """
        with self._lock:
            return self._get_value_by_key(key)

    #-------------------------------- Functionality --------------------------------

    @property
    def function_callable(self) -> Callable[[Mapping[IHK, IHV]], Mapping[OHK, OHV]]:
        """Get the function callable."""
        return self._one_way_function_callable

    def input_variable_keys(self) -> set[IHK]:
        """Get the input variable keys."""
        with self._lock:
            return set(self._input_hooks.keys())
