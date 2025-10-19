from typing import Generic, TypeVar, Optional, Literal
from threading import RLock
import logging
import inspect

from ..hook_protocols.managed_hook import ManagedHookProtocol
from ..mixin_protocols.hook_with_connection_protocol import HookWithConnectionProtocol

from ..._utils import log
from ..._auxiliary.listening_base import ListeningBase
from ..._nexus_system.nexus_manager import NexusManager
from ..._nexus_system.hook_nexus import HookNexus
from ..._nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER
from ..._carries_hooks.carries_single_hook_protocol import CarriesSingleHookProtocol
from ..._publisher_subscriber.publisher import Publisher

T = TypeVar("T")


class ManagedHookBase(ManagedHookProtocol[T], Publisher, ListeningBase, Generic[T]):
    """
    A base class for managed hooks that can get and set values.
    
    ManagedHook represents a single value that can participate in the synchronization system
    without being owned by a specific observable, but unlike regular hooks, it can get and set values.
    It provides a lightweight way to create reactive values with full hook system capabilities.
    
    Type Parameters:
        T: The type of value stored in this hook. Can be any Python type - primitives,
           collections, custom objects, etc.
    
    Multiple Inheritance:
        - ManagedHookProtocol[T]: Implements the managed hook interface for binding and value access
        - Publisher: Can publish notifications to subscribers (async, sync, direct modes)
        - ManagedHookProtocol[T]: Implements the managed hook interface for binding and value access
        - BaseListening: Support for listener callbacks (synchronous notifications)
        - Generic[T]: Type-safe generic value storage
    
    Key Capabilities:
        - **Value Storage**: Stores value in a centralized HookNexus
        - **Bidirectional Binding**: Can connect to other hooks for value synchronization
        - **Validation**: Supports validation callbacks before value changes
        - **Listeners**: Synchronous callbacks on value changes
        - **Publishing**: Asynchronous subscriber notifications
        - **Thread Safety**: All operations protected by reentrant lock
        - **Getter**: Can get values directly
    
    Three Notification Mechanisms:
        1. **Listeners**: Synchronous callbacks via `add_listeners()`
        2. **Subscribers**: Async notifications via `add_subscriber()` (Publisher)
        3. **Connected Hooks**: Bidirectional sync via `connect_hook()`
    
    Example:
        Basic standalone getter hook usage::
        
            from observables._hooks.getter_hook_base import GetterHookBase
            
            # Create a getter hook
            temperature = GetterHookBase(20.0)
            
            # Add listener
            temperature.add_listeners(lambda: print(f"Temp: {temperature.value}"))
            
            # Connect to another hook
            display = GetterHookBase(0.0)
            temperature.connect_hook(display, "use_caller_value")
            
            # Values can only be changed through connected getter hooks
    """

    def __init__(
        self,
        value: T,
        nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER,
        logger: Optional[logging.Logger] = None
        ) -> None:
        """
        Initialize a new standalone GetterHook.
        
        Args:
            value: The initial value for this hook. Can be any Python type.
            nexus_manager: The NexusManager that coordinates value updates and
                validation across all hooks. If not provided, uses the global
                DEFAULT_NEXUS_MANAGER which is shared across the entire application.
                Default is DEFAULT_NEXUS_MANAGER.
            logger: Optional logger for debugging hook operations. If provided,
                operations like connection, disconnection, and value changes will
                be logged. Default is None.
        
        Note:
            The hook is created with publishing disabled by default 
            (preferred_publish_mode="off"). This is because hooks are typically
            used with the listener pattern rather than pub-sub. You can enable
            publishing by adding subscribers and calling publish() explicitly.
        
        Example:
            Create getter hooks with different configurations::
            
                # Simple getter hook with default settings
                counter = GetterHookBase(0)
                
                # Getter hook with custom nexus manager
                from observables._utils.nexus_manager import NexusManager
                custom_manager = NexusManager()
                custom_hook = GetterHookBase(42, nexus_manager=custom_manager)
                
                # Getter hook with logging enabled
                import logging
                logger = logging.getLogger(__name__)
                logged_hook = GetterHookBase("data", logger=logger)
        """

        from ..._nexus_system.hook_nexus import HookNexus

        ListeningBase.__init__(self, logger)
        self._value = value
        self._nexus_manager = nexus_manager

        Publisher.__init__(self, preferred_publish_mode="off", logger=logger)

        self._hook_nexus = HookNexus(value, hooks={self}, nexus_manager=nexus_manager, logger=logger)
        self._lock = RLock()

    @property
    def nexus_manager(self) -> "NexusManager":
        """Get the nexus manager that this hook belongs to."""
        return self._nexus_manager

    @property
    def value(self) -> T:
        """
        Get the value behind this hook (by reference).
        
        Returns:
            The actual value stored in the hook nexus (not a copy).
            
        Important:
            This returns a reference for performance. Do NOT mutate unless
            you created the value. For mutable collections, use immutable
            wrappers or call value_copy() if you need to modify.
        """
        with self._lock:
            return self._get_value()

    def value_copy(self) -> T:
        """
        Get a mutable copy of the value.
        
        Returns:
            A copy of the stored value (if it has a copy() method), otherwise
            the value itself.
            
        Use this when you need to modify the value without affecting the hook.
        """
        with self._lock:
            return self._hook_nexus.value_copy()

    @property
    def value_reference(self) -> T:
        """
        Get the value reference behind this hook.
        
        .. deprecated::
            Use `value` instead. This property is now an alias for `value`.
            Will be removed in a future version.
        
        Returns:
            The actual value stored in the hook nexus (same as `value`).
        """
        import warnings
        warnings.warn(
            "value_reference is deprecated, use 'value' instead",
            DeprecationWarning,
            stacklevel=2
        )
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

    def connect_hook(self, target_hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]", initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> tuple[bool, str]:
        """
        Connect this hook to another hook.

        This method implements the core hook connection process:
        
        1. Get the two nexuses from the hooks to connect
        2. Submit one of the hooks' value to the other nexus
        3. If successful, both nexus must now have the same value
        4. Merge the nexuses to one -> Connection established!
        
        After connection, both hooks will share the same nexus and remain synchronized.

        Args:
            target_hook: The hook or CarriesSingleHookProtocol to connect to
            initial_sync_mode: Determines which hook's value is used initially:
                - "use_caller_value": Use this hook's value (caller = self)
                - "use_target_value": Use the target hook's value
            
        Returns:
            A tuple containing a boolean indicating if the connection was successful and a string message
        """

        from ..._nexus_system.hook_nexus import HookNexus

        with self._lock:

            if target_hook is None: # type: ignore
                raise ValueError("Cannot connect to None hook")

            if isinstance(target_hook, CarriesSingleHookProtocol):
                target_hook = target_hook.hook
            
            if initial_sync_mode == "use_caller_value":
                success, msg = HookNexus[T].connect_hook_pairs((self, target_hook))  # type: ignore
            elif initial_sync_mode == "use_target_value":                
                success, msg = HookNexus[T].connect_hook_pairs((target_hook, self))  # type: ignore
            else:
                raise ValueError(f"Invalid sync mode: {initial_sync_mode}")

            log(self, "connect_to", self._logger, success, msg)

            return success, msg
    
    def disconnect_hook(self) -> None:
        """
        Disconnect this hook from the hook nexus.

        If this is the corresponding nexus has only this one hook, nothing will happen.
        """

        log(self, "disconnect_hook", self._logger, True, "Disconnecting hook initiated")

        with self._lock:

            from ..._nexus_system.hook_nexus import HookNexus

            # Check if we're being called during garbage collection by inspecting the call stack
            is_being_garbage_collected = any(frame.function == '__del__' for frame in inspect.stack())

            # If we're being garbage collected and not in the nexus anymore,
            # it means other hooks were already garbage collected and their weak
            # references were cleaned up. This is fine - just skip the disconnect.
            if is_being_garbage_collected and self not in self._hook_nexus.hooks:
                log(self, "disconnect", self._logger, True, "Hook already removed during garbage collection, skipping disconnect")
                return
            
            if self not in self._hook_nexus.hooks:
                raise ValueError("Hook was not found in its own hook nexus!")
            
            if len(self._hook_nexus.hooks) <= 1:
                # If we're the last hook, we're already effectively disconnected
                log(self, "disconnect", self._logger, True, "Hook was the last in the nexus, so it is already 'disconnected'")
                return
            
            # Create a new isolated nexus for this hook
            new_hook_nexus = HookNexus(self.value, hooks={self}, nexus_manager=self._nexus_manager, logger=self._logger)
            
            # Remove this hook from the current nexus
            self._hook_nexus.remove_hook(self)
            
            # Update this hook's nexus reference
            self._hook_nexus = new_hook_nexus

            log(self, "disconnect", self._logger, True, "Successfully disconnected hook")
            
            # The remaining hooks in the old nexus will continue to be bound together
            # This effectively breaks the connection between this hook and all others

    def is_connected_to(self, hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]") -> bool:
        """
        Check if this hook is connected to another hook or CarriesSingleHookLike.

        Args:
            hook: The hook or CarriesSingleHookProtocol to check if it is connected to

        Returns:
            True if the hook is connected to the other hook or CarriesSingleHookProtocol, False otherwise
        """

        with self._lock:
            if isinstance(hook, CarriesSingleHookProtocol):
                hook = hook.hook
            return hook in self._hook_nexus.hooks
    
    def _replace_hook_nexus(self, hook_nexus: "HookNexus[T]") -> None:
        """
        Replace the hook nexus that this hook belongs to.

        Args:
            hook_nexus: The new hook nexus to replace the current one
        """
        
        with self._lock:
            self._hook_nexus = hook_nexus
        
        log(self, "replace_hook_nexus", self._logger, True, "Successfully replaced hook nexus")

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook."""
        return f"GetterHook(v={self.value}, id={id(self)})"

    def __str__(self) -> str:
        """Get the string representation of this hook."""
        return f"GetterHook(v={self.value}, id={id(self)})"
