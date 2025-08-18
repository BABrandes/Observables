from typing import Any, Generic, TypeVar, overload, Protocol, runtime_checkable, Literal
from typing import Optional
from .._utils.hook import Hook, HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.carries_distinct_tuple_hook import CarriesDistinctTupleHook
from .._utils.base_observable import BaseObservable

T = TypeVar("T")

@runtime_checkable
class ObservableTupleLike(CarriesDistinctTupleHook[T, Any], Protocol[T]):
    """
    Protocol for observable tuple objects.
    """
    
    @property
    def tuple_value(self) -> tuple[T, ...]:
        """
        Get the tuple value.
        """
        ...
    
    @tuple_value.setter
    def tuple_value(self, value: tuple[T, ...]) -> None:
        """
        Set the tuple value.
        """
        ...

class ObservableTuple(BaseObservable[Literal["value"]], ObservableTupleLike[T], Generic[T]):
    """
    An observable wrapper around a tuple that supports bidirectional bindings and reactive updates.
    
    This class provides a reactive wrapper around Python tuples, allowing other objects to
    observe changes and establish bidirectional bindings. It implements the full tuple interface
    while maintaining reactivity and binding capabilities.
    
    Features:
    - Bidirectional bindings with other ObservableTuple instances
    - Full tuple interface compatibility
    - Listener notification system for change events
    - Automatic copying to prevent external modification
    - Type-safe generic implementation
    
    Example:
        >>> # Create an observable tuple
        >>> coordinates = ObservableTuple((1, 2, 3))
        >>> coordinates.add_listeners(lambda: print("Coordinates changed!"))
        >>> coordinates.tuple_value = (4, 5, 6)  # Triggers listener
        Coordinates changed!
        
        >>> # Create bidirectional binding
        >>> coords_copy = ObservableTuple(coordinates)
        >>> coords_copy.tuple_value = (7, 8, 9)  # Updates both tuples
        >>> print(coordinates.tuple_value, coords_copy.tuple_value)
        (7, 8, 9) (7, 8, 9)
    
    Args:
        value: Initial tuple, another ObservableTuple to bind to, or None for empty tuple
    """

    @overload
    def __init__(self, tuple_value: tuple[T, ...]) -> None:
        """Initialize with a direct tuple value."""
        ...

    @overload
    def __init__(self, observable_or_hook: CarriesDistinctTupleHook[T, Any]|Hook[tuple[T, ...]]) -> None:
        """Initialize with another observable tuple, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, tuple_value: None) -> None:
        """Initialize with an empty tuple."""
        ...

    def __init__(self, observable_or_hook_or_value: tuple[T, ...] | CarriesDistinctTupleHook[T, Any] | Hook[tuple[T, ...]] | None = None) -> None: # type: ignore
        """
        Initialize the ObservableTuple.
        
        Args:
            value: Initial tuple, observable tuple to bind to, or None for empty tuple

        Raises:
            ValueError: If the initial tuple is not a tuple
        """

        if observable_or_hook_or_value is None:
            initial_value: tuple[T, ...] = ()
            hook: Optional[Hook[tuple[T, ...]]] = None
        elif isinstance(observable_or_hook_or_value, CarriesDistinctTupleHook):
            initial_value: tuple[T, ...] = observable_or_hook_or_value.distinct_tuple_reference
            hook: Optional[Hook[tuple[T, ...]]] = observable_or_hook_or_value.distinct_tuple_hook # type: ignore
        elif isinstance(observable_or_hook_or_value, Hook):
            initial_value: tuple[T, ...] = observable_or_hook_or_value.value
            hook: Optional[Hook[tuple[T, ...]]] = observable_or_hook_or_value
        else:
            initial_value: tuple[T, ...] = observable_or_hook_or_value
            hook: Optional[Hook[tuple[T, ...]]] = None

        super().__init__(
            {"value": initial_value},
            verification_method=lambda x: (True, "Verification method passed") if isinstance(x["value"], tuple) else (False, "Value is not a tuple")
        )

        if hook is not None:
            self.attach(hook, "value", InitialSyncMode.SELF_IS_UPDATED)

    @property
    def collective_hooks(self) -> set[HookLike[Any]]:
        return set()
    
    @property
    def tuple_value(self) -> tuple[T, ...]:
        """
        Get a copy of the current tuple value.
        
        Returns:
            A copy of the current tuple to prevent external modification
        """
        return self._component_hooks["value"].value
    
    @tuple_value.setter
    def tuple_value(self, value: tuple[T, ...]) -> None:
        """
        Set the current tuple value.
        """
        if value != self._component_hooks["value"].value:
            self._set_component_values({"value": value}, notify_binding_system=True)
    
    @property
    def distinct_tuple_reference(self) -> tuple[T, ...]:
        """
        Get the current value of the tuple.
        """
        return self._component_hooks["value"].value
    
    @property
    def distinct_tuple_hook(self) -> HookLike[tuple[T, ...]]:
        """
        Get the hook for the tuple.
        """
        return self._component_hooks["value"]
    
    def __str__(self) -> str:
        """String representation of the observable tuple."""
        return f"OT(tuple={self._component_hooks['value'].value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the observable tuple."""
        return f"ObservableTuple({self._component_hooks['value'].value})"
    
    def __len__(self) -> int:
        """
        Get the length of the tuple.
        
        Returns:
            The number of items in the tuple
        """
        return len(self._component_hooks["value"].value)
    
    def __getitem__(self, index: int) -> T:
        """
        Get an item at the specified index.
        
        Args:
            index: Integer index
            
        Returns:
            The item at the index
            
        Raises:
            IndexError: If the index is out of range
        """
        return self._component_hooks["value"].value[index]
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an item is contained in the tuple.
        
        Args:
            item: The item to check for
            
        Returns:
            True if the item is in the tuple, False otherwise
        """
        return item in self._component_hooks["value"].value
    
    def __iter__(self):
        """
        Get an iterator over the tuple items.
        
        Returns:
            An iterator that yields each item in the tuple
        """
        return iter(self._component_hooks["value"].value)
    
    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another tuple or observable tuple.
        
        Args:
            other: Another tuple or ObservableTuple to compare with
            
        Returns:
            True if the tuples contain the same items in the same order, False otherwise
        """
        if isinstance(other, ObservableTuple):
            return self._component_hooks["value"].value == other._component_hooks["value"].value
        return self._component_hooks["value"].value == other
    
    def __ne__(self, other: Any) -> bool:
        """
        Check inequality with another tuple or observable tuple.
        
        Args:
            other: Another tuple or ObservableTuple to compare with
            
        Returns:
            True if the tuples are not equal, False otherwise
        """
        return not (self == other)
    
    def __lt__(self, other: Any) -> bool:
        """
        Check if this tuple is less than another tuple or observable tuple.
        
        Args:
            other: Another tuple or ObservableTuple to compare with
            
        Returns:
            True if this tuple is lexicographically less than the other, False otherwise
        """
        if isinstance(other, ObservableTuple):
            return self._component_hooks["value"].value < other._component_hooks["value"].value
        return self._component_hooks["value"].value < other
    
    def __le__(self, other: Any) -> bool:
        """
        Check if this tuple is less than or equal to another tuple or observable tuple.
        
        Args:
            other: Another tuple or ObservableTuple to compare with
            
        Returns:
            True if this tuple is lexicographically less than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableTuple):
            return self._component_hooks["value"].value <= other._component_hooks["value"].value
        return self._component_hooks["value"].value <= other
    
    def __gt__(self, other: Any) -> bool:
        """
        Check if this tuple is greater than another tuple or observable tuple.
        
        Args:
            other: Another tuple or ObservableTuple to compare with
            
        Returns:
            True if this tuple is lexicographically greater than the other, False otherwise
        """
        if isinstance(other, ObservableTuple):
            return self._component_hooks["value"].value > other._component_hooks["value"].value
        return self._component_hooks["value"].value > other
    
    def __ge__(self, other: Any) -> bool:
        """
        Check if this tuple is greater than or equal to another tuple or observable tuple.
        
        Args:
            other: Another tuple or ObservableTuple to compare with
            
        Returns:
            True if this tuple is lexicographically greater than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableTuple):
            return self._component_hooks["value"].value >= other._component_hooks["value"].value
        return self._component_hooks["value"].value >= other
    
    def __add__(self, other: Any) -> tuple[T, ...]:
        """
        Concatenate this tuple with another tuple or observable tuple.
        
        Args:
            other: Another tuple or ObservableTuple to concatenate with
            
        Returns:
            A new tuple containing all items from both tuples
        """
        if isinstance(other, ObservableTuple):
            return self._component_hooks["value"].value + other._component_hooks["value"].value
        return self._component_hooks["value"].value + other
    
    def __mul__(self, other: int) -> tuple[T, ...]:
        """
        Repeat the tuple a specified number of times.
        
        Args:
            other: The number of times to repeat the tuple
            
        Returns:
            A new tuple with the original items repeated
        """
        return self._component_hooks["value"].value * other
    
    def __rmul__(self, other: int) -> tuple[T, ...]:
        """
        Repeat the tuple a specified number of times (right multiplication).
        
        Args:
            other: The number of times to repeat the tuple
            
        Returns:
            A new tuple with the original items repeated
        """
        return other * self._component_hooks["value"].value
    
    def __hash__(self) -> int:
        """
        Get the hash value based on the current tuple contents.
        
        Returns:
            Hash value of the tuple
        """
        return hash(self._component_hooks["value"].value)