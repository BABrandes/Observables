from typing import Any, Generic, Optional, TypeVar, overload, Callable
from .._utils.hook import Hook
from .._utils.sync_mode import SyncMode
from .._utils.carries_distinct_set_hook import CarriesDistinctSetHook
from .._utils.observable import Observable

T = TypeVar("T")

class ObservableSet(Observable, CarriesDistinctSetHook[T], Generic[T]):
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
    def __init__(self, hook: CarriesDistinctSetHook[T]|Hook[set[T]], validator: Optional[Callable[[set[T]], bool]] = None):
        """Initialize with a direct set value."""
        ...

    @overload
    def __init__(self, value: set[T]):
        """Initialize with another observable set, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, value: None):
        """Initialize with an empty set."""
        ...

    def __init__(self, hook_or_value: set[T] | CarriesDistinctSetHook[T] | None = None):
        """
        Initialize the ObservableSet.
        
        Args:
            value: Initial set, observable set to bind to, or None for empty set

        Raises:
            ValueError: If the initial set is not a set
        """
        if hook_or_value is None:
            initial_value: set[T] = set()
            hook: Optional[Hook[set[T]]] = None
        elif isinstance(hook_or_value, CarriesDistinctSetHook):
            initial_value: set[T] = hook_or_value.get_set_value()
            hook: Optional[Hook[set[T]]] = hook_or_value._get_set_hook()
        elif isinstance(hook_or_value, Hook):
            initial_value: set[T] = hook_or_value._get_callback()
            hook: Optional[Hook[set[T]]] = hook_or_value
        else:
            initial_value: set[T] = hook_or_value.copy()
            hook: Optional[Hook[set[T]]] = None
        
        def verification_method(x: dict[str, Any]) -> tuple[bool, str]:
            if not isinstance(x["value"], set):
                return False, "Value is not a set"
            return True, "Verification method passed"
        
        super().__init__(
            {
                "value": initial_value
            },
            {
                "value": Hook(self, self._get_set, self._set_set)
            },
            verification_method=verification_method
        )

        if hook is not None:
            self.bind_to(hook)
    

    @property
    def value(self) -> set[T]:
        """
        Get a copy of the current set value.
        
        Returns:
            A copy of the current set to prevent external modification
        """
        return self._get_set().copy()    
    
    def _get_set(self) -> set[T]:
        """
        Get the current set value. No copy is made!
        
        Returns:
            The current set value
        """
        return self._component_values["value"]
    
    def _set_set(self, set_to_set: set[T]) -> None:
        """
        Internal method to set set from hook.
        
        Args:
            set_to_set: The new set to set
        """
        self.set_set(set_to_set)
    
    def _get_set_hook(self) -> Hook[set[T]]:
        """
        Internal method to get hook for binding system.
        
        Returns:
            The hook for the set
        """
        return self._component_hooks["value"]
    
    def get_set_value(self) -> set[T]:
        """
        Get the current value of the set as a copy.
        
        Returns:
            A copy of the current set value
        """
        return self._component_values["value"].copy()
    
    def set_set(self, set_to_set: set[T]) -> None:
        """
        Set the entire set to a new value.
        
        This method replaces the current set with a new one, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            set_to_set: The new set to set
        """
        if set_to_set == self._get_set():
            return
        # Use the protocol method to set the value
        self.set_observed_values((set_to_set,))

    def bind_to(self, hook: CarriesDistinctSetHook[T]|Hook[set[T]], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
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
        if hook is None:
            raise ValueError("Cannot bind to None observable")
        if isinstance(hook, CarriesDistinctSetHook):
            hook = hook._get_set_hook()
        self._get_set_hook().establish_binding(hook, initial_sync_mode)

    def unbind_from(self, hook: CarriesDistinctSetHook[T]|Hook[set[T]]) -> None:
        """
        Remove the bidirectional binding with another observable set.
        
        This method removes the binding between this observable set and another,
        preventing further automatic synchronization of changes.
        
        Args:
            observable: The observable set to unbind from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        if isinstance(hook, CarriesDistinctSetHook):
            hook = hook._get_set_hook()
        self._get_set_hook().remove_binding(hook)

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
        binding_state_consistent, binding_state_consistent_message = self._get_set_hook().check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._get_set_hook().check_values_synced()
        if not values_synced:
            return False, values_synced_message
        return True, "Binding system is consistent"
    
    # Standard set methods
    def add(self, item: T) -> None:
        """
        Add an element to the set.
        
        This method adds an item to the set if it's not already present,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The element to add to the set
        """
        if item not in self._component_values["value"]:
            new_set = self._component_values["value"].copy()
            new_set.add(item)
            self.set_observed_values((new_set,))
    
    def remove(self, item: T) -> None:
        """
        Remove an element from the set.
        
        This method removes an item from the set if it's present,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The element to remove from the set
            
        Raises:
            KeyError: If the item is not in the set
        """
        if item in self._get_set():
            new_set = self._get_set().copy()
            new_set.remove(item)
            self.set_observed_values((new_set,))
    
    def discard(self, item: T) -> None:
        """
        Remove an element from the set if it is present.
        
        This method removes an item from the set if it's present,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        Unlike remove(), this method does not raise an error if the item is not found.
        
        Args:
            item: The element to remove from the set
        """
        if item in self._get_set():
            new_set = self._get_set().copy()
            new_set.discard(item)
            self.set_observed_values((new_set,))
    
    def pop(self) -> T:
        """
        Remove and return an arbitrary element from the set.
        
        This method removes and returns an arbitrary element from the set,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Returns:
            The removed element
            
        Raises:
            KeyError: If the set is empty
        """
        item = next(iter(self._get_set()))
        new_set = self._get_set().copy()
        new_set.pop()
        self.set_observed_values((new_set,))
        return item
    
    def clear(self) -> None:
        """
        Remove all elements from the set.
        
        This method removes all elements from the set, making it empty.
        It uses set_observed_values to ensure all changes go through the centralized protocol method.
        """
        if self._get_set():
            new_set = set()
            self.set_observed_values((new_set,))
    
    def update(self, *others) -> None:
        """
        Update the set with elements from all other iterables.
        
        This method adds all elements from the provided iterables to the set,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            *others: Variable number of iterables to add elements from
        """
        new_set = self._get_set().copy()
        for other in others:
            new_set.update(other)
        if new_set != self._get_set():
            self.set_observed_values((new_set,))
    
    def intersection_update(self, *others) -> None:
        """
        Update the set keeping only elements found in this set and all others.
        
        This method modifies the set to contain only elements that are present
        in this set and all the provided iterables, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            *others: Variable number of iterables to intersect with
        """
        new_set = self._get_set().copy()
        for other in others:
            new_set.intersection_update(other)
        if new_set != self._get_set():
            self.set_observed_values((new_set,))
    
    def difference_update(self, *others) -> None:
        """
        Update the set removing elements found in any of the others.
        
        This method removes from this set all elements that are present in any
        of the provided iterables, using set_observed_values to ensure all
        changes go through the centralized protocol method.
        
        Args:
            *others: Variable number of iterables to remove elements from
        """
        new_set = self._get_set().copy()
        for other in others:
            new_set.difference_update(other)
        if new_set != self._get_set():
            self.set_observed_values((new_set,))
    
    def symmetric_difference_update(self, other) -> None:
        """
        Update the set keeping only elements found in either set but not both.
        
        This method modifies the set to contain only elements that are present
        in either this set or the other iterable, but not in both, using
        set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            other: An iterable to compute symmetric difference with
        """
        new_set = self._get_set().copy()
        new_set.symmetric_difference_update(other)
        if new_set != self._get_set():
            self.set_observed_values((new_set,))
    
    def __str__(self) -> str:
        return f"OS(options={self._get_set()})"
    
    def __repr__(self) -> str:
        return f"ObservableSet({self._get_set()})"
    
    def __len__(self) -> int:
        """
        Get the number of elements in the set.
        
        Returns:
            The number of elements in the set
        """
        return len(self._get_set())
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an element is contained in the set.
        
        Args:
            item: The element to check for
            
        Returns:
            True if the element is in the set, False otherwise
        """
        return item in self._get_set()
    
    def __iter__(self):
        """
        Get an iterator over the set elements.
        
        Returns:
            An iterator that yields each element in the set
        """
        return iter(self._get_set())
    
    def __eq__(self, other) -> bool:
        """
        Check equality with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to compare with
            
        Returns:
            True if the sets contain the same elements, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._get_set() == other._get_set()
        return self._get_set() == other
    
    def __ne__(self, other) -> bool:
        """
        Check inequality with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to compare with
            
        Returns:
            True if the sets are not equal, False otherwise
        """
        return not (self == other)
    
    def __le__(self, other) -> bool:
        """
        Check if this set is a subset of another set or observable set.
        
        Args:
            other: Another set or ObservableSet to check against
            
        Returns:
            True if this set is a subset of the other, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._get_set() <= other._get_set()
        return self._get_set() <= other
    
    def __lt__(self, other) -> bool:
        """
        Check if this set is a proper subset of another set or observable set.
        
        Args:
            other: Another set or ObservableSet to check against
            
        Returns:
            True if this set is a proper subset of the other, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._get_set() < other._get_set()
        return self._get_set() < other
    
    def __ge__(self, other) -> bool:
        """
        Check if this set is a superset of another set or observable set.
        
        Args:
            other: Another set or ObservableSet to check against
            
        Returns:
            True if this set is a superset of the other, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._get_set() >= other._get_set()
        return self._get_set() >= other
    
    def __gt__(self, other) -> bool:
        """
        Check if this set is a proper superset of another set or observable set.
        
        Args:
            other: Another set or ObservableSet to check against
            
        Returns:
            True if this set is a proper superset of the other, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._get_set() > other._get_set()
        return self._get_set() > other
    
    def __and__(self, other):
        """
        Compute the intersection with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to intersect with
            
        Returns:
            A new set containing elements common to both sets
        """
        if isinstance(other, ObservableSet):
            return self._get_set() & other._get_set()
        return self._get_set() & other
    
    def __or__(self, other):
        """
        Compute the union with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to union with
            
        Returns:
            A new set containing all elements from both sets
        """
        if isinstance(other, ObservableSet):
            return self._get_set() | other._get_set()
        return self._get_set() | other
    
    def __sub__(self, other):
        """
        Compute the difference with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to subtract from this set
            
        Returns:
            A new set containing elements in this set but not in the other
        """
        if isinstance(other, ObservableSet):
            return self._get_set() - other._get_set()
        return self._get_set() - other
    
    def __xor__(self, other):
        """
        Compute the symmetric difference with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to compute symmetric difference with
            
        Returns:
            A new set containing elements in either set but not in both
        """
        if isinstance(other, ObservableSet):
            return self._get_set() ^ other._get_set()
        return self._get_set() ^ other
    
    def __hash__(self) -> int:
        """
        Get the hash value based on the current set contents.
        
        Returns:
            Hash value of the set as a frozenset
        """
        return hash(frozenset(self._get_set()))
    
    def get_observed_component_values(self) -> tuple[set[T]]:
        """
        Get the values of all observables that are bound to this observable.
        
        This method is part of the Observable protocol and provides access to
        the current values of all bound observables.
        
        Returns:
            A tuple containing the current set value
        """
        return tuple(self._get_set())
    
    def set_observed_values(self, values: tuple[set[T]]) -> None:
        """
        Set the values of all observables that are bound to this observable.
        
        This method is part of the Observable protocol and allows external
        systems to update this observable's value. It handles all internal
        state changes, binding updates, and listener notifications.
        
        Args:
            values: A tuple containing the new set value to set
        """
        new_set = values[0]
        
        self._set_component_values(
            {"value": new_set}
        )