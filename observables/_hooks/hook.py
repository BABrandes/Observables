from typing import Generic, TypeVar, TYPE_CHECKING, Optional, Callable
import logging
from .hook_like import HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.general import log
from threading import RLock

if TYPE_CHECKING:
    from .._utils.nexus_manager import NexusManager
    from .._utils.hook_nexus import HookNexus

T = TypeVar("T")


class Hook(HookLike[T], Generic[T]):
    """
    A hook that can be used to store a value that is not owned by any observable.
    """

    from .._utils.nexus_manager import DEFAULT_NEXUS_MANAGER

    def __init__(
        self,
        value: T,
        validate_value_in_isolation_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
        nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER,
        logger: Optional[logging.Logger] = None
        ) -> None:

        from .._utils.hook_nexus import HookNexus

        self._value = value
        self._validate_value_in_isolation_callback = validate_value_in_isolation_callback
        self._logger = logger
        self._nexus_manager = nexus_manager

        self._hook_nexus = HookNexus(nexus_manager, value, self)
        self._lock = RLock()

    @property
    def nexus_manager(self) -> "NexusManager":
        """Get the nexus manager that this hook belongs to."""
        return self._nexus_manager

    @property
    def value(self) -> T:
        """Get the value behind this hook."""
        with self._lock:
            return self._get_value()

    @property
    def value_reference(self) -> T:
        """Get the value reference behind this hook."""
        with self._lock:
            return self._get_value_reference()
    
    @property
    def previous_value(self) -> T:
        """Get the previous value behind this hook."""
        with self._lock:
            return self._get_previous_value()

    @property
    def hook_nexus(self) -> "HookNexus[T]":
        """Get the hook nexus that this hook belongs to."""
        with self._lock:
            return self._get_hook_nexus()

    @property
    def lock(self) -> RLock:
        """Get the lock for thread safety."""
        return self._lock

    def _get_value(self) -> T:
        """Get the value behind this hook."""
        return self._hook_nexus.value

    def _get_value_reference(self) -> T:
        """Get the value reference behind this hook."""
        return self._hook_nexus.value_reference

    def _get_previous_value(self) -> T:
        """Get the previous value behind this hook."""
        return self._hook_nexus.previous_value

    def _get_hook_nexus(self) -> "HookNexus[T]":
        """Get the hook nexus that this hook belongs to."""
        return self._hook_nexus

    def connect(self, hook: "HookLike[T]", initial_sync_mode: "InitialSyncMode") -> tuple[bool, str]:
        """
        Connect this hook to another hook.

        Args:
            hook: The hook to connect to
            initial_sync_mode: The initial synchronization mode
        """

        with self._lock:

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

        with self._lock:

            if len(self._hook_nexus.hooks) <= 1:
                raise ValueError("Hook is already disconnected")
            
            # Create a new isolated group for this hook
            from .._utils.hook_nexus import HookNexus
            new_group = HookNexus(self._nexus_manager, self.value, self)
            
            # Remove this hook from the current group
            self._hook_nexus.remove_hook(self)
            
            # Update this hook's group reference
            self._hook_nexus = new_group

            log(self, "detach", self._logger, True, "Successfully detached hook")
            
            # The remaining hooks in the old group will continue to be bound together
            # This effectively breaks the connection between this hook and all others

    def is_connected_to(self, hook: "HookLike[T]") -> bool:
        """
        Check if this hook is attached to another hook.
        """

        with self._lock:
            return hook in self._hook_nexus.hooks
    
    def _replace_hook_nexus(self, hook_nexus: "HookNexus[T]") -> None:
        """
        Replace the hook nexus that this hook belongs to.
        """
        
        self._hook_nexus = hook_nexus
        
        log(self, "replace_hook_nexus", self._logger, True, "Successfully replaced hook nexus")

    def validate_value_in_isolation(self, value: T) -> tuple[bool, str]:
        """
        Validate the value in isolation.
        """

        if self._validate_value_in_isolation_callback is not None:
            return self._validate_value_in_isolation_callback(value)
        else:
            return True, "No validate value in isolation callback provided"