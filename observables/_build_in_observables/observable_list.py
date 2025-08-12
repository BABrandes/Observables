from typing import Any, Generic, TypeVar, overload
from typing import Optional
from .._utils._internal_binding_handler import InternalBindingHandler, SyncMode, DEFAULT_SYNC_MODE
from .._utils._carries_bindable_list import CarriesBindableList
from .._utils.observable import Observable

T = TypeVar("T")

class ObservableList(Observable, CarriesBindableList[T], Generic[T]):
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

        Raises:
            ValueError: If the initial list is not a list
        """

        if value is None:
            initial_value: list[T] = []
            bindable_list_carrier: Optional[CarriesBindableList[T]] = None
        elif isinstance(value, CarriesBindableList):
            initial_value: list[T] = value._get_list().copy()
            bindable_list_carrier: Optional[CarriesBindableList[T]] = value
        else:
            initial_value: list[T] = value.copy()
            bindable_list_carrier: Optional[CarriesBindableList[T]] = None

        def verification_method(x: dict[str, Any]) -> tuple[bool, str]:
            if not isinstance(x["value"], list):
                return False, "Value is not a list"
            return True, "Verification method passed"
            
        super().__init__(
            {
                "value": initial_value
            },
            {
                "value": InternalBindingHandler(self, self._get_list, self._set_list)
            },
            verification_method=verification_method
        )

        if bindable_list_carrier is not None:
            self.bind_to_observable(bindable_list_carrier)

    @property
    def value(self) -> list[T]:
        """
        Get a copy of the current list value.
        
        Returns:
            A copy of the current list to prevent external modification
        """
        return self._get_list().copy()
    
    def _set_list(self, list_to_set: list[T]) -> None:
        """
        Internal method to set list from binding system.
        
        Args:
            list_to_set: The new list to set
        """
        self.set_list(list_to_set)
    
    def _get_list(self) -> list[T]:
        """
        Get the current list value. No copy is made!
        
        Returns:
            The current list value
        """
        return self._component_values["value"]
    
    def _get_list_binding_handler(self) -> InternalBindingHandler[list[T]]:
        """Internal method to get binding handler for binding system."""
        return self._component_binding_handlers["value"]
    
    def set_list(self, list_to_set: list[T]) -> None:
        """
        Set the entire list to a new value.
        
        This method replaces the current list with a new one, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            list_to_set: The new list to set
        """
        if list_to_set == self._get_list():
            return
        # Use the protocol method to set the value
        self.set_observed_values((list_to_set,))

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
        self._get_list_binding_handler().establish_binding(observable._get_list_binding_handler(), initial_sync_mode)

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
        self._get_list_binding_handler().remove_binding(observable._get_list_binding_handler())

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
        binding_state_consistent, binding_state_consistent_message = self._get_list_binding_handler().check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._get_list_binding_handler().check_values_synced()
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
        new_list = self._get_list().copy()
        new_list.append(item)
        self.set_observed_values((new_list,))
    
    def extend(self, iterable) -> None:
        """
        Extend the list by appending elements from the iterable.
        
        Args:
            iterable: The iterable containing elements to add
        """
        new_list = self._get_list().copy()
        new_list.extend(iterable)
        if new_list != self._get_list():
            self.set_observed_values((new_list,))
    
    def insert(self, index: int, item: T) -> None:
        """
        Insert an item at a given position.
        
        Args:
            index: The position to insert the item at
            item: The item to insert
        """
        new_list = self._get_list().copy()
        new_list.insert(index, item)
        self.set_observed_values((new_list,))
    
    def remove(self, item: T) -> None:
        """
        Remove the first occurrence of a value from the list.
        
        This method removes the first occurrence of the specified item from the list,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The item to remove from the list
            
        Note:
            If the item is not found in the list, no action is taken and no
            notifications are triggered.
        """
        if item in self._get_list():
            new_list = self._get_list().copy()
            new_list.remove(item)
            self.set_observed_values((new_list,))
    
    def pop(self, index: int = -1) -> T:
        """
        Remove and return the item at the specified index.
        
        This method removes the item at the specified index from the list and returns it,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            index: The index of the item to remove (default: -1, last item)
            
        Returns:
            The removed item
            
        Raises:
            IndexError: If the index is out of range
        """
        item = self._component_values["value"][index]
        new_list = self._get_list().copy()
        new_list.pop(index)
        self.set_observed_values((new_list,))
        return item
    
    def clear(self) -> None:
        """
        Remove all items from the list.
        
        This method removes all items from the list, making it empty. It uses
        set_observed_values to ensure all changes go through the centralized protocol method.
        """
        if self._get_list():
            new_list = []
            self.set_observed_values((new_list,))
    
    def sort(self, key=None, reverse=False) -> None:
        """
        Sort the list in place.
        
        This method sorts the list in ascending order (or descending if reverse=True),
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            key: Optional function to extract comparison key from each element
            reverse: If True, sort in descending order (default: False)
        """
        new_list = self._get_list().copy()
        new_list.sort(key=key, reverse=reverse)
        if new_list != self._get_list():
            self.set_observed_values((new_list,))
    
    def reverse(self) -> None:
        """
        Reverse the elements of the list in place.
        
        This method reverses the order of elements in the list, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        """
        new_list = self._get_list().copy()
        new_list.reverse()
        if new_list != self._get_list():
            self.set_observed_values((new_list,))
    
    def count(self, item: T) -> int:
        """
        Return the number of occurrences of a value in the list.
        
        Args:
            item: The item to count
            
        Returns:
            The number of times the item appears in the list
        """
        return self._get_list().count(item)
    
    def index(self, item: T, start=0, stop=None) -> int:
        """
        Return the first index of a value in the list.
        
        Args:
            item: The item to find
            start: Start index for the search (default: 0)
            stop: End index for the search (default: end of list)
            
        Returns:
            The index of the first occurrence of the item
            
        Raises:
            ValueError: If the item is not found in the specified range
        """
        return self._get_list().index(item, start, stop)
    
    def __str__(self) -> str:
        return f"OL(value={self._get_list()})"
    
    def __repr__(self) -> str:
        return f"ObservableList({self._get_list()})"
    
    def __len__(self) -> int:
        """
        Get the length of the list.
        
        Returns:
            The number of items in the list
        """
        return len(self._get_list())
    
    def __getitem__(self, index):
        """
        Get an item at the specified index or slice.
        
        Args:
            index: Integer index or slice object
            
        Returns:
            The item at the index or a slice of items
            
        Raises:
            IndexError: If the index is out of range
        """
        return self._get_list()[index]
    
    def __setitem__(self, index, value):
        """
        Set an item at the specified index or slice.
        
        This method sets the item at the specified index or slice, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            index: Integer index or slice object
            value: The value to set (can be a single item or iterable for slices)
            
        Raises:
            IndexError: If the index is out of range
        """
        new_list = self._get_list().copy()
        new_list[index] = value
        if new_list != self._get_list():
            self.set_observed_values((new_list,))
    
    def __delitem__(self, index):
        """
        Delete an item at the specified index or slice.
        
        This method deletes the item at the specified index or slice, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            index: Integer index or slice object
            
        Raises:
            IndexError: If the index is out of range
        """
        new_list = self._get_list().copy()
        del new_list[index]
        if new_list != self._get_list():
            self.set_observed_values((new_list,))
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an item is contained in the list.
        
        Args:
            item: The item to check for
            
        Returns:
            True if the item is in the list, False otherwise
        """
        return item in self._get_list()
    
    def __iter__(self):
        """
        Get an iterator over the list items.
        
        Returns:
            An iterator that yields each item in the list
        """
        return iter(self._get_list())
    
    def __reversed__(self):
        """
        Get a reverse iterator over the list items.
        
        Returns:
            A reverse iterator that yields each item in the list in reverse order
        """
        return reversed(self._get_list())
    
    def __eq__(self, other) -> bool:
        """
        Check equality with another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if the lists contain the same items in the same order, False otherwise
        """
        if isinstance(other, ObservableList):
            return self._get_list() == other._get_list()
        return self._get_list() == other
    
    def __ne__(self, other) -> bool:
        """
        Check inequality with another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if the lists are not equal, False otherwise
        """
        return not (self == other)
    
    def __lt__(self, other) -> bool:
        """
        Check if this list is less than another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if this list is lexicographically less than the other, False otherwise
        """
        if isinstance(other, ObservableList):
            return self._get_list() < other._get_list()
        return self._get_list() < other
    
    def __le__(self, other) -> bool:
        """
        Check if this list is less than or equal to another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if this list is lexicographically less than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableList):
            return self._get_list() <= other._get_list()
        return self._get_list() <= other
    
    def __gt__(self, other) -> bool:
        """
        Check if this list is greater than another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if this list is lexicographically greater than the other, False otherwise
        """
        if isinstance(other, ObservableList):
            return self._get_list() > other._get_list()
        return self._get_list() > other
    
    def __ge__(self, other) -> bool:
        """
        Check if this list is greater than or equal to another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if this list is lexicographically greater than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableList):
            return self._get_list() >= other._get_list()
        return self._get_list() >= other
    
    def __add__(self, other):
        """
        Concatenate this list with another list or observable list.
        
        Args:
            other: Another list or ObservableList to concatenate with
            
        Returns:
            A new list containing all items from both lists
        """
        if isinstance(other, ObservableList):
            return self._get_list() + other._get_list()
        return self._get_list() + other
    
    def __mul__(self, other):
        """
        Repeat the list a specified number of times.
        
        Args:
            other: The number of times to repeat the list
            
        Returns:
            A new list with the original items repeated
        """
        return self._get_list() * other
    
    def __rmul__(self, other):
        """
        Repeat the list a specified number of times (right multiplication).
        
        Args:
            other: The number of times to repeat the list
            
        Returns:
            A new list with the original items repeated
        """
        return other * self._get_list()
    
    def __hash__(self) -> int:
        """
        Get the hash value based on the current list contents.
        
        Returns:
            Hash value of the list as a tuple
        """
        return hash(tuple(self._get_list()))
    
    def get_observed_component_values(self) -> tuple[list[T]]:
        """
        Get the values of all observables that are bound to this observable.
        
        This method is part of the Observable protocol and provides access to
        the current values of all bound observables.
        
        Returns:
            A tuple containing the current list value
        """
        return tuple(self._get_list())
    
    def set_observed_values(self, values: tuple[list[T]]) -> None:
        """
        Set the values of all observables that are bound to this observable.
        
        This method is part of the Observable protocol and allows external
        systems to update this observable's value. It handles all internal
        state changes, binding updates, and listener notifications.
        
        Args:
            values: A tuple containing the new list value to set
        """
        # Extract the list from the tuple (values should be a single-element tuple)
        new_list = values[0]
        
        # Update internal state
        self._set_component_values(
            {"value": new_list}
        )