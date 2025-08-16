import threading
from typing import Callable, Generic, Optional, TypeVar, TYPE_CHECKING, runtime_checkable, Protocol
from .sync_mode import SyncMode
from .hook_group import HookGroup

if TYPE_CHECKING:
    from .base_observable import BaseObservable

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
    def owner(self) -> "BaseObservable":
        """
        Get the owner of this hook.
        """
        ...
    
    @property
    def hook_group(self) -> "HookGroup[T]":
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
    def can_send(self) -> bool:
        """
        Check if this hook can send values.
        """
        ...

    @property
    def is_being_invalidated(self) -> bool:
        """
        Check if this hook is currently being invalidated.
        """
        ...

    @is_being_invalidated.setter
    def is_being_invalidated(self, value: bool) -> None:
        """
        Set if this hook is currently being invalidated.
        """
        ...

    def connect_to(self, hook: "HookLike[T]", sync_mode: "SyncMode") -> None:
        """
        Connect this hook to another hook.
        """
        ...

    def disconnect(self) -> None:
        """
        Disconnect this hook from the binding system.
        """
        ...

    def invalidate(self) -> tuple[bool, str]:
        """
        Invalidate this hook.
        """
        ...

    def check_binding_system(self) -> tuple[bool, str]:
        """
        Check the consistency of the binding system.
        """
        ...

    def is_connected_to(self, hook: "HookLike[T]") -> bool:
        """
        Check if this hook is connected to another hook.
        """
        ...

    def _binding_system_callback_get(self) -> T:
        """
        Get the value from the callback.
        """
        ...

    def _binding_system_callback_set(self, value: T) -> None:
        """
        Set the value via the callback.
        """
        ...

    def _binding_system_replace_hook_group(self, hook_group: "HookGroup[T]") -> None:
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
            owner: "BaseObservable",
            get_callback: Optional[Callable[[], T]] = None,
            set_callback: Optional[Callable[[T], None]] = None,
            ) -> None:

        self._owner = owner
        self._hook_group: "HookGroup[T]" = HookGroup(self)
        self._callback_get_value: Optional[Callable[[], T]] = get_callback
        self._callback_set_value: Optional[Callable[[T], None]] = set_callback
        self._is_being_invalidated = False
        self._is_currently_notifying = False
        self._lock = threading.RLock()

    @property
    def value(self) -> T:
        """Get the value behind this hook."""
        return self.hook_group.value

    @property
    def owner(self) -> "BaseObservable":
        """Get the owner of this hook."""
        return self._owner
    
    @property
    def hook_group(self) -> "HookGroup[T]":
        """Get the hook group that this hook belongs to."""
        return self._hook_group
    
    @property
    def lock(self) -> threading.RLock:
        """Get the lock for thread safety."""
        return self._lock
    
    @property
    def can_receive(self) -> bool:
        """Check if this hook can receive values."""
        return True if self._callback_set_value is not None else False
    
    @property
    def can_send(self) -> bool:
        """Check if this hook can send values."""
        return True if self._callback_get_value is not None else False
    
    @property
    def is_being_invalidated(self) -> bool:
        """Check if this hook is currently being invalidated."""
        return self._is_being_invalidated
    
    @is_being_invalidated.setter
    def is_being_invalidated(self, value: bool) -> None:
        """Set if this hook is currently being invalidated."""
        self._is_being_invalidated = value

    def connect_to(self, hook: "HookLike[T]", sync_mode: "SyncMode") -> None:
        """
        Connect this hook to another hook.
        """
        
        if sync_mode == SyncMode.UPDATE_SELF_FROM_OBSERVABLE:
            HookGroup[T].connect_hooks(hook, self)
        elif sync_mode == SyncMode.UPDATE_OBSERVABLE_FROM_SELF:
            HookGroup[T].connect_hooks(self, hook)
        else:
            raise ValueError(f"Invalid sync mode: {sync_mode}")
    
    def disconnect(self) -> None:
        """
        Disconnect this hook from the binding system.
        """
        # Check if already disconnected
        if len(self._hook_group.hooks) <= 1:
            raise ValueError("Hook is already disconnected")
        
        # Create a new isolated group for this hook
        new_group = HookGroup(self)
        
        # Remove this hook from the current group
        self._hook_group.remove_hook(self)
        
        # Update this hook's group reference
        self._hook_group = new_group
        
        # The remaining hooks in the old group will continue to be bound together
        # This effectively breaks the connection between this hook and all others
    
    def invalidate(self) -> tuple[bool, str]:
        """
        Invalidate this hook.
        """
        return self._hook_group.invalidate(self)

    def check_binding_system(self) -> tuple[bool, str]:
        """
        Check the consistency of the binding system.
        """
        return self._hook_group.check_all_hooks_synced(self._hook_group)
    
    def is_connected_to(self, hook: "HookLike[T]") -> bool:
        """
        Check if this hook is connected to another hook.
        """
        return hook in self._hook_group._hooks # type: ignore
    
    def _binding_system_callback_get(self) -> T:
        """
        Get the value from the callback.
        """
        if self._callback_get_value is None:
            raise ValueError("Callback get value is None")
        return self._callback_get_value()
    
    def _binding_system_callback_set(self, value: T) -> None:
        """
        Set the value via the callback.
        """
        if self._callback_set_value is None:
            raise ValueError("Callback set value is None")
        self._callback_set_value(value)

    def _binding_system_replace_hook_group(self, hook_group: "HookGroup[T]") -> None:
        """
        Replace the hook group that this hook belongs to.
        """
        self._hook_group = hook_group