from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from .hook import Hook
from .carries_distinct_hook import CarriesDistinctHook

T = TypeVar("T")

class CarriesDistinctListHook(CarriesDistinctHook, Generic[T]):
    """
    Abstract base class for observables that carry a list and can participate in bindings via. a hook.
    
    This abstract base class defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for lists via. a hook.
    It extends the base CarriesDistinctHook interface with specific methods for
    list management.
    
    Classes implementing this interface must provide:
    - Methods to get and set lists
    - Validation logic for list changes
    - Access to the internal hook
    
    This interface is implemented by:
    - ObservableList
    
    Note:
        This is an internal interface not intended for direct use by end users.
        Use the concrete ObservableList class instead.
    """

    @abstractmethod
    def _get_list_hook(self) -> Hook[list[T]]:
        """
        Get the hook for list.
        
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
    def get_list_value(self) -> list[T]:
        """
        Get the current value of the list as a copy.
        """
        ...
    