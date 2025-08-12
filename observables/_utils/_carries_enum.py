from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from enum import Enum
from ._internal_binding_handler import InternalBindingHandler
from ._carries_bindable import CarriesBindable

E = TypeVar("E", bound=Enum)

class CarriesEnum(CarriesBindable, Generic[E]):
    """
    Abstract base class for observables that carry an enum value and can participate in bindings.
    
    This abstract base class defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for enum values.
    It extends the base CarriesBindable interface with specific methods for
    enum management.
    
    Classes implementing this interface must provide:
    - Methods to get and set enum values
    - Validation logic for enum changes
    - Access to the internal binding handler
    
    This interface is implemented by:
    - ObservableEnum
    
    Note:
        This is an internal interface not intended for direct use by end users.
        Use the concrete ObservableEnum class instead.
    """

    @abstractmethod
    def _set_enum(self, enum_to_set: E) -> None:
        """
        Set the enum value from the binding system.
        
        This method is called by the binding system when another observable
        wants to update this observable's enum value. Implementations should
        handle the enum change and trigger appropriate notifications.
        
        Args:
            enum_to_set: The new enum value to set
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...
    
    @abstractmethod
    def _get_enum(self) -> E:
        """
        Get the current enum value for the binding system.
        
        This method is called by the binding system to retrieve the
        current enum value of this observable. Implementations should return
        the current value without any side effects.
        
        Returns:
            The current enum value stored in this observable
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...

    @abstractmethod
    def _get_enum_binding_handler(self) -> InternalBindingHandler[E]:
        """
        Get the binding handler for enum bindings.
        
        This method provides access to the internal binding handler that
        manages bidirectional bindings for this observable. The binding
        system uses this handler to establish and manage connections.
        
        Returns:
            The internal binding handler for enum bindings
            
        Note:
            This is an internal method called by the binding system.
            It should not be called directly by users.
        """
        ...