from typing import TypeVar, TYPE_CHECKING, runtime_checkable, Protocol, Any
from .hook_like import HookLike

if TYPE_CHECKING:
    from .._utils.base_carries_hooks import BaseCarriesHooks

T = TypeVar("T")

@runtime_checkable
class OwnedHookLike(HookLike[T], Protocol[T]):
    """
    Protocol for owned hook objects.
    """
    
    @property
    def owner(self) -> "BaseCarriesHooks[Any, Any]":
        """
        Get the owner of this hook.
        """
        ...

    def invalidate_owner(self) -> None:
        """Invalidate the owner of this hook."""
        self.owner.invalidate()