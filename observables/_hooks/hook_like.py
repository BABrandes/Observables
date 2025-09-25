from threading import RLock
from typing import TypeVar, runtime_checkable, Protocol, TYPE_CHECKING, Literal
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

        ** The returned value is a copy, so modifying is allowed.
        """
        ...

    @property
    def value_reference(self) -> T:
        """
        Get the value reference behind this hook.

        *This is a reference to the value behind this hook, not a copy. Do not modify it!*

        Returns:
            The value reference behind this hook.
        """
        ...

    @property
    def previous_value(self) -> T:
        """
        Get the previous value behind this hook.

        ** The returned value is a copy, so modifying is allowed.
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

    def _internal_invalidate(self, submitted_value: T) -> None:
        """
        Internal invalidate for the nexus to use before the hook is invalidated.
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

    def _replace_hook_nexus(self, hook_nexus: "HookNexus[T]") -> None:
        """
        Replace the hook nexus that this hook belongs to.
        """
        ...

    def submit_single_value(self, value: T) -> tuple[bool, str]:
        """
        Submit a value to this hook. This will not invalidate the hook!

        Args:
            value: The value to submit
        """
        ...

    def is_valid_value(self, value: T, ) -> tuple[bool, str]:
        """
        Check if the value is valid for submission.
        """

        ...

    def is_valid_value_in_isolation(self, value: T) -> tuple[Literal[True, False, "InternalInvalidationNeeded"], str]:
        """
        Check if the value is valid for submission in isolation.
        """
        ...