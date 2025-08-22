from logging import Logger
from typing import Any, Generic, Optional, TypeVar, overload, Protocol, runtime_checkable, Iterable, Literal
from .._utils.hook import HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.carries_hooks import CarriesHooks
from .._utils.base_observable import BaseObservable

T = TypeVar("T")

@runtime_checkable
class ObservableSetLike(CarriesHooks[Any], Protocol[T]):
    """
    Protocol for observable set objects.
    """
    
    @property
    def set_value(self) -> set[T]:
        """
        Get the set value.
        """
        ...
    
    @set_value.setter
    def set_value(self, value: set[T]) -> None:
        """
        Set the set value.
        """
        ...

    @property
    def set_value_hook(self) -> HookLike[set[T]]:
        """
        Get the hook for the set.
        """
        ...

    def change_set_value(self, value: set[T]) -> None:
        """
        Set the set value.
        """
        ...

class ObservableSet(BaseObservable[Literal["value"]], ObservableSetLike[T], Generic[T]):
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
    def __init__(self, set_value: set[T], logger: Optional[Logger] = None) -> None:
        """Initialize with a direct set value."""
        ...

    @overload
    def __init__(self, observable_or_hook: HookLike[set[T]], logger: Optional[Logger] = None) -> None:
        """Initialize with another observable set, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, observable: ObservableSetLike[T], logger: Optional[Logger] = None) -> None:
        """Initialize from another ObservableSetLike object."""
        ...

    @overload
    def __init__(self, set_value: None, logger: Optional[Logger] = None) -> None:
        """Initialize with an empty set."""
        ...

    def __init__(self, observable_or_hook_or_value: set[T] | HookLike[set[T]] | None = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize the ObservableSet.
        
        Args:
            value: Initial set, observable set to bind to, or None for empty set

        Raises:
            ValueError: If the initial set is not a set
        """
        if observable_or_hook_or_value is None:
            initial_value: set[T] = set()
            hook: Optional[HookLike[set[T]]] = None 
        elif isinstance(observable_or_hook_or_value, ObservableSetLike):
            initial_value: set[T] = observable_or_hook_or_value.set_value # type: ignore
            hook: Optional[HookLike[set[T]]] = observable_or_hook_or_value.set_value_hook # type: ignore
        elif isinstance(observable_or_hook_or_value, HookLike):
            initial_value: set[T] = observable_or_hook_or_value.value
            hook: Optional[HookLike[set[T]]] = observable_or_hook_or_value
        else:
            initial_value: set[T] = observable_or_hook_or_value.copy() # type: ignore
            hook: Optional[HookLike[set[T]]] = None
        
        super().__init__(
            {"value": initial_value},
            verification_method=lambda x: (True, "Verification method passed") if isinstance(x["value"], set) else (False, "Value is not a set"),
            logger=logger
        )

        if hook is not None:
            self.attach(hook, "value", InitialSyncMode.PULL_FROM_TARGET)
    
    @property
    def set_value(self) -> set[T]:
        """
        Get a copy of the current set value.
        
        Returns:
            A copy of the current set to prevent external modification
        """
        return self._component_hooks["value"].value.copy()    
    
    @set_value.setter
    def set_value(self, value: set[T]) -> None:
        """
        Set the current value of the set.
        """
        if value == self._component_hooks["value"].value:
            return
        self._set_component_values({"value": value}, notify_binding_system=True)

    def change_set_value(self, value: set[T]) -> None:
        """
        Set the current value of the set.
        """
        if value == self._component_hooks["value"].value:
            return
        self._set_component_values({"value": value}, notify_binding_system=True)

    @property
    def set_value_hook(self) -> HookLike[set[T]]:
        """
        Get the hook for the set.
        """
        return self._component_hooks["value"]
    
    # Standard set methods
    def add(self, item: T) -> None:
        """
        Add an element to the set.
        
        This method adds an item to the set if it's not a already present,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The element to add to the set
        """
        if item not in self._component_hooks["value"].value:
            new_set = self._component_hooks["value"].value.copy()
            new_set.add(item)
            self._set_component_values({"value": new_set}, notify_binding_system=True)
    
    def remove(self, item: T) -> None:
        """
        Remove an element from the set.
        
        This method removes an item from the set,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The element to remove from the set
            
        Raises:
            KeyError: If the item is not in the set
        """
        if item not in self._component_hooks["value"].value:
            raise KeyError(item)
        
        new_set = self._component_hooks["value"].value.copy()
        new_set.remove(item)
        self._set_component_values({"value": new_set}, notify_binding_system=True)
    
    def discard(self, item: T) -> None:
        """
        Remove an element from the set if it is present.
        
        This method removes an item from the set if it's present,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        Unlike remove(), this method does not raise an error if the item is not found.
        
        Args:
            item: The element to remove from the set
        """
        if item in self._component_hooks["value"].value:
            new_set = self._component_hooks["value"].value.copy()
            new_set.discard(item)
            self._set_component_values({"value": new_set}, notify_binding_system=True)
    
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
        if not self._component_hooks["value"].value:
            raise KeyError("pop from an empty set")
        
        item = next(iter(self._component_hooks["value"].value))
        new_set = self._component_hooks["value"].value.copy()
        new_set.remove(item)
        self._set_component_values({"value": new_set}, notify_binding_system=True)
        return item
    
    def clear(self) -> None:
        """
        Remove all elements from the set.
        
        This method removes all elements from the set, making it empty.
        It uses set_observed_values to ensure all changes go through the centralized protocol method.
        """
        if self._component_hooks["value"].value:
            new_set: set[T] = set()
            self._set_component_values({"value": new_set}, notify_binding_system=True)
    
    def update(self, *others: Iterable[T]) -> None:
        """
        Update the set with elements from all other iterables.
        
        This method adds all elements from the provided iterables to the set,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            *others: Variable number of iterables to add elements from
        """
        new_set = self._component_hooks["value"].value.copy()
        for other in others:
            new_set.update(other)
        if new_set != self._component_hooks["value"].value:
            self._set_component_values({"value": new_set}, notify_binding_system=True)
    
    def intersection_update(self, *others: Iterable[T]) -> None:
        """
        Update the set keeping only elements found in this set and all others.
        
        This method modifies the set to contain only elements that are present
        in this set and all the provided iterables, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            *others: Variable number of iterables to intersect with
        """
        new_set = self._component_hooks["value"].value.copy()
        for other in others:
            new_set.intersection_update(other)
        if new_set != self._component_hooks["value"].value:
            self._set_component_values({"value": new_set}, notify_binding_system=True)
    
    def difference_update(self, *others: Iterable[T]) -> None:
        """
        Update the set removing elements found in any of the others.
        
        This method removes from this set all elements that are present in any
        of the provided iterables, using set_observed_values to ensure all
        changes go through the centralized protocol method.
        
        Args:
            *others: Variable number of iterables to remove elements from
        """
        new_set = self._component_hooks["value"].value.copy()
        for other in others:
            new_set.difference_update(other)
        if new_set != self._component_hooks["value"].value:
            self._set_component_values({"value": new_set}, notify_binding_system=True)
    
    def symmetric_difference_update(self, other: Iterable[T]) -> None:
        """
        Update the set keeping only elements found in either set but not both.
        
        This method modifies the set to contain only elements that are present
        in either this set or the other iterable, but not in both, using
        set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            other: An iterable to compute symmetric difference with
        """
        current_set = self._component_hooks["value"].value
        new_set = current_set.copy()
        new_set.symmetric_difference_update(other)
        
        # Only update if there's an actual change
        if new_set != current_set:
            self._set_component_values({"value": new_set}, notify_binding_system=True)
    
    def __str__(self) -> str:
        return f"OS(options={self._component_hooks['value'].value})"
    
    def __repr__(self) -> str:
        return f"ObservableSet({self._component_hooks['value'].value})"
    
    def __len__(self) -> int:
        """
        Get the number of elements in the set.
        
        Returns:
            The number of elements in the set
        """
        return len(self._component_hooks["value"].value)
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an element is contained in the set.
        
        Args:
            item: The element to check for
            
        Returns:
            True if the element is in the set, False otherwise
        """
        return item in self._component_hooks["value"].value
    
    def __iter__(self):
        """
        Get an iterator over the set elements.
        
        Returns:
            An iterator that yields each element in the set
        """
        return iter(self._component_hooks["value"].value)
    
    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to compare with
            
        Returns:
            True if the sets contain the same elements, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._component_hooks["value"].value == other._component_hooks["value"].value
        return self._component_hooks["value"].value == other
    
    def __ne__(self, other: Any) -> bool:
        """
        Check inequality with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to compare with
            
        Returns:
            True if the sets are not equal, False otherwise
        """
        return not (self == other)
    
    def __le__(self, other: Any) -> bool:
        """
        Check if this set is a subset of another set or observable set.
        
        Args:
            other: Another set or ObservableSet to check against
            
        Returns:
            True if this set is a subset of the other, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._component_hooks["value"].value <= other._component_hooks["value"].value
        return self._component_hooks["value"].value <= other
    
    def __lt__(self, other: Any) -> bool:
        """
        Check if this set is a proper subset of another set or observable set.
        
        Args:
            other: Another set or ObservableSet to check against
            
        Returns:
            True if this set is a proper subset of the other, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._component_hooks["value"].value < other._component_hooks["value"].value
        return self._component_hooks["value"].value < other
    
    def __ge__(self, other: Any) -> bool:
        """
        Check if this set is a superset of another set or observable set.
        
        Args:
            other: Another set or ObservableSet to check against
            
        Returns:
            True if this set is a superset of the other, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._component_hooks["value"].value >= other._component_hooks["value"].value
        return self._component_hooks["value"].value >= other
    
    def __gt__(self, other: Any) -> bool:
        """
        Check if this set is a proper superset of another set or observable set.
        
        Args:
            other: Another set or ObservableSet to check against
            
        Returns:
            True if this set is a proper superset of the other, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._component_hooks["value"].value > other._component_hooks["value"].value
        return self._component_hooks["value"].value > other
    
    def __and__(self, other: Any) -> set[T]:
        """
        Compute the intersection with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to intersect with
            
        Returns:
            A new set containing elements common to both sets
        """
        if isinstance(other, ObservableSet):
            return self._component_hooks["value"].value & other._component_hooks["value"].value
        return self._component_hooks["value"].value & other
    
    def __or__(self, other: Any) -> set[T]:
        """
        Compute the union with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to union with
            
        Returns:
            A new set containing all elements from both sets
        """
        if isinstance(other, ObservableSet):
            return self._component_hooks["value"].value | other._component_hooks["value"].value
        return self._component_hooks["value"].value | other
    
    def __sub__(self, other: Any) -> set[T]:
        """
        Compute the difference with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to subtract from this set
            
        Returns:
            A new set containing elements in this set but not in the other
        """
        if isinstance(other, ObservableSet):
            return self._component_hooks["value"].value - other._component_hooks["value"].value
        return self._component_hooks["value"].value - other
    
    def __xor__(self, other: Any) -> set[T]:
        """
        Compute the symmetric difference with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to compute symmetric difference with
            
        Returns:
            A new set containing elements in either set but not in both
        """
        if isinstance(other, ObservableSet):
            return self._component_hooks["value"].value ^ other._component_hooks["value"].value
        return self._component_hooks["value"].value ^ other
    
    def __hash__(self) -> int:
        """
        Get the hash value based on the current set contents.
        
        Returns:
            Hash value of the set as a frozenset
        """
        return hash(frozenset(self._component_hooks["value"].value))