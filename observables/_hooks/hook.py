from typing import Generic, TypeVar, Optional, Callable
import logging
from .hook_like import HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.general import log
from threading import RLock
from .._utils.base_listening import BaseListening

from .._utils.nexus_manager import NexusManager
from .._utils.hook_nexus import HookNexus
from .._utils.default_nexus_manager import DEFAULT_NEXUS_MANAGER

T = TypeVar("T")


class Hook(HookLike[T], BaseListening, Generic[T]):
    """
    A standalone hook in the new hook-based architecture.
    
    This represents a single value that can participate in the sync system without
    being owned by a specific observable. Hooks are grouped into HookNexus instances
    that share the same value and can be synchronized together.
    
    In the new architecture, hooks replace the old binding system and provide:
    - Value storage and retrieval
    - Validation through callbacks
    - Listener notification support
    - Connection to other hooks via HookNexus
    """

    def __init__(
        self,
        value: T,
        validate_value_in_isolation_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
        nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER,
        logger: Optional[logging.Logger] = None
        ) -> None:

        from .._utils.hook_nexus import HookNexus

        BaseListening.__init__(self, logger)
        self._value = value
        self._validate_value_in_isolation_callback = validate_value_in_isolation_callback
        self._nexus_manager = nexus_manager

        self._hook_nexus = HookNexus(value, hooks={self}, nexus_manager=nexus_manager, logger=logger)
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

    def connect_hook(self, hook: "HookLike[T]", initial_sync_mode: "InitialSyncMode") -> tuple[bool, str]:
        """
        Connect this hook to another hook in the new architecture.

        This method merges the hook nexuses of both hooks, allowing them to share
        the same value and be synchronized together. This replaces the old binding
        system with a more flexible hook-based approach.

        Args:
            hook: The hook to connect to
            initial_sync_mode: The initial synchronization mode
            
        Returns:
            Tuple of (success: bool, message: str)
        """

        with self._lock:

            if hook is None: # type: ignore
                raise ValueError("Cannot connect to None hook")
            
            if initial_sync_mode == InitialSyncMode.USE_CALLER_VALUE:
                from .._utils.hook_nexus import HookNexus
                success, msg = HookNexus[T].connect_hook_pairs((self, hook))
            elif initial_sync_mode == InitialSyncMode.USE_TARGET_VALUE:
                from .._utils.hook_nexus import HookNexus
                success, msg = HookNexus[T].connect_hook_pairs((hook, self))
            else:
                raise ValueError(f"Invalid sync mode: {initial_sync_mode}")

            log(self, "connect_to", self._logger, success, msg)

            return success, msg
    
    def disconnect(self) -> None:
        """
        Disconnect this hook from the hook nexus.

        If this is the corresponding nexus has only this one hook, nothing will happen.
        """

        with self._lock:

            if self not in self._hook_nexus.hooks:
                raise ValueError("Hook is already disconnected")
            
            if len(self._hook_nexus.hooks) <= 1:
                # If we're the last hook, we're already effectively disconnected
                return
            
            # Create a new isolated nexus for this hook
            from .._utils.hook_nexus import HookNexus
            new_group = HookNexus(self.value, hooks={self}, nexus_manager=self._nexus_manager, logger=self._logger)
            
            # Remove this hook from the current nexus
            self._hook_nexus.remove_hook(self)
            
            # Update this hook's nexus reference
            self._hook_nexus = new_group

            log(self, "detach", self._logger, True, "Successfully detached hook")
            
            # The remaining hooks in the old nexus will continue to be bound together
            # This effectively breaks the connection between this hook and all others

    def is_connected_to(self, hook: "HookLike[T]") -> bool:
        """
        Check if this hook is connected to another hook.
        """

        with self._lock:
            return hook in self._hook_nexus.hooks
    
    def _replace_hook_nexus(self, hook_nexus: "HookNexus[T]") -> None:
        """
        Replace the hook nexus that this hook belongs to.

        Args:
            hook_nexus: The new hook nexus to replace the current one
        """
        
        self._hook_nexus = hook_nexus
        
        log(self, "replace_hook_nexus", self._logger, True, "Successfully replaced hook nexus")

    def validate_value_in_isolation(self, value: T) -> tuple[bool, str]:
        """
        Validate the value in isolation. This is used to validate the value of a hook
        in isolation, without considering the value of other hooks in the same nexus.

        Args:
            value: The value to validate

        Returns:
            Tuple of (success: bool, message: str)
        """

        if self._validate_value_in_isolation_callback is not None:
            return self._validate_value_in_isolation_callback(value)
        else:
            return True, "No validate value in isolation callback provided"