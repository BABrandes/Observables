from abc import abstractmethod
from typing import TypeVar, Protocol, runtime_checkable  
from .hook import HookLike
from .base_carries_distinct_hook import BaseCarriesDistinctHook

T = TypeVar("T")

@runtime_checkable
class CarriesDistinctIndexableSingleValueHook(BaseCarriesDistinctHook, Protocol[T]):
    """
    Protocol for objects that carry a single value and can be indexed.
    
    This protocol defines the interface that must be implemented by any
    observable class that wants to support indexed access to single values.
    It extends the base BaseCarriesDistinctHook protocol with specific methods for
    indexed single value management.
    
    Classes implementing this protocol must provide:
    - Methods to get and set values at specific indices
    - Access to hooks for individual indices
    - Validation logic for indexed value changes
    
    This protocol is implemented by:
    - ObservableTuple (for individual element access)
    - ObservableList (for individual element access)
    
    Note:
        This protocol can be used directly by end users for type hints and
        interface definitions when working with indexable observables.
        The individual methods remain internal implementation details.
    """

    @abstractmethod
    def _get_indexable_single_value_hook(self, index: int) -> HookLike[T]:
        """
        INTERNAL. Do not use this method directly.
        
        Method to get the hook for the indexable single value.
        
        Returns:
            The hook for the indexable single value
        """
        ...

    @abstractmethod
    def _get_indexable_single_value(self, index: int) -> T:
        """
        Get the value at the given index.
        """
        ...

    @abstractmethod
    def _set_indexable_single_value(self, index: int, value: T) -> None:
        """
        INTERNAL. Do not use this method directly.
        
        Method to set the value at the given index.
        """
        ...