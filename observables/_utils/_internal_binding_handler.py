from typing import Callable, Generic, TypeVar, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .._utils.observable import Observable

T = TypeVar("T")

class SyncMode(Enum):
    """
    Synchronization modes for establishing bidirectional bindings between observables.
    
    This enum defines how two observables should synchronize their values when
    establishing a bidirectional binding. The initial sync mode determines which
    observable's value is used as the source of truth during binding establishment.
    
    Attributes:
        UPDATE_VALUE_FROM_OBSERVABLE: Use the target observable's value for initial sync
        UPDATE_OBSERVABLE_FROM_SELF: Use this observable's value for initial sync
    
    Example:
        >>> from observables import ObservableSingleValue, SyncMode
        
        >>> # Create observables with different values
        >>> source = ObservableSingleValue(10)
        >>> target = ObservableSingleValue(20)
        
        >>> # Bind with different sync modes
        >>> # This will set target to 10 (source's value)
        >>> source.bind_to_observable(target, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        >>> print(target.value)  # Output: 10
        
        >>> # This would set source to 20 (target's value)
        >>> # source.bind_to_observable(target, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
    """
    UPDATE_VALUE_FROM_OBSERVABLE = "update_value_from_observable"
    UPDATE_OBSERVABLE_FROM_SELF = "update_observable_from_self"

DEFAULT_SYNC_MODE = SyncMode.UPDATE_OBSERVABLE_FROM_SELF

class InternalBindingHandler(Generic[T]):

    def __init__(self, owner: "Observable", get_callback: Callable[[], T], set_callback: Callable[[T], None]):

        self._owner = owner
        self._bound_binding_handlers: set["InternalBindingHandler[T]"] = set()
        self._get_callback: Callable[[], T] = get_callback
        self._set_callback: Callable[[T], None] = set_callback
        self._is_updating_from_binding = False
        self._is_establishing_binding = False
        self._is_checking_binding_state = False
        self._is_notifying = False

    def establish_binding(
            self,
            binding_handler: "InternalBindingHandler[T]",
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

        def set_establishing_binding_flags(is_establishing_binding: bool):
            self._is_establishing_binding = is_establishing_binding
            binding_handler._is_establishing_binding = is_establishing_binding

        # Step 1: Safety check: prevent binding establishment if already in progress
        if self._is_establishing_binding:
            raise ValueError(f"Cannot establish binding while already establishing a binding")
        for bound_binding_handler in self._bound_binding_handlers:
            if bound_binding_handler._is_establishing_binding:
                raise ValueError(f"Cannot establish binding while {bound_binding_handler} is establishing a binding")
        for bound_binding_handler in binding_handler._bound_binding_handlers:
            if bound_binding_handler._is_establishing_binding:
                raise ValueError(f"Cannot establish binding while {bound_binding_handler} is establishing a binding")
            
        # Step 2: Get the value to sync
        match initial_sync_mode:
            case SyncMode.UPDATE_VALUE_FROM_OBSERVABLE:
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
            elif binding_handler in self._bound_binding_handlers:
                raise ValueError(f"Already bound to {binding_handler}")
            
            # Step 6: Establish the connection between self and binding_handler
            self._bound_binding_handlers.add(binding_handler)
            binding_handler._bound_binding_handlers.add(self)

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

    def remove_binding(self, binding_handler: "InternalBindingHandler[T]") -> None:
        """
        Remove a binding between this handler and the given binding handler.
        Since the network is fully connected (everyone to everyone), removing one binding
        disconnects the entire network. All handlers will be unbound from each other.
        """
        # Safety check: prevent removal during binding establishment
        if self._is_establishing_binding:
            raise ValueError(f"Cannot remove binding while establishing a binding")
        
        # Check binding state
        if binding_handler is None:
            raise ValueError(f"Cannot remove binding to None binding handler")
        elif binding_handler == self:
            raise ValueError(f"Cannot remove binding from self")
        
        if binding_handler not in self._bound_binding_handlers or self not in binding_handler._bound_binding_handlers:
            raise ValueError(f"Cannot remove binding that is not bound to {self} or {binding_handler}")

        self._bound_binding_handlers.remove(binding_handler)
        binding_handler._bound_binding_handlers.remove(self)

        state_consistent, state_consistent_message = self.check_binding_state_consistency()
        if not state_consistent:
            raise ValueError(state_consistent_message)

    def is_bound_to(self, binding_handler: "InternalBindingHandler[T]") -> bool:
        """
        Check if this handler is bound to the given binding handler.
        Since bindings are bidirectional, this checks if we notify the given handler.
        """
        return binding_handler in self._bound_binding_handlers
    
    def notify_bindings(self, value: T) -> None:
        """
        Notify all bound handlers of a value change.
        Since bindings are bidirectional, this notifies all handlers that this handler is bound to.
        This method is transitive - it will propagate through the entire binding chain.
        """
        # Safety check: prevent notification during binding establishment
        if self._is_establishing_binding:
            raise ValueError(f"Cannot notify bindings while establishing a binding")
        
        # Safety check: prevent notification during value updates from binding
        if self._is_updating_from_binding:
            return
        
        # Prevent recursive calls by checking if we're already processing
        if self._is_notifying:
            return

        self._is_notifying = True
        for bound_binding_handler in self._bound_binding_handlers:
            bound_binding_handler._set_callback(value)
        self._is_notifying = False
    
    def check_binding_state_consistency(self) -> tuple[bool, str]:
        """
        Check that all bindings are bidirectional.
        This ensures that if A is bound to B, then B is also bound to A.
        """

        if self._is_checking_binding_state:
            return True, "Already checking binding state"

        self._is_checking_binding_state = True

        for binding_handler in self._bound_binding_handlers:
            if self not in binding_handler._bound_binding_handlers:
                return False, f"Binding state inconsistency detected: {self} is bound to {binding_handler}, but {binding_handler} is not bound to {self}. All bindings must be bidirectional."

        self._is_checking_binding_state = False

        return True, "All bindings are bidirectional"
    
    def check_values_synced(self) -> tuple[bool, str]:
        """
        Check if all bound handlers have synchronized values.
        This ensures that after binding, all handlers have consistent values.
        """
        if not self._bound_binding_handlers:
            return True, "No bindings to check" # No bindings to check
        
        # Get the reference value from this handler
        reference_value = self._get_callback()
        
        # Check that all bound handlers have the same value
        for binding_handler in self._bound_binding_handlers:
            handler_value = binding_handler._get_callback()
            if handler_value != reference_value:
                return False, f"Value synchronization check failed: {self} has value {reference_value}, but {binding_handler} has value {handler_value}. All bound handlers should have synchronized values."
        return True, "All values are synced"