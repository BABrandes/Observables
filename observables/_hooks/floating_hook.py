from threading import RLock
from typing import Generic, TypeVar, Optional, TYPE_CHECKING
from logging import Logger
from .hook_like import HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.base_listening import BaseListening

if TYPE_CHECKING:
    from .._utils.hook_nexus import HookNexus

T = TypeVar("T")

class FloatingHook(HookLike[T], BaseListening, Generic[T]):
    """
    A floating hook that can be used to store a value that is not owned by any observable.
    """

    def __init__(self, value: T, logger: Optional[Logger] = None):
        super().__init__()  # Initialize BaseListening
        self._value = value
        self._previous_value = value
        self._logger = logger
        self._lock = RLock()
        self._hook_nexus: Optional["HookNexus[T]"] = None
        self._in_submission = False
        
        # Create a simple hook nexus for this floating hook
        from .._utils.hook_nexus import HookNexus
        self._hook_nexus = HookNexus(value, self)

    @property
    def value(self) -> T:
        """Get the value behind this hook."""
        with self._lock:
            if not self.is_active:
                raise ValueError("Hook is deactivated")
            assert self._hook_nexus is not None
            return self._hook_nexus.value
    
    @property
    def previous_value(self) -> T:
        """Get the previous value behind this hook."""
        with self._lock:
            if not self.is_active:
                raise ValueError("Hook is deactivated")
            assert self._hook_nexus is not None
            return self._hook_nexus.previous_value

    @property
    def hook_nexus(self) -> "HookNexus[T]":
        """Get the hook nexus that this hook belongs to."""
        with self._lock:
            if not self.is_active:
                raise ValueError("Hook is deactivated")
            assert self._hook_nexus is not None
            return self._hook_nexus
    
    @property
    def lock(self) -> RLock:
        """Get the lock for thread safety."""
        return self._lock
    
    @property
    def can_be_invalidated(self) -> bool:
        """Check if this hook can be invalidated."""
        return False  # Floating hooks don't support invalidation

    def invalidate(self) -> None:
        """Invalidate this hook."""
        raise ValueError("Floating hooks cannot be invalidated")

    @property
    def in_submission(self) -> bool:
        """Check if this hook is currently being submitted."""
        return self._in_submission
    
    @in_submission.setter
    def in_submission(self, value: bool) -> None:
        """Set if this hook is currently being submitted."""
        self._in_submission = value

    def connect(self, hook: "HookLike[T]", initial_sync_mode: "InitialSyncMode") -> tuple[bool, str]:
        """Connect this hook to another hook."""
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        if hook is None:  # type: ignore
            raise ValueError("Cannot connect to None hook")
        if not hook.is_active:
            raise ValueError("Hook is deactivated")
        
        from .._utils.hook_nexus import HookNexus
        if initial_sync_mode == InitialSyncMode.USE_CALLER_VALUE:
            success, msg = HookNexus[T].connect_hooks(self, hook)
        elif initial_sync_mode == InitialSyncMode.USE_TARGET_VALUE:
            success, msg = HookNexus[T].connect_hooks(hook, self)
        else:
            raise ValueError(f"Invalid sync mode: {initial_sync_mode}")

        return success, msg
    
    def disconnect(self) -> None:
        """Disconnect this hook from the hook nexus."""
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        assert self._hook_nexus is not None
        if len(self._hook_nexus.hooks) <= 1:
            raise ValueError("Hook is already disconnected")
        
        # Create a new isolated group for this hook
        from .._utils.hook_nexus import HookNexus
        new_group = HookNexus(self.value, self)
        
        # Remove this hook from the current group
        self._hook_nexus.remove_hook(self)
        
        # Update this hook's group reference
        self._hook_nexus = new_group
    
    def submit_single_value(self, value: T) -> tuple[bool, str]:
        """Submit a value to this hook."""
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        assert self._hook_nexus is not None
        self.in_submission = True
        success, msg = self._hook_nexus.submit_single_value(
            value=value,
            hooks_not_to_invalidate=set(),
            hooks_to_consider=None,
        )
        self.in_submission = False
        self._notify_listeners()
        return success, msg
    
    def is_connected_to(self, hook: "HookLike[T]") -> bool:
        """Check if this hook is connected to another hook."""
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        assert self._hook_nexus is not None
        return hook in self._hook_nexus._hooks  # type: ignore
    
    def is_valid_value(self, value: T) -> tuple[bool, str]:
        """Check if the value is valid."""
        return True, "Floating hooks accept any value"  # Floating hooks don't validate
    
    def _replace_hook_nexus(self, hook_nexus: "HookNexus[T]") -> None:
        """Replace the hook nexus that this hook belongs to."""
        if not self.is_active:
            raise ValueError("Hook is deactivated")
        self._hook_nexus = hook_nexus

    def deactivate(self) -> None:
        """Deactivate this hook."""
        with self._lock:
            if not self.is_active:
                raise ValueError("Hook is already deactivated")
            assert self._hook_nexus is not None
            self._hook_nexus.remove_hook(self)
            self._hook_nexus = None
    
    def activate(self, initial_value: T) -> None:
        """Activate this hook."""
        with self._lock:
            if self.is_active:
                raise ValueError("Hook is already activated")
            from .._utils.hook_nexus import HookNexus
            self._hook_nexus = HookNexus(initial_value, self)

    @property
    def is_active(self) -> bool:
        """Check if this hook is active."""
        return self._hook_nexus is not None