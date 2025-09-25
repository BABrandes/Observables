from threading import RLock
import logging
from typing import Callable, Generic, Optional, TypeVar, TYPE_CHECKING, Any, Literal
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.base_listening import BaseListening
from .owned_hook_like import OwnedHookLike
from .._utils.general import log
from .hook_like import HookLike

if TYPE_CHECKING:
    from .._utils.carries_hooks import CarriesHooks
    from .._utils.hook_nexus import HookNexus

T = TypeVar("T")

class OwnedHook(OwnedHookLike[T], BaseListening, Generic[T]):
    """
    A owned hook that provides value access and basic capabilities.
    
    This class focuses on:
    - Value access via callbacks
    - Basic capabilities (sending/receiving)
    - Owner reference and auxiliary information
    
    Complex binding logic is delegated to the BindingSystem class.
    """

    def __init__(
            self,
            owner: "CarriesHooks[Any, Any]",
            initial_value: T,
            invalidate_callback: Optional[Callable[["HookLike[T]"], tuple[bool, str]]] = None,
            internal_invalidation_callback: Optional[Callable[["T"], None]] = None,
            logger: Optional[logging.Logger] = None
            ) -> None:

        super().__init__()  # Initialize BaseListening
        self._owner: "CarriesHooks[Any, T]" = owner
        self._hook_nexus: "HookNexus[T]"
        self._invalidate_callback: Optional[Callable[["HookLike[T]"], tuple[bool, str]]] = invalidate_callback
        self._internal_invalidation_callback: Optional[Callable[[T], None]] = internal_invalidation_callback
        self._in_submission = False
        self._lock = RLock()
        self._logger = logger

        from .._utils.hook_nexus import HookNexus

        self._hook_nexus = HookNexus(initial_value, self)

        log(self, "BidirectionalHook.__init__", self._logger, True, "Successfully initialized hook")

    @property
    def value(self) -> T:
        """Get the value behind this hook."""
        with self._lock:
            assert self._hook_nexus is not None
            return self._hook_nexus.value

    @property
    def value_reference(self) -> T:
        """Get the value reference behind this hook."""
        with self._lock:
            assert self._hook_nexus is not None
            return self._hook_nexus.value_reference
    
    @property
    def previous_value(self) -> T:
        """Get the previous value behind this hook."""
        with self._lock:
            assert self._hook_nexus is not None
            return self._hook_nexus.previous_value

    @property
    def owner(self) -> "CarriesHooks[Any, T]":
        """Get the owner of this hook."""
        return self._owner
    
    @property
    def hook_nexus(self) -> "HookNexus[T]":
        """Get the hook nexus that this hook belongs to."""
        with self._lock:
            assert self._hook_nexus is not None
            return self._hook_nexus
    
    @property
    def lock(self) -> RLock:
        """Get the lock for thread safety."""
        return self._lock
    
    @property
    def can_be_invalidated(self) -> bool:
        """Check if this hook can be invalidated."""
        return True if self._invalidate_callback is not None else False

    def invalidate(self) -> None:
        """Invalidate this hook."""
        if self._invalidate_callback is None:
            raise ValueError("Invalidate callback is None")
        self._invalidate_callback(self)

    def _internal_invalidate(self, submitted_value: T) -> None:
        """Internal invalidate for the nexus to use before the hook is invalidated."""
        if self._internal_invalidation_callback:
            self._internal_invalidation_callback(submitted_value)
        
    @property
    def in_submission(self) -> bool:
        """Check if this hook is currently being submitted."""
        return self._in_submission
    
    @in_submission.setter
    def in_submission(self, value: bool) -> None:
        """Set if this hook is currently being submitted."""
        self._in_submission = value

    def connect(self, hook: "HookLike[T]", initial_sync_mode: "InitialSyncMode") -> tuple[bool, str]:
        """
        Connect this hook to another hook.

        Args:
            hook: The hook to connect to
            initial_sync_mode: The initial synchronization mode
        """

        if hook is None: # type: ignore
            raise ValueError("Cannot connect to None hook")
        
        if initial_sync_mode == InitialSyncMode.USE_CALLER_VALUE:
            from .._utils.hook_nexus import HookNexus
            success, msg = HookNexus[T].connect_hooks(self, hook)
        elif initial_sync_mode == InitialSyncMode.USE_TARGET_VALUE:
            from .._utils.hook_nexus import HookNexus
            success, msg = HookNexus[T].connect_hooks(hook, self)
        else:
            raise ValueError(f"Invalid sync mode: {initial_sync_mode}")

        log(self, "connect_to", self._logger, success, msg)

        return success, msg
    
    def disconnect(self) -> None:
        """
        Detach this hook from the hook group.
        """
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

        log(self, "detach", self._logger, True, "Successfully detached hook")
        
        # The remaining hooks in the old group will continue to be bound together
        # This effectively breaks the connection between this hook and all others

    def _is_valid_value_as_part_of_owner(self, value: T) -> tuple[Literal[True, False, "InternalInvalidationNeeded"], str]:
        """
        Check if the value is valid as part of the owner.

        *This method does not check if the value is valid as part of the hook nexus.*
        """

        hook_key = self._owner.get_hook_key(self)

        success, msg = self._owner.is_valid_value(hook_key, value)
        if success == False:
            return False, msg
        else:
            return True, "Value is valid"
    
    def is_connected_to(self, hook: "HookLike[T]") -> bool:
        """
        Check if this hook is attached to another hook.
        """
        assert self._hook_nexus is not None
        return hook in self._hook_nexus._hooks # type: ignore
    
    def _replace_hook_nexus(self, hook_nexus: "HookNexus[T]") -> None:
        """
        Replace the hook nexus that this hook belongs to.
        """
        
        old_nexus = self._hook_nexus
        self._hook_nexus = hook_nexus
        
        # Update the owner's cache if it has one
        if hasattr(self._owner, '_update_hook_cache'):
            self._owner._update_hook_cache(self, old_nexus)  # type: ignore
        
        log(self, "replace_hook_nexus", self._logger, True, "Successfully replaced hook nexus")