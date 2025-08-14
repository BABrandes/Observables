from abc import abstractmethod
from typing import Callable, Generic, TypeVar
from .hook import Hook
from .carries_distinct_hook import CarriesDistinctHook

T = TypeVar("T")

class CarriesDistinctIndexableSingleValueHook(CarriesDistinctHook, Generic[T]):
    """
    Interface for objects that carry a single value and can be indexed.
    """

    @abstractmethod
    def _get_indexable_single_value_hook(self, index: int) -> Hook[T]:
        """
        Get the hook for the indexable single value.
        """
        ...

    @abstractmethod
    def get_indexable_single_value(self, index: int) -> T:
        """
        Get the value at the given index.
        """
        ...