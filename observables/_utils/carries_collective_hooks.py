from typing import Protocol, TYPE_CHECKING, Any, runtime_checkable, Mapping, TypeVar
from .initial_sync_mode import InitialSyncMode
from .carries_hooks import CarriesHooks
from .hook import HookLike

if TYPE_CHECKING:
    from .hook_nexus import HookNexus

HK = TypeVar("HK")

@runtime_checkable
class CarriesCollectiveHooks(CarriesHooks[HK], Protocol[HK]):
    """
    Protocol for observables that carry a set of hooks that can be used to synchronize their values.
    """ 

    @property
    def _collective_hooks(self) -> set["HookLike[Any]"]:
        ...

    def attach_multiple(self, hooks: Mapping[HK, HookLike[Any]], initial_sync_mode: InitialSyncMode) -> None:
        ...

    def _are_valid_values(self, values: Mapping["HookNexus[Any]", Any]) -> tuple[bool, str]:
        ...