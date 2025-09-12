from typing import Protocol, runtime_checkable, Mapping, TypeVar, final
from .initial_sync_mode import InitialSyncMode
from .carries_hooks import CarriesHooks
from .._hooks.owned_hook_like import OwnedHookLike

HK = TypeVar("HK")
HV = TypeVar("HV")

@runtime_checkable
class CarriesCollectiveHooks(CarriesHooks[HK, HV], Protocol[HK, HV]):
    """
    Protocol for observables that carry a set of hooks that can be used to synchronize their values.
    """ 

    def get_collective_hook_keys(self) -> set[HK]:
        ...

    def connect_multiple_hooks(self, hooks: Mapping[HK, OwnedHookLike[HV]], initial_sync_mode: InitialSyncMode) -> None:
        ...

    def is_valid_hook_values(self, values: Mapping[HK, HV]) -> tuple[bool, str]:
        ...

    #########################################################

    @property
    @final
    def _collective_hook_keys(self) -> set[HK]:
        return self.get_collective_hook_keys()

    @property
    @final
    def _collective_hooks(self) -> set[OwnedHookLike[HV]]:
        return {self.get_hook(key) for key in self._collective_hook_keys}