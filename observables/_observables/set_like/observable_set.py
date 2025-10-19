from typing import Any, Generic, Optional, TypeVar, overload, Iterable, Literal, Iterator, Set
from collections.abc import Set as AbstractSet
from logging import Logger

from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ..._carries_hooks.complex_observable_base import ComplexObservableBase
from .protocols import ObservableSetProtocol

T = TypeVar("T")
   
class ObservableSet(ComplexObservableBase[Literal["value"], Literal["length"], AbstractSet[T], int, "ObservableSet"], ObservableSetProtocol[T], Set[T], Generic[T]):
    """
    An observable wrapper around a set that supports bidirectional bindings and reactive updates.
    
    This class provides a reactive wrapper around Python sets, allowing other objects to
    observe changes and establish bidirectional bindings. It implements the full set interface
    while maintaining reactivity and binding capabilities.
    
    Features:
    - Bidirectional bindings with other ObservableSet instances
    - Full set interface compatibility (add, remove, discard, pop, etc.)
    - Listener notification system for change events
    - Immutable internal storage using frozenset
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
    def __init__(self, set_value: AbstractSet[T], logger: Optional[Logger] = None) -> None:
        """Initialize with any set (automatically converted to frozenset)."""
        ...

    @overload
    def __init__(self, observable_or_hook: Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]], logger: Optional[Logger] = None) -> None:
        """Initialize with a hook, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, observable: ObservableSetProtocol[T], logger: Optional[Logger] = None) -> None:
        """Initialize from another ObservableSetLike object."""
        ...

    @overload
    def __init__(self, set_value: None, logger: Optional[Logger] = None) -> None:
        """Initialize with an empty set."""
        ...

    def __init__(self, observable_or_hook_or_value: AbstractSet[T] | Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]] | None = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize the ObservableSet.
        
        Args:
            value: Initial set, observable set to bind to, or None for empty set.
                   Sets are automatically converted to frozenset by the nexus system.

        Raises:
            ValueError: If the initial value is not a valid set type
        """
        if observable_or_hook_or_value is None:
            initial_value: AbstractSet[T] = set()
            hook: Optional[ManagedHookProtocol[AbstractSet[T]]] = None 
        elif isinstance(observable_or_hook_or_value, ObservableSetProtocol):
            initial_value = observable_or_hook_or_value.value # type: ignore
            hook = observable_or_hook_or_value.value_hook # type: ignore
        elif isinstance(observable_or_hook_or_value, ManagedHookProtocol):
            initial_value = observable_or_hook_or_value.value # type: ignore
            hook = observable_or_hook_or_value # type: ignore
        else:
            # Pass set directly - nexus system will convert to frozenset
            initial_value = observable_or_hook_or_value # type: ignore
            hook = None
        
        super().__init__(
            initial_hook_values={"value": initial_value}, # type: ignore
            verification_method=lambda x: (True, "Verification method passed") if isinstance(x["value"], frozenset) else (False, "Value has not been converted to immutable frozenset!"), # type: ignore
            secondary_hook_callbacks={"length": lambda x: len(x["value"])}, # type: ignore
            logger=logger
        )

        if hook is not None:
            self._link(hook, "value", "use_target_value") # type: ignore

    #########################################################
    # ObservableSetProtocol implementation
    #########################################################

    #-------------------------------- set value --------------------------------

    @property
    def value_hook(self) -> Hook[AbstractSet[T]]:
        """
        Get the hook for the set.
        
        This hook can be used for binding operations with other observables.
        Returns frozenset for immutability.
        """
        return self._primary_hooks["value"] # type: ignore

    @property
    def value(self) -> AbstractSet[T]:
        """
        Get the current set value as immutable AbstractSet.
        
        Returns:
            The current AbstractSet value (immutable).
            
        Note:
            Returns AbstractSet for immutability. Use add(), remove(), etc.
            for modifications, or create a new AbstractSet and assign.
        """
        return self._primary_hooks["value"].value # type: ignore
    
    @value.setter
    def value(self, value: Iterable[T]) -> None:
        """
        Set the current value of the set.
        
        Args:
            value: Any set (automatically converted to frozenset by nexus system)
        """
        # Let nexus system handle immutability conversion
        success, msg = self._submit_values({"value": frozenset(value)})
        if not success:
            raise ValueError(msg)

    def change_value(self, new_value: Iterable[T]) -> None:
        """
        Change the set value (lambda-friendly method).
        
        This method is equivalent to setting the .value property but can be used
        in lambda expressions and other contexts where property assignment isn't suitable.
        
        Args:
            new_value: Any iterable (will be converted to frozenset)
        """
        success, msg = self._submit_values({"value": frozenset(new_value)})
        if not success:
            raise ValueError(msg)

    #-------------------------------- length --------------------------------

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
    
    #########################################################
    # Standard set methods
    #########################################################
    
    # Standard set methods
    def add(self, item: T) -> None:
        """
        Add an element to the set.
        
        Creates a new frozenset with the added element.
        
        Args:
            item: The element to add to the set
        """
        if item not in self._primary_hooks["value"].value: # type: ignore
            new_set = self._primary_hooks["value"].value | {item} # type: ignore
            success, msg = self._submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
    def remove(self, item: T) -> None:
        """
        Remove an element from the set.
        
        Creates a new frozenset without the element.
        
        Args:
            item: The element to remove from the set
            
        Raises:
            KeyError: If the item is not in the set
        """
        if item not in self._primary_hooks["value"].value: # type: ignore
            raise KeyError(item)
        
        new_set = self._primary_hooks["value"].value - {item} # type: ignore
        success, msg = self._submit_values({"value": new_set})
        if not success:
            raise ValueError(msg)
    
    def discard(self, item: T) -> None:
        """
        Remove an element from the set if it is present.
        
        Creates a new frozenset without the element (if present).
        Unlike remove(), this method does not raise an error if the item is not found.
        
        Args:
            item: The element to remove from the set
        """
        if item in self._primary_hooks["value"].value: # type: ignore
            new_set = self._primary_hooks["value"].value - {item} # type: ignore
            success, msg = self._submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
    def pop(self) -> T:
        """
        Remove and return an arbitrary element from the set.
        
        Creates a new frozenset without the popped element.
        
        Returns:
            The removed element
            
        Raises:
            KeyError: If the set is empty
        """
        if not self._primary_hooks["value"].value: # type: ignore
            raise KeyError("pop from an empty set")
        
        item: T = next(iter(self._primary_hooks["value"].value)) # type: ignore
        new_set = self._primary_hooks["value"].value - {item} # type: ignore
        success, msg = self._submit_values({"value": new_set})
        if not success:
            raise ValueError(msg)
        return item 
    
    def clear(self) -> None:
        """
        Remove all elements from the set.
        
        Creates an empty frozenset.
        """
        if self._primary_hooks["value"].value:
            new_set: frozenset[T] = frozenset()
            success, msg = self._submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
    def update(self, *others: Iterable[T]) -> None:
        """
        Update the set with elements from all other iterables.
        
        Creates a new frozenset with all elements from current set and provided iterables.
        
        Args:
            *others: Variable number of iterables to add elements from
        """
        new_set: frozenset[T] = self._primary_hooks["value"].value # type: ignore
        for other in others:
            new_set = new_set | frozenset(other) # type: ignore
        if new_set != self._primary_hooks["value"].value:
            success, msg = self._submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
    def intersection_update(self, *others: Iterable[T]) -> None:
        """
        Update the set keeping only elements found in this set and all others.
        
        Creates a new frozenset with only common elements.
        
        Args:
            *others: Variable number of iterables to intersect with
        """
        new_set: frozenset[T] = self._primary_hooks["value"].value # type: ignore
        for other in others:
            new_set = new_set & frozenset(other) # type: ignore
        if new_set != self._primary_hooks["value"].value:
            success, msg = self._submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
    def difference_update(self, *others: Iterable[T]) -> None:
        """
        Update the set removing elements found in any of the others.
        
        Creates a new frozenset without elements from the provided iterables.
        
        Args:
            *others: Variable number of iterables to remove elements from
        """
        new_set: frozenset[T] = self._primary_hooks["value"].value # type: ignore
        for other in others:
            new_set = new_set - frozenset(other) # type: ignore
        if new_set != self._primary_hooks["value"].value:
            success, msg = self._submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
    def symmetric_difference_update(self, other: Iterable[T]) -> None:
        """
        Update the set keeping only elements found in either set but not both.
        
        Creates a new frozenset with symmetric difference.
        
        Args:
            other: An iterable to compute symmetric difference with
        """
        current_set: frozenset[T] = self._primary_hooks["value"].value # type: ignore
        new_set = current_set ^ frozenset(other) # type: ignore
        
        # Only update if there's an actual change
        if new_set != current_set:
            success, msg = self._submit_values({"value": new_set})
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
    
    def __contains__(self, item: object) -> bool:
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
    
    def __and__(self, other: Any) -> Set[T]:
        """
        Compute the intersection with another set or observable set.
        
        Args:
            other: Another iterable or ObservableSet to intersect with
            
        Returns:
            A new frozenset containing elements common to both sets
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value & other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value & frozenset(other) # type: ignore
    
    def __or__(self, other: Any) -> Set[T]:
        """
        Compute the union with another set or observable set.
        
        Args:
            other: Another iterable or ObservableSet to union with
            
        Returns:
            A new frozenset containing all elements from both sets
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value | other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value | frozenset(other) # type: ignore
    
    def __sub__(self, other: Any) -> Set[T]:
        """
        Compute the difference with another set or observable set.
        
        Args:
            other: Another iterable or ObservableSet to subtract from this set
            
        Returns:
            A new frozenset containing elements in this set but not in the other
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value - other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value - frozenset(other) # type: ignore
    
    def __xor__(self, other: Any) -> Set[T]:
        """
        Compute the symmetric difference with another set or observable set.
        
        Args:
            other: Another iterable or ObservableSet to compute symmetric difference with
            
        Returns:
            A new frozenset containing elements in either set but not in both
        """
        if isinstance(other, ObservableSet):
            return self._primary_hooks["value"].value ^ other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value ^ frozenset(other) # type: ignore