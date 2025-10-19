from typing import TypeVar, Protocol, runtime_checkable, Literal

from .._carries_hooks.carries_hooks_protocol import CarriesHooksProtocol
from .._carries_hooks.carries_single_hook_protocol import CarriesSingleHookProtocol
from .._hooks.hook_aliases import Hook

T = TypeVar("T")

@runtime_checkable
class ObservableSingleValueProtocol(CarriesSingleHookProtocol[T], CarriesHooksProtocol[Literal["value"], T], Protocol[T]):
    """
    Protocol for observable single value objects.
    """
    
    @property
    def value(self) -> T:
        """
        Get the value.
        """
        ...
    
    @value.setter
    def value(self, value: T) -> None:
        """
        Set the value.
        """
        ...

    def change_value(self, new_value: T) -> None:
        """
        Change the value (lambda-friendly method).
        """
        ...

    @property
    def hook(self) -> Hook[T]: # type: ignore
        """
        Get the hook for the value.
        """
        ...
    