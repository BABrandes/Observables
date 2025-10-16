from typing import Generic, TypeVar

from _utils.base_listening import BaseListening
from .publisher import Publisher

T = TypeVar("T")

class ValuePublisher(Publisher, BaseListening, Generic[T]):
    """
    A publisher that publishes a value.
    """

    def __init__(self, value: T):
        BaseListening.__init__(self)
        Publisher.__init__(self)
        self._value = value

    def publish(self):
        super().publish()

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        self._value = value
        self.publish()