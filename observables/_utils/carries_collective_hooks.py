from typing import Protocol, Any, runtime_checkable, Mapping, TypeVar, final
from .initial_sync_mode import InitialSyncMode
from .carries_hooks import CarriesHooks
from .hook import HookLike

HK = TypeVar("HK")

@runtime_checkable
class CarriesCollectiveHooks(CarriesHooks[HK], Protocol[HK]):
    """
    Protocol for observables that carry a set of hooks that can be used to synchronize their values.
    """ 

    def get_collective_hook_keys(self) -> set[HK]:
        ...

    def connect_multiple_hooks(self, hooks: Mapping[HK, HookLike[Any]], initial_sync_mode: InitialSyncMode) -> None:
        ...

    def is_valid_hook_values(self, values: Mapping[HK, Any]) -> tuple[bool, str]:
        ...

    #########################################################

    @property
    @final
    def _collective_hook_keys(self) -> set[HK]:
        return self.get_collective_hook_keys()

    @property
    @final
    def _collective_hooks(self) -> set[HookLike[Any]]:
        return {self.get_hook(key) for key in self._collective_hook_keys}