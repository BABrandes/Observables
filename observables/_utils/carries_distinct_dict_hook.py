from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from .hook import Hook
from .carries_distinct_hook import CarriesDistinctHook

K = TypeVar("K")
V = TypeVar("V")

class CarriesDistinctDictHook(CarriesDistinctHook, Generic[K, V]):
    """
    Abstract base class for observables that carry a dictionary and can participate in bindings via. a hook.
    
    This abstract base class defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for dictionaries via. a hook.
    It extends the base CarriesDistinctHook interface with specific methods for
    dictionary management.
    
    Classes implementing this interface must provide:
    - Methods to get and set dictionaries
    - Validation logic for dictionary changes
    - Access to the internal hook
    
    This interface is implemented by:
    - ObservableDict
    
    Note:
        This is an internal interface not intended for direct use by end users.
        Use the concrete ObservableDict class instead.
    """

    @abstractmethod
    def _get_dict_hook(self) -> Hook[dict[K, V]]:
        """
        INTERNAL. Do not use this method directly.
        
        Method to get the hook for dictionary.
        
        This method provides access to the internal hook that
        manages bidirectional bindings for this observable. The binding
        system uses this hook to establish and manage connections.
        
        Returns:
            The internal hook for dictionary
            
        Note:
            This is an internal method called by the hook system.
            It should not be called directly by users.
        """
        ...

    @abstractmethod
    def _get_dict_value(self) -> dict[K, V]:
        """
        INTERNAL. Do not use this method directly.
        
        Method to get dictionary for binding system.
        
        Returns:
            The current dictionary value
        """
        ...

    @abstractmethod
    def _set_dict_value(self, dict_to_set: dict[K, V]) -> None:
        """
        INTERNAL. Do not use this method directly.
        
        Method to set the current value of the dictionary.
        """
        ...
    