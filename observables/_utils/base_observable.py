import threading
from abc import abstractmethod
from typing import Any, Callable, Optional
from .base_listening import BaseListening
from .hook import Hook
from collections.abc import Mapping

class BaseObservable(BaseListening):
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
            component_values: dict[str, Any],
            component_hooks: dict[str, Hook[Any]],
            verification_method: Optional[Callable[[Mapping[str, Any]], tuple[bool, str]]] = None,
            component_copy_methods: dict[str, Optional[Callable[[Any], Any]]] = {}):
        """
        Initialize the BaseObservable.

        Args:
            component_values: A dictionary of component values.
            component_hooks: A dictionary of component hooks.
            component_copy_methods: A dictionary of component copy methods.

        If the component_copy_methods is not provided, the method will try to use the copy method of the value if it is available.
        If the component_copy_methods is None, the value will not be copied. This is dangerous and should not be used.
        """

        super().__init__()

        if component_values.keys() != component_hooks.keys():
            raise ValueError("The keys of the component_values and component_hooks must be the same")

        self._component_values: dict[str, Any] = {}
        self._component_hooks: dict[str, Hook[Any]] = component_hooks.copy()
        self._verification_method: Optional[Callable[[Mapping[str, Any]], tuple[bool, str]]] = verification_method
        self._component_copy_methods: dict[str, Optional[Callable[[Any], Any]]] = component_copy_methods.copy()
        # Thread safety: Lock for protecting component values and hooks
        self._lock = threading.RLock()
        self._set_component_values_from_dict(component_values, skip_notification=True)

    @classmethod
    @abstractmethod
    def _mandatory_component_value_keys(cls) -> set[str]:
        """
        Get the mandatory component value keys.
        """
        ...

    def _set_component_values_from_tuples(self, *tuple_of_values: tuple[str, Any], reverting_to_old_values: bool = False, skip_notification: bool = False) -> None:
        """
        Set the values of the component values.
        """
        with self._lock:
            # Convert tuple of (key, value) pairs to a dictionary
            dict_of_values = dict(tuple_of_values)
            self._set_component_values_from_dict(dict_of_values, reverting_to_old_values=reverting_to_old_values, skip_notification=skip_notification)

    def _set_component_values_from_dict(self, dict_of_values: dict[str, Any], reverting_to_old_values: bool = False, skip_notification: bool = False) -> None:
        """
        Set the values of the component values.

        This method will copy the values if the copy method is provided.
        It will also verify the values if the verification method is provided.
        It will also notify the hooks and the listeners.

        This is the only method that should be used to set the component values.

        Args:
            dict_of_values: A dictionary of values.
            reverting_to_old_values: If True, it means, the method was called by the _set_component_values method due to an error, and we are reverting to the old values.
        """
        with self._lock:

            # Safety check: prevent setting values with keys that are not in the mandatory component value keys
            if not set(dict_of_values.keys()).issubset(self.__class__._mandatory_component_value_keys()):
                raise ValueError(f"Invalid values: {dict_of_values}. The keys must be a subset of {self.__class__._mandatory_component_value_keys()}")
            
            # Verification method: check if the values are valid
            if self._verification_method is not None:
                verification_result, verification_message = self._verification_method(dict_of_values)
                if not verification_result:
                    raise ValueError(f"Invalid values: {dict_of_values}. {verification_message}")
            
            # Copy the values
            old_component_values: dict[str, Any] = self._component_values.copy()
            new_component_values: dict[str, Any] = {}

            for key, value in dict_of_values.items():
                copy_method: Optional[Callable[[Any], Any]] = None
                if key in self._component_copy_methods:
                    copy_method = self._component_copy_methods[key]
                elif hasattr(value, "copy") and callable(value.copy):
                    copy_method = lambda x: x.copy()
                
                if copy_method is not None:
                    new_component_values[key] = copy_method(value)
                else:
                    new_component_values[key] = value

            # Safety check: prevent setting values that are the same as the old values
            if old_component_values.items() == new_component_values.items():
                return
            
            # Set the new values
            self._component_values = new_component_values

            # Notify bindings
            if not skip_notification:
                try:
                    # Get a copy of hooks to avoid holding lock during notifications
                    hooks_copy = self._component_hooks.copy()
                    values_copy = new_component_values.copy()
                except Exception as e:
                    if not reverting_to_old_values:
                        self._set_component_values_from_dict(old_component_values, reverting_to_old_values=True)
                        raise ValueError(f"Error notifying the hooks (Reverting to old values): {e}")
                    else:
                        raise ValueError(f"Fatal error notifying the hooks, could not recover: {e}")
                
                # Notify hooks outside of lock to prevent deadlocks
                try:
                    for key, value in values_copy.items():
                        hooks_copy[key].notify_bindings(value)
                except Exception as e:
                    if not reverting_to_old_values:
                        self._set_component_values_from_dict(old_component_values, reverting_to_old_values=True)
                        raise ValueError(f"Error notifying the hooks (Reverting to old values): {e}")
                    else:
                        raise ValueError(f"Fatal error notifying the hooks, could not recover: {e}")
                
                # Notify listeners
                self._notify_listeners()

    @property
    def observed_component_values(self) -> tuple[Any, ...]:
        """
        Get the values of all observables that are bound to this observable.

        The main purpose of this method is for serialization of the observable.
        """
        with self._lock:
            return tuple(self._component_values.values())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        """
        Check the consistency of the binding system.
        
        This method performs comprehensive checks on all bindings to ensure they are in a consistent state and
        values are properly synchronized.
        
        Returns:
            Tuple of (is_consistent, message) where is_consistent is a boolean
            indicating if the system is consistent, and message provides details
            about any inconsistencies found.
        """
        with self._lock:
            # Get a copy to avoid holding lock during iteration
            hooks_copy = self._component_hooks.copy()

        # Check consistency outside of lock to prevent deadlocks
        for _, value in hooks_copy.items():
            binding_state_consistent, binding_state_consistent_message = value.check_binding_state_consistency()
            if not binding_state_consistent:
                return False, binding_state_consistent_message
            values_synced, values_synced_message = value.check_values_synced()
            if not values_synced:
                return False, values_synced_message

        return True, "Binding system is consistent"
    
    def _get_component_value(self, key: str) -> Any:
        """
        Get the value of a component.
        """
        with self._lock:
            return self._component_values[key]
    
    def _set_component_value(self, key: str, value: Any) -> None:
        """
        Set the value of a component.
        """
        with self._lock:
            current_values = self._component_values.copy()
            current_values[key] = value
            self._set_component_values_from_dict(current_values)