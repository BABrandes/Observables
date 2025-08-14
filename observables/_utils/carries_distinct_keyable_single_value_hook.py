from abc import abstractmethod
from typing import Generic, TypeVar
from .hook import Hook
from .carries_distinct_hook import CarriesDistinctHook

K = TypeVar("K")
V = TypeVar("V")

class CarriesKeyableSingleValueHook(CarriesDistinctHook, Generic[K, V]):
    """
    Interface for objects that carry a single value and can be indexed.
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