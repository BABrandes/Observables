from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from ._internal_binding_handler import InternalBindingHandler
from ._carries_bindable import CarriesBindable

K = TypeVar("K")
V = TypeVar("V")

class CarriesBindableDict(CarriesBindable, Generic[K, V]):
    """
    Abstract base class for observables that carry a dictionary and can participate in bindings.
    
    This abstract base class defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for dictionaries.
    It extends the base CarriesBindable interface with specific methods for
    dictionary management.
    
    Classes implementing this interface must provide:
    - Methods to get and set dictionaries
    - Validation logic for dictionary changes
    - Access to the internal binding handler
    
    This interface is implemented by:
    - ObservableDict
    
    Note:
        This is an internal interface not intended for direct use by end users.
        Use the concrete ObservableDict class instead.
    """

    @abstractmethod
    def _set_dict(self, dict_to_set: dict[K, V]) -> None:
        """
        Set the dictionary from the binding system.
        
        This method is called by the binding system when another observable
        wants to update this observable's dictionary. Implementations should
        handle the dictionary change and trigger appropriate notifications.
        
        Args:
            dict_to_set: The new dictionary to set
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...
    
    @abstractmethod
    def _get_dict(self) -> dict[K, V]:
        """
        Get the current dictionary for the binding system.
        
        This method is called by the binding system to retrieve the
        current dictionary of this observable. Implementations should return
        the current dictionary without any side effects.
        
        Returns:
            The current dictionary stored in this observable
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...

    @abstractmethod
    def _get_dict_binding_handler(self) -> InternalBindingHandler[dict[K, V]]:
        """
        Get the binding handler for dictionary bindings.
        
        This method provides access to the internal binding handler that
        manages bidirectional bindings for this observable. The binding
        system uses this handler to establish and manage connections.
        
        Returns:
            The internal binding handler for dictionary bindings
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...
