from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from _internal_binding_handler import InternalBindingHandler
from _carries_bindable import CarriesBindable

T = TypeVar("T")

class CarriesBindableSingleValue(ABC, CarriesBindable, Generic[T]):

    @abstractmethod
    def _set_single_value(self, single_value_to_set: T) -> None:
        ...
    
    @abstractmethod
    def _get_single_value(self) -> T:
        ...

    @abstractmethod
    def _check_single_value(self, single_value_to_check: T) -> bool:
        ...

    @abstractmethod
    def _get_single_value_binding_handler(self) -> InternalBindingHandler[T]:
        ...