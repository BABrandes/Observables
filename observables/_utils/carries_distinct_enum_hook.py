from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from enum import Enum
from .hook import Hook
from .carries_distinct_hook import CarriesDistinctHook

E = TypeVar("E", bound=Enum)

class CarriesDistinctEnumHook(CarriesDistinctHook, Generic[E]):
    """
    Abstract base class for observables that carry an enum value and can participate in bindings via. a hook.
    
    This abstract base class defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for enum values.
    It extends the base CarriesDistinctHook interface with specific methods for
    enum management.
    
    Classes implementing this interface must provide:
    - Methods to get and set enum values
    - Validation logic for enum changes
    - Access to the internal hook
    
    This interface is implemented by:
    - ObservableEnum
    
    Note:
        This is an internal interface not intended for direct use by end users.
        Use the concrete ObservableEnum class instead.
    """

    @abstractmethod
    def _get_enum_hook(self) -> Hook[E]:
        """
        INTERNAL. Do not use this method directly.
        
        Method to get the hook for enum.
        
        This method provides access to the internal hook that
        manages bidirectional bindings for this observable. The binding
        system uses this hook to establish and manage connections.
        
        Returns:
            The internal hook for enum
            
        Note:
            This is an internal method called by the hook system.
            It should not be called directly by users.
        """
        ...

    @abstractmethod
    def _get_enum_value(self) -> E:
        """
        INTERNAL. Do not use this method directly.
        
        Method to get enum for binding system.
        
        Returns:
            The current enum value
        """
        ...

    @abstractmethod
    def _set_enum_value(self, enum_value_to_set: E) -> None:
        """
        INTERNAL. Do not use this method directly.
        
        Method to set the current value of the enum.
        """
        ...