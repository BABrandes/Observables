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

    @property
    def can_be_invalidated(self) -> bool:
        """Check if this hook can be invalidated."""
        return True

    def invalidate(self) -> None:
        """Invalidate this hook."""
        self.owner.invalidate()