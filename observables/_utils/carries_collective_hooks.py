from typing import Protocol, TYPE_CHECKING, Any, runtime_checkable, Mapping
from .carries_hooks import CarriesHooks

if TYPE_CHECKING:
    from .hook_nexus import HookNexus
    from .hook import HookLike

@runtime_checkable
class CarriesCollectiveHooks(CarriesHooks, Protocol):
    """
    Protocol for observables that carry a set of hooks that can be used to synchronize their values.
    """ 

    @property
    def collective_hooks(self) -> set["HookLike[Any]"]:
        ...

    def _are_valid_values(self, values: Mapping["HookNexus[Any]", Any]) -> tuple[bool, str]:
        ...