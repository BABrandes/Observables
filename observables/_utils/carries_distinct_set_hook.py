from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from .hook import Hook
from .carries_distinct_hook import CarriesDistinctHook

T = TypeVar("T")

class CarriesDistinctSetHook(CarriesDistinctHook, Generic[T]):
    """
    Abstract base class for observables that carry a set and can participate in bindings via. a hook.
    
    This abstract base class defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for sets via. a hook.
    It extends the base CarriesDistinctHook interface with specific methods for
    set management.
    
    Classes implementing this interface must provide:
    - Methods to get and set sets
    - Validation logic for set changes
    - Access to the internal hook
    
    This interface is implemented by:
    - ObservableSet
    - ObservableSelectionOption (for options binding)
    
    Note:
        This is an internal interface not intended for direct use by end users.
        Use the concrete ObservableSet class instead.
    """

    @abstractmethod
    def _get_set_hook(self) -> Hook[set[T]]:
        """
        Get the hook for set.
        
        This method provides access to the internal hook that
        manages bidirectional bindings for this observable. The binding
        system uses this hook to establish and manage connections.
        
        Returns:
            The internal hook for set
            
        Note:
            This is an internal method called by the hook system.
            It should not be called directly by users.
        """
        ...

    @abstractmethod
    def get_set_value(self) -> set[T]:
        """
        Get the current value of the set as a copy.
        """
        ...
    