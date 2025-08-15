from abc import abstractmethod
from typing import TypeVar, Protocol, runtime_checkable
from enum import Enum
from .hook import HookLike
from .base_carries_distinct_hook import BaseCarriesDistinctHook

E = TypeVar("E", bound=Enum)

@runtime_checkable
class CarriesDistinctEnumHook(BaseCarriesDistinctHook, Protocol[E]):
    """
    Protocol for observables that carry an enum value and can participate in bindings via. a hook.
    
    This protocol defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for enum values.
    It extends the base BaseCarriesDistinctHook protocol with specific methods for
    enum management.
    
    Classes implementing this protocol must provide:
    - Methods to get and set enum values
    - Validation logic for enum changes
    - Access to the internal hook
    
    This protocol is implemented by:
    - ObservableEnum
    
    Note:
        This protocol can be used directly by end users for type hints and
        interface definitions when working with enum observables.
        The individual methods remain internal implementation details.
    """

    @abstractmethod
    def _get_enum_hook(self) -> HookLike[E]:
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