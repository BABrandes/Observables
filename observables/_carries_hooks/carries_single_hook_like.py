from typing import Protocol, Literal, TypeVar, runtime_checkable

from .carries_hooks_like import CarriesHooksLike
from .._hooks.hook_like import HookLike

HK = Literal["value"]
HV = TypeVar("HV")

@runtime_checkable
class CarriesSingleHookLike(CarriesHooksLike[HK, HV], Protocol[HV]):
    """
    Protocol for objects that carry a single hook.
    """

    @property
    def hook(self) -> HookLike[HV]:
        """
        Get the hook for the single value.
        """
        ...