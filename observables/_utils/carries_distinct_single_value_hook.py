from abc import abstractmethod
from typing import TypeVar, runtime_checkable, Protocol
from .hook import Hook
from .base_carries_distinct_hook import BaseCarriesDistinctHook

T = TypeVar("T")

@runtime_checkable
class CarriesDistinctSingleValueHook(BaseCarriesDistinctHook, Protocol[T]):
    """
    Protocol for observables that carry a single value and can participate in bindings via. a hook.
    
    This protocol defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for single values.
    It extends the base BaseCarriesDistinctHook protocol with specific methods for
    single value management.
    
    Classes implementing this protocol must provide:
    - Methods to get and set single values
    - Validation logic for value changes
    - Access to the internal binding handler
    
    This protocol is implemented by:
    - ObservableSingleValue
    - ObservableSelectionOption (for selected_option binding)
    
    Note:
        This protocol can be used directly by end users for type hints and
        interface definitions when working with single value observables.
        The individual methods remain internal implementation details.
    """

    @abstractmethod
    def _get_single_value_hook(self) -> Hook[T]:
        """
        INTERNAL. Do not use this method directly.
        
        Method to get the hook for the single value.
        
        Returns:
            The hook for the single value
        """
        ...

    @abstractmethod
    def _get_single_value(self) -> T:
        """
        INTERNAL. Do not use this method directly.
        
        Method to get the current value of the single value.
        
        Returns:
            The current value of the single value
        """
        ...

    @abstractmethod
    def _set_single_value(self, single_value_to_set: T) -> None:
        """
        INTERNAL. Do not use this method directly.
        
        Method to set the current value of the single value.
        """
        ...