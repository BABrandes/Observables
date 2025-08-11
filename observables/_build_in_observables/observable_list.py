from typing import Generic, TypeVar, overload
from typing import Optional
from .._utils._listening_base import ListeningBase
from .._utils._internal_binding_handler import InternalBindingHandler, SyncMode, DEFAULT_SYNC_MODE
from .._utils._carries_bindable_list import CarriesBindableList

T = TypeVar("T")

class ObservableList(ListeningBase, CarriesBindableList[T], Generic[T]):
    """
    An observable wrapper around a list that supports bidirectional bindings and reactive updates.
    
    This class provides a reactive wrapper around Python lists, allowing other objects to
    observe changes and establish bidirectional bindings. It implements the full list interface
    while maintaining reactivity and binding capabilities.
    
    Features:
    - Bidirectional bindings with other ObservableList instances
    - Full list interface compatibility (append, extend, insert, remove, etc.)
    - Listener notification system for change events
    - Automatic copying to prevent external modification
    - Type-safe generic implementation
    
    Example:
        >>> # Create an observable list
        >>> todo_list = ObservableList(["Buy groceries", "Walk dog"])
        >>> todo_list.add_listeners(lambda: print("List changed!"))
        >>> todo_list.append("Read book")  # Triggers listener
        List changed!
        
        >>> # Create bidirectional binding
        >>> todo_copy = ObservableList(todo_list)
        >>> todo_copy.append("Exercise")  # Updates both lists
        >>> print(todo_list.value, todo_copy.value)
        ['Buy groceries', 'Walk dog', 'Read book', 'Exercise'] ['Buy groceries', 'Walk dog', 'Read book', 'Exercise']
    
    Args:
        value: Initial list, another ObservableList to bind to, or None for empty list
    """

    @overload
    def __init__(self, value: list[T]):
        """Initialize with a direct list value."""
        ...

    @overload
    def __init__(self, value: CarriesBindableList[T]):
        """Initialize with another observable list, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, value: None):
        """Initialize with an empty list."""
        ...

    def __init__(self, value: list[T] | CarriesBindableList[T] | None = None):
        """
        Initialize the ObservableList.
        
        Args:
            value: Initial list, observable list to bind to, or None for empty list
        """
        super().__init__()
        if value is None:
            initial_value: list[T] = []
            bindable_list_carrier: Optional[CarriesBindableList[T]] = None
        elif isinstance(value, CarriesBindableList):
            initial_value: list[T] = value._get_list().copy()
            bindable_list_carrier: Optional[CarriesBindableList[T]] = value
        else:
            initial_value: list[T] = value.copy()
            bindable_list_carrier: Optional[CarriesBindableList[T]] = None
            
        self._value: list[T] = initial_value
        self._binding_handler: InternalBindingHandler[list[T]] = InternalBindingHandler(self, self._get_list, self._set_list, self._check_list)

        if bindable_list_carrier is not None:
            self.bind_to_observable(bindable_list_carrier)

    @property
    def value(self) -> list[T]:
        """
        Get a copy of the current list value.
        
        Returns:
            A copy of the current list to prevent external modification
        """
        return self._value.copy()
    
    def _set_list(self, list_to_set: list[T]) -> None:
        """Internal method to set list from binding system."""
        self.set_list(list_to_set)
    
    def _get_list(self) -> list[T]:
        """Internal method to get list for binding system."""
        return self._value
    
    def _check_list(self, list_to_check: list[T]) -> bool:
        """Internal method to check list validity for binding system."""
        return True

    def _get_list_binding_handler(self) -> InternalBindingHandler[list[T]]:
        """Internal method to get binding handler for binding system."""
        return self._binding_handler
    
    def set_list(self, list_to_set: list[T]) -> None:
        """
        Set the entire list to a new value.
        
        This method replaces the current list with a new one, triggering binding updates
        and listener notifications. If the new list is identical to the current one,
        no action is taken.
        
        Args:
            list_to_set: The new list to set
        """
        if list_to_set == self._value:
            return
        self._value = list_to_set.copy()
        self._binding_handler.notify_bindings(self._value)
        self._notify_listeners()

    def bind_to_observable(self, observable: CarriesBindableList[T], initial_sync_mode: SyncMode = DEFAULT_SYNC_MODE) -> None:
        """
        Establish a bidirectional binding with another observable list.
        
        This method creates a bidirectional binding between this observable list and another,
        ensuring that changes to either observable are automatically propagated to the other.
        The binding can be configured with different initial synchronization modes.
        
        Args:
            observable: The observable list to bind to
            initial_sync_mode: How to synchronize values initially
            
        Raises:
            ValueError: If observable is None
        """
        if observable is None:
            raise ValueError("Cannot bind to None observable")
        self._binding_handler.establish_binding(observable._get_list_binding_handler(), initial_sync_mode)

    def unbind_from_observable(self, observable: CarriesBindableList[T]) -> None:
        """
        Remove the bidirectional binding with another observable list.
        
        This method removes the binding between this observable list and another,
        preventing further automatic synchronization of changes.
        
        Args:
            observable: The observable list to unbind from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        self._binding_handler.remove_binding(observable._get_list_binding_handler())

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
    
    # Standard list methods
    def append(self, item: T) -> None:
        """
        Add an item to the end of the list.
        
        Args:
            item: The item to add to the list
        """
        self._value.append(item)
        self._binding_handler.notify_bindings(self._value)
        self._notify_listeners()
    
    def extend(self, iterable) -> None:
        """
        Extend the list by appending elements from the iterable.
        
        Args:
            iterable: The iterable containing elements to add
        """
        old_value = self._value.copy()
        self._value.extend(iterable)
        if old_value != self._value:
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def insert(self, index: int, item: T) -> None:
        """
        Insert an item at a given position.
        
        Args:
            index: The position to insert the item at
            item: The item to insert
        """
        self._value.insert(index, item)
        self._binding_handler.notify_bindings(self._value)
        self._notify_listeners()
    
    def remove(self, item: T) -> None:
        """Remove the first occurrence of a value"""
        if item in self._value:
            self._value.remove(item)
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def pop(self, index: int = -1) -> T:
        """Remove and return item at index (default last)"""
        item = self._value.pop(index)
        self._binding_handler.notify_bindings(self._value)
        self._notify_listeners()
        return item
    
    def clear(self) -> None:
        """Remove all items from the list"""
        if self._value:
            self._value.clear()
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def sort(self, key=None, reverse=False) -> None:
        """Sort the list in ascending order and return None"""
        old_value = self._value.copy()
        self._value.sort(key=key, reverse=reverse)
        if old_value != self._value:
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def reverse(self) -> None:
        """Reverse the elements of the list in place"""
        old_value = self._value.copy()
        self._value.reverse()
        if old_value != self._value:
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def count(self, item: T) -> int:
        """Return number of occurrences of value"""
        return self._value.count(item)
    
    def index(self, item: T, start=0, stop=None) -> int:
        """Return first index of value"""
        return self._value.index(item, start, stop)
    
    def __str__(self) -> str:
        return f"OL(value={self._value})"
    
    def __repr__(self) -> str:
        return f"ObservableList({self._value})"
    
    def __len__(self) -> int:
        return len(self._value)
    
    def __getitem__(self, index):
        """Get item at index or slice"""
        return self._value[index]
    
    def __setitem__(self, index, value):
        """Set item at index or slice"""
        if isinstance(index, slice):
            # Handle slice assignment
            old_value = self._value.copy()
            self._value[index] = value
            if old_value != self._value:
                self._binding_handler.notify_bindings(self._value)
                self._notify_listeners()
        else:
            # Handle single index assignment
            if self._value[index] != value:
                self._value[index] = value
                self._binding_handler.notify_bindings(self._value)
                self._notify_listeners()
    
    def __delitem__(self, index):
        """Delete item at index or slice"""
        old_value = self._value.copy()
        del self._value[index]
        if old_value != self._value:
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def __contains__(self, item: T) -> bool:
        return item in self._value
    
    def __iter__(self):
        """Iterate over the list"""
        return iter(self._value)
    
    def __reversed__(self):
        """Reverse iterate over the list"""
        return reversed(self._value)
    
    def __eq__(self, other) -> bool:
        """Compare with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value == other._value
        return self._value == other
    
    def __ne__(self, other) -> bool:
        """Compare with another list or observable"""
        return not (self == other)
    
    def __lt__(self, other) -> bool:
        """Compare with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value < other._value
        return self._value < other
    
    def __le__(self, other) -> bool:
        """Compare with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value <= other._value
        return self._value <= other
    
    def __gt__(self, other) -> bool:
        """Compare with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value > other._value
        return self._value > other
    
    def __ge__(self, other) -> bool:
        """Compare with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value >= other._value
        return self._value >= other
    
    def __add__(self, other):
        """Concatenate with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value + other._value
        return self._value + other
    
    def __mul__(self, other):
        """Repeat the list"""
        return self._value * other
    
    def __rmul__(self, other):
        """Repeat the list (right multiplication)"""
        return other * self._value
    
    def __hash__(self) -> int:
        """Hash based on the current value"""
        return hash(tuple(self._value))