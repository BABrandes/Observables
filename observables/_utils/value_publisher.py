from typing import Generic, TypeVar
from .publisher import Publisher

T = TypeVar("T")

class ValuePublisher(Publisher, Generic[T]):
    """
    A publisher that publishes a value.
    """

    def __init__(self, value: T):
        super().__init__()
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