import threading
from typing import Callable, Generic, Optional, TypeVar, TYPE_CHECKING, runtime_checkable, Protocol
from .initial_sync_mode import InitialSyncMode
from .hook_nexus import HookNexus

if TYPE_CHECKING:
    from .carries_hooks import CarriesHooks

T = TypeVar("T")

@runtime_checkable
class HookLike(Protocol[T]):
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
    def owner(self) -> "CarriesHooks":
        """
        Get the owner of this hook.
        """
        ...
    
    @property
    def hook_nexus(self) -> "HookNexus[T]":
        """
        Get the hook group that this hook belongs to.
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
    def can_receive(self) -> bool:
        """
        Check if this hook can receive values.
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

    def connect_to(self, hook: "HookLike[T]", sync_mode: "InitialSyncMode") -> None:
        """
        Connect this hook to another hook.
        """
        ...

    def detach(self) -> None:
        """
        Detach this hook from the hook group.
        """
        ...

    def submit_value(self, value: T) -> tuple[bool, str]:
        """
        Submit a single value to this hook.
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

    def invalidate(self) -> None:
        """
        Invalidates the value.
        """
        ...

    def _replace_hook_group(self, hook_group: "HookNexus[T]") -> None:
        """
        Replace the hook group that this hook belongs to.
        """
        ...

class Hook(HookLike[T], Generic[T]):
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
            owner: "CarriesHooks",
            value: T,
            invalidate_callback: Optional[Callable[["HookLike[T]"], None]] = None,
            ) -> None:

        self._owner: "CarriesHooks" = owner
        self._hook_group: "HookNexus[T]" = HookNexus(value, self)
        self._invalidate_callback: Optional[Callable[["HookLike[T]"], None]] = invalidate_callback
        self._in_submission = False
        self._lock = threading.RLock()

    @property
    def value(self) -> T:
        """Get the value behind this hook."""
        return self.hook_nexus.value

    @property
    def owner(self) -> "CarriesHooks":
        """Get the owner of this hook."""
        return self._owner
    
    @property
    def hook_nexus(self) -> "HookNexus[T]":
        """Get the hook group that this hook belongs to."""
        return self._hook_group
    
    @property
    def lock(self) -> threading.RLock:
        """Get the lock for thread safety."""
        return self._lock
    
    @property
    def can_receive(self) -> bool:
        """Check if this hook can receive values."""
        return True if self._invalidate_callback is not None else False

    @property
    def in_submission(self) -> bool:
        """Check if this hook is currently being submitted."""
        return self._in_submission
    
    @in_submission.setter
    def in_submission(self, value: bool) -> None:
        """Set if this hook is currently being submitted."""
        self._in_submission = value

    def connect_to(self, hook: "HookLike[T]", sync_mode: "InitialSyncMode") -> None:
        """
        Connect this hook to another hook.
        """
        
        if sync_mode == InitialSyncMode.SELF_IS_UPDATED:
            HookNexus[T].connect_hooks(hook, self)
        elif sync_mode == InitialSyncMode.SELF_UPDATES:
            HookNexus[T].connect_hooks(self, hook)
        else:
            raise ValueError(f"Invalid sync mode: {sync_mode}")
    
    def detach(self) -> None:
        """
        Detach this hook from the hook group.
        """
        # Check if already disconnected
        if len(self._hook_group.hooks) <= 1:
            raise ValueError("Hook is already disconnected")
        
        # Create a new isolated group for this hook
        new_group = HookNexus(self.value, self)
        
        # Remove this hook from the current group
        self._hook_group.remove_hook(self)
        
        # Update this hook's group reference
        self._hook_group = new_group
        
        # The remaining hooks in the old group will continue to be bound together
        # This effectively breaks the connection between this hook and all others
    
    def submit_value(self, value: T) -> tuple[bool, str]:
        """
        Submit a value to this hook.
        """
        self.in_submission = True
        success, msg = self._hook_group.submit_single_value(value, {self})
        self.in_submission = False
        return success, msg
    
    def is_attached_to(self, hook: "HookLike[T]") -> bool:
        """
        Check if this hook is attached to another hook.
        """
        return hook in self._hook_group._hooks # type: ignore
    
    def invalidate(self) -> None:
        """
        Invalidates the value.
        """
        if self._invalidate_callback is None:
            raise ValueError("Invalidate callback is None")
        self._invalidate_callback(self)

    def is_valid_value(self, value: T) -> tuple[bool, str]:
        """
        Check if the value is valid.
        """
        return self.owner._is_valid_value(self, value) # type: ignore
    
    def _replace_hook_group(self, hook_group: "HookNexus[T]") -> None:
        """
        Replace the hook group that this hook belongs to.
        """
        self._hook_group = hook_group