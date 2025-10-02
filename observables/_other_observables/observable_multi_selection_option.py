from logging import Logger
from typing import Any, Generic, TypeVar, Optional, overload, Protocol, runtime_checkable, Literal, Mapping, Iterator
from .._hooks.hook_like import HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.base_observable import BaseObservable
from .._utils.carries_hooks_like import CarriesHooksLike
from .._utils.observable_serializable import ObservableSerializable

T = TypeVar("T")

@runtime_checkable
class ObservableMultiSelectionOptionLike(CarriesHooksLike[Any, Any], Protocol[T]):
    """
    Protocol for observable multi-selection option objects.
    """
    
    @property
    def selected_options(self) -> set[T]:
        """
        Get the selected options.
        """
        ...
    
    @selected_options.setter
    def selected_options(self, value: set[T]) -> None:
        """
        Set the selected options.
        """
        ...

    @property
    def available_options(self) -> set[T]:
        """
        Get the available options.
        """
        ...
    
    @available_options.setter
    def available_options(self, value: set[T]) -> None:
        """
        Set the available options.
        """
        ...

    @property
    def available_options_hook(self) -> HookLike[set[T]]:
        """
        Get the hook for the available options.
        """
        ...

    @property
    def selected_options_hook(self) -> HookLike[set[T]]:
        """
        Get the hook for the selected options.
        """
        ...

    def change_selected_options(self, selected_options: set[T]) -> None:
        """
        Change the selected options.
        """
        ...

    def change_available_options(self, available_options: set[T]) -> None:
        """
        Change the available options.
        """
        ...

    def change_selected_options_and_available_options(self, selected_options: set[T], available_options: set[T]) -> None:
        """
        Set the selected options and available options.
        """
        ...

    def add_selected_option(self, item: T) -> None:
        """
        Add an item to the selected options set.
        """
        ...

    def remove_selected_option(self, item: T) -> None:
        """
        Remove an item from the selected options set.
        """
        ...

