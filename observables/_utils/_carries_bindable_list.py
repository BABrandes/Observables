from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from ._internal_binding_handler import InternalBindingHandler
from ._carries_bindable import CarriesBindable

T = TypeVar("T")

class CarriesBindableList(CarriesBindable, Generic[T]):
    """
    Abstract base class for observables that carry a list and can participate in bindings.
    
    This abstract base class defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for lists.
    It extends the base CarriesBindable interface with specific methods for
    list management.
    
    Classes implementing this interface must provide:
    - Methods to get and set lists
    - Validation logic for list changes
    - Access to the internal binding handler
    
    This interface is implemented by:
    - ObservableList
    
    Note:
        This is an internal interface not intended for direct use by end users.
        Use the concrete ObservableList class instead.
    """

    @abstractmethod
    def _set_list(self, list_to_set: list[T]) -> None:
        """
        Set the list from the binding system.
        
        This method is called by the binding system when another observable
        wants to update this observable's list. Implementations should
        handle the list change and trigger appropriate notifications.
        
        Args:
            list_to_set: The new list to set
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...
    
    @abstractmethod
    def _get_list(self) -> list[T]:
        """
        Get the current list for the binding system.
        
        This method is called by the binding system to retrieve the
        current list of this observable. Implementations should return
        the current list without any side effects.
        
        Returns:
            The current list stored in this observable
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...

    @abstractmethod
    def _check_list(self, list_to_check: list[T]) -> bool:
        """
        Check if a list is valid for this observable.
        
        This method is called by the binding system to validate lists
        before they are set. Implementations should return True if the
        list is acceptable, False otherwise.
        
        Args:
            list_to_check: The list to validate
            
        Returns:
            True if the list is valid, False otherwise
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...

    @abstractmethod
    def _get_list_binding_handler(self) -> InternalBindingHandler[list[T]]:
        """
        Get the binding handler for list bindings.
        
        This method provides access to the internal binding handler that
        manages bidirectional bindings for this observable. The binding
        system uses this handler to establish and manage connections.
        
        Returns:
            The internal binding handler for list bindings
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...
    