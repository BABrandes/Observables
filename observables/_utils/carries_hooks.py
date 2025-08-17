from typing import Protocol, TYPE_CHECKING, Any, runtime_checkable

if TYPE_CHECKING:
    from .hook import HookLike

@runtime_checkable
class CarriesHooks(Protocol):
    """
    Protocol for observables that carry a set of hooks.
    """

    @property
    def hooks(self) -> set["HookLike[Any]"]:
        ...

    def _is_valid_value(self, hook: "HookLike[Any]", value: Any) -> tuple[bool, str]:
        ...

    def _invalidate_hooks(self, hooks: set["HookLike[Any]"]) -> None:
        ...