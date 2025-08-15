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
    def connected_hooks(self) -> set["HookLike[T]"]:
        """
        Get the set of connected hooks as a copy.
        """
        ...

    def _remove_connected_hook(self, hook: "HookLike[T]") -> None:
        """
        Internal method to remove a connected hook.
        """
        ...

    def _add_connected_hook(self, hook: "HookLike[T]") -> None:
        """
        Internal method to add a connected hook.
        """
        ...
    
    @property
    def auxiliary_information(self) -> Optional[dict[str, Any]]:
        """
        Get the auxiliary information of this hook.
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
    def is_receiving(self) -> bool:
        """
        Check if this hook can receive values.
        """
        ...
    
    @property
    def is_sending(self) -> bool:
        """
        Check if this hook can send values.
        """
        ...
    
    @property
    def is_updating_from_binding(self) -> bool:
        """
        Check if this hook is currently updating from a binding.
        """
        ...
    
    @property
    def is_establishing_binding(self) -> bool:
        """
        Check if this hook is currently establishing a binding.
        """
        ...
    
    @property
    def is_checking_binding_state(self) -> bool:
        """
        Check if this hook is currently checking binding state.
        """
        ...
    
    @property
    def is_notifying(self) -> bool:
        """
        Check if this hook is currently notifying bindings.
        """
        ...
    
    # Methods
    def establish_binding(self, hook_for_binding: "HookLike[T]", initial_sync_mode: SyncMode = SyncMode.UPDATE_OBSERVABLE_FROM_SELF) -> None:
        """
        Establish a binding between this hook and the given hook for binding.
        """
        ...
    
    def remove_binding(self, hook_for_binding: "HookLike[T]") -> None:
        """
        Remove a binding between this hook and the given hook for binding.
        """
        ...
    
    def is_bound_to(self, hook_for_binding: "HookLike[T]") -> bool:
        """
        Check if this hook is bound to the given hook for binding.
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
    
    # Internal methods (used by the binding system)
    def _get_callback(self, auxiliary_information: Optional[dict[str, Any]] = None) -> T:
        """
        Get the value from the callback.
        """
        ...
    
    def _set_callback(self, value: T, auxiliary_information: Optional[dict[str, Any]] = None) -> None:
        """
        Set the value via the callback.
        """
        ...


