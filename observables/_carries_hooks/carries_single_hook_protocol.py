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
    def _get_single_value_hook(self) -> OwnedHookProtocol[HV]:
        """
        Get the hook for the single value.

        ** This method is not thread-safe and should only be called by the get_single_value_hook method.

        Returns:
            The hook for the single value
        """
        ...