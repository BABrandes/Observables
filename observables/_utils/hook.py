import threading
import logging
from typing import Callable, Generic, Optional, TypeVar, TYPE_CHECKING, runtime_checkable, Protocol, Any
from .initial_sync_mode import InitialSyncMode
from .hook_nexus import HookNexus
from .base_listening import BaseListeningLike, BaseListening
from .general import log

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
    def lock(self) -> threading.RLock:
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

class Hook(HookLike[T], BaseListening, Generic[T]):
    """
    A simple hook that provides value access and basic capabilities.
    
    This class focuses on:
    - Value access via callbacks
    - Basic capabilities (sending/receiving)
    - Owner reference and auxiliary information
    
    Complex binding logic is delegated to the BindingSystem class.
    """

    def __init__(
            self,
            owner: "CarriesHooks[Any]",
            value: T,
            invalidate_callback: Optional[Callable[["HookLike[T]"], tuple[bool, str]]] = None,
            logger: Optional[logging.Logger] = None
            ) -> None:

        super().__init__()  # Initialize BaseListening
        self._owner: "CarriesHooks[Any]" = owner
        self._hook_nexus: "Optional[HookNexus[T]]" = None
        self._invalidate_callback: Optional[Callable[["HookLike[T]"], tuple[bool, str]]] = invalidate_callback
        self._in_submission = False
        self._lock = threading.RLock()
        self._logger = logger

        self.activate(value)

        log(self, "Hook.__init__", self._logger, True, "Successfully initialized hook")

    @property
    def value(self) -> T:
        """Get the value behind this hook."""
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        assert self._hook_nexus is not None
        return self.hook_nexus.value
    
    @value.setter
    def value(self, value: T) -> None:
        """Set the value behind this hook."""
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        assert self._hook_nexus is not None
        success, msg = self._hook_nexus.submit_single_value(value, {self})  # Ignore self to prevent double notifications
        log(self, "value.setter", self._logger, success, msg)

    @property
    def previous_value(self) -> T:
        """Get the previous value behind this hook."""
        return self.hook_nexus.previous_value

    @property
    def owner(self) -> "CarriesHooks[Any]":
        """Get the owner of this hook."""
        return self._owner
    
    @property
    def hook_nexus(self) -> "HookNexus[T]":
        """Get the hook nexus that this hook belongs to."""
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        assert self._hook_nexus is not None
        return self._hook_nexus
    
    @property
    def invalidation_callback(self) -> Callable[["HookLike[T]"], tuple[bool, str]]:
        """
        The callback to be called when the value is invalidated.
        """

        if self._invalidate_callback is None:
            raise ValueError("Invalidate callback is None")     
        return self._invalidate_callback
    
    @property
    def lock(self) -> threading.RLock:
        """Get the lock for thread safety."""
        return self._lock
    
    @property
    def can_be_invalidated(self) -> bool:
        """Check if this hook can be invalidated."""
        return True if self._invalidate_callback is not None else False

    @property
    def in_submission(self) -> bool:
        """Check if this hook is currently being submitted."""
        return self._in_submission
    
    @in_submission.setter
    def in_submission(self, value: bool) -> None:
        """Set if this hook is currently being submitted."""
        self._in_submission = value

    def connect_to(self, hook: "HookLike[T]", sync_mode: "InitialSyncMode") -> tuple[bool, str]:
        """
        Connect this hook to another hook.
        """

        if not self.is_active:
            raise ValueError("Hook is deactivated")
        if not hook.is_active:
            raise ValueError("Hook is deactivated")
        
        if sync_mode == InitialSyncMode.PUSH_TO_TARGET:
            success, msg = HookNexus[T].connect_hooks(self, hook, sync_mode)
        elif sync_mode == InitialSyncMode.PULL_FROM_TARGET:
            success, msg = HookNexus[T].connect_hooks(self, hook, sync_mode)
        else:
            raise ValueError(f"Invalid sync mode: {sync_mode}")

        log(self, "connect_to", self._logger, success, msg)

        return success, msg
    
    def detach(self) -> None:
        """
        Detach this hook from the hook group.
        """
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        assert self._hook_nexus is not None
        if len(self._hook_nexus.hooks) <= 1:
            raise ValueError("Hook is already disconnected")
        
        # Create a new isolated group for this hook
        new_group = HookNexus(self.value, self)
        
        # Remove this hook from the current group
        self._hook_nexus.remove_hook(self)
        
        # Update this hook's group reference
        self._hook_nexus = new_group

        log(self, "detach", self._logger, True, "Successfully detached hook")
        
        # The remaining hooks in the old group will continue to be bound together
        # This effectively breaks the connection between this hook and all others
    
    def submit_value(self, value: T) -> tuple[bool, str]:
        """
        Submit a value to this hook.
        """
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        assert self._hook_nexus is not None
        self.in_submission = True
        success, msg = self._hook_nexus.submit_single_value(value, {self})
        self.in_submission = False
        log(self, "submit_value", self._logger, success, msg)
        return success, msg
    
    def is_attached_to(self, hook: "HookLike[T]") -> bool:
        """
        Check if this hook is attached to another hook.
        """
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        assert self._hook_nexus is not None
        return hook in self._hook_nexus._hooks # type: ignore
    
    def is_valid_value(self, value: T) -> tuple[bool, str]:
        """
        Check if the value is valid.
        """
        success, msg = self.owner._is_valid_value(self, value) # type: ignore
        log(self, "is_valid_value", self._logger, success, msg)
        return success, msg
    
    def _replace_hook_nexus(self, hook_nexus: "HookNexus[T]") -> None:
        """
        Replace the hook nexus that this hook belongs to.
        """
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        self._hook_nexus = hook_nexus
        log(self, "replace_hook_nexus", self._logger, True, "Successfully replaced hook nexus")

    def deactivate(self) -> None:
        """
        Deactivate this hook. The hook will also be detached.
        
        No value can be submitted to this hook.
        No value can be received from this hook.
        """
        if not self.is_active:
            raise ValueError("Hook is already deactivated")
        assert self._hook_nexus is not None
        self._hook_nexus.remove_hook(self)
        self._hook_nexus = None
        log(self, "deactivate", self._logger, True, "Successfully deactivated hook")
    
    def activate(self, initial_value: T) -> None:
        """
        Activate this hook.
        
        This hook can now be used to submit and receive values.
        """
        if self.is_active:
            raise ValueError("Hook is already activated")
        self._hook_nexus = HookNexus(initial_value, self)
        log(self, "activate", self._logger, True, "Successfully activated hook")

    @property
    def is_active(self) -> bool:
        """
        Check if this hook is active.
        """
        return self._hook_nexus is not None