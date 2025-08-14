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
        Get the hook for the keyable single value.

        Args:
            key: The key to get the hook for

        Returns:
            The hook for the keyable single value
        """
        ...

    @abstractmethod
    def get_keyable_single_value(self, key: K) -> V:
        """
        Get the value at the given key.
        """
        ...