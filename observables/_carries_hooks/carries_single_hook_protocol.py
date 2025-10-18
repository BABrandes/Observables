from typing import Protocol, Literal, TypeVar, runtime_checkable

from .._hooks.hook_protocols.owned_hook_protocol import OwnedHookProtocol

from .carries_hooks_protocol import CarriesHooksProtocol

HK = Literal["value"]
HV = TypeVar("HV")

@runtime_checkable
class CarriesSingleHookProtocol(CarriesHooksProtocol[HK, HV], Protocol[HV]):
    """
    Protocol for objects that carry a single hook.
    """

    @property
    def hook(self) -> OwnedHookProtocol[HV]:
        """
        Get the hook for the single value.
        """
        ...