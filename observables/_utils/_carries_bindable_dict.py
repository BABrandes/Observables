from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Dict
from _internal_binding_handler import InternalBindingHandler
from _carries_bindable import CarriesBindable

K = TypeVar("K")
V = TypeVar("V")

class CarriesBindableDict(ABC, CarriesBindable, Generic[K, V]):

    @abstractmethod
    def _set_dict(self, dict_to_set: Dict[K, V]) -> None:
        ...

    @abstractmethod
    def _get_dict(self) -> Dict[K, V]:
        ...

    @abstractmethod
    def _check_dict(self, dict_to_check: Dict[K, V]) -> bool:
        ...

    @abstractmethod
    def _get_dict_binding_handler(self) -> InternalBindingHandler[Dict[K, V]]:
        ...
