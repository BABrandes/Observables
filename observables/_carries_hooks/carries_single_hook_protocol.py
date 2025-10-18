from typing import Protocol, Literal, TypeVar, runtime_checkable

from .carries_hooks_protocol import CarriesHooksProtocol
from .._hooks.hook_protocol import HookProtocol

HK = Literal["value"]
HV = TypeVar("HV")

@runtime_checkable
class CarriesSingleHookProtocol(CarriesHooksProtocol[HK, HV], Protocol[HV]):
    """
    Protocol for objects that carry a single hook.
    """

    @property
    def hook(self) -> HookProtocol[HV]:
        """
        Get the hook for the single value.
        """
        ...