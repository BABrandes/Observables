from typing import Generic, TypeVar, Optional, Mapping, Callable
from logging import Logger
from .._hooks.owned_hook import OwnedHook
from .._hooks.hook_like import HookLike
from .._hooks.owned_hook_like import OwnedHookLike
from .._utils.base_listening import BaseListening
from .._utils.base_carries_hooks import BaseCarriesHooks
from .._utils.hook_nexus import HookNexus

SHK = TypeVar("SHK")
SHV = TypeVar("SHV")

class ObservableSync(BaseListening, BaseCarriesHooks[SHK, SHV, "ObservableSync"], Generic[SHK, SHV]):
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
    
    Key Features:
    
    1. **Robust Validation**: The sync_values_callback is tested with every possible
       combination of the provided initial values (A, AB, AC, B, BC, C, ABC for 3 values).
       This ensures the callback handles all valid states correctly.
    
    2. **Initial Value Safety**: The observable starts with the provided initial values
       and validates that they form a valid state according to the sync callback.
    
    3. **External Integration**: After initialization, external hooks can be connected
       to the internal sync hooks for bidirectional data flow.
    
    4. **Type Safety**: Full generic type support for sync keys and values.
    
    5. **Error Handling**: Comprehensive validation with clear error messages for
       invalid callback implementations or state transitions.
    
    Showcase Example - Square Root Constraint:
    
    A powerful demonstration of ObservableSync maintaining a mathematical constraint
    where square_value = root_value^2 and domain distinguishes +/- sqrt(x) solutions:
    
    ```python
    def sync_callback(submitted_values: Mapping[str, float | str]) -> tuple[bool, dict[str, float | str]]:
        # Maintain constraint: square_value = root_value^2
        result: dict[str, float | str] = {}
        root = submitted_values.get("root_value")
        square = submitted_values.get("square_value")
        domain = submitted_values.get("domain")
        
        # When all values present, validate consistency
        if all(k in submitted_values for k in ["root_value", "square_value", "domain"]):
            if abs(square - root * root) > 1e-10:
                return (False, {})  # Inconsistent
            expected_domain = "positive" if root >= 0 else "negative"
            if domain != expected_domain:
                return (False, {})
            return (True, {})  # All consistent
        
        # If root_value changed, update square and domain
        if "root_value" in submitted_values:
            result["square_value"] = root * root
            result["domain"] = "positive" if root >= 0 else "negative"
        
        # If square_value and domain changed together, compute root
        elif "square_value" in submitted_values and "domain" in submitted_values:
            if square < 0:
                return (False, {})
            sqrt_val = square ** 0.5
            result["root_value"] = -sqrt_val if domain == "negative" else sqrt_val
        
        return (True, result)
    
    # Create the synchronized observable
    sync = ObservableSync[str, float | str](
        sync_values_initially_valid={
            "square_value": 4.0,
            "root_value": 2.0,
            "domain": "positive"
        },
        sync_values_callback=sync_callback
    )
    
    # Change root → square and domain update automatically
    sync.get_sync_hook("root_value").submit_value(-5.0)
    # Result: square_value=25.0, root_value=-5.0, domain="negative"
    
    # Change square with domain → root updates with correct sign
    sync.submit_values({"square_value": 49.0, "domain": "negative"})
    # Result: square_value=49.0, root_value=-7.0, domain="negative"
    ```
    
    Basic Usage Pattern:
    
    ```python
    # Define how values should be synchronized
    def sync_callback(values: Mapping[str, int]) -> tuple[bool, dict[str, int]]:
        # Ensure sum is always 100
        current_sum = sum(values.values())
        if current_sum != 100:
            # Adjust first value to make sum 100
            first_key = next(iter(values.keys()))
            adjusted = {**values, first_key: 100 - sum(v for k, v in values.items() if k != first_key)}
            return (True, adjusted)
        return (True, dict(values))
    
    # Create synchronized observable
    sync = ObservableSync(
        sync_values_initially_valid={"field1": 30, "field2": 70},
        sync_values_callback=sync_callback
    )
    
    # Connect to external observables
    external_field1.connect_hook(sync.get_sync_hook("field1"), InitialSyncMode.USE_CALLER_VALUE)
    external_field2.connect_hook(sync.get_sync_hook("field2"), InitialSyncMode.USE_CALLER_VALUE)
    ```
    
    The ObservableSync ensures that whenever any connected hook changes, all hooks
    are updated to maintain the synchronized state defined by the callback.
    """


    def __init__(
        self,
        sync_values_initially_valid: Mapping[SHK, SHV],
        sync_values_callback: Callable[[Mapping[SHK, SHV]], tuple[bool, dict[SHK, SHV]]],
        logger: Optional[Logger] = None):
        """
        Args:
            sync_values_initially_valid: The initial values for the sync hooks
            sync_values_callback: The callback that defines the relationship between the sync hooks (It takes "submitted_values"). It should return a tuple with a boolean indicating if the value combination is valid and a dict of synched values. It will be completed by the ObservableSync. If it is not valid, it should return (False, Any).
            logger: The logger to use
        """

        self._sync_values_callback = sync_values_callback

        # Validate sync_values_callback with every combination of given values
        success, message = self._validate_sync_callback_with_combinations(sync_values_initially_valid, sync_values_callback)
        if not success:
            raise ValueError(f"Sync callback validation failed: {message}")

        # Create sync hooks with initial values
        self._sync_hooks: dict[SHK, OwnedHook[SHV]] = {}
        for key, initial_value in sync_values_initially_valid.items():
            sync_hook: OwnedHook[SHV] = OwnedHook[SHV](
                owner=self,
                initial_value=initial_value, # type: ignore
                logger=logger
            )
            self._sync_hooks[key] = sync_hook

        BaseListening.__init__(self, logger)

        def add_values_to_be_updated_callback(
            self_ref: "ObservableSync[SHK, SHV]",
            current_values: Mapping[SHK, SHV],
            submitted_values: Mapping[SHK, SHV]
        ) -> Mapping[SHK, SHV]:
            """
            Add values to be updated by triggering transformations.
            This callback is called when any hook value changes.
            """

            values_to_be_added: dict[SHK, SHV] = {}

            # First, perform the sync values callback with submitted values
            success, synced_values = self_ref._sync_values_callback(submitted_values) # type: ignore
            if not success:
                raise ValueError(f"Sync callback returned invalid values for combination {submitted_values}")

            # Build completed_values by merging: submitted_values, then synced_values, then current values
            completed_values: dict[SHK, SHV] = {}
            for key in self_ref._sync_hooks.keys():
                if key in submitted_values:
                    completed_values[key] = submitted_values[key] # type: ignore
                elif key in synced_values:
                    completed_values[key] = synced_values[key] # type: ignore
                else:
                    completed_values[key] = current_values[key] # type: ignore

            # Now add all synced values to the values to be added, if they are not already in the submitted values
            for key in synced_values:
                if not key in submitted_values:
                    values_to_be_added[key] = synced_values[key] # type: ignore

            # Call the sync values callback with the completed values to check if it is valid
            try:
                success, _ = self_ref._sync_values_callback(completed_values)
                if not success:
                    raise ValueError(f"Sync callback returned invalid values for combination {completed_values}")
            except Exception as e:
                raise ValueError(f"Sync callback validation failed: {e}")

            return values_to_be_added

        BaseCarriesHooks.__init__( # type: ignore
            self,
            logger=logger,
            invalidate_callback=None,
            validate_complete_values_in_isolation_callback=None,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback
        )

    def _validate_sync_callback_with_combinations(self, sync_values_to_be_validated: Mapping[SHK, SHV], sync_values_callback: Callable[[Mapping[SHK, SHV]], tuple[bool, dict[SHK, SHV]]]) -> tuple[bool, str]:
        """
        Validate the sync_values_callback with every combination of given values.
        For example, if 3 values are synced (A, B, C), it tests A, AB, AC, B, BC, C, ABC.
        This ensures a valid state from the beginning, assuming sync_values_callback is correct.
        """
        import itertools
        
        keys = list(sync_values_to_be_validated.keys())
        
        # Test every possible combination of keys (excluding empty set)
        for r in range(1, len(keys) + 1):  # Start from 1, not 0
            for combination in itertools.combinations(keys, r):
                # Create a subset of values for this combination
                test_values = {key: sync_values_to_be_validated[key] for key in combination}
                
                try:
                    # Get the result of the sync callback
                    success, result_values = sync_values_callback(test_values)

                    if not success:
                        return False, f"Sync callback returned invalid values for combination {combination}"

                    # Complete the result with the values that are not in the result
                    for key in sync_values_to_be_validated:
                        if key not in result_values:
                            result_values[key] = sync_values_to_be_validated[key]
                    
                    # Validate that the result has the same keys as input
                    if result_values != sync_values_to_be_validated:
                        return False, f"Sync callback returned different keys for combination {combination}: expected {sync_values_to_be_validated}, got {result_values}"
                        
                except Exception:
                    return False, f"Sync callback validation failed for combination {combination}"

        return True, "Sync callback validation passed for all combinations"

    #########################################################################
    # BaseCarriesHooks abstract methods
    #########################################################################

    def _get_hook(self, key: SHK) -> "OwnedHookLike[SHV]":
        """Get a hook by its key."""
        if key in self._sync_hooks:
            return self._sync_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_value_reference_of_hook(self, key: SHK) -> SHV:
        if key in self._sync_hooks:
            return self._sync_hooks[key].value # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_hook_keys(self) -> set[SHK]:
        return set(self._sync_hooks.keys())

    def _get_hook_key(self, hook_or_nexus: "HookLike[SHV]|HookNexus[SHV]") -> SHK:
        for key, hook in self._sync_hooks.items():
            if hook is hook_or_nexus:
                return key
        raise ValueError(f"Hook {hook_or_nexus} not found in hooks")

    #########################################################################
    # Public methods
    #########################################################################

    def get_sync_hook(self, key: SHK) -> OwnedHook[SHV]:
        return self._sync_hooks[key] # type: ignore

    def get_sync_keys(self) -> set[SHK]:
        return set(self._sync_hooks.keys())

    def get_sync_hooks(self) -> dict[SHK, OwnedHook[SHV]]:
        return self._sync_hooks.copy() # type: ignore