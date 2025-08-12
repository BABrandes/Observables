from typing import Any, Callable, Optional
from abc import abstractmethod
from .._utils._listening_base import ListeningBase
from .._utils._internal_binding_handler import InternalBindingHandler
from collections.abc import Mapping

class Observable(ListeningBase):
    """
    Class defining the interface for all observable objects in the library.

    This class serves as a contract that ensures all observable classes implement
    a consistent set of methods and behaviors. It enables type safety, polymorphism,
    and enables the creation of generic utilities that work with any observable type.
    
    **Purpose:**
    The Observable class provides a standardized interface that allows different
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
        from observables import Observable

        def process_observables(obs_list: List[Observable]) -> None:
            for obs in obs_list:
                # All observables implement the same interface
                obs.add_listener(lambda: print("Changed!"))
    
    2. **Class-Based Functions:**
        def create_binding(source: Observable, target: Observable) -> None:
            # Works with any observable type
            source.bind_to_observable(target)
    
    3. **Type-Safe Factories:**
        T = TypeVar('T', bound=Observable)
        
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
            component_binding_handlers: dict[str, InternalBindingHandler[Any]],
            verification_method: Optional[Callable[[Mapping[str, Any]], tuple[bool, str]]] = None,
            component_copy_methods: dict[str, Optional[Callable[[Any], Any]]] = {}):
        """
        Initialize the Observable.

        Args:
            component_values: A dictionary of component values.
            component_binding_handlers: A dictionary of component binding handlers.
            component_copy_methods: A dictionary of component copy methods.

        If the component_copy_methods is not provided, the method will try to use the copy method of the value if it is available.
        If the component_copy_methods is None, the value will not be copied. This is dangerous and should not be used.
        """

        super().__init__()

        if component_values.keys() != component_binding_handlers.keys():
            raise ValueError("The keys of the component_values and component_binding_handlers must be the same")

        self._component_values: dict[str, Any] = {}
        self._component_binding_handlers: dict[str, InternalBindingHandler[Any]] = component_binding_handlers.copy()
        self._verification_method: Optional[Callable[[Mapping[str, Any]], tuple[bool, str]]] = verification_method
        self._component_copy_methods: dict[str, Optional[Callable[[Any], Any]]] = component_copy_methods.copy()
        self._set_component_values(component_values)

    def _set_component_values(self, dict_of_values: dict[str, Any], reverting_to_old_values: bool = False) -> None:
        """
        Set the values of the component values.

        This method will copy the values if the copy method is provided.
        It will also verify the values if the verification method is provided.
        It will also notify the binding handlers and the listeners.

        This is the only method that should be used to set the component values.

        Args:
            dict_of_values: A dictionary of values.
            reverting_to_old_values: If True, it means, the method was called by the _set_component_values method due to an error, and we are reverting to the old values.
        """

        if self._verification_method is not None:
            verification_result, verification_message = self._verification_method(dict_of_values)
            if not verification_result:
                raise ValueError(f"Invalid values: {dict_of_values}. {verification_message}")
            
        old_component_values: dict[str, Any] = self._component_values.copy()

        for key, value in dict_of_values.items():
            copy_method: Optional[Callable[[Any], Any]] = None
            if key in self._component_copy_methods:
                copy_method = self._component_copy_methods[key]
            elif hasattr(value, "copy") and callable(value.copy):
                copy_method = lambda x: x.copy()
            
            if copy_method is not None:
                self._component_values[key] = copy_method(value)
            else:
                self._component_values[key] = value

        try:
            for key, value in dict_of_values.items():
                self._component_binding_handlers[key].notify_bindings(value)
        except Exception as e:
            if not reverting_to_old_values:
                self._set_component_values(old_component_values, reverting_to_old_values=True)
                raise ValueError(f"Error notifying the binding handlers (Reverting to old values): {e}")
            else:
                raise ValueError(f"Fatal error notifying the binding handlers, could not recover: {e}")
        
        self._notify_listeners()

    @property
    def observed_component_values(self) -> tuple[Any, ...]:
        """
        Get the values of all observables that are bound to this observable.

        The main purpose of this method is for serialization of the observable.
        """
        return tuple(self._component_values.values())