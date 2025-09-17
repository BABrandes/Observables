import threading
from typing import Callable, Generic, Mapping, Optional, TypeVar
from logging import Logger
from .base_listening import BaseListening
from .._hooks.owned_hook_like import OwnedHookLike
from .._hooks.owned_hook import OwnedHook
from .._hooks.hook_like import HookLike
from .carries_collective_hooks import CarriesCollectiveHooks
from .hook_nexus import HookNexus
from .initial_sync_mode import InitialSyncMode
from .general import log

PHK = TypeVar("PHK")
SHK = TypeVar("SHK")
PHV = TypeVar("PHV", covariant=True)
SHV = TypeVar("SHV", covariant=True)

class BaseObservable(BaseListening, CarriesCollectiveHooks[PHK|SHK, PHV|SHV], Generic[PHK, SHK, PHV,SHV]):
    """
    Base class defining the interface for all observable objects in the library.

    This class serves as a contract that ensures all observable classes implement
    a consistent set of methods and behaviors. It enables type safety, polymorphism,
    and enables the creation of generic utilities that work with any observable type.
    
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
            act_on_invalidation_callback: Optional[Callable[[], None]] = None,
            logger: Optional[Logger] = None):
        """
        Initialize the BaseObservable.

        Args:
            component_hooks: A dictionary of component hooks.
            verification_method: A method to verify the component values.
        """

        super().__init__(logger)

        self._logger: Optional[Logger] = logger
        self._act_on_invalidation_callback: Optional[Callable[[], None]] = act_on_invalidation_callback

        self._primary_hooks: dict[PHK, OwnedHookLike[PHV]] = {}
        # Reverse lookup caches for O(1) _get_key_for operations
        self._hook_to_key_cache: dict[OwnedHookLike[PHV], PHK] = {}
        self._nexus_to_key_cache: dict[HookNexus[PHV], PHK] = {}

        initial_primary_hook_values: dict[PHK, PHV] = {}
        for key, value in initial_component_values_or_hooks.items():
            if isinstance(value, HookLike):
                initial_value: PHV = value.value # type: ignore
            else:
                initial_value = value
            initial_primary_hook_values[key] = initial_value
            # Create invalidation callback that doesn't capture 'self' in closure
            invalidation_callback = self._create_invalidation_callback(key)
            hook: OwnedHookLike[PHV] = OwnedHook(self, initial_value, invalidation_callback, logger) # type: ignore
            self._primary_hooks[key] = hook
            
            # Populate reverse lookup caches for O(1) performance
            self._hook_to_key_cache[hook] = key
            self._nexus_to_key_cache[hook.hook_nexus] = key
            
            if isinstance(value, OwnedHookLike):
                value.connect(hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore

        self._secondary_hooks: dict[SHK, OwnedHookLike[SHV]] = {}
        self._secondary_hook_callbacks: dict[SHK, Callable[[Mapping[PHK, PHV]], SHV]] = {}
        # Reverse lookup caches for secondary hooks
        self._secondary_hook_to_key_cache: dict[OwnedHookLike[SHV], SHK] = {}
        self._secondary_nexus_to_key_cache: dict[HookNexus[SHV], SHK] = {}
        
        for key, _callback in secondary_hook_callbacks.items():
            self._secondary_hook_callbacks[key] = _callback
            value = _callback(initial_primary_hook_values)
            secondary_hook: OwnedHookLike[SHV] = OwnedHook[SHV](self, value, None, logger)
            self._secondary_hooks[key] = secondary_hook
            
            # Populate secondary hook reverse lookup caches
            self._secondary_hook_to_key_cache[secondary_hook] = key
            self._secondary_nexus_to_key_cache[secondary_hook.hook_nexus] = key

        self._verification_method: Optional[Callable[[dict[PHK, PHV]], tuple[bool, str]]] = verification_method
        # Thread safety: Lock for protecting component values and hooks
        self._lock = threading.RLock()

        if self._verification_method is not None:
            success, message = self._verification_method(initial_primary_hook_values)
            if not success:
                raise ValueError(f"Verification method failed: {message}")

    #########################################################################
    # CarriesHooks interface
    #########################################################################

    def get_hook(self, key: PHK|SHK) -> OwnedHookLike[PHV|SHV]:
        if key in self._primary_hooks:
            return self._primary_hooks[key] # type: ignore
        elif key in self._secondary_hooks:
            return self._secondary_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")

    def get_hook_value_as_reference(self, key: PHK|SHK) -> PHV|SHV:
        if key in self._primary_hooks:
            return self._primary_hooks[key].value # type: ignore
        elif key in self._secondary_hooks:
            return self._secondary_hooks[key].value # type: ignore
        else:
            raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")

    def get_hook_keys(self) -> set[PHK|SHK]:
        return set(self._primary_hooks.keys()) | set(self._secondary_hooks.keys())

    def get_hook_key(self, hook_or_nexus: "OwnedHookLike[PHV|SHV]|HookNexus[PHV|SHV]") -> PHK|SHK:
        """
        Get the key for a hook using O(1) cache lookup with lazy population.
        """
        try:
            return self._get_key_for_primary_hook(hook_or_nexus)
        except ValueError:
            pass
        try:
            return self._get_key_for_secondary_hook(hook_or_nexus)
        except ValueError:
            raise ValueError(f"Hook {hook_or_nexus} not found in component_hooks or secondary_hooks")

    def connect(self, hook: HookLike[PHV|SHV], to_key: PHK|SHK, initial_sync_mode: InitialSyncMode) -> None:
        """
        Connect a hook to the observable.

        Args:
            hook: The hook to connect
            to_key: The key to connect the hook to
            initial_sync_mode: The initial synchronization mode

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """
        if to_key in self._primary_hooks:
            self._primary_hooks[to_key].connect(hook, initial_sync_mode) # type: ignore
        elif to_key in self._secondary_hooks:
            self._secondary_hooks[to_key].connect(hook, initial_sync_mode) # type: ignore
        else:
            raise ValueError(f"Key {to_key} not found in component_hooks or secondary_hooks")

    def disconnect(self, key: Optional[PHK|SHK]=None) -> None:
        """
        Disconnect a hook from the observable.

        Args:
            key: The key to disconnect the hook from

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """
        if key is None:
            for hook in self._primary_hooks.values():
                try:
                    hook.disconnect()
                except ValueError as e:
                    if "already disconnected" in str(e):
                        # Hook is already disconnected, ignore
                        pass
                    else:
                        raise
        else:
            try:
                if key in self._primary_hooks:
                    self._primary_hooks[key].disconnect() # type: ignore
                elif key in self._secondary_hooks:
                    self._secondary_hooks[key].disconnect() # type: ignore
                else:
                    raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")
            except ValueError as e:
                if "already disconnected" in str(e):
                    # Hook is already disconnected, ignore
                    pass
                else:
                    raise

    def is_valid_hook_value(self, hook_key: PHK|SHK, value: PHV|SHV) -> tuple[bool, str]:
        """
        Check if the value is valid.

        Args:
            hook_key: The key of the hook to check
            value: The value to check

        Returns:
            A tuple containing a boolean indicating if the value is valid and a string explaining why
        """
        if self._verification_method is None:
            return True, "No verification method provided. Default is True"
        else:
            # Check if the key corresponds to a secondary hook
            if hook_key in self._secondary_hooks:
                # Secondary hooks don't need validation since they're computed from component values
                return True, "Secondary hooks are always valid as they're computed values"
            
            # Must be a primary hook
            return self._verification_method({hook_key: value}) # type: ignore

    def invalidate_hooks(self) -> tuple[bool, str]:
        """
        Invalidate the the values of the component hooks.

        Args:
            keys: The keys of the component hooks to invalidate.
            hooks_not_to_invalidate: The hooks to not invalidate (The validity of the values will still be checked!)
        """

        if self._act_on_invalidation_callback is not None:
            try:
                self._act_on_invalidation_callback()
            except Exception as e:
                log(self, "invalidate", self._logger, False, f"Error in the act_on_invalidation_callback: {e}")
                raise ValueError(f"Error in the act_on_invalidation_callback: {e}")
        self._notify_listeners()
        log(self, "invalidate", self._logger, True, "Successfully invalidated")
        return True, "Successfully invalidated"

    def destroy(self) -> None:
        """
        Destroy the observable by disconnecting all hooks, removing listeners, and invalidating.
        
        This method should be called before the observable is deleted to ensure proper
        memory cleanup and prevent memory leaks. After calling this method, the observable
        should not be used anymore as it will be in an invalid state.
        
        Example:
            >>> obs = ObservableSingleValue("test")
            >>> obs.cleanup()  # Properly clean up before deletion
            >>> del obs
        """
        self.disconnect(None)
        self.remove_all_listeners()

    #########################################################################
    # CarriesCollectiveHooks interface
    #########################################################################

    def get_collective_hook_keys(self) -> set[PHK|SHK]:
        """
        Get the collective hooks for the observable.
        """
        return set(self._primary_hooks.keys()) | set(self._secondary_hooks.keys())

    def connect_multiple_hooks(self, hooks: Mapping[PHK|SHK, HookLike[PHV|SHV]], initial_sync_mode: InitialSyncMode) -> None:
        """
        Attach multiple hooks to the observable.

        Args:
            hooks: A mapping of keys to hooks
            initial_sync_mode: The initial synchronization mode

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """

        hook_pairs: list[tuple[HookLike[PHV|SHV], HookLike[PHV|SHV]]] = []
        for key, hook in hooks.items():
            if key in self._primary_hooks:
                hook_of_observable = self._primary_hooks[key] # type: ignore
            elif key in self._secondary_hooks:
                hook_of_observable = self._secondary_hooks[key] # type: ignore
            else:
                raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")
            match initial_sync_mode:
                case InitialSyncMode.USE_CALLER_VALUE:
                    hook_pairs.append((hook_of_observable, hook)) # type: ignore
                case InitialSyncMode.USE_TARGET_VALUE:
                    hook_pairs.append((hook, hook_of_observable)) # type: ignore
                case _: # type: ignore
                    raise ValueError(f"Invalid initial sync mode: {initial_sync_mode}")
        HookNexus[PHV|SHV].connect_hook_pairs(*hook_pairs)

    def is_valid_hook_values(self, values: Mapping[PHK|SHK, PHV|SHV]) -> tuple[bool, str]: # type: ignore
        """
        Check if the values are valid.
        """
        if self._verification_method is None:
            return True, "No verification method provided. Default is True"
        else:
            dict_of_values: Mapping[PHK, PHV] = self._get_primary_values_as_references()
            # Check if any of the keys correspond to secondary hooks
            for key, value in values.items():
                if key in self._secondary_hooks:
                    # Secondary hooks don't need validation since they're computed from component values
                    return True, "Secondary hooks are always valid as they're computed values"
            
            for key, value in values.items():
                dict_of_values[key] = value # type: ignore
            return self._verification_method(dict_of_values) # type: ignore

    #########################################################################
    # Other private methods
    #########################################################################

    def _update_hook_cache(self, hook: HookLike[PHV|SHV], old_nexus: Optional[HookNexus[PHV|SHV]] = None) -> None:
        """
        Update the reverse lookup cache when a hook's nexus changes.
        
        This method should be called whenever a hook gets a new nexus
        (e.g., during binding operations).
        """
        # Find the key for this hook
        key = None
        for k, h in self._primary_hooks.items():
            if h is hook:
                key = k
                break
        
        if key is not None:
            # Update component hook caches
            if old_nexus is not None:
                # Remove old nexus from cache
                self._nexus_to_key_cache.pop(old_nexus, None) # type: ignore
            # Add new nexus to cache
            self._nexus_to_key_cache[hook.hook_nexus] = key # type: ignore
            return
        
        # Check secondary hooks
        for k, h in self._secondary_hooks.items():
            if h is hook:
                key = k
                break
        
        if key is not None:
            # Update secondary hook caches
            if old_nexus is not None:
                # Remove old nexus from cache
                self._secondary_nexus_to_key_cache.pop(old_nexus, None) # type: ignore
            # Add new nexus to cache
            self._secondary_nexus_to_key_cache[hook.hook_nexus] = key # type: ignore

    def _update_secondary_hooks(self) -> None:
        """
        Update all secondary hooks by recomputing their values from current component values.
        
        This method is called whenever component values change to ensure secondary hooks
        stay synchronized with the current state.
        """
        if not self._secondary_hooks:
            return
            
        current_component_values = self._get_primary_values_as_references()
        
        for key, callback in self._secondary_hook_callbacks.items():
            try:
                new_value = callback(current_component_values)
                secondary_hook = self._secondary_hooks[key]
                
                # Only update if the value actually changed to avoid unnecessary notifications
                if secondary_hook.value != new_value:
                    secondary_hook.submit_single_value(new_value)
                    
            except Exception as e:
                log(self, "update_secondary_hooks", self._logger, False, f"Error updating secondary hook '{key}': {e}")
                # Continue with other secondary hooks even if one fails
                
        log(self, "update_secondary_hooks", self._logger, True, "Successfully updated secondary hooks")

    def _set_component_values(self, dict_of_values: dict[PHK, PHV], notify_binding_system: bool) -> None:
        """
        Set the values of the component values.

        Args:
            dict_of_values: A dictionary of (key, value) pairs to set
            notify_binding_system: Whether to notify the binding system. If False, the binding system will not be notified and the values will not be invalidated (Use for updates from the binding system)

        Raises:
            ValueError: If the verification method fails
        """

        log(self, "_set_component_values", self._logger, True, f"Setting component values: {dict_of_values}")

        with self._lock:
            if len(self._primary_hooks) == 0:
                error_msg = "No component hooks provided"
                log(self, "set_component_values", self._logger, False, error_msg)
                raise ValueError(error_msg)
            
            future_component_values: dict[PHK, PHV] = {key: hook.value for key, hook in self._primary_hooks.items()}
            
            for key, value in dict_of_values.items():
                if key not in self._primary_hooks:
                    error_msg = f"Key {key} not found in component_values"
                    log(self, "set_component_values", self._logger, False, error_msg)
                    raise ValueError(error_msg)
                future_component_values[key] = value
            
            if self._verification_method is not None:
                success, message = self._verification_method(future_component_values)
                if not success:
                    error_msg = f"Verification method failed: {message}"
                    log(self, "set_component_values", self._logger, False, error_msg)
                    raise ValueError(error_msg)

            if notify_binding_system:
                if len(dict_of_values) == 1:
                    key, value = next(iter(dict_of_values.items()))
                    hook = self._primary_hooks[key]
                    hook.submit_single_value(value)
                else:
                    OwnedHookLike[PHV|SHV].submit_multiple_values(*list(zip(self._primary_hooks.values(), dict_of_values.values())))

            # Update secondary hooks after component values have changed
            self._update_secondary_hooks()

            log(self, "set_component_values", self._logger, True, "Successfully set component values")

    def _get_key_for_primary_hook(self, hook_or_nexus: OwnedHookLike[PHV|SHV]|HookNexus[PHV|SHV]) -> PHK:
        """
        Get the key for a hook using O(1) cache lookup with lazy population.
        """
        if isinstance(hook_or_nexus, HookNexus):
            # Try cached lookup first
            key = self._nexus_to_key_cache.get(hook_or_nexus) # type: ignore
            if key is not None:
                return key
                
            # Cache miss - do linear search and populate cache
            for k, h in self._primary_hooks.items():
                if h.hook_nexus is hook_or_nexus:
                    # Update cache for future O(1) lookups
                    self._nexus_to_key_cache[hook_or_nexus] = k # type: ignore
                    return k
            raise ValueError(f"Hook nexus {hook_or_nexus} not found in component_hooks")
        else:
            # Try cached lookup first
            key = self._hook_to_key_cache.get(hook_or_nexus) # type: ignore
            if key is not None:
                return key
                
            # Cache miss - do linear search and populate cache
            for k, h in self._primary_hooks.items():
                if h is hook_or_nexus:
                    # Update cache for future O(1) lookups
                    self._hook_to_key_cache[hook_or_nexus] = k # type: ignore
                    return k
            raise ValueError(f"Hook {hook_or_nexus} not found in component_hooks")
        
    def _get_key_for_secondary_hook(self, hook_or_nexus: OwnedHookLike[PHV|SHV]|HookNexus[PHV|SHV]) -> SHK:
        """
        Get the key for an secondary hook using O(1) cache lookup with lazy population.
        """
        if isinstance(hook_or_nexus, HookNexus):
            # Try cached lookup first
            key = self._secondary_nexus_to_key_cache.get(hook_or_nexus) # type: ignore
            if key is not None:
                return key
                
            # Cache miss - do linear search and populate cache
            for k, h in self._secondary_hooks.items():
                if h.hook_nexus is hook_or_nexus:
                    # Update cache for future O(1) lookups
                    self._secondary_nexus_to_key_cache[hook_or_nexus] = k # type: ignore
                    return k
            raise ValueError(f"Hook nexus {hook_or_nexus} not found in secondary_hooks")
        else:
            # Try cached lookup first
            key = self._secondary_hook_to_key_cache.get(hook_or_nexus) # type: ignore
            if key is not None:
                return key
                
            # Cache miss - do linear search and populate cache
            for k, h in self._secondary_hooks.items():
                if h is hook_or_nexus:
                    # Update cache for future O(1) lookups
                    self._secondary_hook_to_key_cache[hook_or_nexus] = k # type: ignore
                    return k
            raise ValueError(f"Hook {hook_or_nexus} not found in secondary_hooks")

    def _verify_state(self) -> tuple[bool, str]:
        """
        Verify the state of the observable.
        """
        if self._verification_method is None:
            return True, "No verification method provided. Default is True"
        return self._verification_method(self.primary_values)

    def _get_primary_values_as_references(self) -> Mapping[PHK, PHV]:
        """
        Get the values of the primary component hooks as references.

        This method can be used for serializing the observable.

        ** The returned values are references, so modifying them will modify the observable.
        Use with caution.

        Returns:
            A dictionary of keys to values
        """

        primary_values: dict[PHK, PHV] = {}
        for key, hook in self._primary_hooks.items():
            primary_values[key] = hook.value # type: ignore

        return primary_values

    def _create_invalidation_callback(self, key: PHK) -> Callable[["HookLike[PHV]"], tuple[bool, str]]:
        """
        Create an invalidation callback for a specific key without circular references.
        
        Uses a bound method approach to avoid closure-based circular references.
        """
        # Create a wrapper class to avoid capturing 'self' in a closure
        class InvalidationCallback:
            def __init__(self, observable: "BaseObservable[PHK, SHK, PHV, SHV]", hook_key: PHK):
                import weakref
                self._observable_ref = weakref.ref(observable)
                self._key = hook_key
            
            def __call__(self, hook: "HookLike[PHV]") -> tuple[bool, str]:
                observable = self._observable_ref()
                if observable is None:
                    return False, "Observable was garbage collected"
                return observable.invalidate_hooks()
        
        return InvalidationCallback(self, key)

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