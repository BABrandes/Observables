from threading import RLock
from typing import Callable, TypeVar, TYPE_CHECKING, runtime_checkable, Protocol, Any
from .initial_sync_mode import InitialSyncMode
from .hook_nexus import HookNexus
from .base_listening import BaseListeningLike

if TYPE_CHECKING:
    from .carries_hooks import CarriesHooks

T = TypeVar("T")

@runtime_checkable
class HookLike(BaseListeningLike, Protocol[T]):
    """
    Protocol for hook objects.
    """
    
    # Properties
    @property
    def value(self) -> T:
        """
        Get the value behind this hook.
        """
        ...

    @value.setter
    def value(self, value: T) -> None:
        """
        Set the value behind this hook.
        """
        ...

    @property
    def previous_value(self) -> T:
        """
        Get the previous value behind this hook.
        """
        ...
    
    @property
    def owner(self) -> "CarriesHooks[Any]":
        """
        Get the owner of this hook.
        """
        ...
    
    @property
    def hook_nexus(self) -> "HookNexus[T]":
        """
        Get the hook nexus that this hook belongs to.
        """
        ...

    @property
    def invalidation_callback(self) -> Callable[["HookLike[T]"], tuple[bool, str]]:
        """
        The callback to be called when the value is invalidated.
        """
        ...

    @property
    def lock(self) -> RLock:
        """
        Get the lock for thread safety.
        """
        ...
    
    # State flags
    @property
    def can_be_invalidated(self) -> bool:
        """
        Check if this hook can be invalidated.
        """
        ...

    @property
    def in_submission(self) -> bool:
        """
        Check if this hook is currently being submitted.
        """
        ...

    @in_submission.setter
    def in_submission(self, value: bool) -> None:
        """
        Set if this hook is currently being submitted.
        """
        ...

    def connect_to(self, hook: "HookLike[T]", sync_mode: "InitialSyncMode") -> tuple[bool, str]:
        """
        Connect this hook to another hook.
        """
        ...

    def detach(self) -> None:
        """
        Detach this hook from the hook nexus.
        """
        ...

    def is_attached_to(self, hook: "HookLike[T]") -> bool:
        """
        Check if this hook is connected to another hook.
        """
        ...

    def is_valid_value(self, value: T) -> tuple[bool, str]:
        """
        Check if the value is valid.
        """
        ...

    def _replace_hook_nexus(self, hook_nexus: "HookNexus[T]") -> None:
        """
        Replace the hook nexus that this hook belongs to.
        """
        ...

    def deactivate(self) -> None:
        """
        Deactivate this hook. The hook will also be detached.

        No value can be submitted to this hook.
        No value can be received from this hook.
        """
        ...
    
    def activate(self, initial_value: T) -> None:
        """
        Activate this hook.
        """
        ...
    
    @property
    def is_active(self) -> bool:
        """
        Check if this hook is active.
        """
        ...