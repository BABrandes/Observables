from typing import Callable, Generic, Mapping, Optional, TypeVar, Any
from logging import Logger
from .._hooks.owned_hook_like import OwnedHookLike
from .._hooks.owned_hook import OwnedHook
from .._hooks.hook_like import HookLike
from .hook_nexus import HookNexus
from .base_carries_hooks import BaseCarriesHooks
from .general import log
from .nexus_manager import NexusManager
from .default_nexus_manager import DEFAULT_NEXUS_MANAGER
from .base_listening import BaseListening


PHK = TypeVar("PHK")
SHK = TypeVar("SHK")
PHV = TypeVar("PHV", covariant=True)
SHV = TypeVar("SHV", covariant=True)
O = TypeVar("O", bound="BaseObservable[Any, Any, Any, Any, Any]")

class BaseObservable(BaseListening, BaseCarriesHooks[PHK|SHK, PHV|SHV, O], Generic[PHK, SHK, PHV, SHV, O]):
    """
    Base class for all observable objects in the new hook-based architecture.

    This class combines BaseListening and BaseCarriesHooks to provide the complete
    interface for observables in the new architecture. It replaces the old binding
    system with a more flexible hook-based approach.
    
    **New Architecture Features:**
    - **Hook Management**: Manages primary and secondary hooks for different purposes
    - **Value Submission**: Uses submit_values() with NexusManager for synchronization
    - **Custom Logic**: Supports add_values_to_be_updated_callback and validation callbacks
    - **Listener Support**: Integrates with BaseListening for change notifications
    
    **Purpose:**
    The BaseObservable class provides a standardized interface that allows different
    observable types (ObservableEnum, ObservableDict, ObservableList, etc.) to be
    used interchangeably in generic contexts while maintaining type safety.
    
    **Benefits:**
    - **Type Safety**: Enables static type checking and IDE support
    - **Polymorphism**: Allows functions to accept any observable type
    - **Consistency**: Guarantees all observables have the same core interface
    - **Extensibility**: Enables class-based features and utilities
    
    **Usage Examples:**
    
    1. **Generic Collections:**
        from typing import List
        from observables import BaseObservable

        def process_observables(obs_list: List[BaseObservable]) -> None:
            for obs in obs_list:
                # All observables implement the same interface
                obs.add_listener(lambda: print("Changed!"))
    
    2. **Class-Based Functions:**
        def create_binding(source: BaseObservable, target: BaseObservable) -> None:
            # Works with any observable type
            source.bind_to_observable(target)
    
    3. **Type-Safe Factories:**
        T = TypeVar('T', bound=BaseObservable)
        
        def create_observable(obs_type: Type[T], *args, **kwargs) -> T:
            return obs_type(*args, **kwargs)
    
    **Implementation Notes:**
    - This class is currently a marker class (empty) but may be extended
      with required methods in future versions
    - All observable classes in the library implement this class
    - The class enables structural typing in Python's type system
    
    **Future Considerations:**
    As the library evolves, this class may be extended to include:
    - Required method signatures for core observable operations
    - Common property definitions
    - Standard event handling interfaces
    - Performance optimization hints
    
    **Related Classes:**
    - ObservableEnum: Observable wrapper for enum values
    - ObservableDict: Observable wrapper for dictionaries
    - ObservableList: Observable wrapper for lists
    - ObservableSet: Observable wrapper for sets
    - ObservableSingleValue: Observable wrapper for single values
    - ObservableSelectionOption: Observable wrapper for selection options
    """

    def __init__(
            self,
            initial_component_values_or_hooks: Mapping[PHK, PHV|HookLike[PHV]],
            verification_method: Optional[Callable[[Mapping[PHK, PHV]], tuple[bool, str]]] = None,
            secondary_hook_callbacks: Mapping[SHK, Callable[[Mapping[PHK, PHV]], SHV]] = {},
            add_values_to_be_updated_callback: Optional[Callable[[O, Mapping[PHK, PHV], Mapping[PHK, PHV]], Mapping[PHK, PHV]]] = None,
            invalidate_callback: Optional[Callable[[], None]] = None,
            logger: Optional[Logger] = None,
            nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER):
        """
        Initialize the BaseObservable.

        Args:
            component_hooks: A dictionary of component hooks.
            verification_method: A method to verify the component values.
        """

        #-------------------------------- Initialization start --------------------------------

        # Initialize fields
        self._primary_hooks: dict[PHK, OwnedHookLike[PHV]] = {}
        self._secondary_hooks: dict[SHK, OwnedHookLike[SHV]] = {}
        self._secondary_values: dict[SHK, SHV] = {}
        """Just to ensure that the secondary values cannot be modified from outside. They can be different, but only within the nexus manager's equality check. These values are never used for anything else."""

        # Eager Caching
        self._primary_hook_keys = set(initial_component_values_or_hooks.keys())
        self._secondary_hook_keys = set(secondary_hook_callbacks.keys())

        # Some checks:
        if self._primary_hook_keys & self._secondary_hook_keys:
            raise ValueError("Primary hook keys and secondary hook keys must be disjoint")

        # Initialize the BaseListening
        BaseListening.__init__(self, logger)

        #--------------------------------Initialize BaseCarriesHooks--------------------------------

        def internal_invalidate_callback(self_ref: O) -> tuple[bool, str]:
            if invalidate_callback is not None:
                try:
                    invalidate_callback()
                except Exception as e:
                    log(self_ref, "invalidate", self_ref._logger, False, f"Error in the act_on_invalidation_callback: {e}")
                    raise ValueError(f"Error in the act_on_invalidation_callback: {e}")
            log(self_ref, "invalidate", self_ref._logger, True, "Successfully invalidated")
            return True, "Successfully invalidated"

        def internal_validation_in_isolation_callback(self_ref: O, values: Mapping[PHK|SHK, PHV|SHV]) -> tuple[bool, str]:
            if verification_method is None:
                return True, "No verification method provided. Default is True"
            else:
                primary_values_dict: dict[PHK, PHV] = self_ref.primary_values.copy()
                for key, value in values.items():
                    if key in self_ref._primary_hooks:
                        primary_values_dict[key] = value # type: ignore
                    elif key in self_ref._secondary_hooks:
                        # Check if internal secondary values are equal to the values
                        if not self_ref.nexus_manager.is_equal(self_ref._secondary_values[key], value):
                            return False, f"Internal secondary value for key {key} ( {self_ref._secondary_values[key]} ) is not equal to the submitted value {value}"
                    else:
                        raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")
                success, msg = verification_method(primary_values_dict)
                return success, msg

        def internal_add_values_to_be_updated_callback(self_ref: O, current_values: Mapping[PHK|SHK, PHV|SHV], submitted_values: Mapping[PHK|SHK, PHV|SHV]) -> Mapping[PHK|SHK, PHV|SHV]:
            # Step 1: Complete the primary values
            primary_values: dict[PHK, PHV] = {}
            for key, hook in self_ref._primary_hooks.items():
                if key in submitted_values:
                    primary_values[key] = submitted_values[key] # type: ignore
                else:
                    primary_values[key] = hook.value

            # Step 2: Generate additionally values if add_values_to_be_updated_callback is provided
            if add_values_to_be_updated_callback is not None:
                current_values_only_primary: Mapping[PHK, PHV] = {}
                for key, value in current_values.items():
                    if key in self_ref._primary_hook_keys:
                        current_values_only_primary[key] = value # type: ignore
                submitted_values_only_primary: Mapping[PHK, PHV] = {}
                for key, value in submitted_values.items():
                    if key in self_ref._primary_hook_keys:
                        submitted_values_only_primary[key] = value # type: ignore

                additional_primary_values = add_values_to_be_updated_callback(self_ref, current_values_only_primary, submitted_values_only_primary)
                if self_ref._secondary_hook_keys & additional_primary_values.keys():
                    raise ValueError(f"Additional values keys must be disjoint with secondary hook keys")

                primary_values.update(additional_primary_values)

            # Step 3: Generate the secondary values
            additional_values: dict[PHK|SHK, PHV|SHV] = {}
            for key in self_ref._secondary_hooks.keys():
                value = self_ref._secondary_hook_callbacks[key](primary_values)
                self_ref._secondary_values[key] = value
                additional_values[key] = value

            # Step 4: Return the additional values
            return additional_values
        
        BaseCarriesHooks.__init__( # type: ignore
            self,
            logger=logger,
            invalidate_callback=internal_invalidate_callback,
            validate_complete_values_in_isolation_callback=internal_validation_in_isolation_callback,
            add_values_to_be_updated_callback=internal_add_values_to_be_updated_callback,
            nexus_manager=nexus_manager
        )

        #-------------------------------- Set inital end --------------------------------

        initial_primary_hook_values: dict[PHK, PHV] = {}
        for key, value in initial_component_values_or_hooks.items():

            if isinstance(value, HookLike):
                initial_value: PHV = value.value # type: ignore
            else:
                initial_value = value

            initial_primary_hook_values[key] = initial_value
            hook: OwnedHookLike[PHV] = OwnedHook(self, initial_value, logger, nexus_manager) # type: ignore
            self._primary_hooks[key] = hook
            
            if isinstance(value, OwnedHookLike):
                value.connect_hook(hook, "value", "use_target_value") # type: ignore

        self._secondary_hook_callbacks: dict[SHK, Callable[[Mapping[PHK, PHV]], SHV]] = {}
        for key, _callback in secondary_hook_callbacks.items():
            self._secondary_hook_callbacks[key] = _callback
            value = _callback(initial_primary_hook_values)
            self._secondary_values[key] = value
            secondary_hook: OwnedHookLike[SHV] = OwnedHook[SHV](self, value, logger, nexus_manager)
            self._secondary_hooks[key] = secondary_hook

        #-------------------------------- Initialize finished --------------------------------

    #########################################################################
    # BaseCarriesHooks abstract methods implementation
    #########################################################################

    def _get_hook(self, key: PHK|SHK) -> OwnedHookLike[PHV|SHV]:
        
        if key in self._primary_hooks:
            return self._primary_hooks[key] # type: ignore
        elif key in self._secondary_hooks:
            return self._secondary_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")

    def _get_value_reference_of_hook(self, key: PHK|SHK) -> PHV|SHV:
        if key in self._primary_hooks:
            return self._primary_hooks[key].value # type: ignore
        elif key in self._secondary_hooks:
            return self._secondary_hooks[key].value # type: ignore
        else:
            raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")

    def _get_hook_keys(self) -> set[PHK|SHK]:
        return set(self._primary_hooks.keys()) | set(self._secondary_hooks.keys())

    def _get_hook_key(self, hook_or_nexus: "OwnedHookLike[PHV|SHV]|HookNexus[PHV|SHV]") -> PHK|SHK:
        """
        Get the key for a hook or nexus.

        Args:
            hook_or_nexus: The hook or nexus to get the key for

        Returns:
            The key for the hook or nexus

        Raises:
            ValueError: If the hook or nexus is not found in component_hooks or secondary_hooks
        """
        if isinstance(hook_or_nexus, HookNexus):
            for key, hook in self._primary_hooks.items():
                if hook.hook_nexus == hook_or_nexus:
                    return key
            for key, hook in self._secondary_hooks.items():
                if hook.hook_nexus == hook_or_nexus:
                    return key
            raise ValueError(f"Hook {hook_or_nexus} not found in component_hooks or secondary_hooks")
        elif isinstance(hook_or_nexus, OwnedHookLike): # type: ignore
            for key, hook in self._primary_hooks.items():
                if hook == hook_or_nexus:
                    return key
            for key, hook in self._secondary_hooks.items():
                if hook == hook_or_nexus:
                    return key
            raise ValueError(f"Hook {hook_or_nexus} not found in component_hooks or secondary_hooks")
        else:
            raise ValueError(f"Hook {hook_or_nexus} not found in component_hooks or secondary_hooks")

    #########################################################################
    # Other private methods
    #########################################################################

    def _get_key_for_primary_hook(self, hook_or_nexus: OwnedHookLike[PHV|SHV]|HookNexus[PHV|SHV]) -> PHK:
        """
        Get the key for a hook using O(1) cache lookup with lazy population.
        """
        for key, hook in self._primary_hooks.items():
            if hook == hook_or_nexus or hook.hook_nexus == hook_or_nexus:
                return key
        raise ValueError(f"Hook {hook_or_nexus} is not a primary hook!")

    def _get_key_for_secondary_hook(self, hook_or_nexus: OwnedHookLike[PHV|SHV]|HookNexus[PHV|SHV]) -> SHK:
        """
        Get the key for an secondary hook using O(1) cache lookup with lazy population.
        """
        for key, hook in self._secondary_hooks.items():
            if hook == hook_or_nexus or hook.hook_nexus == hook_or_nexus:
                return key
        raise ValueError(f"Hook {hook_or_nexus} is not a secondary hook!")

        primary_values: dict[PHK, PHV] = {}
        for key, hook in self._primary_hooks.items():
            primary_values[key] = hook.value # type: ignore

        return primary_values

    #########################################################################
    # Other public methods
    #########################################################################

    @property
    def primary_hooks(self) -> dict[PHK, OwnedHookLike[PHV]]:
        """
        Get the primary hooks of the observable.
        """
        return self._primary_hooks.copy()
    
    @property
    def secondary_hooks(self) -> dict[SHK, OwnedHookLike[SHV]]:
        """
        Get the secondary hooks of the observable.
        """
        return self._secondary_hooks.copy()

    @property
    def primary_values(self) -> dict[PHK, PHV]:
        """
        Get the values of the primary component hooks as a dictionary.
        """
        return {key: hook.value for key, hook in self._primary_hooks.items()}
    
    @property
    def secondary_values(self) -> dict[SHK, SHV]:
        """
        Get the values of the secondary component hooks as a dictionary.
        """
        return {key: hook.value for key, hook in self._secondary_hooks.items()}

    @property
    def primary_hook_keys(self) -> set[PHK]:
        """
        Get the keys of the primary component hooks.
        """
        return self._primary_hook_keys

    @property
    def secondary_hook_keys(self) -> set[SHK]:
        """
        Get the keys of the secondary component hooks.
        """
        return self._secondary_hook_keys