from typing import Protocol, TYPE_CHECKING, Any, runtime_checkable, TypeVar, Optional
from .initial_sync_mode import InitialSyncMode

if TYPE_CHECKING:
    from .hook_like import HookLike

HK = TypeVar("HK", contravariant=True)

@runtime_checkable
class CarriesHooks(Protocol[HK]):
    """
    Protocol for observables that carry a set of hooks.
    """

    @property
    def hooks(self) -> set["HookLike[Any]"]:
        ...

    def get_component_value(self, key: HK) -> Any:
        ...

    def get_component_hook(self, key: HK) -> "HookLike[Any]":
        ...

    def connect(self, hook: "HookLike[Any]", to_key: HK, initial_sync_mode: InitialSyncMode) -> None:
        ...

    def disconnect(self, key: Optional[HK]) -> None:
        ...

    def _is_valid_value(self, hook: "HookLike[Any]", value: Any) -> tuple[bool, str]:
        ...

    def _invalidate_hooks(self, hooks: set["HookLike[Any]"]) -> None:
        ...