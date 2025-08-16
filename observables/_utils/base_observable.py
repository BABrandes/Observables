import threading
from abc import abstractmethod
from typing import Any, Callable, Optional
from .base_listening import BaseListening
from .hook import HookLike
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
            component_hooks: dict[str, HookLike[Any]],
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

        self._component_hooks: dict[str, HookLike[Any]] = component_hooks.copy()
        self._verification_method: Optional[Callable[[Mapping[str, Any]], tuple[bool, str]]] = verification_method
        self._component_copy_methods: dict[str, Optional[Callable[[Any], Any]]] = component_copy_methods.copy()
        # Thread safety: Lock for protecting component values and hooks
        self._lock = threading.RLock()
        
        # Initialize component values first
        self._component_values: dict[str, Any] = {}
        for key, value in component_values.items():
            self._component_values[key] = value

    @classmethod
    @abstractmethod
    def _mandatory_component_value_keys(cls) -> set[str]:
        """
        Get the mandatory component value keys.
        """
        ...

    def _set_component_values(self, *tuple_of_values: tuple[str, Any], notify_binding_system: bool, notify_listeners: bool = True) -> None:
        """
        Set the values of the component values.

        Args:
            *tuple_of_values: A tuple of (key, value) pairs to set
            notify_binding_system: Whether to notify the binding system. If False, the binding system will not be notified and the values will not be invalidated (Use for updates from the binding system)
            notify_listeners: Whether to notify the listeners. If False, the listeners will not be notified and the values will not be updated.

        Raises:
            ValueError: If the verification method fails
        """
        with self._lock:
            
            updated_component_values: dict[str, Any] = self._component_values.copy()
            for key, value in tuple_of_values:
                if key not in self._component_values:
                    raise ValueError(f"Key {key} not found in component_values")
                updated_component_values[key] = value
            if self._verification_method is not None:
                success, message = self._verification_method(updated_component_values)
                if not success:
                    raise ValueError(f"Verification method failed: {message}")
            
            self._component_values = updated_component_values
            
            if notify_binding_system:
                for key, value in tuple_of_values:
                    self._component_hooks[key].invalidate()

            if notify_listeners:
                self._notify_listeners()

    @property
    def observed_component_values(self) -> tuple[Any, ...]:
        """
        Get the values of all observables that are bound to this observable.

        The main purpose of this method is for serialization of the observable.
        """
        with self._lock:
            return tuple(self._component_values.values())

    def check_status_consistency(self) -> tuple[bool, str]:
        """
        Check the consistency of the status of the observable.
        
        This method performs comprehensive checks on all bindings to ensure they are in a consistent state .
        
        Returns:
            Tuple of (is_consistent, message) where is_consistent is a boolean
            indicating if the system is consistent, and message provides details
            about any inconsistencies found.
        """
        with self._lock:
            if self._verification_method is not None:
                success, message = self._verification_method(self._component_values)
                if not success:
                    return False, f"Verification method failed: {message}"

            for hook in self._component_hooks.values():
                binding_state_consistent, binding_state_consistent_message = hook.check_binding_system()
                if not binding_state_consistent:
                    return False, binding_state_consistent_message

        return True, "Status of the observable is consistent"
    
    def _get_component_value(self, key: str) -> Any:
        """
        Get the value of a component.
        """
        with self._lock:
            return self._component_values[key]