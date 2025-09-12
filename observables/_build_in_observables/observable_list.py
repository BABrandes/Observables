from logging import Logger
from typing import Any, Generic, TypeVar, overload, Protocol, runtime_checkable, Iterable, Callable, Literal, Mapping, Optional, Iterator
from .._hooks.hook_like import HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.carries_hooks import CarriesHooks
from .._utils.base_observable import BaseObservable
from .._utils.observable_serializable import ObservableSerializable

T = TypeVar("T")

@runtime_checkable
class ObservableListLike(CarriesHooks[Any, Any], Protocol[T]):
    """
    Protocol for observable list objects.
    """
    
    @property
    def value(self) -> list[T]:
        """
        Get the list value.
        """
        ...
    
    @value.setter
    def value(self, value: list[T]) -> None:
        """
        Set the list value.
        """
        ...

    def change_value(self, new_value: list[T]) -> None:
        """
        Change the list value (lambda-friendly method).
        """
        ...
    
    @property
    def value_hook(self) -> HookLike[list[T]]:
        """
        Get the hook for the list.
        """
        ...
    
    @property
    def length(self) -> int:
        """
        Get the current length of the list.
        """
        ...
    
    @property
    def length_hook(self) -> HookLike[int]:
        """
        Get the hook for the list length.
        """
        ...
    

