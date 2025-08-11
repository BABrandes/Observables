from typing import Any
from abc import abstractmethod
from .._utils._listening_base import ListeningBase

class Observable(ListeningBase):
    """
    Protocol defining the interface for all observable objects in the library.
    
    This protocol serves as a contract that ensures all observable classes implement
    a consistent set of methods and behaviors. It enables type safety, polymorphism,
    and enables the creation of generic utilities that work with any observable type.
    
    **Purpose:**
    The Observable protocol provides a standardized interface that allows different
    observable types (ObservableEnum, ObservableDict, ObservableList, etc.) to be
    used interchangeably in generic contexts while maintaining type safety.
    
    **Benefits:**
    - **Type Safety**: Enables static type checking and IDE support
    - **Polymorphism**: Allows functions to accept any observable type
    - **Consistency**: Guarantees all observables have the same core interface
    - **Extensibility**: Enables protocol-based features and utilities
    
    **Usage Examples:**
    
    1. **Generic Collections:**
        from typing import List
        from observables import Observable
        
        def process_observables(obs_list: List[Observable]) -> None:
            for obs in obs_list:
                # All observables implement the same interface
                obs.add_listener(lambda: print("Changed!"))
    
    2. **Protocol-Based Functions:**
        def create_binding(source: Observable, target: Observable) -> None:
            # Works with any observable type
            source.bind_to_observable(target)
    
    3. **Type-Safe Factories:**
        T = TypeVar('T', bound=Observable)
        
        def create_observable(obs_type: Type[T], *args, **kwargs) -> T:
            return obs_type(*args, **kwargs)
    
    **Implementation Notes:**
    - This protocol is currently a marker interface (empty) but may be extended
      with required methods in future versions
    - All observable classes in the library implement this protocol
    - The protocol enables structural typing in Python's type system
    
    **Future Considerations:**
    As the library evolves, this protocol may be extended to include:
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
    
    @abstractmethod
    def get_observed_values(self) -> tuple[Any, ...]:
        """
        Get the values of all observables that are bound to this observable.

        The main purpose of this method is for serialization of the observable.
        """
        ...

    @abstractmethod
    def set_observed_values(self, values: tuple[Any, ...]) -> None:
        """
        Set the values of all observables that are bound to this observable.

        The main purpose of this method is for deserialization of the observable.
        """
        ...