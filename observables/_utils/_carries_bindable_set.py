from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from ._internal_binding_handler import InternalBindingHandler
from ._carries_bindable import CarriesBindable

T = TypeVar("T")

class CarriesBindableSet(CarriesBindable, Generic[T]):
    """
    Abstract base class for observables that carry a set and can participate in bindings.
    
    This abstract base class defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for sets.
    It extends the base CarriesBindable interface with specific methods for
    set management.
    
    Classes implementing this interface must provide:
    - Methods to get and set sets
    - Validation logic for set changes
    - Access to the internal binding handler
    
    This interface is implemented by:
    - ObservableSet
    - ObservableSelectionOption (for options binding)
    
    Note:
        This is an internal interface not intended for direct use by end users.
        Use the concrete ObservableSet class instead.
    """

    @abstractmethod
    def _set_set(self, set_to_set: set[T]) -> None:
        """
        Set the set from the binding system.
        
        This method is called by the binding system when another observable
        wants to update this observable's set. Implementations should
        handle the set change and trigger appropriate notifications.
        
        Args:
            set_to_set: The new set to set
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...
    
    @abstractmethod
    def _get_set(self) -> set[T]:
        """
        Get the current set for the binding system.
        
        This method is called by the binding system to retrieve the
        current set of this observable. Implementations should return
        the current set without any side effects.
        
        Returns:
            The current set stored in this observable
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...

    @abstractmethod
    def _get_set_binding_handler(self) -> InternalBindingHandler[set[T]]:
        """
        Get the binding handler for set bindings.
        
        This method provides access to the internal binding handler that
        manages bidirectional bindings for this observable. The binding
        system uses this handler to establish and manage connections.
        
        Returns:
            The internal binding handler for set bindings
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...
    