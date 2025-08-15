from abc import abstractmethod
from typing import Generic, TypeVar
from .hook import Hook
from .base_carries_distinct_hook import BaseCarriesDistinctHook

K = TypeVar("K")
V = TypeVar("V")

class CarriesDistinctKeyableSingleValueHook(BaseCarriesDistinctHook, Generic[K, V]):
    """
    Protocol for objects that carry a single value and can be keyed.
    
    This protocol defines the interface that must be implemented by any
    observable class that wants to support keyed access to single values.
    It extends the base BaseCarriesDistinctHook protocol with specific methods for
    keyed single value management.
    
    Classes implementing this protocol must provide:
    - Methods to get and set values at specific keys
    - Access to hooks for individual keys
    - Validation logic for keyed value changes
    
    This protocol is implemented by:
    - ObservableDict (for individual key-value pair access)
    
    Note:
        This protocol can be used directly by end users for type hints and
        interface definitions when working with keyable observables.
        The individual methods remain internal implementation details.
    """

    @abstractmethod
    def _get_keyable_single_value_hook(self, key: K) -> Hook[V]:
        """
        INTERNAL. Do not use this method directly.

        Method to get the hook for the keyable single value.
        
        Args:
            key: The key to get the hook for

        Returns:
            The hook for the keyable single value
        """
        ...

    @abstractmethod
    def _get_keyable_single_value(self, key: K) -> V:
        """
        INTERNAL. Do not use this method directly.

        Method to get the value at the given key.

        Returns:
            The value at the given key
        """
        ...

    @abstractmethod
    def _set_keyable_single_value(self, key: K, value: V) -> None:
        """
        INTERNAL. Do not use this method directly.

        Method to set the value at the given key.
        """
        ...