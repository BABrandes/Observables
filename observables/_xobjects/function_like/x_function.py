from typing import Generic, TypeVar, Optional, Mapping, Callable
from logging import Logger

from ..._hooks.owned_hook import OwnedHook
from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ..._hooks.hook_protocols.owned_full_hook_protocol import OwnedFullHookProtocol
from ..._auxiliary.listening_base import ListeningBase
from ..._carries_hooks.carries_some_hooks_base import CarriesSomeHooksBase
from ..._nexus_system.nexus import Nexus
from ..._nexus_system.update_function_values import UpdateFunctionValues
from ..._nexus_system.submission_error import SubmissionError
from .function_values import FunctionValues

SHK = TypeVar("SHK")
SHV = TypeVar("SHV")

class ObservableFunction(ListeningBase, CarriesSomeHooksBase[SHK, SHV, "ObservableFunction"], Generic[SHK, SHV]):
    """
    An observable that maintains synchronized relationships between multiple hooks using a function.

    Main Purpose:
    
    This observable ensures that multiple hooks maintain a consistent state according to a 
    custom synchronization function. When any hook changes, the function computes what other 
    hooks need to update to maintain the constraint.
    
    Example use cases:
    - Mathematical relationships: Hook A and Hook B must always sum to a constant
    - Conditional dependencies: Hook A (boolean) controls whether Hook B has a value
    - State machines: Multiple hooks representing different states that must be consistent
    - Form validation: Multiple input fields that must satisfy cross-field constraints
    
    Key Features:
    
    1. **Complete State Access**: The function receives both submitted_values (what changed) 
       and current_values (complete current state) to compute synchronized values.
    
    2. **Bidirectional Sync**: Can connect to external hooks for bidirectional data flow,
       ensuring all connected observables stay synchronized.
    
    3. **Type Safety**: Full generic type support for hook keys and values.
    
    4. **Error Handling**: Comprehensive validation with clear error messages for
       invalid callback implementations or state transitions.
    
    Example - Sum Constraint:
    
    Maintain a constraint where field1 + field2 always equals 100:
    
    ```python
    from observables import XValue, XFunction
    from observables._observables.function_like.function_values import FunctionValues
    
    def sum_function(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
        # Ensure sum is always 100
        result: dict[str, int] = {}
        
        # If field1 changed, adjust field2
        if "field1" in values.submitted:
            result["field2"] = 100 - values.submitted["field1"]
        # If field2 changed, adjust field1
        elif "field2" in values.submitted:
            result["field1"] = 100 - values.submitted["field2"]
        
        # Validate the final state using current values
        field1 = values.submitted.get("field1", values.current["field1"])
        field2 = result.get("field2", values.submitted.get("field2", values.current["field2"]))
        if field1 + field2 != 100:
            return (False, {})
        
        return (True, result)
    
    # Create the synchronized observable
    field1 = XValue(30)
    field2 = XValue(70)
    
    sync = XFunction(
        function_input_hooks={"field1": field1.hook, "field2": field2.hook},
        function_callable=sum_function
    )
    
    # Change field1 → field2 updates automatically
    field1.value = 40  # field2 becomes 60
    ```
    
    Example - Square Root Constraint:
    
    Maintain square_value = root_value^2 with domain for +/- selection:
    
    ```python
    def sqrt_function(values: FunctionValues[str, float | str]) -> tuple[bool, dict[str, float | str]]:
        result: dict[str, float | str] = {}
        
        # If root_value changed, update square and domain
        if "root_value" in values.submitted:
            root = values.submitted["root_value"]
            result["square_value"] = root * root  # type: ignore
            result["domain"] = "positive" if root >= 0 else "negative"  # type: ignore
        
        # If square_value and domain changed, compute root
        elif "square_value" in values.submitted and "domain" in values.submitted:
            square = values.submitted["square_value"]
            domain = values.submitted["domain"]
            if square < 0:  # type: ignore
                return (False, {})
            sqrt_val = square ** 0.5  # type: ignore
            result["root_value"] = -sqrt_val if domain == "negative" else sqrt_val
        
        return (True, result)
    ```
    
    The ObservableFunction ensures that whenever any connected hook changes, all hooks
    are updated to maintain the synchronized state defined by the function.
    """


    def __init__(
        self,
        complete_variables_per_key: Mapping[SHK, Hook[SHV]|ReadOnlyHook[SHV]],
        completing_function_callable: Callable[[FunctionValues[SHK, SHV]], tuple[bool, dict[SHK, SHV]]],
        logger: Optional[Logger] = None):
        """
        Initialize the ObservableFunction.

        Args:
            complete_variables_per_key: Dictionary mapping hook keys to their initial values or hooks.
                These are the hooks that will be synchronized by the function.
            completing_function_callable: The synchronization function that maintains relationships between hooks.
                Signature: (values: FunctionValues[K, V]) -> (success, synced_values)
                - values.submitted: The values that were just changed
                - values.current: The complete current state of all hooks
                - Returns: (bool indicating validity, dict of values to update)
                The function should return (False, {}) if the submitted values are invalid.
            logger: Optional logger for debugging and monitoring.
        
        Example:
            >>> def my_function(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
            ...     if 'field1' in values.submitted:
            ...         return (True, {'field2': 100 - values.submitted['field1']})
            ...     return (True, {})
        """

        self._completing_function_callable = completing_function_callable

        # Create sync hooks with initial values
        self._sync_hooks: dict[SHK, OwnedHook[SHV]] = {}
        for key, initial_value in complete_variables_per_key.items():
            sync_hook: OwnedHook[SHV] = OwnedHook[SHV](
                owner=self,
                initial_value=initial_value.value if isinstance(initial_value, ManagedHookProtocol) else initial_value, # type: ignore
                logger=logger
            )
            self._sync_hooks[key] = sync_hook

        ListeningBase.__init__(self, logger)

        def add_values_to_be_updated_callback(
            self_ref: "ObservableFunction[SHK, SHV]",
            update_values: UpdateFunctionValues[SHK, SHV]
        ) -> Mapping[SHK, SHV]:
            """
            Add values to be updated by triggering the synchronization function.
            This callback is called when any hook value changes.
            
            The function_callable receives a FunctionValues object containing both 
            submitted (what changed) and current (complete current state) values.
            """

            values_to_be_added: dict[SHK, SHV] = {}
               
            # Create FunctionValues object and call the function
            function_values = FunctionValues(submitted=update_values.submitted, current=update_values.current)
            success, synced_values = self_ref._completing_function_callable(function_values)

            if not success:
                raise ValueError(f"Function callable returned invalid values for combination {update_values.submitted}")

            # Build completed_values by merging: submitted_values, then synced_values, then current values
            completed_values: dict[SHK, SHV] = {}
            for key in self_ref._sync_hooks.keys():
                if key in update_values.submitted:
                    completed_values[key] = update_values.submitted[key] # type: ignore
                elif key in synced_values:
                    completed_values[key] = synced_values[key] # type: ignore
                else:
                    completed_values[key] = update_values.current[key] # type: ignore

            # Add all synced values to the values to be added, if they are not already in the submitted values
            for key in synced_values: # type: ignore
                if not key in update_values.submitted:
                    values_to_be_added[key] = synced_values[key] # type: ignore

            # Call the function again with completed values to validate the final state
            try:
                completed_function_values = FunctionValues(submitted=completed_values, current=completed_values)
                success, _ = self_ref._completing_function_callable(completed_function_values)
                if not success:
                    raise ValueError(f"Function callable returned invalid values for final state {completed_values}")
            except Exception as e:
                raise ValueError(f"Function callable validation failed: {e}")

            return values_to_be_added

        CarriesSomeHooksBase.__init__( # type: ignore
            self,
            logger=logger,
            invalidate_callback=None,
            validate_complete_values_in_isolation_callback=None,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback
        )

        # Connect internal hooks to external hooks if provided
        for key, external_hook_or_value in complete_variables_per_key.items():
            internal_hook = self._sync_hooks[key]
            if isinstance(external_hook_or_value, ManagedHookProtocol): # type: ignore
                internal_hook.join(external_hook_or_value, "use_caller_value") # type: ignore

    #########################################################################
    # CarriesSomeHooksBase abstract methods
    #########################################################################

    def _get_hook_by_key(self, key: SHK) -> OwnedFullHookProtocol[SHV]:
        """
        Get a hook by its key.
        
        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The hook associated with the key.
        """
        if key in self._sync_hooks:
            return self._sync_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_value_by_key(self, key: SHK) -> SHV:
        """
        Get a value by its key.

        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The value of the hook.
        """

        if key in self._sync_hooks:
            return self._sync_hooks[key].value # type: ignore
        else:
            raise ValueError(f"Key {key} not found in hooks")

    def _get_hook_keys(self) -> set[SHK]:
        """
        Get all hook keys.

        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The set of all hook keys.
        """
        return set(self._sync_hooks.keys())

    def _get_key_by_hook_or_nexus(self, hook_or_nexus: "Hook[SHV]|Nexus[SHV]") -> SHK:
        """
        Get a key by its hook or nexus.

        ** This method is not thread-safe and should only be called by internally.

        Returns:
            The key associated with the hook or nexus.
        """
        for key, hook in self._sync_hooks.items():
            if hook is hook_or_nexus:
                return key
        raise ValueError(f"Hook {hook_or_nexus} not found in hooks")

    #########################################################################
    # Public methods
    #########################################################################

    #-------------------------------- Hooks, values, and keys --------------------------------

    def hook(self, key: SHK) -> Hook[SHV]:
        """
        Get a hook by its key.

        ** Thread-safe **

        Returns:
            The hook associated with the key.
        """
        with self._lock:
            return self._get_hook_by_key(key)

    def keys(self) -> set[SHK]:
        """
        Get all hook keys.

        ** Thread-safe **

        Returns:
            The set of all hook keys.
        """
        with self._lock:
            return set(self._get_hook_keys())

    def key(self, hook: Hook[SHV]) -> SHK:
        """
        Get a key by its hook.

        ** Thread-safe **

        Returns:
            The key associated with the hook.
        """
        with self._lock:
            return self._get_key_by_hook_or_nexus(hook)

    def hooks(self) -> dict[SHK, Hook[SHV]]:
        """
        Get all hooks.

        ** Thread-safe **

        Returns:
            The dictionary of hooks.
        """
        with self._lock:
            return self._get_dict_of_hooks() # type: ignore

    def value(self, key: SHK) -> SHV:
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
    def completing_function_callable(self) -> Callable[[FunctionValues[SHK, SHV]], tuple[bool, dict[SHK, SHV]]]:
        """Get the completing function callable."""
        return self._completing_function_callable

    def change_values(self, values: Mapping[SHK, SHV]) -> None:
        """
        Change the values of the observable.
        """
        success, msg = self._submit_values(values)
        if not success:
            raise SubmissionError(msg, values)