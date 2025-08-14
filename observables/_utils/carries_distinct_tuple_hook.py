from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from .hook import Hook
from .carries_distinct_hook import CarriesDistinctHook

T = TypeVar("T")

class CarriesDistinctTupleHook(CarriesDistinctHook, Generic[T]):
    """
    Abstract base class for observables that carry a tuple and can participate in bindings via. a hook.
    
    This abstract base class defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for tuples via. a hook.
    It extends the base CarriesDistinctHook interface with specific methods for
    tuple management.
    """

    @abstractmethod
    def _get_tuple_hook(self) -> Hook[tuple[T]]:
        """
        INTERNAL. Do not use this method directly.
        
        Method to get the hook for tuple.
        
        This method provides access to the internal hook that
        manages bidirectional bindings for this observable. The binding
        system uses this hook to establish and manage connections.
        
        Returns:
            The internal hook for tuple
            
        Note:
            This is an internal method called by the hook system.
            It should not be called directly by users.
        """
        ...

    @abstractmethod
    def _get_tuple_value(self) -> tuple[T]:
        """
        INTERNAL. Do not use this method directly.
        
        Method to get the current value of the tuple.
        
        Returns:
            The current value of the tuple
        """
        ...

    @abstractmethod
    def _set_tuple_value(self, tuple_to_set: tuple[T]) -> None:
        """
        INTERNAL. Do not use this method directly.
        
        Method to set the current value of the tuple.
        """
        ...