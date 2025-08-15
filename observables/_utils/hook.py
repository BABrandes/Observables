import threading
from typing import Any, Callable, Generic, Optional, TypeVar, TYPE_CHECKING, runtime_checkable, Protocol
from .sync_mode import SyncMode

if TYPE_CHECKING:
    from .base_observable import BaseObservable

T = TypeVar("T")

@runtime_checkable
class HookLike(Protocol[T]):
    """
    Protocol for hook objects.
    """
    ...

    def establish_binding(self, binding_handler: "Hook[T]", initial_sync_mode: SyncMode = SyncMode.UPDATE_OBSERVABLE_FROM_SELF) -> None:
        """
        Establish a binding between this hook and the given binding handler.
        """
        ...
    
    def remove_binding(self, binding_handler: "Hook[T]") -> None:
        """
        Remove a binding between this hook and the given binding handler.
        """
        ...
    
    def is_bound_to(self, binding_handler: "Hook[T]") -> bool:
        """
        Check if this hook is bound to the given binding handler.
        """
        ...
    
    def notify_bindings(self, value: T) -> None:
        """
        Notify all connected hooks of a value change.
        """
        ...
    
    def check_binding_state_consistency(self) -> tuple[bool, str]:
        """
        Check that all connections are bidirectional.
        """
        ...
    
    def check_values_synced(self) -> tuple[bool, str]:
        """
        Check if all connected hooks have synchronized values.
        """
        ...
    
    def value(self) -> T:
        """
        Get the value behind this hook.
        """
        ...

