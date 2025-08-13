from typing import Any, Generic, Optional, TypeVar, overload
from .._utils._internal_binding_handler import InternalBindingHandler, SyncMode, DEFAULT_SYNC_MODE
from .._utils._carries_bindable_single_value import CarriesBindableSingleValue
from .._utils._carries_bindable_set import CarriesBindableSet
from .._utils.observable import Observable

T = TypeVar("T")

class ObservableMultiSelectionOption(Observable, CarriesBindableSet[T], Generic[T]):
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
    def __init__(self, selected_options: CarriesBindableSet[T], available_options: CarriesBindableSet[T]):
        """Initialize with observable available options and observable selected options."""
        ...

    @overload
    def __init__(self, selected_options: set[T], available_options: CarriesBindableSet[T]):
        """Initialize with observable available options and direct selected options."""
        ...

    @overload
    def __init__(self, selected_options: CarriesBindableSet[T], available_options: set[T]):
        """Initialize with direct available options and observable selected options."""
        ...
    
    @overload
    def __init__(self, selected_options: set[T], available_options: set[T]):
        """Initialize with direct available options and direct selected options."""
        ...

    def __init__(self, selected_options: set[T] | CarriesBindableSet[T], available_options: set[T] | CarriesBindableSet[T]):
        """
        Initialize the ObservableMultiSelectionOption.
        
        Args:
            selected_options: Initially selected options or observable set to bind to
            available_options: Set of available options or observable set to bind to
            
        Raises:
            ValueError: If any selected option is not in available options set
        """
        
        if isinstance(available_options, CarriesBindableSet):
            initial_available_options: set[T] = available_options._get_set().copy()
            bindable_set_carrier: Optional[CarriesBindableSet[T]] = available_options
        else:
            initial_available_options: set[T] = available_options.copy()
            bindable_set_carrier: Optional[CarriesBindableSet[T]] = None

        if isinstance(selected_options, CarriesBindableSet):
            initial_selected_options: set[T] = selected_options._get_set().copy()
            bindable_selected_options_carrier: Optional[CarriesBindableSet[T]] = selected_options
        else:
            initial_selected_options: set[T] = selected_options.copy()
            bindable_selected_options_carrier: Optional[CarriesBindableSet[T]] = None

        if initial_selected_options and not initial_selected_options.issubset(initial_available_options):
            invalid_options = initial_selected_options - initial_available_options
            raise ValueError(f"Selected options {invalid_options} not in available options {initial_available_options}")
        
        def verification_method(x: dict[str, Any]) -> tuple[bool, str]:
            if not isinstance(x["available_options"], set):
                return False, "Available options is not a set"
            
            if not isinstance(x["selected_options"], set):
                return False, "Selected options is not a set"
            
            if x["selected_options"] and not x["selected_options"].issubset(x["available_options"]):
                invalid_options = x["selected_options"] - x["available_options"]
                return False, f"Selected options {invalid_options} not in available options {x['available_options']}"

            return True, "Verification method passed"

        super().__init__(
            {
                "selected_options": initial_selected_options,
                "available_options": initial_available_options
            },
            {
                "selected_options": InternalBindingHandler(self, self._get_selected_options_set, self._set_selected_options_set),
                "available_options": InternalBindingHandler(self, self._get_available_options_set, self._set_available_options_set)
            },
            verification_method=verification_method
        )

        if bindable_set_carrier is not None:
            self.bind_available_options_to_observable(bindable_set_carrier)
        if bindable_selected_options_carrier is not None:
            self.bind_selected_options_to_observable(bindable_selected_options_carrier)

    @property
    def available_options(self) -> set[T]:
        """
        Get a copy of the available options.
        
        Returns:
            A copy of the available options set to prevent external modification
        """
        return self._component_values["available_options"].copy()
    
    @available_options.setter
    def available_options(self, value: set[T]) -> None:
        """
        Set the available options.
        
        This setter automatically calls set_available_options() to ensure proper validation
        and notification.
        
        Args:
            value: New set of available options
        """
        self.set_available_options(value)
    
    @property
    def selected_options(self) -> set[T]:
        """
        Get a copy of the currently selected options.
        
        Returns:
            A copy of the currently selected options set to prevent external modification
        """
        return self._component_values["selected_options"].copy()
    
    @selected_options.setter
    def selected_options(self, value: set[T]) -> None:
        """
        Set the selected options.
        
        This setter automatically calls set_selected_options() to ensure proper validation
        and notification.
        
        Args:
            value: New set of selected options
        """
        self.set_selected_options(value)

    @property
    def selected_options_not_empty(self) -> set[T]:
        """
        Get the current selected options if they are not empty.
        
        Returns:
            The current selected options

        Raises:
            ValueError: If the selected options is empty
        """
        selected_options = self._component_values["selected_options"]
        if not selected_options:
            raise ValueError("Selected options is empty")
        return selected_options.copy()
    
    def _get_available_options_set(self) -> set[T]:
        """
        Get the current available options set. No copy is made!
        
        Returns:
            The current available options set
        """
        return self._component_values["available_options"]
    
    def _get_selected_options_set(self) -> set[T]:
        """
        Get the current selected options set. No copy is made!
        
        Returns:
            The current selected options set
        """
        return self._component_values["selected_options"]
    
    def _set_available_options_set(self, value: set[T]) -> None:
        """
        Internal method to set available options from binding system.
        
        Args:
            value: The new available options set to set
        """
        self.set_available_options(value)
    
    def _set_selected_options_set(self, value: set[T]) -> None:
        """
        Internal method to set selected options from binding system.
        
        Args:
            value: The new selected options set to set
        """
        self.set_selected_options(value)
    
    def _get_set(self) -> set[T]:
        """
        Get the current selected options set for the CarriesBindableSet interface.
        No copy is made!
        
        Returns:
            The current selected options set
        """
        return self._component_values["selected_options"]
    
    def _set_set(self, value: set[T]) -> None:
        """
        Internal method to set selected options from binding system for the CarriesBindableSet interface.
        
        Args:
            value: The new selected options set to set
        """
        self.set_selected_options(value)
    
    def _get_selected_options_binding_handler(self) -> InternalBindingHandler[set[T]]:
        """
        Internal method to get selected options binding handler.
        
        Returns:
            The binding handler for the selected options
        """
        return self._component_binding_handlers["selected_options"]
    
    def _get_available_options_binding_handler(self) -> InternalBindingHandler[set[T]]:
        """
        Internal method to get available options binding handler.
        
        Returns:
            The binding handler for the available options set
        """
        return self._component_binding_handlers["available_options"]
    
    def _get_set_binding_handler(self) -> InternalBindingHandler[set[T]]:
        """
        Internal method to get selected options binding handler for the CarriesBindableSet interface.
        
        Returns:
            The binding handler for the selected options
        """
        return self._component_binding_handlers["selected_options"]
    
    def set_selected_options_and_available_options(self, selected_options: set[T], options: set[T]) -> None:
        """
        Set both the selected options and available options atomically.
        
        This method allows setting both values at once, ensuring consistency
        and triggering appropriate notifications. It's useful when you need
        to update both values simultaneously without intermediate invalid states.
        
        Args:
            selected_options: The new selected options (can be empty)
            options: The new set of available options
            
        Raises:
            ValueError: If any selected option is not in options set
        """
        if selected_options and not selected_options.issubset(options):
            invalid_options = selected_options - options
            raise ValueError(f"Selected options {invalid_options} not in options {options}")
        
        if options == self._component_values["available_options"] and selected_options == self._component_values["selected_options"]:
            return
        
        # Use the protocol method to set the values
        self._set_component_values({"selected_options": selected_options, "available_options": options})
    
    def set_available_options(self, available_options: set[T]) -> None:
        """
        Set the available options set.
        
        This method updates the available options, ensuring that all current
        selected options remain valid.
        
        Args:
            available_options: The new set of available options
            
        Raises:
            ValueError: If current selected options are not in the new available options set
        """
        if available_options == self._component_values["available_options"]:
            return
        
        self._raise_if_selected_options_not_in_available_options(self._component_values["selected_options"], available_options)

        # Use the protocol method to set the values
        self._set_component_values({"selected_options": self._component_values["selected_options"], "available_options": available_options})

    def set_selected_options(self, selected_options: set[T]) -> None:
        """
        Set the selected options.
        
        This method updates the selected options, ensuring that they are valid
        according to the current available options.
        
        Args:
            selected_options: The new set of selected options
            
        Raises:
            ValueError: If any selected option is not in the available options
        """
        if selected_options == self._component_values["selected_options"]:
            return
        
        self._raise_if_selected_options_not_in_available_options(selected_options, self._component_values["available_options"])

        # Use the protocol method to set the values
        self._set_component_values({"selected_options": selected_options, "available_options": self._component_values["available_options"]})

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

    def bind_selected_options_to_observable(self, observable: CarriesBindableSet[T], initial_sync_mode: SyncMode = DEFAULT_SYNC_MODE) -> None:
        """
        Establish a bidirectional binding for the selected options with another observable.
        
        This method creates a bidirectional binding between this observable's selected options
        and another observable, ensuring that changes to either are automatically propagated.
        
        Args:
            observable: The observable to bind the selected options to
            initial_sync_mode: How to synchronize values initially
            
        Raises:
            ValueError: If the observable is None
        """
        if observable is None:
            raise ValueError("Observable is None")
        self._get_selected_options_binding_handler().establish_binding(observable._get_set_binding_handler(), initial_sync_mode)

    def bind_available_options_to_observable(self, observable: CarriesBindableSet[T], initial_sync_mode: SyncMode = DEFAULT_SYNC_MODE) -> None:        
        """
        Establish a bidirectional binding for the available options set with another observable.
        
        This method creates a bidirectional binding between this observable's available options set
        and another observable, ensuring that changes to either are automatically propagated.
        
        Args:
            observable: The observable to bind the available options to
            initial_sync_mode: How to synchronize values initially
            
        Raises:
            ValueError: If the observable is None
        """
        if observable is None:
            raise ValueError("Observable is None")
        self._get_available_options_binding_handler().establish_binding(observable._get_set_binding_handler(), initial_sync_mode)

    def unbind_selected_options_from_observable(self, observable: CarriesBindableSet[T]) -> None:
        """
        Remove the bidirectional binding for the selected options with another observable.
        
        This method removes the binding between this observable's selected options
        and another observable, preventing further automatic synchronization.
        
        Args:
            observable: The observable to unbind the selected options from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        self._get_selected_options_binding_handler().remove_binding(observable._get_set_binding_handler())

    def unbind_available_options_from_observable(self, observable: CarriesBindableSet[T]) -> None:
        """
        Remove the bidirectional binding for the available options set with another observable.
        
        This method removes the binding between this observable's available options set
        and another observable, preventing further automatic synchronization.
        
        Args:
            observable: The observable to unbind the available options from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        self._get_available_options_binding_handler().remove_binding(observable._get_set_binding_handler())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        """
        Check the consistency of the binding system.
        
        This method performs comprehensive checks on both the selected options
        and available options bindings to ensure they are in a consistent state and
        values are properly synchronized.
        
        Returns:
            Tuple of (is_consistent, message) where is_consistent is a boolean
            indicating if the system is consistent, and message provides details
            about any inconsistencies found.
        """
        binding_state_consistent, binding_state_consistent_message = self._get_selected_options_binding_handler().check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        binding_state_consistent, binding_state_consistent_message = self._get_available_options_binding_handler().check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._get_selected_options_binding_handler().check_values_synced()
        if not values_synced:
            return False, values_synced_message
        values_synced, values_synced_message = self._get_available_options_binding_handler().check_values_synced()
        if not values_synced:
            return False, values_synced_message
        return True, "Binding system is consistent"
    
    def add(self, item: T) -> None:
        """
        Add an item to the selected options set.
        
        This method adds a new item to the selected options, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The item to add to the selected options set
        """
        new_selected_options = self._get_selected_options_set().copy()
        if item not in new_selected_options:
            new_selected_options.add(item)
        self._set_component_values({"selected_options": new_selected_options, "available_options": self._get_available_options_set()})
    
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
        new_selected_options = self._get_selected_options_set().copy()
        if item not in new_selected_options:
            raise KeyError(f"Item {item} not in selected options")
        new_selected_options.remove(item)
        self._set_component_values({"selected_options": new_selected_options, "available_options": self._get_available_options_set()})
    
    def discard(self, item: T) -> None:
        """
        Remove an item from the selected options set if it exists.
        
        This method removes an item from the selected options if it exists, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The item to remove from the selected options set
        """
        new_selected_options = self._get_selected_options_set().copy()
        new_selected_options.discard(item)
        self._set_component_values({"selected_options": new_selected_options, "available_options": self._get_available_options_set()})
    
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
        new_selected_options = self._get_selected_options_set().copy()
        if not new_selected_options:
            raise KeyError("Selected options set is empty")
        item = new_selected_options.pop()
        self._set_component_values({"selected_options": new_selected_options, "available_options": self._get_available_options_set()})
        return item
    
    def clear(self) -> None:
        """
        Remove all items from the selected options set.
        
        This method removes all items from the selected options, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        """
        self._set_component_values({"selected_options": set(), "available_options": self._get_available_options_set()})
    
    def add_available_option(self, item: T) -> None:
        """
        Add an item to the available options set.
        
        This method adds a new item to the available options, using
        _set_component_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The item to add to the available options set
        """
        new_available_options = self._get_available_options_set().copy()
        if item not in new_available_options:
            new_available_options.add(item)
        self._set_component_values({"selected_options": self._get_selected_options_set(), "available_options": new_available_options})
    
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
        new_available_options = self._get_available_options_set().copy()
        if item not in new_available_options:
            raise KeyError(f"Item {item} not in available options")
        new_available_options.remove(item)
        
        new_selected_options = self._get_selected_options_set().copy()
        new_selected_options.discard(item)
        
        self._set_component_values({"selected_options": new_selected_options, "available_options": new_available_options})
    
    def __str__(self) -> str:
        return f"OMSO(available_options={self._get_available_options_set()}, selected={self._get_selected_options_set()})"
    
    def __repr__(self) -> str:
        return f"ObservableMultiSelectionOption({self._get_selected_options_set()}, {self._get_available_options_set()})"
    
    def __len__(self) -> int:
        """
        Get the number of selected options.
        
        Returns:
            The number of selected options
        """
        return len(self._get_selected_options_set())
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an item is in the selected options.
        
        Args:
            item: The item to check for
            
        Returns:
            True if the item is in the selected options set, False otherwise
        """
        return item in self._get_selected_options_set()
    
    def __iter__(self):
        """
        Get an iterator over the selected options.
        
        Returns:
            An iterator that yields each selected option in the set
        """
        return iter(self._get_selected_options_set())
    
    def __eq__(self, other) -> bool:
        """
        Check equality with another multi-selection option or observable.
        
        Args:
            other: Another ObservableMultiSelectionOption to compare with
            
        Returns:
            True if both options sets and selected options are equal, False otherwise
        """
        if isinstance(other, ObservableMultiSelectionOption):
            return (self._get_available_options_set() == other._get_available_options_set() and 
                   self._get_selected_options_set() == other._get_selected_options_set())
        return False
    
    def __ne__(self, other) -> bool:
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
        return hash((frozenset(self._get_available_options_set()), frozenset(self._get_selected_options_set())))
    
    def __bool__(self) -> bool:
        """
        Convert the multi-selection option to a boolean.
        
        Returns:
            True if there are selected options, False if selected_options is empty
        """
        return bool(self._get_selected_options_set())
    






