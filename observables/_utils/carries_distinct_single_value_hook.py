from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from .hook import Hook
from .carries_distinct_hook import CarriesDistinctHook

T = TypeVar("T")

class CarriesDistinctSingleValueHook(CarriesDistinctHook, Generic[T]):
    """
    Abstract base class for observables that carry a single value and can participate in bindings via. a hook.
    
    This abstract base class defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for single values.
    It extends the base CarriesDistinctHook interface with specific methods for
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