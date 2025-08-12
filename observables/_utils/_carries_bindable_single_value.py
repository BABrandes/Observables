from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from ._internal_binding_handler import InternalBindingHandler
from ._carries_bindable import CarriesBindable

T = TypeVar("T")

class CarriesBindableSingleValue(CarriesBindable, Generic[T]):
    """
    Abstract base class for observables that carry a single value and can participate in bindings.
    
    This abstract base class defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for single values.
    It extends the base CarriesBindable interface with specific methods for
    single value management.
    
    Classes implementing this interface must provide:
    - Methods to get and set single values
    - Validation logic for value changes
    - Access to the internal binding handler
    
    This interface is implemented by:
    - ObservableSingleValue
    - ObservableSelectionOption (for selected_option binding)
    
    Note:
        This is an internal interface not intended for direct use by end users.
        Use the concrete ObservableSingleValue class instead.
    """

    @abstractmethod
    def _set_single_value(self, single_value_to_set: T) -> None:
        """
        Set the single value from the binding system.
        
        This method is called by the binding system when another observable
        wants to update this observable's value. Implementations should
        handle the value change and trigger appropriate notifications.
        
        Args:
            single_value_to_set: The new value to set
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...
    
    @abstractmethod
    def _get_single_value(self) -> T:
        """
        Get the current single value for the binding system.
        
        This method is called by the binding system to retrieve the
        current value of this observable. Implementations should return
        the current value without any side effects.
        
        Returns:
            The current value stored in this observable
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...
        
    @abstractmethod
    def _get_single_value_binding_handler(self) -> InternalBindingHandler[T]:
        """
        Get the binding handler for single value bindings.
        
        This method provides access to the internal binding handler that
        manages bidirectional bindings for this observable. The binding
        system uses this handler to establish and manage connections.
        
        Returns:
            The internal binding handler for single value bindings
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...