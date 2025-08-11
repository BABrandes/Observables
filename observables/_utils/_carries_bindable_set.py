from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from _internal_binding_handler import InternalBindingHandler
from _carries_bindable import CarriesBindable

T = TypeVar("T")

class CarriesBindableSet(ABC, CarriesBindable, Generic[T]):

    @abstractmethod
    def _set_set(self, set_to_set: set[T]) -> None:
        ...

    @abstractmethod
    def _get_set(self) -> set[T]:
        ...

    @abstractmethod
    def _check_set(self, set_to_check: set[T]) -> bool:
        ...

    @abstractmethod
    def _get_set_binding_handler(self) -> InternalBindingHandler[set[T]]:
        ...
    