class Hook(HookLike[T], Generic[T]):

    def __init__(self, owner: "BaseObservable", get_callback: Callable[[], T]|Callable[[dict[str, Any]], T], set_callback: Callable[[T], None]|Callable[[T, dict[str, Any]], None], auxiliary_information: Optional[dict[str, Any]] = None):

        self._owner = owner
        self._connected_hooks: set["Hook[T]"] = set()
        self._get_callback: Callable[[], T]|Callable[[dict[str, Any]], T] = get_callback
        self._set_callback: Callable[[T], None]|Callable[[T, dict[str, Any]], None] = set_callback
        self._auxiliary_information: Optional[dict[str, Any]] = auxiliary_information
        self._is_updating_from_binding = False
        self._is_establishing_binding = False
        self._is_checking_binding_state = False
        self._is_notifying = False
        # Thread safety: Lock for protecting binding operations and state
        self._lock = threading.RLock()

    @property
    def value(self) -> T:
        """
        Get the value behind this hook.
        """
        return self._get_callback()

    @property
    def owner(self) -> "BaseObservable":
        """
        Get the owner of this hook.
        """
        return self._owner
    
    @property
    def connected_hooks(self) -> set["Hook[T]"]:
        """
        Get the set of connected hooks.
        """
        with self._lock:
            return self._connected_hooks.copy()
    
    @property
    def auxiliary_information(self) -> Optional[dict[str, Any]]:
        """
        Get the auxiliary information of this hook.
        """
        return self._auxiliary_information.copy()

    def establish_binding(
            self,
            binding_handler: "Hook[T]",
            initial_sync_mode: SyncMode = SyncMode.UPDATE_OBSERVABLE_FROM_SELF
            ) -> None:
        """
        Establishes a bidirectional binding between the owner and the binding handler.
        The binding handler is called when the owner's value changes.
        The owner is also called when the binding handler's value changes.
        The initial sync mode determines which value is used for initial synchronization.

        Args:
            binding_handler: The binding handler to bind to.
            initial_sync_mode: Determines which value is used for initial synchronization.
        """
        # Thread safety: Acquire locks from both hooks to prevent deadlocks
        # Use a consistent ordering to prevent deadlocks
        if id(self) < id(binding_handler):
            lock1, lock2 = self._lock, binding_handler._lock
        else:
            lock1, lock2 = binding_handler._lock, self._lock
        
        with lock1:
            with lock2:
                self._establish_binding_unsafe(binding_handler, initial_sync_mode)

    def _establish_binding_unsafe(
            self,
            binding_handler: "Hook[T]",
            initial_sync_mode: SyncMode
            ) -> None:
        """
        Internal method for establishing bindings without locks.
        This method should only be called when the caller already holds the necessary locks.
        """
        def set_establishing_binding_flags(is_establishing_binding: bool):
            self._is_establishing_binding = is_establishing_binding
            binding_handler._is_establishing_binding = is_establishing_binding

        # Step 1: Safety check: prevent binding establishment if already in progress
        if self._is_establishing_binding:
            raise ValueError(f"Cannot establish binding while already establishing a binding")
        for bound_binding_handler in self._connected_hooks:
            if bound_binding_handler._is_establishing_binding:
                raise ValueError(f"Cannot establish binding while {bound_binding_handler} is establishing a binding")
        for bound_binding_handler in binding_handler._connected_hooks:
            if bound_binding_handler._is_establishing_binding:
                raise ValueError(f"Cannot establish binding while {bound_binding_handler} is establishing a binding")
            
        # Step 2: Get the value to sync
        match initial_sync_mode:
            case SyncMode.UPDATE_SELF_FROM_OBSERVABLE:
                value_to_sync: T = binding_handler._get_callback()
            case SyncMode.UPDATE_OBSERVABLE_FROM_SELF:
                value_to_sync: T = self._get_callback()
            case _:
                raise ValueError(f"Invalid initial sync mode: {initial_sync_mode}")
            
        try:

            # Step 4: Tell everyone that we're establishing a binding
            set_establishing_binding_flags(True)

            # Step 5: Check binding state
            if binding_handler is None:
                raise ValueError(f"Cannot bind to None binding handler")
            elif binding_handler == self:
                raise ValueError(f"Cannot bind observable to itself")
            elif binding_handler in self._connected_hooks:
                raise ValueError(f"Already bound to {binding_handler}")
            
            # Step 6: Establish the connection between self and binding_handler
            self._connected_hooks.add(binding_handler)
            binding_handler._connected_hooks.add(self)

            # Step 7: Check binding state to ensure all connections are bidirectional
            binding_state_consistent, binding_state_consistent_message = self.check_binding_state_consistency()
            if not binding_state_consistent:
                raise ValueError(binding_state_consistent_message)
            
            # Step 8: Reset the establishing binding flag - binding is now established, tell everyone.
            set_establishing_binding_flags(False)

        except Exception as e:
            set_establishing_binding_flags(False)
            raise e

        # Step 9: Sync the value
        self._set_callback(value_to_sync)
        binding_handler._set_callback(value_to_sync)

    def remove_binding(self, binding_handler: "Hook[T]") -> None:
        """
        Remove a binding between this handler and the given binding handler.
        Since the network is fully connected (everyone to everyone), removing one binding
        disconnects the entire network. All handlers will be unbound from each other.
        """
        # Thread safety: Acquire locks from both hooks to prevent deadlocks
        # Use a consistent ordering to prevent deadlocks
        if id(self) < id(binding_handler):
            lock1, lock2 = self._lock, binding_handler._lock
        else:
            lock1, lock2 = binding_handler._lock, self._lock
        
        with lock1:
            with lock2:
                self._remove_binding_unsafe(binding_handler)

    def _remove_binding_unsafe(self, binding_handler: "Hook[T]") -> None:
        """
        Internal method for removing bindings without locks.
        This method should only be called when the caller already holds the necessary locks.
        """
        # Safety check: prevent removal during binding establishment
        if self._is_establishing_binding:
            raise ValueError(f"Cannot remove binding while establishing a binding")
        
        # Check binding state
        if binding_handler is None:
            raise ValueError(f"Cannot remove binding to None binding handler")
        elif binding_handler == self:
            raise ValueError(f"Cannot remove binding from self")
        
        if binding_handler not in self._connected_hooks or self not in binding_handler._connected_hooks:
            raise ValueError(f"Cannot remove binding that is not bound to {self} or {binding_handler}")

        self._connected_hooks.remove(binding_handler)
        binding_handler._connected_hooks.remove(self)

        state_consistent, state_consistent_message = self.check_binding_state_consistency()
        if not state_consistent:
            raise ValueError(state_consistent_message)

    def is_bound_to(self, binding_handler: "Hook[T]") -> bool:
        """
        Check if this handler is bound to the given binding handler.
        Since bindings are bidirectional, this checks if we notify the given handler.
        """
        with self._lock:
            return binding_handler in self._connected_hooks
    
    def notify_bindings(self, value: T) -> None:
        """
        Notify all connected hooks of a value change.
        Since connections are bidirectional, this notifies all hooks that this hook is connected to.
        This method is transitive - it will propagate through the entire binding chain.
        """
        with self._lock:
            # Safety check: prevent notification during binding establishment
            if self._is_establishing_binding:
                raise ValueError(f"Cannot notify bindings while establishing a binding")
            
            # Safety check: prevent notification during value updates from binding
            if self._is_updating_from_binding:
                return
            
            # Prevent recursive calls by checking if we're already processing
            if self._is_notifying:
                return

            # Get a copy of connected hooks to avoid holding lock during callbacks
            connected_hooks_copy = self._connected_hooks.copy()
            self._is_notifying = True
        
        # Execute callbacks outside of lock to prevent deadlocks
        try:
            for connected_hook in connected_hooks_copy:
                connected_hook._set_callback(value)
        finally:
            with self._lock:
                self._is_notifying = False
    
    def check_binding_state_consistency(self) -> tuple[bool, str]:
        """
        Check that all connections are bidirectional.
        This ensures that if A is connected to B, then B is also connected to A.
        """
        with self._lock:
            if self._is_checking_binding_state:
                return True, "Already checking binding state"

            self._is_checking_binding_state = True

            # Get a copy to avoid holding lock during iteration
            connected_hooks_copy = self._connected_hooks.copy()

        # Check consistency outside of lock to prevent deadlocks
        try:
            for connected_hook in connected_hooks_copy:
                if not connected_hook.is_bound_to(self):
                    return False, f"Binding state inconsistency detected: {self} is connected to {connected_hook}, but {connected_hook} is not connected to {self}. All connections must be bidirectional."
        finally:
            with self._lock:
                self._is_checking_binding_state = False

        return True, "All connections are bidirectional"
    
    def check_values_synced(self) -> tuple[bool, str]:
        """
        Check if all connected hooks have synchronized values.
        This ensures that after binding, all hooks have consistent values.
        """
        with self._lock:
            if not self._connected_hooks:
                return True, "No bindings to check" # No bindings to check
            
            # Get a copy to avoid holding lock during iteration
            connected_hooks_copy = self._connected_hooks.copy()
        
        # Get the reference value from this handler
        if self._auxiliary_information is None:
            reference_value = self._get_callback()
        else:
            reference_value = self._get_callback(self._auxiliary_information)
        
        # Check that all connected hooks have the same value
        for connected_hook in connected_hooks_copy:
            if connected_hook._auxiliary_information is None:
                handler_value = connected_hook._get_callback()
            else:
                handler_value = connected_hook._get_callback(connected_hook._auxiliary_information)
            if handler_value != reference_value:
                return False, f"Value synchronization check failed: {self} has value {reference_value}, but {connected_hook} has value {handler_value}. All connected hooks should have synchronized values."
        return True, "All values are synced"