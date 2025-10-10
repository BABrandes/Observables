from typing import Mapping, Optional, Generic, TypeVar, Protocol, Any, runtime_checkable
from typing_extensions import Self
from logging import Logger

HK = TypeVar("HK")
HV = TypeVar("HV", covariant=True)

class ObservableSerializable(Generic[HK, HV]):
    @property
    def dict_of_value_references_for_serialization(self) -> Mapping[HK, HV]:
        ...

    @classmethod
    def create_from_values(
        cls: type[Self],
        values: Mapping[HK, HV],
        logger: Optional[Logger] = None,
    ) -> Self:
        return cls(values, logger=logger) # type: ignore

O = TypeVar("O", bound=ObservableSerializable[Any, Any], covariant=True)

@runtime_checkable
class HasSerializable(Protocol[O]):
    @property
    def as_serializable(self) -> O:
        ...