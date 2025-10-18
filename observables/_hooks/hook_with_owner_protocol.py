from typing import TypeVar, TYPE_CHECKING, Any, Protocol, runtime_checkable
from .hook_protocol import HookProtocol

if TYPE_CHECKING:
    from .._carries_hooks.carries_hooks_protocol import CarriesHooksProtocol

T = TypeVar("T")

@runtime_checkable
class HookWithOwnerProtocol(HookProtocol[T], Protocol[T]):
    """
    Protocol for hook objects that have an owner.
    """
    
    @property
    def owner(self) -> "CarriesHooksProtocol[Any, Any]":
        """
        Get the owner of this hook.
        """
        ...

