from typing import TypeVar, TYPE_CHECKING, Any, Protocol, runtime_checkable
from .hook_like import HookLike

if TYPE_CHECKING:
    from .._carries_hooks.carries_hooks_like import CarriesHooksLike

T = TypeVar("T")

@runtime_checkable
class HookWithOwnerLike(HookLike[T], Protocol[T]):
    """
    Protocol for hook objects that have an owner.
    """
    
    @property
    def owner(self) -> "CarriesHooksLike[Any, Any]":
        """
        Get the owner of this hook.
        """
        ...

