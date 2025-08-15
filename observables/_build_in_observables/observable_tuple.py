from typing import Any, Generic, TypeVar, overload, Protocol, runtime_checkable
from typing import Optional
from .._utils.hook import Hook, SyncMode
from .._utils.carries_distinct_tuple_hook import CarriesDistinctTupleHook
from .._utils.carries_distinct_indexable_single_value_hook import CarriesDistinctIndexableSingleValueHook
from .._utils.carries_distinct_single_value_hook import CarriesDistinctSingleValueHook
from .._utils.indexable_hook_manager import IndexableHookManager
from .._utils.base_observable import BaseObservable

T = TypeVar("T")

@runtime_checkable
class ObservableTupleLike(CarriesDistinctTupleHook[T], CarriesDistinctIndexableSingleValueHook[T], Protocol[T]):
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

    def bind_to(self, observable_or_hook: CarriesDistinctTupleHook[T]|Hook[tuple[T, ...]], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding with another observable tuple.
        """
        ...

    def unbind_from(self, observable_or_hook: CarriesDistinctTupleHook[T]|Hook[tuple[T, ...]]) -> None:
        """
        Remove the bidirectional binding with another observable tuple.
        """
        ...

class ObservableTuple(BaseObservable, ObservableTupleLike[T], Generic[T]):
    """
    An observable wrapper around a tuple that supports bidirectional bindings and reactive updates.
    
    This class provides a reactive wrapper around Python tuples, allowing other objects to
    observe changes and establish bidirectional bindings. It implements the full tuple interface
    while maintaining reactivity and binding capabilities.
    
    Features:
    - Bidirectional bindings with other ObservableTuple instances
    - Full tuple interface compatibility (append, extend, insert, remove, etc.)
    - Listener notification system for change events
    - Automatic copying to prevent external modification
    - Type-safe generic implementation
    
    Example:
        >>> # Create an observable tuple
        >>> todo_tuple = ObservableTuple(["Buy groceries", "Walk dog"])
        >>> todo_tuple.add_listeners(lambda: print("Tuple changed!"))
        >>> todo_tuple.append("Read book")  # Triggers listener
        Tuple changed!
        
        >>> # Create bidirectional binding
        >>> todo_copy = ObservableTuple(todo_tuple)
        >>> todo_copy.append("Exercise")  # Updates both tuples
        >>> print(todo_tuple.value, todo_copy.value)
        ['Buy groceries', 'Walk dog', 'Read book', 'Exercise'] ['Buy groceries', 'Walk dog', 'Read book', 'Exercise']
    
    Args:
        value: Initial tuple, another ObservableTuple to bind to, or None for empty tuple
    """

    @classmethod
    def _mandatory_component_value_keys(cls) -> set[str]:
        """
        Get the mandatory component value keys.
        """
        return {"value"}

    @overload
    def __init__(self, value: tuple[T, ...]):
        """Initialize with a direct tuple value."""
        ...

    @overload
    def __init__(self, value: CarriesDistinctTupleHook[T]):
        """Initialize with another observable tuple, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, value: None):
        """Initialize with an empty tuple."""
        ...

    def __init__(self, value: tuple[T, ...] | CarriesDistinctTupleHook[T] | None = None):
        """
        Initialize the ObservableList.
        
        Args:
            value: Initial list, observable list to bind to, or None for empty list

        Raises:
            ValueError: If the initial list is not a list
        """

        if value is None:
            initial_value: tuple[T, ...] = ()
            bindable_tuple_carrier: Optional[CarriesDistinctTupleHook[T]] = None
        elif isinstance(value, CarriesDistinctTupleHook):
            initial_value: tuple[T, ...] = value._get_tuple_value()
            bindable_tuple_carrier: Optional[CarriesDistinctTupleHook[T]] = value
        else:
            initial_value: tuple[T, ...] = value
            bindable_tuple_carrier: Optional[CarriesDistinctTupleHook[T]] = None

        def verification_method(x: dict[str, Any]) -> tuple[bool, str]:
            if not isinstance(x["value"], tuple):
                return False, "Value is not a tuple"
            return True, "Verification method passed"
            
        super().__init__(
            {
                "value": initial_value
            },
            {
                "value": Hook(self, self._get_tuple_value, self._set_tuple_value)
            },
            verification_method=verification_method
        )

        if bindable_tuple_carrier is not None:
            self.bind_to(bindable_tuple_carrier)

        self._indexable_hook_manager: IndexableHookManager[T] = IndexableHookManager(self, "value", len(initial_value), lambda idx: self._get_tuple_value()[idx], self._set_indexable_single_value)

    @property
    def tuple_value(self) -> tuple[T, ...]:
        """
        Get a copy of the current tuple value.
        
        Returns:
            A copy of the current tuple to prevent external modification
        """
        return self._get_tuple_value()
    
    @tuple_value.setter
    def tuple_value(self, new_value: tuple[T, ...]) -> None:
        """
        Set the current tuple value.
        
        Args:
            new_value: The new tuple to set
        """
        self._set_tuple_value(new_value)
    
    def _set_tuple_value(self, tuple_to_set: tuple[T, ...]) -> None:
        """
        INTERNAL. Do not use this method directly.

        Set the entire tuple to a new value.
        
        This method replaces the current tuple with a new one, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            tuple_to_set: The new tuple to set
        """
        if tuple_to_set == self._get_tuple_value():
            return
        
        # Check if there are individual element bindings that need to be validated
        element_binding_keys = [key for key in self._component_hooks if key.startswith("value_")]
        if element_binding_keys:
            try:
                highest_index = max(int(key.split("_")[-1]) for key in element_binding_keys)
                if len(tuple_to_set) <= highest_index:
                    raise ValueError(f"New tuple has {len(tuple_to_set)} elements but needs at least {highest_index + 1} elements for existing bindings")
            except ValueError:
                pass
        
        # Use the protocol method to set the value
        self.set_observed_values((tuple_to_set,))
    
    def _get_tuple_value(self) -> tuple[T, ...]:
        """
        INTERNAL. Do not use this method directly.

        Method to get the current tuple value for binding system. No copy is made!
        
        Returns:
            The current tuple value
        """
        return self._component_values["value"]
    
    def _get_tuple_hook(self) -> Hook[tuple[T, ...]]:
        """Internal method to get hook for binding system."""
        return self._component_hooks["value"]

    def _get_indexable_single_value_hook(self, index: int) -> Hook[T]:
        """Internal method to get hook for indexable single value binding system."""
        return self._component_hooks[f"value_{index}"]
    
    def _get_indexable_single_value(self, index: int) -> T:
        """
        INTERNAL. Do not use this method directly.
        
        Get the value at the given index.
        
        Args:
            index: The index of the element to get
            
        Returns:
            The value at the specified index
            
        Raises:
            IndexError: If the index is out of bounds
        """
        if index < 0 or index >= len(self._component_values["value"]):
            raise IndexError(f"Index {index} is out of bounds for tuple of length {len(self._component_values['value'])}")
        return self._component_values["value"][index]
    
    def _set_indexable_single_value(self, index: int, value: T) -> None:
        """
        INTERNAL. Do not use this method directly.
        
        Set the value at the given index.
        
        Args:
            index: The index of the element to set
            value: The new value for the element
        """

        current_tuple: list[T] = list(self._get_tuple_value())
        if index < 0 or index >= len(current_tuple):
            raise ValueError(f"Index {index} is out of bounds for tuple of length {len(current_tuple)}")
        
        current_tuple[index] = value
        
        # Update the internal value directly to avoid circular calls
        old_value = self._component_values["value"]
        if old_value == tuple(current_tuple):
            return
        self._component_values["value"] = tuple(current_tuple)
        
        # Notify the main tuple binding handler
        self._component_hooks["value"].notify_bindings(tuple(current_tuple))
        
        # Notify listeners
        self._notify_listeners()

    def bind_to(self, hook: CarriesDistinctTupleHook[T]|Hook[tuple[T, ...]], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding with another observable tuple.
        
        This method creates a bidirectional binding between this observable tuple and another,
        ensuring that changes to either observable are automatically propagated to the other.
        The binding can be configured with different initial synchronization modes.
        
        Args:
            observable: The observable tuple to bind to
            initial_sync_mode: How to synchronize values initially
            
        Raises:
            ValueError: If observable is None
        """
        if hook is None:
            raise ValueError("Cannot bind to None observable")
        if isinstance(hook, CarriesDistinctTupleHook):
            hook = hook._get_tuple_hook()
        self._get_tuple_hook().establish_binding(hook, initial_sync_mode)

    def bind_to_item(self, hook: CarriesDistinctIndexableSingleValueHook[T]|CarriesDistinctSingleValueHook[T]|Hook[T], tuple_index: int,  *, hook_index_or_key: Optional[int] = None, initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding with another observable single value.
        
        This method creates a bidirectional binding between this observable tuple and another,
        ensuring that changes to either observable are automatically propagated to the other.
        The binding can be configured with different initial synchronization modes.

        Args:
            observable: The observable single value to bind to
            tuple_index: The index of the value in the tuple
            hook_index_or_key: The index of the value of a CarriesIndexableSingleValueHook or the key of a CarriesKeyableSingleValueHook
            initial_sync_mode: How to synchronize values initially
            
        Raises:
            ValueError: If observable is None
        """

        if hook is None:
            raise ValueError("Cannot bind to None observable")
        
        if not isinstance(tuple_index, int):
            raise ValueError(f"Index must be an integer, got {type(tuple_index).__name__}")
        
        if tuple_index < 0 or tuple_index >= len(self._get_tuple_value()):
            raise ValueError(f"Index {tuple_index} is out of bounds for tuple of length {len(self._get_tuple_value())}")
        
        # Establish the binding
        if isinstance(hook, CarriesDistinctIndexableSingleValueHook):
            hook = hook._get_indexable_single_value_hook(tuple_index)
        elif isinstance(hook, CarriesDistinctSingleValueHook):
            hook = hook._get_single_value_hook()
        
        self._indexable_hook_manager.add_hook_to_hook(tuple_index, hook, initial_sync_mode)

    def unbind_from_item(self, hook: CarriesDistinctIndexableSingleValueHook[T]|CarriesDistinctSingleValueHook[T]|Hook[T], tuple_index: int,  *, hook_index_or_key: Optional[int] = None) -> None:
        """
        Remove the bidirectional binding with another observable single value.
        
        This method removes the binding between this observable tuple and another,
        preventing further automatic synchronization of changes.

        Args:
            hook: The hook to unbind from
            tuple_index: The index of the value in the tuple
            hook_index_or_key: The index of the value of a CarriesIndexableSingleValueHook or the key of a CarriesKeyableSingleValueHook

        Raises:
            ValueError: If observable is None
        """

        if hook is None:
            raise ValueError("Cannot unbind from None observable")
        
        if not isinstance(tuple_index, int):
            raise ValueError(f"Index must be an integer, got {type(tuple_index).__name__}")
        
        if tuple_index < 0 or tuple_index >= len(self._get_tuple_value()):
            raise ValueError(f"Index {tuple_index} is out of bounds for tuple of length {len(self._get_tuple_value())}")
        
        if isinstance(hook, CarriesDistinctIndexableSingleValueHook):
            hook = hook._get_indexable_single_value_hook(tuple_index)
        elif isinstance(hook, CarriesDistinctSingleValueHook):
            hook = hook._get_single_value_hook()
        
        self._indexable_hook_manager.remove_hook_from_hook(tuple_index, hook)

    def unbind_from(self, hook: CarriesDistinctTupleHook[T]|Hook[tuple[T, ...]]) -> None:
        """
        Remove the bidirectional binding with another observable tuple.
        
        This method removes the binding between this observable tuple and another,
        preventing further automatic synchronization of changes.
        
        Args:
            observable: The observable tuple to unbind from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        if hook is None:
            raise ValueError("Cannot unbind from None observable")
        if isinstance(hook, CarriesDistinctTupleHook):
            hook = hook._get_tuple_hook()
        self._get_tuple_hook().remove_binding(hook)
    
    def get_observed_component_values(self) -> tuple[tuple[T, ...]]:
        """
        Get the values of all observables that are bound to this observable.
        
        This method is part of the Observable protocol and provides access to
        the current values of all bound observables.
        
        Returns:
            A tuple containing the current tuple value
        """
        return tuple(self._get_tuple_value())
    
    def set_observed_values(self, values: tuple[tuple[T, ...]]) -> None:
        """
        Set the values of all observables that are bound to this observable.
        
        This method is part of the Observable protocol and allows external
        systems to update this observable's value. It handles all internal
        state changes, binding updates, and listener notifications.
        
        Args:
            values: A tuple containing the new tuple value to set
        """
        # Extract the tuple from the tuple (values should be a single-element tuple)
        new_tuple = values[0]

        # Handle the individual element hooks: If the tuple is longer than the number of element hooks, create new hooks, if it is shorter, remove the hooks
        if len(new_tuple) > len(self._indexable_hook_manager.managed_hooks):
            for index in range(len(self._indexable_hook_manager.managed_hooks), len(new_tuple)):
                self._indexable_hook_manager.create_and_place_managed_hook(index)
        elif len(new_tuple) < len(self._indexable_hook_manager.managed_hooks):
            for index in range(len(new_tuple), len(self._indexable_hook_manager.managed_hooks)):
                self._indexable_hook_manager.remove_hook(index)
        
        # Update internal state
        self._set_component_values_from_dict(
            {"value": new_tuple}
        )
        
        # Notify all individual element hooks of the change
        for index in range(len(new_tuple)):
            hook_key = f"value_{index}"
            if hook_key in self._component_hooks:
                hook = self._component_hooks[hook_key]
                hook.notify_bindings(new_tuple[index])
    
    def __str__(self) -> str:
        """String representation of the observable tuple."""
        return f"OT(tuple={self._get_tuple_value()})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the observable tuple."""
        return f"ObservableTuple({self._get_tuple_value()})"