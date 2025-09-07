import threading
from typing import Any, Callable, Generic, Mapping, Optional, TypeVar, final
from logging import Logger
from .base_listening import BaseListening
from .hook import Hook, HookLike
from .carries_collective_hooks import CarriesCollectiveHooks
from .hook_nexus import HookNexus
from .initial_sync_mode import InitialSyncMode
from .general import log

HK = TypeVar("HK")
EHK = TypeVar("EHK")

class BaseObservable(BaseListening, CarriesCollectiveHooks[HK|EHK], Generic[HK, EHK]):
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
            initial_component_values_or_hooks: Mapping[HK, Any|HookLike[Any]],
            verification_method: Optional[Callable[[Mapping[HK, Any]], tuple[bool, str]]] = None,
            secondary_hook_callbacks: Mapping[EHK, Callable[[Mapping[HK, Any]], Any]] = {},
            logger: Optional[Logger] = None):
        """
        Initialize the BaseObservable.

        Args:
            component_hooks: A dictionary of component hooks.
            verification_method: A method to verify the component values.
        """

        super().__init__(logger)

        self._logger: Optional[Logger] = logger

        self._primary_hooks: dict[HK, HookLike[Any]] = {}
        # Reverse lookup caches for O(1) _get_key_for operations
        self._hook_to_key_cache: dict[HookLike[Any], HK] = {}
        self._nexus_to_key_cache: dict[HookNexus[Any], HK] = {}
        
        for key, value in initial_component_values_or_hooks.items():
            if isinstance(value, HookLike):
                initial_value = value.value
            else:
                initial_value = value
            # Create invalidation callback that doesn't capture 'self' in closure
            invalidation_callback = self._create_invalidation_callback(key)
            hook: HookLike[Any] = Hook(self, initial_value, invalidation_callback, logger)
            self._primary_hooks[key] = hook
            
            # Populate reverse lookup caches for O(1) performance
            self._hook_to_key_cache[hook] = key
            self._nexus_to_key_cache[hook.hook_nexus] = key
            
            if isinstance(value, HookLike):
                value.connect(hook, InitialSyncMode.USE_TARGET_VALUE)

        self._secondary_hooks: dict[EHK, HookLike[Any]] = {}
        self._secondary_hook_callbacks: dict[EHK, Callable[[Mapping[HK, Any]], Any]] = {}
        # Reverse lookup caches for secondary hooks
        self._secondary_hook_to_key_cache: dict[HookLike[Any], EHK] = {}
        self._secondary_nexus_to_key_cache: dict[HookNexus[Any], EHK] = {}
        
        for key, callback in secondary_hook_callbacks.items():
            self._secondary_hook_callbacks[key] = callback
            value = callback(initial_component_values_or_hooks)
            secondary_hook: HookLike[Any] = Hook(self, value, None, logger)
            self._secondary_hooks[key] = secondary_hook
            
            # Populate secondary hook reverse lookup caches
            self._secondary_hook_to_key_cache[secondary_hook] = key
            self._secondary_nexus_to_key_cache[secondary_hook.hook_nexus] = key

        self._verification_method: Optional[Callable[[dict[HK, Any]], tuple[bool, str]]] = verification_method
        # Thread safety: Lock for protecting component values and hooks
        self._lock = threading.RLock()

        if self._verification_method is not None:
            success, message = self._verification_method(initial_component_values_or_hooks)
            if not success:
                raise ValueError(f"Verification method failed: {message}")

    def _create_invalidation_callback(self, key: HK) -> Callable[["HookLike[Any]"], tuple[bool, str]]:
        """
        Create an invalidation callback for a specific key without circular references.
        
        Uses a bound method approach to avoid closure-based circular references.
        """
        # Create a wrapper class to avoid capturing 'self' in a closure
        class InvalidationCallback:
            def __init__(self, observable: "BaseObservable[Any, Any]", hook_key: HK):
                import weakref
                self._observable_ref = weakref.ref(observable)
                self._key = hook_key
            
            def __call__(self, hook: "HookLike[Any]") -> tuple[bool, str]:
                observable = self._observable_ref()
                if observable is None:
                    return False, "Observable was garbage collected"
                return observable._invalidate({self._key})
        
        return InvalidationCallback(self, key)

    def _invalidate(self, keys: set[HK]) -> tuple[bool, str]:
        """
        Invalidate the the values of the component hooks of the given keys.

        Args:
            keys: The keys of the component hooks to invalidate.
        """
        try:
            self._act_on_invalidation(keys)
        except Exception as e:
            log(self, "invalidate", self._logger, False, f"Error in act_on_invalidation: {e}")
            raise ValueError(f"Error in act_on_invalidation: {e}")
        self._notify_listeners()
        log(self, "invalidate", self._logger, True, "Successfully invalidated")
        return True, "Successfully invalidated"

    def _invalidate_hooks(self, hooks: set[HookLike[Any]]) -> None: # type: ignore
        """
        Invalidate the hooks.
        """
        keys: set[HK] = set()
        for hook in hooks:
            key = self._get_key_for(hook)
            keys.add(key)
        self._invalidate(keys)

        log(self, "invalidate_hooks", self._logger, True, "Successfully invalidated hooks")

    def _act_on_invalidation(self, keys: set[HK]) -> None:
        """
        Act on the invalidation of a component hook. This method is called when a hook is invalidated.
        This method should be overridden by the subclass to act on the invalidation of the component hooks.

        Args:
            keys: The keys of the component hooks to invalidate.
        """
        pass

    def _update_hook_cache(self, hook: HookLike[Any], old_nexus: Optional[HookNexus[Any]] = None) -> None:
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
                self._nexus_to_key_cache.pop(old_nexus, None)
            # Add new nexus to cache
            self._nexus_to_key_cache[hook.hook_nexus] = key
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
                self._secondary_nexus_to_key_cache.pop(old_nexus, None)
            # Add new nexus to cache
            self._secondary_nexus_to_key_cache[hook.hook_nexus] = key

    def _update_secondary_hooks(self) -> None:
        """
        Update all secondary hooks by recomputing their values from current component values.
        
        This method is called whenever component values change to ensure secondary hooks
        stay synchronized with the current state.
        """
        if not self._secondary_hooks:
            return
            
        current_component_values = self._primary_component_values
        
        for key, callback in self._secondary_hook_callbacks.items():
            try:
                new_value = callback(current_component_values)
                secondary_hook = self._secondary_hooks[key]
                
                # Only update if the value actually changed to avoid unnecessary notifications
                if secondary_hook.value != new_value:
                    secondary_hook.value = new_value
                    
            except Exception as e:
                log(self, "update_secondary_hooks", self._logger, False, f"Error updating secondary hook '{key}': {e}")
                # Continue with other secondary hooks even if one fails
                
        log(self, "update_secondary_hooks", self._logger, True, "Successfully updated secondary hooks")

    def _set_component_values(self, dict_of_values: dict[HK, Any], notify_binding_system: bool) -> None:
        """
        Set the values of the component values.

        Args:
            dict_of_values: A dictionary of (key, value) pairs to set
            notify_binding_system: Whether to notify the binding system. If False, the binding system will not be notified and the values will not be invalidated (Use for updates from the binding system)

        Raises:
            ValueError: If the verification method fails
        """
        with self._lock:
            if len(self._primary_hooks) == 0:
                error_msg = "No component hooks provided"
                log(self, "set_component_values", self._logger, False, error_msg)
                raise ValueError(error_msg)
            
            future_component_values: dict[HK, Any] = {key: hook.value for key, hook in self._primary_hooks.items()}
            
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
                    hook.value = value
                else:
                    HookLike[Any].set_multiple_values(dict_of_values, self._primary_hooks)

            # Update secondary hooks after component values have changed
            self._update_secondary_hooks()

            # Notify listeners of this observable (Hook specific listeners are notified by the hook system)
            self._notify_listeners()

            log(self, "set_component_values", self._logger, True, "Successfully set component values")

    def _get_key_for(self, hook_or_nexus: HookLike[Any]|HookNexus[Any]) -> HK:
        """
        Get the key for a hook using O(1) cache lookup with lazy population.
        """
        if isinstance(hook_or_nexus, HookNexus):
            # Try cached lookup first
            key = self._nexus_to_key_cache.get(hook_or_nexus)
            if key is not None:
                return key
                
            # Cache miss - do linear search and populate cache
            for k, h in self._primary_hooks.items():
                if h.hook_nexus is hook_or_nexus:
                    # Update cache for future O(1) lookups
                    self._nexus_to_key_cache[hook_or_nexus] = k
                    return k
            raise ValueError(f"Hook nexus {hook_or_nexus} not found in component_hooks")
        else:
            # Try cached lookup first
            key = self._hook_to_key_cache.get(hook_or_nexus)
            if key is not None:
                return key
                
            # Cache miss - do linear search and populate cache
            for k, h in self._primary_hooks.items():
                if h is hook_or_nexus:
                    # Update cache for future O(1) lookups
                    self._hook_to_key_cache[hook_or_nexus] = k
                    return k
            raise ValueError(f"Hook {hook_or_nexus} not found in component_hooks")
        
    def _get_key_for_secondary_hook(self, hook_or_nexus: HookLike[Any]|HookNexus[Any]) -> EHK:
        """
        Get the key for an secondary hook using O(1) cache lookup with lazy population.
        """
        if isinstance(hook_or_nexus, HookNexus):
            # Try cached lookup first
            key = self._secondary_nexus_to_key_cache.get(hook_or_nexus)
            if key is not None:
                return key
                
            # Cache miss - do linear search and populate cache
            for k, h in self._secondary_hooks.items():
                if h.hook_nexus is hook_or_nexus:
                    # Update cache for future O(1) lookups
                    self._secondary_nexus_to_key_cache[hook_or_nexus] = k
                    return k
            raise ValueError(f"Hook nexus {hook_or_nexus} not found in secondary_hooks")
        else:
            # Try cached lookup first
            key = self._secondary_hook_to_key_cache.get(hook_or_nexus)
            if key is not None:
                return key
                
            # Cache miss - do linear search and populate cache
            for k, h in self._secondary_hooks.items():
                if h is hook_or_nexus:
                    # Update cache for future O(1) lookups
                    self._secondary_hook_to_key_cache[hook_or_nexus] = k
                    return k
            raise ValueError(f"Hook {hook_or_nexus} not found in secondary_hooks")
    
    def _is_valid_value(self, hook: HookLike[Any], value: Any) -> tuple[bool, str]:
        """
        Check if the value is valid.
        """
        if self._verification_method is None:
            return True, "No verification method provided. Default is True"
        else:
            # Check if this is an secondary hook first
            for _, h in self._secondary_hooks.items():
                if h is hook:
                    # Secondary hooks don't need validation since they're computed from component values
                    return True, "Secondary hooks are always valid as they're computed values"
            
            # Must be a component hook
            return self._verification_method({self._get_key_for(hook): value})
        
    def _are_valid_values(self, values: Mapping["HookNexus[Any]", Any]) -> tuple[bool, str]: # type: ignore
        """
        Check if the values are valid.
        """
        if self._verification_method is None:
            return True, "No verification method provided. Default is True"
        else:
            dict_of_values: dict[HK, Any] = self._primary_component_values
            for nexus, value in values.items():
                dict_of_values[self._get_key_for(nexus)] = value
            return self._verification_method(dict_of_values)
        
    def _get_component_value_reference(self, key: HK) -> Any:
        """
        Internal method to get the value of a component hook as a reference.

        The value is returned as a reference.

        Args:
            key: The key of the component hook to get the value of

        Returns:
            The value of the component hook as a reference
        """
        with self._lock:
            return self._primary_hooks[key].value

    @property
    def _primary_component_values(self) -> dict[HK, Any]:
        """
        Get the values of the primary component hooks as a dictionary copy.
        """
        with self._lock:
            return {key: hook.value for key, hook in self._primary_hooks.items()}
        
    def _verify_state(self) -> tuple[bool, str]:
        """
        Verify the state of the observable.
        """
        if self._verification_method is None:
            return True, "No verification method provided. Default is True"
        return self._verification_method(self._primary_component_values)
    

    @property
    def _collective_hooks(self) -> set[HookLike[Any]]:
        """
        Get the collective hooks for the observable.
        """
        return set(self._primary_hooks.values()) | set(self._secondary_hooks.values())
    
    #########################################################
    # Public API
    #########################################################

    @property
    def hooks(self) -> set[HookLike[Any]]:
        """
        Get the hooks of the observable.

        Returns:
            A set of hooks
        """
        return set(self._primary_hooks.values()) | set(self._secondary_hooks.values())
    
    @property
    def primary_hooks(self) -> set[HookLike[Any]]:
        """
        Get the primary hooks of the observable.
        """
        return set(self._primary_hooks.values())
    
    @property
    def secondary_hooks(self) -> set[HookLike[Any]]:
        """
        Get the secondary hooks of the observable.
        """
        return set(self._secondary_hooks.values())
    
    @property
    def component_values_dict(self) -> dict[HK|EHK, Any]:
        """
        Get the values of the component (primary and secondary) hooks as a dictionary.
        """
        values_dict: dict[HK|EHK, Any] = {}
        for key, hook in self._primary_hooks.items():
            values_dict[key] = hook.value
        for key, hook in self._secondary_hooks.items():
            values_dict[key] = hook.value
        return values_dict
    
    @property
    def primary_component_values(self) -> dict[HK, Any]:
        """
        Get the values of the primary component hooks as a dictionary.
        """
        return {key: hook.value for key, hook in self._primary_hooks.items()}
    
    @property
    def secondary_component_values(self) -> dict[EHK, Any]:
        """
        Get the values of the secondary component hooks as a dictionary.
        """
        return {key: hook.value for key, hook in self._secondary_hooks.items()}
    
    def get_component_value(self, key: HK|EHK) -> Any:
        """
        Get the value of a component (primary and secondary) hook.

        If copying is available, the copy is returned.

        Args:
            key: The key to get the value for

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """
        if key not in self._primary_hooks and key not in self._secondary_hooks:
            raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")
        if key in self._primary_hooks:
            value = self._primary_hooks[key].value # type: ignore
            if hasattr(value, "copy"):
                return value.copy()
        elif key in self._secondary_hooks:
            value = self._secondary_hook_callbacks[key](self._primary_component_values) # type: ignore
        else:
            raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")
        return value
    
    def get_component_hook(self, key: HK|EHK) -> HookLike[Any]:
        """
        Get a hook by key. Primary and secondary hooks are both supported.

        Args:
            key: The key to get the hook for

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """
        if key in self._primary_hooks:
            return self._primary_hooks[key] # type: ignore
        elif key in self._secondary_hooks:
            return self._secondary_hooks[key] # type: ignore
        else:
            raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")
    
    def connect(self, hook: HookLike[Any], to_key: HK|EHK, initial_sync_mode: InitialSyncMode) -> None:
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
    

    def connect_multiple(self, hooks: Mapping[HK|EHK, HookLike[Any]], initial_sync_mode: InitialSyncMode) -> None:
        """
        Attach multiple hooks to the observable.

        Args:
            hooks: A mapping of keys to hooks
            initial_sync_mode: The initial synchronization mode

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """

        hook_pairs: list[tuple[HookLike[Any], HookLike[Any]]] = []
        for key, hook in hooks.items():
            if key in self._primary_hooks:
                hook_of_observable = self._primary_hooks[key] # type: ignore
            elif key in self._secondary_hooks:
                hook_of_observable = self._secondary_hooks[key] # type: ignore
            else:
                raise ValueError(f"Key {key} not found in component_hooks or secondary_hooks")
            match initial_sync_mode:
                case InitialSyncMode.USE_CALLER_VALUE:
                    hook_pairs.append((hook_of_observable, hook))
                case InitialSyncMode.USE_TARGET_VALUE:
                    hook_pairs.append((hook, hook_of_observable))
                case _: # type: ignore
                    raise ValueError(f"Invalid initial sync mode: {initial_sync_mode}")
        HookNexus[Any].connect_hook_pairs(*hook_pairs)
    
    def disconnect(self, key: Optional[HK|EHK]=None) -> None:
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
    
    @final
    def get_primary_component_values_as_references(self) -> Mapping[HK, Any]:
        """
        Get the values of the primary component hooks as references.

        This method can be used for serializing the observable.

        ** The returned values are references, so modifying them will modify the observable.
        Use with caution.

        Returns:
            A dictionary of keys to values
        """
        return self._primary_component_values.copy()