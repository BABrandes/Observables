from typing import Generic, TypeVar, Optional, Mapping, Callable
from logging import Logger
from .._hooks.owned_hook import OwnedHook
from .._hooks.hook_like import HookLike
from .._hooks.owned_hook_like import OwnedHookLike
from .._utils.base_listening import BaseListening
from .._utils.base_carries_hooks import BaseCarriesHooks
from .._utils.hook_nexus import HookNexus

SHK = TypeVar("SHK")
OHK = TypeVar("OHK")
SHV = TypeVar("SHV")
OHV = TypeVar("OHV")

class ObservableSync(BaseListening, BaseCarriesHooks[SHK|OHK, SHV|OHV, "ObservableSync"], Generic[SHK, OHK, SHV, OHV]):
    """
    A specialized observable that maintains synchronized state across multiple hooks with validation.

    Main Purpose - Synchronization:
    
    This observable ensures that a set of hooks maintain synchronized state according to a 
    user-defined callback function. The sync_values_callback defines the relationship between
    the hooks and is validated with every possible combination of values during initialization.
    
    Example use cases:
    - Conditional dependencies: Hook A (boolean) controls whether Hook B has a value
    - Mathematical relationships: Hook A and Hook B must always sum to a constant
    - State machines: Multiple hooks representing different states that must be consistent
    - Form validation: Multiple input fields that must satisfy cross-field constraints
    
    Secondary Purpose - Output Transformation:
    
    Based on the synchronized values, this observable can generate derived output values
    through an optional output_values_callback. These output hooks are read-only and
    automatically update when the sync values change.
    
    Example use cases:
    - Computed fields: Display calculated values based on input fields
    - Status indicators: Show overall system state derived from multiple components
    - Aggregations: Sum, average, or other statistics from multiple inputs
    
    Key Features:
    
    1. **Robust Validation**: The sync_values_callback is tested with every possible
       combination of the provided initial values (A, AB, AC, B, BC, C, ABC for 3 values).
       This ensures the callback handles all valid states correctly.
    
    2. **Initial Value Safety**: The observable starts with the provided initial values
       and validates that they form a valid state according to the sync callback.
    
    3. **External Integration**: After initialization, external hooks can be connected
       to the internal sync hooks for bidirectional data flow.
    
    4. **Type Safety**: Full generic type support for sync keys/values and output keys/values.
    
    5. **Error Handling**: Comprehensive validation with clear error messages for
       invalid callback implementations or state transitions.
    
    Usage Pattern:
    
    ```python
    # Define how values should be synchronized
    def sync_callback(values: Mapping[str, int]) -> Mapping[str, int]:
        # Ensure sum is always 100
        current_sum = sum(values.values())
        if current_sum != 100:
            # Adjust first value to make sum 100
            first_key = next(iter(values.keys()))
            return {**values, first_key: 100 - sum(v for k, v in values.items() if k != first_key)}
        return values
    
    # Define output transformation
    def output_callback(values: Mapping[str, int]) -> Mapping[str, str]:
        return {
            "status": f"Sum: {sum(values.values())}",
            "count": f"Fields: {len(values)}"
        }
    
    # Create synchronized observable
    sync = ObservableSync(
        sync_values_initially_valid={"field1": 30, "field2": 70},
        sync_values_callback=sync_callback,
        output_values_callback=output_callback
    )
    
    # Connect to external observables
    external_field1.connect_hook(sync._get_sync_hook("field1"), InitialSyncMode.USE_CALLER_VALUE)
    external_field2.connect_hook(sync._get_sync_hook("field2"), InitialSyncMode.USE_CALLER_VALUE)
    ```
    
    The ObservableSync ensures that whenever any connected hook changes, all hooks
    are updated to maintain the synchronized state defined by the callback.
    """


    def __init__(
        self,
        sync_values_initially_valid: Mapping[SHK, SHV],
        sync_values_callback: Callable[[Mapping[SHK, SHV], Mapping[SHK, SHV]], Mapping[SHK, SHV]],
        output_values_callback: Optional[Callable[[Mapping[SHK, SHV]], Mapping[OHK, OHV]]] = None,
        logger: Optional[Logger] = None):
        """
        Args:
            sync_values_initially_valid: The initial values for the sync hooks
            sync_values_callback: The callback that defines the relationship between the sync hooks (It takes "current_values" and "submitted_values")
            output_values_callback: The callback that defines the relationship between the sync hooks and the output hooks (It takes "synced_values")
            logger: The logger to use
        """

        self._sync_values_callback = sync_values_callback
        self._output_hook_callback = output_values_callback

        # Validate sync_values_callback with every combination of given values
        self._validate_sync_callback_with_combinations(sync_values_initially_valid, sync_values_callback)

        # Create sync hooks with initial values
        self._sync_hooks: dict[SHK, OwnedHook[SHV]] = {}
        for key, initial_value in sync_values_initially_valid.items():
            sync_hook: OwnedHook[SHV] = OwnedHook[SHV](
                owner=self,
                initial_value=initial_value, # type: ignore
                logger=logger
            )
            self._sync_hooks[key] = sync_hook


        # Create output hooks
        self._output_hooks: dict[OHK, OwnedHook[OHV]] = {}
        
        if output_values_callback is not None:
            # Validate output callback first
            try:
                output_hook_values: Mapping[OHK, OHV] = output_values_callback(sync_values_initially_valid)
            except Exception as e:
                raise ValueError(f"Output callback validation failed: {e}")
            
            # Create output hooks
            for key, value in output_hook_values.items():
                output_hook: OwnedHook[OHV] = OwnedHook[OHV](
                    owner=self,
                    initial_value=value,
                    logger=logger
                )
                self._output_hooks[key] = output_hook

        BaseListening.__init__(self, logger)

        def add_values_to_be_updated_callback(
            self_ref: "ObservableSync[SHK, OHK, SHV, OHV]",
            current_values: Mapping[SHK|OHK, SHV|OHV],
            submitted_values: Mapping[SHK|OHK, SHV|OHV]
        ) -> Mapping[SHK|OHK, SHV|OHV]:
            """
            Add values to be updated by triggering transformations.
            This callback is called when any hook value changes.
            """

            values_to_be_added: dict[SHK|OHK, SHV|OHV] = {}

            ########### SYNC PART ###########

            # Merge current values with submitted values to get complete state
            # Only include sync hook values, not output hook values
            complete_values: dict[SHK, SHV] = {}
            for key in self_ref._sync_hooks.keys():
                if key in submitted_values:
                    complete_values[key] = submitted_values[key] # type: ignore
                elif key in current_values:
                    complete_values[key] = current_values[key] # type: ignore

            # First, perform the sync values callback with complete values
            synced_values: Mapping[SHK, SHV] = self_ref._sync_values_callback(current_values, complete_values) # type: ignore

            # Check that ALL sync hook values are in the synced values
            if len(synced_values) != len(self_ref._sync_hooks):
                raise ValueError(f"Synced values {synced_values} do not have the same length as the sync hooks {self_ref._sync_hooks}")
            for key in self_ref._sync_hooks.keys():
                if key not in synced_values:
                    raise ValueError(f"Key {key} not found in synced values")

            # Now add all synced values to the values to be added, if they are not already in the submitted values
            for key in synced_values:
                if not key in submitted_values:
                    values_to_be_added[key] = synced_values[key] # type: ignore

            ########### OUTPUT PART ###########

            # Call the output hook callback using the synced values
            if self_ref._output_hook_callback is not None:
                output_values: Mapping[OHK, OHV] = self_ref._output_hook_callback(synced_values)
            else:
                output_values = {}

            # Check that ALL output hook values are in the output values
            if len(output_values) != len(self_ref._output_hooks):
                raise ValueError(f"Output values {output_values} do not have the same length as the output hooks {self_ref._output_hooks}")
            for key in self_ref._output_hooks.keys():
                if key not in output_values:
                    raise ValueError(f"Key {key} not found in output values")

            # Now add all output values to the values to be added
            for key in output_values:
                values_to_be_added[key] = output_values[key] # type: ignore 

            return values_to_be_added

        BaseCarriesHooks.__init__( # type: ignore
            self,
            logger=logger,
            invalidate_callback=None,
            validate_complete_values_in_isolation_callback=None,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback
        )

        # Apply output values to hooks if present
        if self._output_hook_callback is not None:
            output_values = self._output_hook_callback(sync_values_initially_valid)
            for key, value in output_values.items():
                self._output_hooks[key].submit_value(value)

    def _validate_sync_callback_with_combinations(self, sync_values_initially_valid: Mapping[SHK, SHV], sync_values_callback: Callable[[Mapping[SHK, SHV], Mapping[SHK, SHV]], Mapping[SHK, SHV]]) -> None:
        """
        Validate the sync_values_callback with every combination of given values.
        For example, if 3 values are synced (A, B, C), it tests A, AB, AC, B, BC, C, ABC.
        This ensures a valid state from the beginning, assuming sync_values_callback is correct.
        """
        import itertools
        
        keys = list(sync_values_initially_valid.keys())
        
        # Test every possible combination of keys (excluding empty set)
        for r in range(1, len(keys) + 1):  # Start from 1, not 0
            for combination in itertools.combinations(keys, r):
                # Create a subset of values for this combination
                test_values = {key: sync_values_initially_valid[key] for key in combination}
                
                try:
                    # Test the sync callback with this combination
                    result = sync_values_callback(sync_values_initially_valid, test_values)
                    
                    # Validate that the result has the same keys as input
                    if set(result.keys()) != set(test_values.keys()):
                        raise ValueError(f"Sync callback returned different keys for combination {combination}: expected {set(test_values.keys())}, got {set(result.keys())}")
                        
                except Exception as e:
                    raise ValueError(f"Sync callback validation failed for combination {combination}: {e}")

    #########################################################################
    # BaseCarriesHooks abstract methods
    #########################################################################

    def _get_hook(self, key: SHK|OHK) -> "OwnedHookLike[SHV|OHV]":
        """Get a hook by its key (either input or output)."""
        if key in self._sync_hooks:
            return self._sync_hooks[key] # type: ignore
        elif key in self._output_hooks:
            return self._output_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_value_reference_of_hook(self, key: SHK|OHK) -> SHV|OHV:
        if key in self._sync_hooks:
            return self._sync_hooks[key].value # type: ignore
        elif key in self._output_hooks:
            return self._output_hooks[key].value # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_hook_keys(self) -> set[SHK|OHK]:
        return set(self._sync_hooks.keys()) | set(self._output_hooks.keys())

    def _get_hook_key(self, hook_or_nexus: "HookLike[SHV|OHV]|HookNexus[SHV|OHV]") -> SHK|OHK:
        for key, hook in self._sync_hooks.items():
            if hook is hook_or_nexus:
                return key
        for key, hook in self._output_hooks.items():
            if hook is hook_or_nexus:
                return key
        raise ValueError(f"Hook {hook_or_nexus} not found in hooks")

    #########################################################################
    # Other private methods
    #########################################################################

    def get_sync_hook(self, key: SHK) -> OwnedHook[SHV]:
        return self._sync_hooks[key] # type: ignore
    
    def get_output_hook(self, key: OHK) -> OwnedHook[OHV]:
        return self._output_hooks[key] # type: ignore

    def get_sync_keys(self) -> set[SHK]:
        return set(self._sync_hooks.keys())
    
    def get_output_keys(self) -> set[OHK]:
        return set(self._output_hooks.keys())

    def get_sync_hooks(self) -> dict[SHK, OwnedHook[SHV]]:
        return self._sync_hooks.copy() # type: ignore
    
    def get_output_hooks(self) -> dict[OHK, OwnedHook[OHV]]:
        return self._output_hooks.copy() # type: ignore