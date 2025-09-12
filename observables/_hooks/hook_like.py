from threading import RLock
from typing import TypeVar, runtime_checkable, Protocol, TYPE_CHECKING
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.base_listening import BaseListeningLike

if TYPE_CHECKING:
    from .._utils.hook_nexus import HookNexus

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

    @property
    def previous_value(self) -> T:
        """
        Get the previous value behind this hook.
        """
        ...
    
    @property
    def hook_nexus(self) -> "HookNexus[T]":
        """
        Get the hook nexus that this hook belongs to.
        """
        ...

    @property
    def lock(self) -> RLock:
        """
        Get the lock for thread safety.
        """
        ...

    def invalidate(self) -> None:
        """Invalidate this hook."""
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

    def connect(self, hook: "HookLike[T]", initial_sync_mode: "InitialSyncMode") -> tuple[bool, str]:
        """
        Connect this hook to another hook.

        Args:
            hook: The hook to connect to
            initial_sync_mode: The initial synchronization mode
        """
        ...

    def disconnect(self) -> None:
        """
        Disconnect this hook from the hook nexus.

        The hook will be disconnected.
        """
        ...

    def is_connected_to(self, hook: "HookLike[T]") -> bool:
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

    def submit_single_value(self, value: T) -> tuple[bool, str]:
        """
        Submit a value to this hook.
        """
        ...