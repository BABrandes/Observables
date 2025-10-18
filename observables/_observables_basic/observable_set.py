from typing import Any, Generic, Optional, TypeVar, overload, Protocol, runtime_checkable, Iterable, Literal, Iterator, Mapping
from logging import Logger

from .._hooks.hook_aliases import Hook, ReadOnlyHook
from .._carries_hooks.carries_hooks_protocol import CarriesHooksProtocol
from .._carries_hooks.complex_observable_base import ComplexObservableBase
from .._carries_hooks.observable_serializable import ObservableSerializable

T = TypeVar("T")

@runtime_checkable
class ObservableSetProtocol(CarriesHooksProtocol[Any, Any], Protocol[T]):
    """
    Protocol for observable set objects.
    """
    
    @property
    def value(self) -> set[T]:
        """
        Get the set value.
        """
        ...
    
    @value.setter
    def value(self, value: set[T]) -> None:
        """
        Set the set value.
        """
        ...

    @property
    def value_hook(self) -> Hook[set[T]]:
        """
        Get the hook for the set.
        """
        ...

    def change_value(self, value: set[T]) -> None:
        """
        Change the set value (lambda-friendly method).
        """
        ...
    
    @property
    def length(self) -> int:
        """
        Get the current length of the set.
        """
        ...
    
    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the set length.
        """
        ...
    

class ObservableSet(ComplexObservableBase[Literal["value"], Literal["length"], set[T], int, "ObservableSet"], ObservableSetProtocol[T], ObservableSerializable[Literal["value"], set[T]], Generic[T]):
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
    def __init__(self, observable_or_hook: Hook[set[T]], logger: Optional[Logger] = None) -> None:
        """Initialize with another observable set, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, observable: ObservableSetProtocol[T], logger: Optional[Logger] = None) -> None:
        """Initialize from another ObservableSetLike object."""
        ...

    @overload
    def __init__(self, set_value: None, logger: Optional[Logger] = None) -> None:
        """Initialize with an empty set."""
        ...

    def __init__(self, observable_or_hook_or_value: set[T] | Hook[set[T]] | None = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize the ObservableSet.
        
        Args:
            value: Initial set, observable set to bind to, or None for empty set

        Raises:
            ValueError: If the initial set is not a set
        """
        if observable_or_hook_or_value is None:
            initial_value: set[T] = set()
            hook: Optional[Hook[set[T]]] = None 
        elif isinstance(observable_or_hook_or_value, ObservableSetProtocol):
            initial_value = observable_or_hook_or_value.value # type: ignore
            hook = observable_or_hook_or_value.value_hook # type: ignore
        elif isinstance(observable_or_hook_or_value, Hook):
            initial_value = observable_or_hook_or_value.value
            hook = observable_or_hook_or_value
        else:
            initial_value = observable_or_hook_or_value.copy() # type: ignore
            hook = None
        
        super().__init__(
            initial_component_values_or_hooks={"value": initial_value},
            verification_method=lambda x: (True, "Verification method passed") if isinstance(x["value"], set) else (False, "Value is not a set"), # type: ignore
            secondary_hook_callbacks={"length": lambda x: len(x["value"])}, # type: ignore
            logger=logger
        )

        if hook is not None:
            self.connect_hook(hook, "value", "use_target_value") # type: ignore

    @property
    def value(self) -> set[T]:
        """
        Get a copy of the current set value.
        
        Returns:
            A copy of the current set to prevent external modification
        """
        return self._primary_hooks["value"].value.copy() # type: ignore
    
    @value.setter
    def value(self, value: set[T]) -> None:
        """
        Set the current value of the set.
        """
        if value == self._primary_hooks["value"].value:
            return
        success, msg = self.submit_values({"value": value})
        if not success:
            raise ValueError(msg)

    def change_value(self, value: set[T]) -> None:
        """
        Change the set value (lambda-friendly method).
        
        This method is equivalent to setting the .value property but can be used
        in lambda expressions and other contexts where property assignment isn't suitable.
        
        Args:
            value: The new set value to set
        """
        if value == self._primary_hooks["value"].value:
            return
        success, msg = self.submit_values({"value": value})
        if not success:
            raise ValueError(msg)

    @property
    def value_hook(self) -> Hook[set[T]]:
        """
        Get the hook for the set.
        
        This hook can be used for binding operations with other observables.
        """
        return self._primary_hooks["value"] # type: ignore
    
    @property
    def length(self) -> int:
        """
        Get the current length of the set.
        """
        return len(self._primary_hooks["value"].value) # type: ignore
    
    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the set length.
        
        This hook can be used for binding operations that react to length changes.
        """
        return self._secondary_hooks["length"] # type: ignore
    
    
    # Standard set methods
    def add(self, item: T) -> None:
        """
        Add an element to the set.
        
        This method adds an item to the set if it's not a already present,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The element to add to the set
        """
        if item not in self._primary_hooks["value"].value: # type: ignore
            new_set = self._primary_hooks["value"].value.copy() # type: ignore
            new_set.add(item) # type: ignore
            success, msg = self.submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
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
        if item not in self._primary_hooks["value"].value: # type: ignore
            raise KeyError(item)
        
        new_set = self._primary_hooks["value"].value.copy() # type: ignore
        new_set.remove(item) # type: ignore
        success, msg = self.submit_values({"value": new_set})
        if not success:
            raise ValueError(msg)
    
    def discard(self, item: T) -> None:
        """
        Remove an element from the set if it is present.
        
        This method removes an item from the set if it's present,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        Unlike remove(), this method does not raise an error if the item is not found.
        
        Args:
            item: The element to remove from the set
        """
        if item in self._primary_hooks["value"].value: # type: ignore
            new_set = self._primary_hooks["value"].value.copy() # type: ignore
            new_set.discard(item) # type: ignore
            success, msg = self.submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
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
        if not self._primary_hooks["value"].value: # type: ignore
            raise KeyError("pop from an empty set")
        
        item: T = next(iter(self._primary_hooks["value"].value)) # type: ignore
        new_set = self._primary_hooks["value"].value.copy() # type: ignore
        new_set.remove(item) # type: ignore
        success, msg = self.submit_values({"value": new_set})
        if not success:
            raise ValueError(msg)
        return item 
    
    def clear(self) -> None:
        """
        Remove all elements from the set.
        
        This method removes all elements from the set, making it empty.
        It uses set_observed_values to ensure all changes go through the centralized protocol method.
        """
        if self._primary_hooks["value"].value:
            new_set: set[T] = set()
            success, msg = self.submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
    def update(self, *others: Iterable[T]) -> None:
        """
        Update the set with elements from all other iterables.
        
        This method adds all elements from the provided iterables to the set,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            *others: Variable number of iterables to add elements from
        """
        new_set: set[T] = self._primary_hooks["value"].value.copy() # type: ignore
        for other in others:
            new_set.update(other) # type: ignore
        if new_set != self._primary_hooks["value"].value:
            success, msg = self.submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
    def intersection_update(self, *others: Iterable[T]) -> None:
        """
        Update the set keeping only elements found in this set and all others.
        
        This method modifies the set to contain only elements that are present
        in this set and all the provided iterables, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            *others: Variable number of iterables to intersect with
        """
        new_set: set[T] = self._primary_hooks["value"].value.copy() # type: ignore
        for other in others:
            new_set.intersection_update(other) # type: ignore
        if new_set != self._primary_hooks["value"].value:
            success, msg = self.submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
    def difference_update(self, *others: Iterable[T]) -> None:
        """
        Update the set removing elements found in any of the others.
        
        This method removes from this set all elements that are present in any
        of the provided iterables, using set_observed_values to ensure all
        changes go through the centralized protocol method.
        
        Args:
            *others: Variable number of iterables to remove elements from
        """
        new_set: set[T] = self._primary_hooks["value"].value.copy() # type: ignore
        for other in others:
            new_set.difference_update(other) # type: ignore
        if new_set != self._primary_hooks["value"].value:
            success, msg = self.submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
    def symmetric_difference_update(self, other: Iterable[T]) -> None:
        """
        Update the set keeping only elements found in either set but not both.
        
        This method modifies the set to contain only elements that are present
        in either this set or the other iterable, but not in both, using
        set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            other: An iterable to compute symmetric difference with
        """
        current_set: set[T] = self._primary_hooks["value"].value # type: ignore
        new_set: set[T] = current_set.copy() # type: ignore
        new_set.symmetric_difference_update(other)
        
        # Only update if there's an actual change
        if new_set != current_set:
            success, msg = self.submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
    def __str__(self) -> str:
        return f"OS(options={self._primary_hooks['value'].value})"
    
    def __repr__(self) -> str:
        return f"ObservableSet({self._primary_hooks['value'].value})"
    
    def __len__(self) -> int:
        """
        Get the number of elements in the set.
        
        Returns:
            The number of elements in the set
        """
        return len(self._primary_hooks["value"].value) # type: ignore
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an element is contained in the set.
        
        Args:
            item: The element to check for
            
        Returns:
            True if the element is in the set, False otherwise
        """
        return item in self._primary_hooks["value"].value # type: ignore
    
    def __iter__(self) -> Iterator[T]:
        """
        Get an iterator over the set elements.
        
        Returns:
            An iterator that yields each element in the set
        """
        return iter(self._primary_hooks["value"].value) # type: ignore
    
    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to compare with
            
        Returns:
            True if the sets contain the same elements, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value == other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value == other
    
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
            return self._primary_hooks["value"].value <= other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value <= other
    
    def __lt__(self, other: Any) -> bool:
        """
        Check if this set is a proper subset of another set or observable set.
        
        Args:
            other: Another set or ObservableSet to check against
            
        Returns:
            True if this set is a proper subset of the other, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value < other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value < other
    
    def __ge__(self, other: Any) -> bool:
        """
        Check if this set is a superset of another set or observable set.
        
        Args:
            other: Another set or ObservableSet to check against
            
        Returns:
            True if this set is a superset of the other, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value >= other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value >= other
    
    def __gt__(self, other: Any) -> bool:
        """
        Check if this set is a proper superset of another set or observable set.
        
        Args:
            other: Another set or ObservableSet to check against
            
        Returns:
            True if this set is a proper superset of the other, False otherwise
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value > other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value > other
    
    def __and__(self, other: Any) -> set[T]:
        """
        Compute the intersection with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to intersect with
            
        Returns:
            A new set containing elements common to both sets
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value & other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value & other
    
    def __or__(self, other: Any) -> set[T]:
        """
        Compute the union with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to union with
            
        Returns:
            A new set containing all elements from both sets
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value | other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value | other
    
    def __sub__(self, other: Any) -> set[T]:
        """
        Compute the difference with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to subtract from this set
            
        Returns:
            A new set containing elements in this set but not in the other
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value - other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value - other
    
    def __xor__(self, other: Any) -> set[T]:
        """
        Compute the symmetric difference with another set or observable set.
        
        Args:
            other: Another set or ObservableSet to compute symmetric difference with
            
        Returns:
            A new set containing elements in either set but not in both
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value ^ other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value ^ other
    
    def __hash__(self) -> int:
        """
        Get the hash value based on the current set contents.
        
        Returns:
            Hash value of the set as a frozenset
        """
        return hash(frozenset(self._primary_hooks["value"].value)) # type: ignore

    #### ObservableSerializable implementation ####

    def get_value_references_for_serialization(self) -> Mapping[Literal["value"], set[T]]:
        return {"value": self._primary_hooks["value"].value}

    def set_value_references_from_serialization(self, values: Mapping[Literal["value"], set[T]]) -> None:
        self.submit_values({"value": values["value"]})