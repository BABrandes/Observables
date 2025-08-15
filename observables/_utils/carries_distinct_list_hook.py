from abc import abstractmethod
from typing import TypeVar, Protocol, runtime_checkable
from .hook import Hook
from .base_carries_distinct_hook import BaseCarriesDistinctHook

T = TypeVar("T")

@runtime_checkable
class CarriesDistinctListHook(BaseCarriesDistinctHook, Protocol[T]):
    """
    Protocol for observables that carry a list and can participate in bindings via. a hook.
    
    This protocol defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for lists via. a hook.
    It extends the base BaseCarriesDistinctHook protocol with specific methods for
    list management.
    
    Classes implementing this protocol must provide:
    - Methods to get and set lists
    - Validation logic for list changes
    - Access to the internal hook
    
    This protocol is implemented by:
    - ObservableList
    
    Note:
        This protocol can be used directly by end users for type hints and
        interface definitions when working with list observables.
        The individual methods remain internal implementation details.
    """

    @abstractmethod
    def _get_list_hook(self) -> Hook[list[T]]:
        """
        INTERNAL. Do not use this method directly.
        
        Method to get the hook for list.
        
        This method provides access to the internal hook that
        manages bidirectional bindings for this observable. The binding
        system uses this hook to establish and manage connections.
        
        Returns:
            The internal hook for list
            
        Note:
            This is an internal method called by the hook system.
            It should not be called directly by users.
        """
        ...

    @abstractmethod
    def _get_list_value(self) -> list[T]:
        """
        INTERNAL. Do not use this method directly.
        
        Method to get the current value of the list as a copy.
        
        Returns:
            The current value of the list as a copy
        """
        ...

    @abstractmethod
    def _set_list_value(self, list_to_set: list[T]) -> None:
        """
        INTERNAL. Do not use this method directly.
        
        Method to set the current value of the list.
        """
        ...