class Hook(HookLike[T], Generic[T]):

    def __init__(
            self,
            owner: "BaseObservable",
            get_callback: Optional[Callable[[], T]|Callable[[dict[str, Any]], T]] = None,
            set_callback: Optional[Callable[[T], None]|Callable[[T, dict[str, Any]], None]] = None,
            auxiliary_information: Optional[dict[str, Any]] = None,
            ) -> None:

        self._owner = owner
        self._connected_hooks: set[HookLike[T]] = set()
        self._get_callback: Callable[[], T]|Callable[[dict[str, Any]], T] = get_callback
        self._set_callback: Optional[Callable[[T], None]|Callable[[T, dict[str, Any]], None]] = set_callback
        self._auxiliary_information: Optional[dict[str, Any]] = auxiliary_information
        self._is_receiving = True if set_callback is not None else False
        self._is_sending = True if get_callback is not None else False
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
    def _connected_hooks_no_copy(self) -> set[HookLike[T]]:
        """
        Get the set of connected hooks.
        """
        with self.lock:
            return self._connected_hooks
    
    @property
    def connected_hooks(self) -> set[HookLike[T]]:
        """
        Get the set of connected hooks as a copy.
        """
        with self.lock:
            return self._connected_hooks.copy()
    

    
    @property
    def auxiliary_information(self) -> Optional[dict[str, Any]]:
        """
        Get the auxiliary information of this hook.
        """
        if self._auxiliary_information is None:
            return None
        return self._auxiliary_information.copy()
    
    @property
    def lock(self) -> threading.RLock:
        """
        Get the lock for thread safety.
        """
        return self._lock
    
    @property
    def is_receiving(self) -> bool:
        """
        Check if this hook can receive values.
        """
        return self._is_receiving
    
    @property
    def is_sending(self) -> bool:
        """
        Check if this hook can send values.
        """
        return self._is_sending
    
    @property
    def is_updating_from_binding(self) -> bool:
        """
        Check if this hook is currently updating from a binding.
        """
        return self._is_updating_from_binding
    
    @property
    def is_establishing_binding(self) -> bool:
        """
        Check if this hook is currently establishing a binding.
        """
        return self._is_establishing_binding
    
    @is_establishing_binding.setter
    def is_establishing_binding(self, value: bool) -> None:
        """
        Set if this hook is currently establishing a binding.
        """
        self._is_establishing_binding = value
    
    @property
    def is_checking_binding_state(self) -> bool:
        """
        Check if this hook is currently checking binding state.
        """
        return self._is_checking_binding_state
    
    @is_checking_binding_state.setter
    def is_checking_binding_state(self, value: bool) -> None:
        """
        Set if this hook is currently checking binding state.
        """
        self._is_checking_binding_state = value
    
    @property
    def is_notifying(self) -> bool:
        """
        Check if this hook is currently notifying bindings.
        """
        return self._is_notifying
    
    @is_notifying.setter
    def is_notifying(self, value: bool) -> None:
        """
        Set if this hook is currently notifying bindings.
        """
        self._is_notifying = value
    
    def _remove_connected_hook(self, hook: "HookLike[T]") -> None:
        """
        Internal method to remove a connected hook.
        """
        with self.lock:
            self._connected_hooks.remove(hook)
    
    def _add_connected_hook(self, hook: "HookLike[T]") -> None:
        """
        Internal method to add a connected hook.
        """
        with self.lock:
            self._connected_hooks.add(hook)
    
    def _get_callback(self, auxiliary_information: Optional[dict[str, Any]] = None) -> T:
        """
        Get the value from the callback.
        """
        if auxiliary_information is None:
            auxiliary_information = self._auxiliary_information
        
        if auxiliary_information is None:
            return self._get_callback()
        else:
            return self._get_callback(auxiliary_information)
    
    def _set_callback(self, value: T, auxiliary_information: Optional[dict[str, Any]] = None) -> None:
        """
        Set the value via the callback.
        """
        if auxiliary_information is None:
            auxiliary_information = self._auxiliary_information
        
        if auxiliary_information is None:
            self._set_callback(value)
        else:
            self._set_callback(value, auxiliary_information)

    def establish_binding(
            self,
            hook_for_binding: HookLike[T],
            initial_sync_mode: SyncMode = SyncMode.UPDATE_OBSERVABLE_FROM_SELF
            ) -> None:
        """
        Establishes a bidirectional binding between the owner and the hook for binding.
        The hook for binding is called when the owner's value changes.
        The owner is also called when the hook for binding's value changes.
        The initial sync mode determines which value is used for initial synchronization.

        Args:
            hook_for_binding: The hook for binding to bind to. This hook will be called when the owner's value changes.
            initial_sync_mode: Determines which value is used for initial synchronization.
        """
        # Thread safety: Acquire locks from both hooks to prevent deadlocks
        # Use a consistent ordering to prevent deadlocks
        if id(self) < id(hook_for_binding):
            lock1, lock2 = self.lock, hook_for_binding.lock
        else:
            lock1, lock2 = hook_for_binding.lock, self.lock
        
        with lock1:
            with lock2:
                self._establish_binding_unsafe(hook_for_binding, initial_sync_mode)

    def _establish_binding_unsafe(
            self,
            hook_for_binding: HookLike[T],
            initial_sync_mode: SyncMode
            ) -> None:
        """
        Internal method for establishing bindings without locks.
        This method should only be called when the caller already holds the necessary locks.
        """
        def set_establishing_binding_flags(is_establishing_binding: bool):
            self._is_establishing_binding = is_establishing_binding
            hook_for_binding.is_establishing_binding = is_establishing_binding

        # Step 1: Safety check: prevent binding establishment if already in progress
        if self.is_establishing_binding:
            raise ValueError(f"Cannot establish binding while already establishing a binding")
        for bound_binding_handler in self.connected_hooks:
            if bound_binding_handler.is_establishing_binding:
                raise ValueError(f"Cannot establish binding while {bound_binding_handler} is establishing a binding")
        for bound_binding_handler in hook_for_binding.connected_hooks:
            if bound_binding_handler.is_establishing_binding:
                raise ValueError(f"Cannot establish binding while {bound_binding_handler} is establishing a binding")
            
        # Step 2: Get the value to sync
        match initial_sync_mode:
            case SyncMode.UPDATE_SELF_FROM_OBSERVABLE:
                if not hook_for_binding.is_sending:
                    raise ValueError(f"Cannot update self from hook_for_binding if hook_for_binding is not sending")
                value_to_sync: T = hook_for_binding._get_callback()
            case SyncMode.UPDATE_OBSERVABLE_FROM_SELF:
                if not self.is_sending:
                    raise ValueError(f"Cannot update hook_for_binding from self if self is not sending")
                value_to_sync: T = self._get_callback()
            case _:
                raise ValueError(f"Invalid initial sync mode: {initial_sync_mode}")
            
        try:

            # Step 4: Tell everyone that we're establishing a binding
            set_establishing_binding_flags(True)

            # Step 5: Check binding state
            if hook_for_binding is None:
                raise ValueError(f"Cannot bind to None hook for binding")
            elif hook_for_binding == self:
                raise ValueError(f"Cannot bind observable to itself")
            elif hook_for_binding in self._connected_hooks:
                raise ValueError(f"Already bound to {hook_for_binding}")
            
            # Step 6: Establish the connection between self and hook_for_binding
            self._add_connected_hook(hook_for_binding)
            hook_for_binding._add_connected_hook(self)

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
        if self.is_receiving:
            self._set_callback(value_to_sync)
        if hook_for_binding.is_receiving:
            hook_for_binding._set_callback(value_to_sync)

    def remove_binding(self, hook_for_binding: HookLike[T]) -> None:
        """
        Remove a binding between this hook and the given hook for binding.
        Since the network is fully connected (everyone to everyone), removing one binding
        disconnects the entire network. All hooks will be unbound from each other.
        """
        # Thread safety: Acquire locks from both hooks to prevent deadlocks
        # Use a consistent ordering to prevent deadlocks
        if id(self) < id(hook_for_binding):
            lock1, lock2 = self.lock, hook_for_binding.lock
        else:
            lock1, lock2 = hook_for_binding.lock, self.lock
        
        with lock1:
            with lock2:
                self._remove_binding_unsafe(hook_for_binding)

    def _remove_binding_unsafe(self, hook_for_binding: HookLike[T]) -> None:
        """
        Internal method for removing bindings without locks.
        This method should only be called when the caller already holds the necessary locks.
        """
        # Safety check: prevent removal during binding establishment
        if self.is_establishing_binding:
            raise ValueError(f"Cannot remove binding while establishing a binding")
        
        # Check binding state
        if hook_for_binding is None:
            raise ValueError(f"Cannot remove binding to None hook for binding")
        elif hook_for_binding == self:
            raise ValueError(f"Cannot remove binding from self")
        
        if hook_for_binding not in self.connected_hooks or self not in hook_for_binding.connected_hooks:
            raise ValueError(f"Cannot remove binding that is not bound to {self} or {hook_for_binding}")

        self._remove_connected_hook(hook_for_binding)
        hook_for_binding._remove_connected_hook(self)

        state_consistent, state_consistent_message = self.check_binding_state_consistency()
        if not state_consistent:
            raise ValueError(state_consistent_message)

    def is_bound_to(self, hook_for_binding: HookLike[T]) -> bool:
        """
        Check if this hook is bound to the given hook for binding.
        Since bindings are bidirectional, this checks if we notify the given hook for binding.
        """
        with self.lock:
            return hook_for_binding in self.connected_hooks
    
    def notify_bindings(self, value: T) -> None:
        """
        Notify all connected hooks of a value change.
        Since connections are bidirectional, this notifies all hooks that this hook is connected to.
        This method is transitive - it will propagate through the entire binding chain. This method is called by the owner of the hook.
        """
        with self.lock:
            # Safety check: prevent notification during binding establishment
            if self.is_establishing_binding:
                raise ValueError(f"Cannot notify bindings while establishing a binding")
            
            # Safety check: prevent notification during value updates from binding
            if self.is_updating_from_binding:
                return
            
            # Prevent recursive calls by checking if we're already processing
            if self.is_notifying:
                return

            # Get a copy of connected hooks to avoid holding lock during callbacks
            connected_hooks_copy = self.connected_hooks
            self._is_notifying = True
        
        # Execute callbacks outside of lock to prevent deadlocks
        for connected_hook in connected_hooks_copy:
            if connected_hook.is_receiving:
                connected_hook._set_callback(value)
        
        # Reset the notifying flag after all callbacks complete successfully
        with self.lock:
            self._is_notifying = False
    
    def check_binding_state_consistency(self) -> tuple[bool, str]:
        """
        Check that all connections are bidirectional.
        This ensures that if A is connected to B, then B is also connected to A.
        """
        with self.lock:
            if self.is_checking_binding_state:
                return True, "Already checking binding state"

            self._is_checking_binding_state = True

            # Get a copy to avoid holding lock during iteration
            connected_hooks_copy = self.connected_hooks

        # Check consistency outside of lock to prevent deadlocks
        try:
            for connected_hook in connected_hooks_copy:
                if not connected_hook.is_bound_to(self):
                    return False, f"Binding state inconsistency detected: {self} is connected to {connected_hook}, but {connected_hook} is not connected to {self}. All connections must be bidirectional."
        finally:
            with self.lock:
                self._is_checking_binding_state = False

        return True, "All connections are bidirectional"
    
    def check_values_synced(self) -> tuple[bool, str]:
        """
        Check if all connected hooks have synchronized values.
        This ensures that after binding, all hooks have consistent values.
        """
        with self.lock:
            if not self.connected_hooks:
                return True, "No bindings to check" # No bindings to check
            
            # Get a copy to avoid holding lock during iteration
            connected_hooks_copy = self.connected_hooks
        
        # Get the reference value from this hook
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
                return False, f"Value synchronization check failed: {self} has value {reference_value}, but {connected_hook} has value {handler_value}. All connected hooks should have synchronized values. This is a bug in the binding system."
        return True, "All values are synced"
