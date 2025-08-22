import threading
from typing import Any, Callable, Mapping, Optional, TypeVar
from logging import Logger
from .base_listening import BaseListening
from .hook import Hook, HookLike
from .carries_collective_hooks import CarriesCollectiveHooks
from .hook_nexus import HookNexus
from .initial_sync_mode import InitialSyncMode
from .general import log

HK = TypeVar("HK")

class BaseObservable(BaseListening, CarriesCollectiveHooks[HK]):
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
            initial_component_values: dict[HK, Any],
            verification_method: Optional[Callable[[dict[HK, Any]], tuple[bool, str]]] = None,
            logger: Optional[Logger] = None):
        """
        Initialize the BaseObservable.

        Args:
            component_hooks: A dictionary of component hooks.
            verification_method: A method to verify the component values.
        """

        super().__init__(logger)

        self._logger: Optional[Logger] = logger

        self._component_hooks: dict[HK, HookLike[Any]] = {}
        for key, value in initial_component_values.items():
            self._component_hooks[key] = Hook(self, value, lambda _, k=key: self._invalidate({k}), logger)

        self._verification_method: Optional[Callable[[dict[HK, Any]], tuple[bool, str]]] = verification_method
        # Thread safety: Lock for protecting component values and hooks
        self._lock = threading.RLock()

        if self._verification_method is not None:
            success, message = self._verification_method(initial_component_values)
            if not success:
                raise ValueError(f"Verification method failed: {message}")

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

    def _set_component_values(self, dict_of_values: dict[HK, Any], notify_binding_system: bool, notify_listeners: bool = True) -> None:
        """
        Set the values of the component values.

        Args:
            dict_of_values: A dictionary of (key, value) pairs to set
            notify_binding_system: Whether to notify the binding system. If False, the binding system will not be notified and the values will not be invalidated (Use for updates from the binding system)
            notify_listeners: Whether to notify the listeners. If False, the listeners will not be notified and the values will not be updated.

        Raises:
            ValueError: If the verification method fails
        """
        with self._lock:
            if len(self._component_hooks) == 0:
                error_msg = "No component hooks provided"
                log(self, "set_component_values", self._logger, False, error_msg)
                raise ValueError(error_msg)
            
            future_component_values: dict[HK, Any] = {key: hook.value for key, hook in self._component_hooks.items()}
            
            for key, value in dict_of_values.items():
                if key not in self._component_hooks:
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
                    for key, value in dict_of_values.items():
                        hook = self._component_hooks[key]
                        hook.value = value
                else:
                    nexus_and_values: Mapping[HookNexus[Any], Any] = {}
                    for key, value in dict_of_values.items():
                        nexus = self._component_hooks[key].hook_nexus
                        nexus_and_values[nexus] = value
                    HookNexus.submit_multiple_values(nexus_and_values)

            if notify_listeners:
                self._notify_listeners()

            log(self, "set_component_values", self._logger, True, "Successfully set component values")

    def _get_key_for(self, hook_or_nexus: HookLike[Any]|HookNexus[Any]) -> HK:
        """
        Get the key for a hook.
        """
        if isinstance(hook_or_nexus, HookNexus):
            for key, h in self._component_hooks.items():
                if h.hook_nexus is hook_or_nexus:
                    return key
            raise ValueError(f"Hook {hook_or_nexus} not found in component_hooks")
        else:
            for key, h in self._component_hooks.items():
                if h is hook_or_nexus:
                    return key
            raise ValueError(f"Hook {hook_or_nexus} not found in component_hooks")
    
    def _is_valid_value(self, hook: HookLike[Any], value: Any) -> tuple[bool, str]:
        """
        Check if the value is valid.
        """
        if self._verification_method is None:
            return True, "No verification method provided. Default is True"
        else:
            return self._verification_method({self._get_key_for(hook): value})
        
    def _are_valid_values(self, values: Mapping["HookNexus[Any]", Any]) -> tuple[bool, str]: # type: ignore
        """
        Check if the values are valid.
        """
        if self._verification_method is None:
            return True, "No verification method provided. Default is True"
        else:
            dict_of_values: dict[HK, Any] = self._component_values
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
            return self._component_hooks[key].value

    @property
    def _component_values(self) -> dict[HK, Any]:
        """
        Get the values of all component hooks as a dictionary copy.
        """
        with self._lock:
            return {key: hook.value for key, hook in self._component_hooks.items()}
        
    def _verify_state(self) -> tuple[bool, str]:
        """
        Verify the state of the observable.
        """
        if self._verification_method is None:
            return True, "No verification method provided. Default is True"
        return self._verification_method(self._component_values)
    

    @property
    def _collective_hooks(self) -> set[HookLike[Any]]:
        """
        Get the collective hooks for the observable.
        """
        return set(self._component_hooks.values())
    
    #########################################################
    # Public API
    #########################################################

    @property
    def hooks(self) -> set[HookLike[Any]]:
        """
        Get the hooks of the observable.
        """
        return set(self._component_hooks.values())
    
    def get_value(self, key: HK) -> Any:
        """
        Get the value of a component hook.

        If copying is available, the copy is returned.
        """
        if not isinstance(key, str):
            raise ValueError(f"Key {key} is not a string")
        if key not in self._component_hooks:
            raise ValueError(f"Key {key} not found in component_hooks")
        value = self._component_hooks[key].value
        if hasattr(value, "copy"):
            return value.copy()
        return value
    
    def get_hook(self, key: HK) -> HookLike[Any]:
        """
        Get a hook by key.
        """
        if not isinstance(key, str):
            raise ValueError(f"Key {key} is not a string")
        if key not in self._component_hooks:
            raise ValueError(f"Key {key} not found in component_hooks")
        return self._component_hooks[key]
    
    def attach(self, hook: HookLike[Any], to_key: HK, initial_sync_mode: InitialSyncMode = InitialSyncMode.PUSH_TO_TARGET) -> None:
        """
        Attach a hook to the observable.
        """
        if not isinstance(to_key, str):
            raise ValueError(f"Key {to_key} is not a string")
        if to_key not in self._component_hooks:
            raise ValueError(f"Key {to_key} not found in component_hooks")
        self._component_hooks[to_key].connect_to(hook, initial_sync_mode)

    def attach_multiple(self, hooks: Mapping[HK, HookLike[Any]], initial_sync_mode: InitialSyncMode = InitialSyncMode.PUSH_TO_TARGET) -> None:
        """
        Attach multiple hooks to the observable.
        """

        hook_pairs: list[tuple[HookLike[Any], HookLike[Any]]] = []
        for key, hook in hooks.items():
            if not isinstance(key, str):
                raise ValueError(f"Key {key} is not a string")
            if key not in self._component_hooks:
                raise ValueError(f"Key {key} not found in component_hooks")
            hook_pairs.append((hook, self._component_hooks[key]))
        HookNexus[Any].connect_hook_pairs(*hook_pairs)
    
    def detach(self, key: Optional[HK]=None) -> None:
        """
        Detach a hook from the observable.
        """
        if key is None:
            for hook in self._component_hooks.values():
                try:
                    hook.detach()
                except ValueError as e:
                    if "already disconnected" in str(e):
                        # Hook is already disconnected, ignore
                        pass
                    else:
                        raise
        else:
            if not isinstance(key, str):
                raise ValueError(f"Key {key} is not a string")
            if key not in self._component_hooks:
                raise ValueError(f"Key {key} not found in component_hooks")
            try:
                self._component_hooks[key].detach()
            except ValueError as e:
                if "already disconnected" in str(e):
                    # Hook is already disconnected, ignore
                    pass
                else:
                    raise