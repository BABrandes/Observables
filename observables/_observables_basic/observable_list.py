from typing import Any, Generic, TypeVar, overload, Protocol, runtime_checkable, Iterable, Callable, Literal, Optional, Iterator, Mapping
from logging import Logger

from .._hooks.hook_like import HookLike
from .._carries_hooks.carries_hooks_like import CarriesHooksLike
from .._carries_hooks.base_observable import BaseObservable
from .._carries_hooks.observable_serializable import ObservableSerializable
from .._nexus_system.submission_error import SubmissionError

T = TypeVar("T")

@runtime_checkable
class ObservableListLike(CarriesHooksLike[Any, Any], Protocol[T]):
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
    

class ObservableList(BaseObservable[Literal["value"], Literal["length"], list[T], int, "ObservableList"], ObservableListLike[T], ObservableSerializable[Literal["value"], list[T]], Generic[T]):
    """
    Observable wrapper for Python lists with full list interface and bidirectional binding.
    
    ObservableList provides a reactive wrapper around standard Python lists, implementing
    the complete list interface while adding listener notifications, validation, and
    bidirectional synchronization capabilities.
    
    Type Parameters:
        T: The type of elements in the list. All elements must be of type T.
           Common examples: int, str, float, custom objects, etc.
    
    Multiple Inheritance:
        - BaseObservable: Core observable functionality with two hooks (value, length)
        - ObservableListLike[T]: Protocol defining the observable list interface
        - ObservableSerializable: Support for serialization callbacks
        - Generic[T]: Type-safe element storage and operations
    
    Hooks:
        - **value_hook**: Primary hook for the entire list (bidirectional, can be modified)
        - **length_hook**: Secondary hook for list length (read-only, computed from value)
    
    Key Features:
        - **Full List Interface**: append(), extend(), insert(), remove(), pop(), clear(), etc.
        - **Automatic Copying**: Input lists are copied to prevent external modification
        - **Bidirectional Binding**: Connect multiple lists to share the same data
        - **Change Notifications**: Listeners triggered on any modification
        - **Secondary Hooks**: Length hook automatically updates when list changes
        - **Thread Safety**: All operations protected by NexusManager's lock
        - **Memory Efficient**: Bound lists share centralized storage via HookNexus
    
    Example:
        Basic list operations::
        
            from observables import ObservableList
            
            # Create observable list
            tasks = ObservableList(["Buy milk", "Walk dog"])
            
            # Add listener
            tasks.add_listeners(lambda: print(f"Tasks: {len(tasks.value)} items"))
            
            # Modify list (triggers listener)
            tasks.append("Read book")  # Prints: "Tasks: 3 items"
            tasks.extend(["Exercise", "Cook"])  # Prints: "Tasks: 5 items"
            
            # Access length via secondary hook
            print(tasks.length_hook.value)  # 5
        
        Bidirectional binding::
        
            tasks1 = ObservableList(["Task A"])
            tasks2 = ObservableList(["Task B"])
            
            # Bind them - both adopt tasks1's value
            tasks1.connect_hook(tasks2.value_hook, "value", "use_caller_value")
            
            # Now both share the same underlying list
            tasks1.append("Task C")
            print(tasks2.value)  # ["Task A", "Task C"]
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
        Initialize an ObservableList.
        
        This constructor supports four initialization patterns:
        
        1. **Direct list**: Pass a list directly (will be copied)
        2. **From hook**: Pass a HookLike[list[T]] to bind to
        3. **From observable**: Pass another ObservableList to bind to
        4. **Empty list**: Pass None to create an empty list
        
        Args:
            observable_or_hook_or_value: Can be one of four types:
                - list[T]: A Python list (will be copied to prevent external modification)
                - HookLike[list[T]]: A hook to bind to (establishes bidirectional connection)
                - ObservableListLike[T]: Another observable list to bind to
                - None: Creates an empty list
            logger: Optional logger for debugging observable operations. If provided,
                operations like appending, extending, value changes, and hook connections
                will be logged. Default is None.
        
        Raises:
            ValueError: If the value is not a list type (validation failure).
        
        Note:
            When initialized with a direct list, the list is **copied** to prevent
            external code from modifying the internal state. This ensures that all
            changes go through the observable's methods and trigger proper notifications.
        
        Example:
            Four initialization patterns::
            
                # 1. Direct list (copied)
                todos = ObservableList(["Task 1", "Task 2"])
                
                # 2. Empty list
                empty = ObservableList()  # or ObservableList(None)
                
                # 3. From another observable (creates binding)
                todos_copy = ObservableList(todos)
                todos.append("Task 3")  # Both update
                
                # 4. With logging
                import logging
                logger = logging.getLogger(__name__)
                logged_list = ObservableList([1, 2, 3], logger=logger)
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

        super().__init__(
            initial_component_values_or_hooks={"value": initial_value},
            verification_method=lambda x: (True, "Verification method passed") if isinstance(x["value"], list) else (False, "Value is not a list"), # type: ignore
            secondary_hook_callbacks={"length": lambda x: len(x["value"])}, # type: ignore
            logger=logger
        )

        if hook is not None:
            self.connect_hook(hook, "value", "use_target_value") # type: ignore

    @property
    def value(self) -> list[T]:
        """
        Get a copy of the current list value.
        
        Returns:
            A copy of the current list to prevent external modification
        """
        return self._primary_hooks["value"].value.copy()
    
    @value.setter
    def value(self, value: list[T]) -> None:
        """
        Set the current value of the list.
        """
        success, msg = self.submit_value("value", value)
        if not success:
            raise SubmissionError(msg, value)

    def change_value(self, new_value: list[T]) -> None:
        """
        Change the list value (lambda-friendly method).
        
        This method is equivalent to setting the .value property but can be used
        in lambda expressions and other contexts where property assignment isn't suitable.
        
        Args:
            new_value: The new list value to set
        """
        success, msg = self.submit_value("value", new_value)
        if not success:
            raise SubmissionError(msg, new_value, "value")

    @property
    def value_hook(self) -> HookLike[list[T]]:
        """
        Get the hook for the list value.
        
        This hook can be used for binding operations with other observables.
        """
        return self._primary_hooks["value"]
    
    @property
    def length(self) -> int:
        """
        Get the current length of the list.
        """
        return len(self._primary_hooks["value"].value)
    
    @property
    def length_hook(self) -> HookLike[int]:
        """
        Get the hook for the list length.
        
        This hook can be used for binding operations that react to length changes.
        """
        return self._secondary_hooks["length"]
    
    
    # Standard list methods
    def append(self, item: T) -> None:
        """
        Add an item to the end of the list.
        
        Args:
            item: The item to add to the list
        """
        new_list = self._primary_hooks["value"].value.copy()
        new_list.append(item) # type: ignore
        success, msg = self.submit_values({"value": new_list})
        if not success:
            raise SubmissionError(msg, new_list, "value")
    
    def extend(self, iterable: Iterable[T]) -> None:
        """
        Extend the list by appending elements from the iterable.
        
        Args:
            iterable: The iterable containing elements to add
        """
        new_list = self._primary_hooks["value"].value.copy()
        new_list.extend(iterable) # type: ignore
        if new_list != self._primary_hooks["value"].value:
            self.value = new_list
    
    def insert(self, index: int, item: T) -> None:
        """
        Insert an item at a given position.
        
        Args:
            index: The position to insert the item at
            item: The item to insert
        """
        new_list = self._primary_hooks["value"].value.copy()
        new_list.insert(index, item) # type: ignore
        self.value = new_list
    
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
        if item in self._primary_hooks["value"].value:
            new_list = self._primary_hooks["value"].value.copy()
            new_list.remove(item) # type: ignore
            if new_list != self._primary_hooks["value"].value:
                self.value = new_list
    
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
        new_list = self._primary_hooks["value"].value.copy()
        new_list.pop(index) # type: ignore
        if new_list != self._primary_hooks["value"].value:
            self.value = new_list
        return item # type: ignore
    
    def clear(self) -> None:
        """
        Remove all items from the list.
        
        This method removes all items from the list, making it empty. It uses
        set_observed_values to ensure all changes go through the centralized protocol method.
        """
        if self._primary_hooks["value"].value:
            new_list: list[T] = []
            if new_list != self._primary_hooks["value"].value:
                self.value = new_list # type: ignore
    
    def sort(self, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> None:
        """
        Sort the list in place.
        
        This method sorts the list in ascending order (or descending if reverse=True),
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            key: Optional function to extract comparison key from each element
            reverse: If True, sort in descending order (default: False)
        """
        new_list = self._primary_hooks["value"].value.copy()
        new_list.sort(key=key, reverse=reverse) # type: ignore
        if new_list != self._primary_hooks["value"].value:
            self.value = new_list
    
    def reverse(self) -> None:
        """
        Reverse the elements of the list in place.
        
        This method reverses the order of elements in the list, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        """
        new_list = self._primary_hooks["value"].value.copy()
        new_list.reverse() # type: ignore
        if new_list != self._primary_hooks["value"].value:
            self.value = new_list
    
    def count(self, item: T) -> int:
        """
        Return the number of occurrences of a value in the list.
        
        Args:
            item: The item to count
            
        Returns:
            The number of times the item appears in the list
        """
        return self._primary_hooks["value"].value.count(item)
    
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
            return list_value.index(item, start)
        else:
            return list_value.index(item, start, stop)
    
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
        return len(self._primary_hooks["value"].value)
    
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
        return self._primary_hooks["value"].value[index]
    
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
        new_list = self._primary_hooks["value"].value.copy()
        new_list[index] = value
        if new_list != self._primary_hooks["value"].value:
            self.value = new_list
    
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
        new_list = self._primary_hooks["value"].value.copy()
        del new_list[index]
        if new_list != self._primary_hooks["value"].value:
            self.value = new_list
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an item is contained in the list.
        
        Args:
            item: The item to check for
            
        Returns:
            True if the item is in the list, False otherwise
        """
        return item in self._primary_hooks["value"].value
    
    def __iter__(self) -> Iterator[T]:
        """
        Get an iterator over the list items.
        
        Returns:
            An iterator that yields each item in the list
        """
        return iter(self._primary_hooks["value"].value)
    
    def __reversed__(self) -> Iterator[T]:
        """
        Get a reverse iterator over the list items.
        
        Returns:
            A reverse iterator that yields each item in the list in reverse order
        """
        return reversed(self._primary_hooks["value"].value)
    
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

    #### ObservableSerializable implementation ####

    def get_value_references_for_serialization(self) -> Mapping[Literal["value"], list[T]]:
        return {"value": self._primary_hooks["value"].value}

    def set_value_references_from_serialization(self, values: Mapping[Literal["value"], list[T]]) -> None:
        self.value = values["value"]