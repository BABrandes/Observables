from typing import Generic, Optional , TypeVar, overload
from .._utils._listening_base import ListeningBase
from .._utils._internal_binding_handler import InternalBindingHandler, SyncMode, DEFAULT_SYNC_MODE
from .._utils._carries_bindable_set import CarriesBindableSet
from .._utils.observable import Observable

T = TypeVar("T")

class ObservableSet(ListeningBase, Observable, CarriesBindableSet[T], Generic[T]):
    """
    An observable wrapper around a set that supports bidirectional bindings and reactive updates.
    
    This class provides a reactive wrapper around Python sets, allowing other objects to
    observe changes and establish bidirectional bindings. It implements the full set interface
    while maintaining reactivity and binding capabilities.
    
    Features:
    - Bidirectional bindings with other ObservableSet instances
    - Full set interface compatibility (add, remove, discard, pop, etc.)
    - Listener notification system for change events
    - Automatic copying to prevent external modification
    - Type-safe generic implementation
    
    Example:
        >>> # Create an observable set
        >>> tags = ObservableSet({"python", "library"})
        >>> tags.add_listeners(lambda: print("Tags changed!"))
        >>> tags.add("observable")  # Triggers listener
        Tags changed!
        
        >>> # Create bidirectional binding
        >>> tags_copy = ObservableSet(tags)
        >>> tags_copy.add("reactive")  # Updates both sets
        >>> print(tags.value, tags_copy.value)
        {'python', 'library', 'observable', 'reactive'} {'python', 'library', 'observable', 'reactive'}
    
    Args:
        value: Initial set, another ObservableSet to bind to, or None for empty set
    """

    @overload
    def __init__(self, value: set[T]):
        """Initialize with a direct set value."""
        ...

    @overload
    def __init__(self, value: CarriesBindableSet[T]):
        """Initialize with another observable set, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, value: None):
        """Initialize with an empty set."""
        ...

    def __init__(self, value: set[T] | CarriesBindableSet[T] | None = None):
        """
        Initialize the ObservableSet.
        
        Args:
            value: Initial set, observable set to bind to, or None for empty set
        """
        super().__init__()
        if value is None:
            initial_value: set[T] = set()
            bindable_set_carrier: Optional[CarriesBindableSet[T]] = None
        elif isinstance(value, CarriesBindableSet):
            initial_value: set[T] = value._get_set().copy()
            bindable_set_carrier: Optional[CarriesBindableSet[T]] = value
        else:
            initial_value: set[T] = value.copy()
            bindable_set_carrier: Optional[CarriesBindableSet[T]] = None
        
        self._binding_handler: InternalBindingHandler[set[T]] = InternalBindingHandler(self, self._get_set, self._set_set, self._check_set)

        self._value: set[T] = initial_value

        if bindable_set_carrier is not None:
            self.bind_to_observable(bindable_set_carrier)
    

    @property
    def value(self) -> set[T]:
        """
        Get a copy of the current set value.
        
        Returns:
            A copy of the current set to prevent external modification
        """
        return self._value.copy()    
    
    def _get_set(self) -> set[T]:
        """Internal method to get set for binding system."""
        return self._value
    
    def _set_set(self, set_to_set: set[T]) -> None:
        """Internal method to set set from binding system."""
        self.set_set(set_to_set)
    
    def _get_set_binding_handler(self) -> InternalBindingHandler[set[T]]:
        """Internal method to get binding handler for binding system."""
        return self._binding_handler
    
    def _check_set(self, set_to_check: set[T]) -> bool:
        """Internal method to check set validity for binding system."""
        return True
    
    def set_set(self, set_to_set: set[T]) -> None:
        """
        Set the entire set to a new value.
        
        This method replaces the current set with a new one, triggering binding updates
        and listener notifications. If the new set is identical to the current one,
        no action is taken.
        
        Args:
            set_to_set: The new set to set
        """
        if set_to_set == self._value:
            return
        self._value = set_to_set.copy()
        self._binding_handler.notify_bindings(self._value)
        self._notify_listeners()

    def bind_to_observable(self, observable: CarriesBindableSet[T], initial_sync_mode: SyncMode = DEFAULT_SYNC_MODE) -> None:
        """
        Establish a bidirectional binding with another observable set.
        
        This method creates a bidirectional binding between this observable set and another,
        ensuring that changes to either observable are automatically propagated to the other.
        The binding can be configured with different initial synchronization modes.
        
        Args:
            observable: The observable set to bind to
            initial_sync_mode: How to synchronize values initially
            
        Raises:
            ValueError: If observable is None
        """
        if observable is None:
            raise ValueError("Cannot bind to None observable")
        self._binding_handler.establish_binding(observable._get_set_binding_handler(), initial_sync_mode)

    def unbind_from_observable(self, observable: CarriesBindableSet[T]) -> None:
        """
        Remove the bidirectional binding with another observable set.
        
        This method removes the binding between this observable set and another,
        preventing further automatic synchronization of changes.
        
        Args:
            observable: The observable set to unbind from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        self._binding_handler.remove_binding(observable._get_set_binding_handler())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        """
        Check the consistency of the binding system.
        
        This method performs comprehensive checks on the binding system to ensure
        that all bindings are in a consistent state and values are properly synchronized.
        
        Returns:
            Tuple of (is_consistent, message) where is_consistent is a boolean
            indicating if the system is consistent, and message provides details
            about any inconsistencies found.
        """
        binding_state_consistent, binding_state_consistent_message = self._binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._binding_handler.check_values_synced()
        if not values_synced:
            return False, values_synced_message
        return True, "Binding system is consistent"
    
    # Standard set methods
    def add(self, item: T) -> None:
        """
        Add an element to the set.
        
        This method adds an item to the set if it's not already present,
        triggering binding updates and listener notifications.
        
        Args:
            item: The element to add to the set
        """
        if item not in self._value:
            self._value.add(item)
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def remove(self, item: T) -> None:
        """
        Remove an element from the set.
        
        This method removes an item from the set if it's present,
        triggering binding updates and listener notifications.
        
        Args:
            item: The element to remove from the set
            
        Raises:
            KeyError: If the item is not in the set
        """
        if item in self._value:
            self._value.remove(item)
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def discard(self, item: T) -> None:
        """
        Remove an element from the set if it is present.
        
        This method removes an item from the set if it's present,
        triggering binding updates and listener notifications.
        Unlike remove(), this method does not raise an error if the item is not found.
        
        Args:
            item: The element to remove from the set
        """
        if item in self._value:
            self._value.discard(item)
    
    def pop(self) -> T:
        """Remove and return an arbitrary set element"""
        item = self._value.pop()
        self._binding_handler.notify_bindings(self._value)
        self._notify_listeners()
        return item
    
    def clear(self) -> None:
        """Remove all elements from the set"""
        if self._value:
            self._value.clear()
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def update(self, *others) -> None:
        """Update the set with elements from all others"""
        old_value = self._value.copy()
        for other in others:
            self._value.update(other)
        if old_value != self._value:
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def intersection_update(self, *others) -> None:
        """Update the set keeping only elements found in it and all others"""
        old_value = self._value.copy()
        for other in others:
            self._value.intersection_update(other)
        if old_value != self._value:
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def difference_update(self, *others) -> None:
        """Update the set removing elements found in others"""
        old_value = self._value.copy()
        for other in others:
            self._value.difference_update(other)
        if old_value != self._value:
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def symmetric_difference_update(self, other) -> None:
        """Update the set keeping only elements found in either set but not both"""
        old_value = self._value.copy()
        self._value.symmetric_difference_update(other)
        if old_value != self._value:
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def __str__(self) -> str:
        return f"OS(options={self._value})"
    
    def __repr__(self) -> str:
        return f"ObservableSet({self._value})"
    
    def __len__(self) -> int:
        return len(self._value)
    
    def __contains__(self, item: T) -> bool:
        return item in self._value
    
    def __iter__(self):
        """Iterate over the options"""
        return iter(self._value)
    
    def __eq__(self, other) -> bool:
        """Compare with another set or observable"""
        if isinstance(other, ObservableSet):
            return self._value == other._value
        return self._value == other
    
    def __ne__(self, other) -> bool:
        """Compare with another set or observable"""
        return not (self == other)
    
    def __le__(self, other) -> bool:
        """Check if this set is a subset of another"""
        if isinstance(other, ObservableSet):
            return self._value <= other._value
        return self._value <= other
    
    def __lt__(self, other) -> bool:
        """Check if this set is a proper subset of another"""
        if isinstance(other, ObservableSet):
            return self._value < other._value
        return self._value < other
    
    def __ge__(self, other) -> bool:
        """Check if this set is a superset of another"""
        if isinstance(other, ObservableSet):
            return self._value >= other._value
        return self._value >= other
    
    def __gt__(self, other) -> bool:
        """Check if this set is a proper superset of another"""
        if isinstance(other, ObservableSet):
            return self._value > other._value
        return self._value > other
    
    def __and__(self, other):
        """Set intersection"""
        if isinstance(other, ObservableSet):
            return self._value & other._value
        return self._value & other
    
    def __or__(self, other):
        """Set union"""
        if isinstance(other, ObservableSet):
            return self._value | other._value
        return self._value | other
    
    def __sub__(self, other):
        """Set difference"""
        if isinstance(other, ObservableSet):
            return self._value - other._value
        return self._value - other
    
    def __xor__(self, other):
        """Set symmetric difference"""
        if isinstance(other, ObservableSet):
            return self._value ^ other._value
        return self._value ^ other
    
    def __hash__(self) -> int:
        """Hash based on the current options"""
        return hash(frozenset(self._value))
    
    def get_observed_values(self) -> tuple[set[T]]:
        return tuple(self._value)
    
    def set_observed_values(self, values: tuple[set[T]]) -> None:
        self.set_set(values[0])