class ObservableMultiSelectionOption(BaseObservable[Literal["selected_options", "available_options"], Literal["number_of_selected_options", "number_of_available_options"], set[T], int, "ObservableMultiSelectionOption"], ObservableSerializable[Literal["selected_options", "available_options"], "ObservableMultiSelectionOption"], ObservableMultiSelectionOptionLike[T], Generic[T]):
    """
    An observable multi-selection option that manages both available options and selected values.
    
    This class combines the functionality of an observable set (for available options) and
    an observable set (for selected options). It ensures that all selected options are always
    valid according to the available options and supports bidirectional bindings for both
    the available options set and the selected values set.
    
    Features:
    - Bidirectional bindings for both available options and selected options
    - Automatic validation ensuring all selected options are in available options set
    - Listener notification system for change events
    - Full set interface for both available options and selections management
    - Type-safe generic implementation
    - Natural support for empty selections (sets can be empty)

    Handling of no selection:
    - The selected options can be empty (sets naturally support empty state)
    - If there are no available options, the selected options will be empty
    
    Example:
        >>> # Create a multi-selection with available options
        >>> country_selector = ObservableMultiSelectionOption(
        ...     selected_options={"USA", "Canada"},
        ...     options={"USA", "Canada", "UK", "Germany"}
        ... )
        >>> country_selector.add_listeners(lambda: print("Selection changed!"))
        >>> country_selector.add_selected_option("UK")  # Triggers listener
        Selection changed!
        
        >>> # Create bidirectional binding for available options
        >>> available_options_source = ObservableSet(["A", "B", "C"])
        >>> selector = ObservableMultiSelectionOption({"A"}, available_options_source)
        >>> available_options_source.add("D")  # Updates selector available options
        >>> print(selector.available_options)
        {'A', 'B', 'C', 'D'}
    
    Args:
        available_options: Set of available options or observable set to bind to
        selected_options: Initially selected options or observable set to bind to
    """

    @overload
    def __init__(self, selected_options: HookLike[set[T]], available_options: HookLike[set[T]], logger: Optional[Logger] = None) -> None:
        """Initialize with observable available options and observable selected options."""
        ...

    @overload
    def __init__(self, selected_options: set[T], available_options: HookLike[set[T]]|HookLike[set[T]], logger: Optional[Logger] = None) -> None:
        """Initialize with observable available options and direct selected options."""
        ...

    @overload
    def __init__(self, selected_options: HookLike[set[T]], available_options: set[T], logger: Optional[Logger] = None) -> None:
        """Initialize with direct available options and observable selected options."""
        ...
    
    @overload
    def __init__(self, selected_options: set[T], available_options: set[T], logger: Optional[Logger] = None) -> None:
        """Initialize with direct available options and direct selected options."""
        ...

    @overload
    def __init__(self, observable: "ObservableMultiSelectionOptionLike[T]", logger: Optional[Logger] = None) -> None:
        """Initialize from another ObservableMultiSelectionOptionLike object."""
        ...

    def __init__(self, selected_options: set[T] | HookLike[set[T]]|"ObservableMultiSelectionOptionLike[T, Any]", available_options: set[T] | HookLike[set[T]] | None = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize the ObservableMultiSelectionOption.
        
        Args:
            selected_options: Initially selected options, observable set to bind to, or ObservableMultiSelectionOptionLike object
            available_options: Set of available options or observable set to bind to (optional if selected_options is ObservableMultiSelectionOptionLike)
            
        Raises:
            ValueError: If any selected option is not in available options set
        """
        
        # Handle initialization from ObservableMultiSelectionOptionLike
        if isinstance(selected_options, ObservableMultiSelectionOptionLike):            
            source_observable = selected_options # type: ignore
            initial_selected_options: set[T] = source_observable.selected_options # type: ignore
            initial_available_options: set[T] = source_observable.available_options # type: ignore
            selected_options_hook: Optional[HookLike[set[T]]] = None
            available_options_hook: Optional[HookLike[set[T]]] = None
            observable: Optional[ObservableMultiSelectionOptionLike[T]] = selected_options
        else:
            observable = None
            # Handle initialization from separate selected_options and available_options
            if available_options is None:
                raise ValueError("available_options must be provided when not initializing from ObservableMultiSelectionOptionLike")
            
            if isinstance(available_options, HookLike):
                initial_available_options: set[T] = available_options.value
                available_options_hook = available_options
            else:
                initial_available_options = available_options.copy()
                available_options_hook = None

            if isinstance(selected_options, HookLike):
                initial_selected_options = selected_options.value
                selected_options_hook = selected_options
            else:
                initial_selected_options = selected_options.copy()
                selected_options_hook = None

        if initial_selected_options and not initial_selected_options.issubset(initial_available_options):
            invalid_options = initial_selected_options - initial_available_options
            raise ValueError(f"Selected options {invalid_options} not in available options {initial_available_options}")

        self._internal_construct_from_values(
            {"selected_options": initial_selected_options, "available_options": initial_available_options},
            logger=logger
        )

        # Establish bindings if hooks were provided
        if observable is not None:
            self.connect_hook(observable.selected_options_hook, "selected_options", InitialSyncMode.USE_TARGET_VALUE) # type: ignore
            self.connect_hook(observable.available_options_hook, "available_options", InitialSyncMode.USE_TARGET_VALUE) # type: ignore
        if available_options_hook is not None:
            self.connect_hook(available_options_hook, "available_options", InitialSyncMode.USE_TARGET_VALUE) # type: ignore
        if selected_options_hook is not None and selected_options_hook is not available_options_hook:
            self.connect_hook(selected_options_hook, "selected_options", InitialSyncMode.USE_TARGET_VALUE) # type: ignore

    def _internal_construct_from_values(
        self,
        initial_values: Mapping[Literal["selected_options", "available_options"], set[T]],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """
        Construct an ObservableMultiSelectionOption instance.
        """

        def is_valid_value(x: Mapping[Literal["selected_options", "available_options"], set[T]|int]) -> tuple[bool, str]:
            
            if "selected_options" in x:
                selected_options: set[T] = x["selected_options"] # type: ignore
            else:
                selected_options = self._primary_hooks["selected_options"].value # type: ignore
            
            if "available_options" in x:
                available_options: set[T] = x["available_options"] # type: ignore
            else:
                available_options = self._primary_hooks["available_options"].value # type: ignore
            
            if selected_options and not selected_options.issubset(available_options):
                return False, f"Selected options {selected_options} not in available options {available_options}"

            return True, "Verification method passed"

        super().__init__(
            initial_values,
            verification_method=is_valid_value,
            secondary_hook_callbacks={"number_of_selected_options": lambda x: len(x["selected_options"]), "number_of_available_options": lambda x: len(x["available_options"])}, # type: ignore
            logger=logger
        )
        
    @property
    def available_options(self) -> set[T]:
        """
        Get a copy of the available options.
        
        Returns:
            A copy of the available options set to prevent external modification
        """
        return self._primary_hooks["available_options"].value.copy()
    
    @available_options.setter
    def available_options(self, value: set[T]) -> None:
        """
        Set the available options.
        
        This setter automatically calls set_available_options() to ensure proper validation
        and notification.
        
        Args:
            value: New set of available options
        """
        self.change_available_options(value)

    @property
    def available_options_hook(self) -> HookLike[set[T]]:
        return self._primary_hooks["available_options"]
    
    @property
    def selected_options_hook(self) -> HookLike[set[T]]:
        return self._primary_hooks["selected_options"]
    
    @property
    def selected_options(self) -> set[T]:
        """
        Get a copy of the currently selected options.
        
        Returns:
            A copy of the currently selected options set to prevent external modification
        """
        return self._primary_hooks["selected_options"].value.copy()
    
    @selected_options.setter
    def selected_options(self, value: set[T]) -> None:
        """
        Set the selected options.
        
        This setter automatically calls set_selected_options() to ensure proper validation
        and notification.
        
        Args:
            value: New set of selected options
        """
        if value == self._primary_hooks["selected_options"].value:
            return
        success, msg = self.submit_values({"selected_options": value})
        if not success:
            raise ValueError(msg)
    
    def change_selected_options_and_available_options(self, selected_options: set[T], available_options: set[T]) -> None:
        """
        Set both the selected options and available options atomically.
        
        This method allows setting both values at once, ensuring consistency
        and triggering appropriate notifications. It's useful when you need
        to update both values simultaneously without intermediate invalid states.
        
        Args:
            selected_options: The new selected options (can be empty)
            available_options: The new set of available options
            
        Raises:
            ValueError: If any selected option is not in options set
        """
        if selected_options and not selected_options.issubset(available_options):
            invalid_options = selected_options - available_options
            raise ValueError(f"Selected options {invalid_options} not in options {available_options}")
        
        if available_options == self._primary_hooks["available_options"].value and selected_options == self._primary_hooks["selected_options"].value:
            return
        
        # Use the protocol method to set the values
        self.submit_values({"selected_options": selected_options, "available_options": available_options})
    
    def change_available_options(self, available_options: set[T]) -> None:
        """
        Set the available options set.
        
        This method updates the available options, ensuring that all current
        selected options remain valid.
        
        Args:
            available_options: The new set of available options
            
        Raises:
            ValueError: If current selected options are not in the new available options set
        """
        if available_options == self.get_value_of_hook("available_options"):
            return
        
        self._raise_if_selected_options_not_in_available_options(self.get_value_of_hook("selected_options"), available_options) # type: ignore

        # Use the protocol method to set the values
        self.submit_values({"available_options": available_options})

    def change_selected_options(self, selected_options: set[T]) -> None:
        """
        Set the selected options.
        
        This method updates the selected options, ensuring that they are valid
        according to the current available options.
        
        Args:
            selected_options: The new set of selected options
            
        Raises:
            ValueError: If any selected option is not in the available options
        """
        if selected_options == self._primary_hooks["selected_options"].value:
            return
        
        self._raise_if_selected_options_not_in_available_options(selected_options, self.get_value_of_hook("available_options")) # type: ignore

        # Use the protocol method to set the values
        self.submit_values({"selected_options": selected_options})

    def _raise_if_selected_options_not_in_available_options(self, selected_options: set[T], available_options: set[T]) -> None:
        """
        Internal method to validate that selected options are valid for the given available options set.
        
        This method checks if the selected options are valid according to the
        whether they all exist in the available options set.
        
        Args:
            selected_options: The selected options to validate
            available_options: The set of available options to check against
            
        Raises:
            ValueError: If any selected option is not in the available options set
        """
        if selected_options and not selected_options.issubset(available_options):
            invalid_options = selected_options - available_options
            raise ValueError(f"Selected options {invalid_options} not in available options {available_options}")

    def __str__(self) -> str:
        # Sort options for consistent string representation
        sorted_selected = sorted(self.get_value_of_hook("selected_options")) # type: ignore
        sorted_available = sorted(self.get_value_of_hook("available_options")) # type: ignore
        return f"OMSO(selected_options={{{', '.join(repr(opt) for opt in sorted_selected)}}}, available_options={{{', '.join(repr(opt) for opt in sorted_available)}}})" # type: ignore
    
    def __repr__(self) -> str:
        # Sort options for consistent string representation
        sorted_selected = sorted(self.get_value_of_hook("selected_options")) # type: ignore
        sorted_available = sorted(self.get_value_of_hook("available_options")) # type: ignore
        return f"ObservableMultiSelectionOption(selected_options={{{', '.join(repr(opt) for opt in sorted_selected)}}}, available_options={{{', '.join(repr(opt) for opt in sorted_available)}}})" # type: ignore
    
    def __len__(self) -> int:
        """
        Get the number of selected options.
        
        Returns:
            The number of selected options
        """
        return len(self.get_value_of_hook_as_reference("selected_options")) # type: ignore
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an item is in the selected options.
        
        Args:
            item: The item to check for
            
        Returns:
            True if the item is in the selected options set, False otherwise
        """
        return item in self.get_value_of_hook("selected_options") # type: ignore
    
    def __iter__(self) -> Iterator[T]:
        """
        Get an iterator over the selected options.
        
        Returns:
            An iterator that yields each selected option in the set
        """
        return iter(self.get_value_of_hook("selected_options")) # type: ignore
    
    def add(self, item: T) -> None:
        """
        Add an item to the selected options set.
        
        This method adds a new item to the selected options, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The item to add to the selected options set
        """
        new_selected_options: set[T] = self.get_value_of_hook("selected_options") # type: ignore
        if item not in new_selected_options:
            new_selected_options.add(item)
            self.submit_values({"selected_options": new_selected_options})
    
    def remove(self, item: T) -> None:
        """
        Remove an item from the selected options set.
        
        This method removes an item from the selected options, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The item to remove from the selected options set
            
        Raises:
            KeyError: If the item is not in the selected options set
        """
        new_selected_options: set[T] = self.get_value_of_hook("selected_options") # type: ignore
        if item not in new_selected_options:
            raise KeyError(f"Item {item} not in selected options")
        new_selected_options.remove(item)
        self.submit_values({"selected_options": new_selected_options})
    
    def discard(self, item: T) -> None:
        """
        Remove an item from the selected options set if it exists.
        
        This method removes an item from the selected options if it exists, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The item to remove from the selected options set
        """
        new_selected_options: set[T] = self.get_value_of_hook("selected_options") # type: ignore
        new_selected_options.discard(item)
        self.submit_values({"selected_options": new_selected_options})
    
    def pop(self) -> T:
        """
        Remove and return an arbitrary item from the selected options set.
        
        This method removes and returns an arbitrary item from the selected options, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        Returns:
            An arbitrary item from the selected options set
            
        Raises:
            KeyError: If the selected options set is empty
        """
        new_selected_options: set[T] = self.get_value_of_hook("selected_options") # type: ignore
        if not new_selected_options:
            raise KeyError("Selected options set is empty")
        item = new_selected_options.pop()
        self.submit_values({"selected_options": new_selected_options})
        return item
    
    def clear(self) -> None:
        """
        Remove all items from the selected options set.
        
        This method removes all items from the selected options, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        """
        self.submit_values({"selected_options": set()}) # type: ignore
    
    def add_selected_option(self, item: T) -> None:
        """
        Add an item to the selected options set.
        
        This method adds a new item to the selected options, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The item to add to the selected options set
            
        Raises:
            ValueError: If the item is not in the available options set
        """


        available_options: set[T] = self.get_value_of_hook("available_options") # type: ignore
        if item not in available_options:
            raise ValueError(f"Item {item} not in available options")
        
        new_selected_options: set[T] = self.get_value_of_hook("selected_options") # type: ignore
        if item not in new_selected_options:
            new_selected_options.add(item)
            self.submit_values({"selected_options": new_selected_options})
    
    def remove_selected_option(self, item: T) -> None:
        """
        Remove an item from the selected options set.
        
        This method removes an item from the selected options, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The item to remove from the selected options set
        """
        new_selected_options: set[T] = self.get_value_of_hook("selected_options") # type: ignore
        if item in new_selected_options:
            new_selected_options.remove(item)
            self.submit_values({"selected_options": new_selected_options})
    
    def add_available_option(self, item: T) -> None:
        """
        Add an item to the available options set.
        
        This method adds a new item to the available options, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The item to add to the available options set
        """
        new_available_options: set[T] = self.get_value_of_hook("available_options") # type: ignore
        if item not in new_available_options:
            new_available_options.add(item)
            self.submit_values({"available_options": new_available_options})
    
    def remove_available_option(self, item: T) -> None:
        """
        Remove an item from the available options set.
        
        This method removes an item from the available options, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        If the item is in the selected options, it will also be removed from there.
        
        Args:
            item: The item to remove from the available options set
            
        Raises:
            KeyError: If the item is not in the available options set
        """
        new_available_options: set[T] = self.get_value_of_hook("available_options") # type: ignore
        if item not in new_available_options:
            raise KeyError(f"Item {item} not in available options")
        new_available_options.remove(item)
        
        new_selected_options: set[T] = self.get_value_of_hook("selected_options") # type: ignore
        new_selected_options.discard(item)
        
        self.submit_values({"selected_options": new_selected_options, "available_options": new_available_options})
    
    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another multi-selection option or observable.
        
        Args:
            other: Another ObservableMultiSelectionOption to compare with
            
        Returns:
            True if both options sets and selected options are equal, False otherwise
        """
        if isinstance(other, ObservableMultiSelectionOption):
            return (self.get_value_of_hook("available_options") == other.get_value_of_hook("available_options") and 
            self.get_value_of_hook("selected_options") == other.get_value_of_hook("selected_options")) # type: ignore
        return False
    
    def __ne__(self, other: Any) -> bool:
        """
        Check inequality with another multi-selection option or observable.
        
        Args:
            other: Another ObservableMultiSelectionOption to compare with
            
        Returns:
            True if the objects are not equal, False otherwise
        """
        return not (self == other)
    
    def __hash__(self) -> int:
        """
        Get the hash value based on the current options and selected options.
        
        Returns:
            Hash value based on the options set and selected options
        """
        return hash((frozenset(self.get_value_of_hook("available_options")), frozenset(self.get_value_of_hook("selected_options")))) # type: ignore
    
    def __bool__(self) -> bool:
        """
        Convert the multi-selection option to a boolean.
        
        Returns:
            True if there are selected options, False if selected_options is empty
        """
        return bool(self.get_value_of_hook("selected_options")) # type: ignore