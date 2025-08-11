from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from _internal_binding_handler import InternalBindingHandler
from _carries_bindable import CarriesBindable

T = TypeVar("T")

class CarriesBindableList(ABC,CarriesBindable, Generic[T]):

    @abstractmethod
    def _set_list(self, list_to_set: list[T]) -> None:
        ...

    @abstractmethod
    def _get_list(self) -> list[T]:
        ...

    @abstractmethod
    def _check_list(self, list_to_check: list[T]) -> bool:
        ...

    @abstractmethod
    def _get_list_binding_handler(self) -> InternalBindingHandler[list[T]]:
        ...
    