class ObservableList(BaseObservable[Literal["value"], Literal["length"], list[T], int], ObservableSerializable[Literal["value"], "ObservableList"], ObservableListLike[T], Generic[T]):
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
    def __init__(self, list_value: list[T], logger: Optional[Logger] = None) -> None:
        """Initialize with a direct list value."""
        ...

    @overload
    def __init__(self, observable_or_hook: HookLike[list[T]], logger: Optional[Logger] = None) -> None:
        """Initialize with another observable list, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, observable: ObservableListLike[T], logger: Optional[Logger] = None) -> None:
        """Initialize from another ObservableListLike object."""
        ...

    @overload
    def __init__(self, list_value: None, logger: Optional[Logger] = None) -> None:
        """Initialize with an empty list."""
        ...

    def __init__(self, observable_or_hook_or_value: list[T] | HookLike[list[T]] | None = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize the ObservableList.
        
        Args:
            value: Initial list, observable list to bind to, or None for empty list

        Raises:
            ValueError: If the initial list is not a list
        """

        if observable_or_hook_or_value is None:
            initial_value: list[T] = []
            hook: Optional[HookLike[list[T]]] = None
        elif isinstance(observable_or_hook_or_value, ObservableListLike):
            initial_value = observable_or_hook_or_value.value # type: ignore
            hook = observable_or_hook_or_value.value_hook # type: ignore
        elif isinstance(observable_or_hook_or_value, HookLike):
            initial_value = observable_or_hook_or_value.value
            hook = observable_or_hook_or_value
        else:
            initial_value = observable_or_hook_or_value.copy()
            hook = None

        self._internal_construct_from_values(
            {"value": initial_value},
            logger=logger,
        )

        if hook is not None:
            self.connect(hook, "value", InitialSyncMode.USE_TARGET_VALUE) # type: ignore

    def _internal_construct_from_values(
        self,
        initial_values: Mapping[Literal["value"], list[T]],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """
        Construct an ObservableList instance.
        """

        super().__init__(
            initial_values,
            verification_method=lambda x: (True, "Verification method passed") if isinstance(x["value"], list) else (False, "Value is not a list"), # type: ignore
            secondary_hook_callbacks={"length": lambda x: len(x["value"])}, # type: ignore
            logger=logger
        )

    @property
    def value(self) -> list[T]:
        """
        Get a copy of the current list value.
        
        Returns:
            A copy of the current list to prevent external modification
        """
        return self._primary_hooks["value"].value.copy() # type: ignore
    
    @value.setter
    def value(self, value: list[T]) -> None:
        """
        Set the current value of the list.
        """
        if value != self._primary_hooks["value"].value: # type: ignore
            self._set_component_values({"value": value}, notify_binding_system=True)

    def change_value(self, new_value: list[T]) -> None:
        """
        Change the list value (lambda-friendly method).
        
        This method is equivalent to setting the .value property but can be used
        in lambda expressions and other contexts where property assignment isn't suitable.
        
        Args:
            new_value: The new list value to set
        """
        if new_value != self._primary_hooks["value"].value:
            self._set_component_values({"value": new_value}, notify_binding_system=True)

    @property
    def value_hook(self) -> HookLike[list[T]]:
        """
        Get the hook for the list value.
        
        This hook can be used for binding operations with other observables.
        """
        return self._primary_hooks["value"] # type: ignore
    
    @property
    def length(self) -> int:
        """
        Get the current length of the list.
        """
        return len(self._primary_hooks["value"].value) # type: ignore
    
    @property
    def length_hook(self) -> HookLike[int]:
        """
        Get the hook for the list length.
        
        This hook can be used for binding operations that react to length changes.
        """
        return self._secondary_hooks["length"] # type: ignore
    
    
    # Standard list methods
    def append(self, item: T) -> None:
        """
        Add an item to the end of the list.
        
        Args:
            item: The item to add to the list
        """
        new_list = self._primary_hooks["value"].value.copy() # type: ignore
        new_list.append(item) # type: ignore
        self._set_component_values({"value": new_list}, notify_binding_system=True)
    
    def extend(self, iterable: Iterable[T]) -> None:
        """
        Extend the list by appending elements from the iterable.
        
        Args:
            iterable: The iterable containing elements to add
        """
        new_list = self._primary_hooks["value"].value.copy() # type: ignore
        new_list.extend(iterable) # type: ignore
        if new_list != self._primary_hooks["value"].value:
            self._set_component_values({"value": new_list}, notify_binding_system=True)
    
    def insert(self, index: int, item: T) -> None:
        """
        Insert an item at a given position.
        
        Args:
            index: The position to insert the item at
            item: The item to insert
        """
        new_list = self._primary_hooks["value"].value.copy() # type: ignore
        new_list.insert(index, item) # type: ignore
        self._set_component_values({"value": new_list}, notify_binding_system=True)
    
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
        if item in self._primary_hooks["value"].value: # type: ignore
            new_list = self._primary_hooks["value"].value.copy() # type: ignore
            new_list.remove(item) # type: ignore
            self._set_component_values({"value": new_list}, notify_binding_system=True)
    
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
        item: T = self._primary_hooks["value"].value[index] # type: ignore
        new_list = self._primary_hooks["value"].value.copy() # type: ignore
        new_list.pop(index) # type: ignore
        self._set_component_values({"value": new_list}, notify_binding_system=True)
        return item # type: ignore
    
    def clear(self) -> None:
        """
        Remove all items from the list.
        
        This method removes all items from the list, making it empty. It uses
        set_observed_values to ensure all changes go through the centralized protocol method.
        """
        if self._primary_hooks["value"].value: # type: ignore
            new_list: list[T] = []
            self._set_component_values({"value": new_list}, notify_binding_system=True)
    
    def sort(self, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> None:
        """
        Sort the list in place.
        
        This method sorts the list in ascending order (or descending if reverse=True),
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            key: Optional function to extract comparison key from each element
            reverse: If True, sort in descending order (default: False)
        """
        new_list = self._primary_hooks["value"].value.copy() # type: ignore
        new_list.sort(key=key, reverse=reverse) # type: ignore
        if new_list != self._primary_hooks["value"].value:
            self._set_component_values({"value": new_list}, notify_binding_system=True)
    
    def reverse(self) -> None:
        """
        Reverse the elements of the list in place.
        
        This method reverses the order of elements in the list, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        """
        new_list = self._primary_hooks["value"].value.copy() # type: ignore
        new_list.reverse() # type: ignore
        if new_list != self._primary_hooks["value"].value:
            self._set_component_values({"value": new_list}, notify_binding_system=True)
    
    def count(self, item: T) -> int:
        """
        Return the number of occurrences of a value in the list.
        
        Args:
            item: The item to count
            
        Returns:
            The number of times the item appears in the list
        """
        return self._primary_hooks["value"].value.count(item) # type: ignore
    
    def index(self, item: T, start: int = 0, stop: Optional[int] = None) -> int:
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
        list_value = self._primary_hooks["value"].value
        if stop is None:
            return list_value.index(item, start) # type: ignore
        else:
            return list_value.index(item, start, stop) # type: ignore
    
    def __str__(self) -> str:
        return f"OL(value={self._primary_hooks['value'].value})"
    
    def __repr__(self) -> str:
        return f"ObservableList({self._primary_hooks['value'].value})"
    
    def __len__(self) -> int:
        """
        Get the length of the list.
        
        Returns:
            The number of items in the list
        """
        return len(self._primary_hooks["value"].value) # type: ignore
    
    def __getitem__(self, index: int) -> T:
        """
        Get an item at the specified index or slice.
        
        Args:
            index: Integer index or slice object
            
        Returns:
            The item at the index or a slice of items
            
        Raises:
            IndexError: If the index is out of range
        """
        return self._primary_hooks["value"].value[index] # type: ignore
    
    def __setitem__(self, index: int, value: T) -> None:
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
        new_list = self._primary_hooks["value"].value.copy() # type: ignore
        new_list[index] = value
        if new_list != self._primary_hooks["value"].value:
            self._set_component_values({"value": new_list}, notify_binding_system=True)
    
    def __delitem__(self, index: int) -> None:
        """
        Delete an item at the specified index or slice.
        
        This method deletes the item at the specified index or slice, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            index: Integer index or slice object
            
        Raises:
            IndexError: If the index is out of range
        """
        new_list = self._primary_hooks["value"].value.copy() # type: ignore
        del new_list[index]
        if new_list != self._primary_hooks["value"].value:
            self._set_component_values({"value": new_list}, notify_binding_system=True)
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an item is contained in the list.
        
        Args:
            item: The item to check for
            
        Returns:
            True if the item is in the list, False otherwise
        """
        return item in self._primary_hooks["value"].value # type: ignore
    
    def __iter__(self) -> Iterator[T]:
        """
        Get an iterator over the list items.
        
        Returns:
            An iterator that yields each item in the list
        """
        return iter(self._primary_hooks["value"].value) # type: ignore
    
    def __reversed__(self) -> Iterator[T]:
        """
        Get a reverse iterator over the list items.
        
        Returns:
            A reverse iterator that yields each item in the list in reverse order
        """
        return reversed(self._primary_hooks["value"].value) # type: ignore
    
    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if the lists contain the same items in the same order, False otherwise
        """
        if isinstance(other, ObservableList):
            return self._primary_hooks["value"].value == other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value == other
    
    def __ne__(self, other: Any) -> bool:
        """
        Check inequality with another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if the lists are not equal, False otherwise
        """
        return not (self == other)
    
    def __lt__(self, other: Any) -> bool:
        """
        Check if this list is less than another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if this list is lexicographically less than the other, False otherwise
        """
        if isinstance(other, ObservableList):
            return self._primary_hooks["value"].value < other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value < other
    
    def __le__(self, other: Any) -> bool:
        """
        Check if this list is less than or equal to another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if this list is lexicographically less than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableList):
            return self._primary_hooks["value"].value <= other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value <= other
    
    def __gt__(self, other: Any) -> bool:
        """
        Check if this list is greater than another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if this list is lexicographically greater than the other, False otherwise
        """
        if isinstance(other, ObservableList):
            return self._primary_hooks["value"].value > other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value > other
    
    def __ge__(self, other: Any) -> bool:
        """
        Check if this list is greater than or equal to another list or observable list.
        
        Args:
            other: Another list or ObservableList to compare with
            
        Returns:
            True if this list is lexicographically greater than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableList):
            return self._primary_hooks["value"].value >= other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value >= other
    
    def __add__(self, other: Any) -> list[T]:
        """
        Concatenate this list with another list or observable list.
        
        Args:
            other: Another list or ObservableList to concatenate with
            
        Returns:
            A new list containing all items from both lists
        """
        if isinstance(other, ObservableList):
            return self._primary_hooks["value"].value + other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value + other
    
    def __mul__(self, other: int) -> list[T]:
        """
        Repeat the list a specified number of times.
        
        Args:
            other: The number of times to repeat the list
            
        Returns:
            A new list with the original items repeated
        """
        return self._primary_hooks["value"].value * other # type: ignore
    
    def __rmul__(self, other: int) -> list[T]:
        """
        Repeat the list a specified number of times (right multiplication).
        
        Args:
            other: The number of times to repeat the list
            
        Returns:
            A new list with the original items repeated
        """
        return other * self._primary_hooks["value"].value # type: ignore
    
    def __hash__(self) -> int:
        """
        Get the hash value based on the current list contents.
        
        Returns:
            Hash value of the list as a tuple
        """
        return hash(tuple(self._primary_hooks["value"].value)) # type: ignore