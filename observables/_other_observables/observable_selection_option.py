from typing import Any, Generic, Optional, TypeVar, overload
from .._utils.hook import Hook
from .._utils.sync_mode import SyncMode
from .._utils.carries_distinct_single_value_hook import CarriesDistinctSingleValueHook
from .._utils.carries_distinct_set_hook import CarriesDistinctSetHook
from .._utils.observable import Observable
from .._utils.hook import Hook

T = TypeVar("T")

class ObservableSelectionOption(Observable, CarriesDistinctSingleValueHook[Optional[T]], CarriesDistinctSetHook[T], Generic[T]):
    """
    An observable selection option that manages both available options and a selected value.
    
    This class combines the functionality of an observable set (for available options) and
    an observable single value (for the selected option). It ensures that the selected
    option is always valid according to the available options and supports bidirectional
    bindings for both the options set and the selected value.
    
    Features:
    - Bidirectional bindings for both options and selected option
    - Automatic validation ensuring selected option is always in options set
    - Listener notification system for change events
    - Full set interface for options management
    - Type-safe generic implementation
    - None selection is allowed by default

    Handling of no selection:
    - If allow_none is True, the selected option can be None
    - If there are no options, the selected option is None, but if allow_none is False, an error is raised
    - If allow_none is False, an error is raised if the selection options are empty
    
    Example:
        >>> # Create a selection with available options
        >>> country_selector = ObservableSelectionOption(
        ...     selected_option="USA",
        ...     options=["USA", "Canada", "UK", "Germany"]
        ... )
        >>> country_selector.add_listeners(lambda: print("Selection changed!"))
        >>> country_selector.selected_option = "Canada"  # Triggers listener
        Selection changed!
        
        >>> # Create bidirectional binding for options
        >>> options_source = ObservableSet(["A", "B", "C"])
        >>> selector = ObservableSelectionOption("A", options_source)
        >>> options_source.add("D")  # Updates selector options
        >>> print(selector.options)
        {'A', 'B', 'C', 'D'}
    
    Args:
        options: Set of available options or observable set to bind to
        selected_option: Initially selected option or observable value to bind to
        allow_none: Whether to allow None values for the selected option, e.g. if the options set is empty
    """
    
    @overload
    def __init__(self, selected_option: CarriesDistinctSingleValueHook[T]|Hook[T], options: CarriesDistinctSetHook[T]|Hook[set[T]], allow_none: bool = True):
        """Initialize with observable options and observable selected option."""
        ...

    @overload
    def __init__(self, selected_option: Optional[T], options: CarriesDistinctSetHook[T]|Hook[set[T]], allow_none: bool = True):
        """Initialize with observable options and direct selected option."""
        ...

    @overload
    def __init__(self, selected_option: CarriesDistinctSingleValueHook[T]|Hook[T], options: set[T], allow_none: bool = True):
        """Initialize with direct options and observable selected option."""
        ...
    
    @overload
    def __init__(self, selected_option: Optional[T], options: set[T], allow_none: bool = True):
        """Initialize with direct options and direct selected option."""
        ...

    def __init__(self, selected_option: Optional[T] | CarriesDistinctSingleValueHook[Optional[T]] | Hook[Optional[T]], options: set[T] | CarriesDistinctSetHook[T] | Hook[set[T]], allow_none: bool = True):
        """
        Initialize the ObservableSelectionOption.
        
        Args:
            selected_option: Initially selected option or observable value to bind to
            options: Set of available options or observable set to bind to
            allow_none: Whether to allow None values for the selected option, e.g. if the options set is empty
            
        Raises:
            ValueError: If selected_option is not in options set
        """

        self._allow_none = allow_none
        
        if isinstance(options, CarriesDistinctSetHook):
            available_options: set[T] = options.get_set_value()
            available_options_hook: Optional[Hook[set[T]]] = options._get_set_hook()
        elif isinstance(options, Hook):
            available_options: set[T] = options._get_callback()
            available_options_hook: Optional[Hook[set[T]]] = options
        else:
            available_options: set[T] = options.copy()
            available_options_hook: Optional[CarriesDistinctSetHook[T]] = None

        if isinstance(selected_option, CarriesDistinctSingleValueHook):
            initial_selected_option: Optional[T] = selected_option.get_single_value()
            selected_option_hook: Optional[Hook[T]] = selected_option._get_single_value_hook()
        elif isinstance(selected_option, Hook):
            initial_selected_option: Optional[T] = selected_option._get_callback()
            selected_option_hook: Optional[Hook[T]] = selected_option
        else:
            initial_selected_option: Optional[T] = selected_option
            selected_option_hook: Optional[Hook[T]] = None

        if not allow_none and (initial_selected_option is None or available_options == set()):
            raise ValueError("Selected option is None but allow_none is False")
        
        if initial_selected_option is not None and initial_selected_option not in available_options:
            raise ValueError(f"Selected option {initial_selected_option} not in options {available_options}")
        
        def verification_method(x: dict[str, Any]) -> tuple[bool, str]:
            if not self._allow_none and x["selected_option"] is None:
                return False, "Selected option is None but allow_none is False"
            
            if not isinstance(x["options"], set):
                return False, "Options is not a set"
            
            if x["selected_option"] is not None and x["selected_option"] not in x["options"]:
                return False, f"Selected option {x['selected_option']} not in options {x['options']}"
            
            if not self._allow_none and x["options"] == set():
                return False, "Options set is empty but allow_none is False"

            return True, "Verification method passed"

        super().__init__(
            {
                "selected_option": initial_selected_option,
                "options": available_options
            },
            {
                "selected_option": Hook(self, self._get_single_value, self._set_single_value),
                "options": Hook(self, self._get_set, self._set_set)
            },
            verification_method=verification_method
        )

        if available_options_hook is not None:
            self.bind_options_to_observable(available_options_hook)
        if selected_option_hook is not None:
            self.bind_selected_option_to_observable(selected_option_hook)

    @property
    def options(self) -> set[T]:
        """
        Get a copy of the available options.
        
        Returns:
            A copy of the available options set to prevent external modification
        """
        return self._component_values["options"].copy()
    
    @options.setter
    def options(self, value: set[T]) -> None:
        """
        Set the available options.
        
        This setter automatically calls change_options() to ensure proper validation
        and notification.
        
        Args:
            value: New set of available options
        """
        self.set_options(value)
    
    @property
    def selected_option(self) -> Optional[T]:
        """
        Get the currently selected option.
        
        Returns:
            The currently selected option
        """
        return self._component_values["selected_option"]
    
    @selected_option.setter
    def selected_option(self, value: Optional[T]) -> None:
        """
        Set the selected option.
        
        This setter automatically calls change_selected_option() to ensure proper validation
        and notification.
        
        Args:
            value: New selected option
        """
        self.set_selected_option(value)

    @property
    def selected_option_not_none(self) -> T:
        """
        Get the current selected option if it is not None.
        
        Returns:
            The current selected option

        Raises:
            ValueError: If the selected option is None
        """
        selected_option = self._component_values["selected_option"]
        if selected_option is None:
            raise ValueError("Selected option is None")
        return selected_option
    
    def _get_set(self) -> set[T]:
        """
        Get the current options set. No copy is made!
        
        Returns:
            The current options set
        """
        return self._component_values["options"]
    
    def _get_single_value(self) -> T:
        """
        Get the current selected option. No copy is made!
        
        Returns:
            The current selected option
        """
        return self._component_values["selected_option"]
    
    def _set_set(self, value: set[T]) -> None:
        """
        Internal method to set options from binding system.
        
        Args:
            value: The new options set to set
        """
        self.set_options(value)
    
    def _set_single_value(self, value: T) -> None:
        """
        Internal method to set selected option from binding system.
        
        Args:
            value: The new selected option to set
        """
        self.set_selected_option(value)
    
    def _get_single_value_binding_handler(self) -> Hook[T]:
        """
        Internal method to get selected option binding handler.
        
        Returns:
            The binding handler for the selected option
        """
        return self._component_hooks["selected_option"]
    
    def _get_set_binding_handler(self) -> Hook[set[T]]:
        """
        Internal method to get options binding handler.
        
        Returns:
            The binding handler for the options set
        """
        return self._component_hooks["options"]
    
    def set_selected_option_and_available_options(self, selected_option: Optional[T], options: set[T]) -> None:
        """
        Set both the selected option and available options atomically.
        
        This method allows setting both values at once, ensuring consistency
        and triggering appropriate notifications. It's useful when you need
        to update both values simultaneously without intermediate invalid states.
        
        Args:
            selected_option: The new selected option (can be None if allow_none=True)
            options: The new set of available options
            
        Raises:
            ValueError: If selected_option is not in options set
            ValueError: If selected_option is None but allow_none is False
            ValueError: If options set is empty but allow_none is False
        """
        if selected_option is not None and selected_option not in options:
            raise ValueError(f"Selected option {selected_option} not in options {options}")
        
        if not self._allow_none and selected_option is None:
            raise ValueError("Selected option is None but allow_none is False")
        
        if not self._allow_none and options == set():
            raise ValueError("Options set is empty but allow_none is False")
        
        if options == self._component_values["options"] and selected_option == self._component_values["selected_option"]:
            return
        
        # Use the protocol method to set the values
        self._set_component_values({"selected_option": selected_option, "options": options})
    
    def set_options(self, options: set[T]) -> None:
        """
        Set the available options set.
        
        This method updates the available options, ensuring that the current
        selected option remains valid. If the new options set is empty, it
        will raise an error to prevent invalid states.
        
        Args:
            options: The new set of available options
            
        Raises:
            ValueError: If trying to set empty options without setting selected option to None
            ValueError: If current selected option is not in the new options set
        """
        if options == self._component_values["options"]:
            return

        if options == set():
            raise ValueError("An empty set of options can not be set without setting the selected option to None, if even it is allowed")
        
        self._raise_if_selected_option_not_in_options(self._component_values["selected_option"], options)

        # Use the protocol method to set the values
        self._set_component_values({"selected_option": self._component_values["selected_option"], "options": options})

    def set_selected_option(self, selected_option: Optional[T]) -> None:
        """
        Set the selected option.
        
        This method updates the selected option, ensuring that it's valid
        according to the current available options and allow_none setting.
        
        Args:
            selected_option: The new selected option
            
        Raises:
            ValueError: If the selected option is not in the available options
            ValueError: If selected option is None but allow_none is False
        """
        if selected_option == self._component_values["selected_option"]:
            return
        
        self._raise_if_selected_option_not_in_options(selected_option, self._component_values["options"])

        # Use the protocol method to set the values
        self._set_component_values({"selected_option": selected_option, "options": self._component_values["options"]})

    def _raise_if_selected_option_not_in_options(self, selected_option: Optional[T], options: set[T]) -> None:
        """
        Internal method to validate that a selected option is valid for the given options set.
        
        This method checks if the selected option is valid according to the
        allow_none setting and whether it exists in the options set.
        
        Args:
            selected_option: The selected option to validate
            options: The set of available options to check against
            
        Raises:
            ValueError: If the selected option is None but allow_none is False
            ValueError: If the selected option is not in the options set
        """
        if not self._allow_none and selected_option is None:
            raise ValueError("Selected option is None but allow_none is False")
        
        if selected_option is not None and selected_option not in options:
            raise ValueError(f"Selected option {selected_option} not in options {options}")

    def bind_selected_option_to_observable(self, hook: Hook[T] | CarriesDistinctSingleValueHook[T], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding for the selected option with another observable.
        
        This method creates a bidirectional binding between this observable's selected option
        and another observable, ensuring that changes to either are automatically propagated.
        
        Args:
            observable: The observable to bind the selected option to
            initial_sync_mode: How to synchronize values initially
            
        Raises:
            ValueError: If the observable is None
        """
        if hook is None:
            raise ValueError("Hook is None")
        if isinstance(hook, CarriesDistinctSingleValueHook):
            hook = hook._get_single_value_hook()
        self._get_single_value_binding_handler().establish_binding(hook, initial_sync_mode)

    def bind_options_to_observable(self, hook: CarriesDistinctSetHook[T], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:        
        """
        Establish a bidirectional binding for the options set with another observable.
        
        This method creates a bidirectional binding between this observable's options set
        and another observable, ensuring that changes to either are automatically propagated.
        
        Args:
            observable: The observable to bind the options to
            initial_sync_mode: How to synchronize values initially
            
        Raises:
            ValueError: If the observable is None
        """
        if hook is None:
            raise ValueError("Observable is None")
        if isinstance(hook, CarriesDistinctSetHook):
            hook = hook._get_set_hook()
        self._get_set_binding_handler().establish_binding(hook, initial_sync_mode)

    def bind_to(self, observable: "ObservableSelectionOption[T]", initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding for the selected option with another instance of this class.
        
        This method creates a bidirectional binding between this observable's selected option
        and another instance of this class, ensuring that changes to either are automatically propagated.
        """

        # First, synchronize the values atomically to maintain consistency
        if initial_sync_mode == SyncMode.UPDATE_SELF_FROM_OBSERVABLE:
            # Update both values at once to maintain consistency
            self.set_selected_option_and_available_options(
                observable.selected_option, 
                observable.options
            )
        elif initial_sync_mode == SyncMode.UPDATE_OBSERVABLE_FROM_SELF:
            # Update the other observable's values at once
            observable.set_selected_option_and_available_options(
                self.selected_option, 
                self.options
            )

        # Then, establish the bindings
        self._get_set_binding_handler().establish_binding(observable._get_set_binding_handler(), initial_sync_mode)
        self._get_single_value_binding_handler().establish_binding(observable._get_single_value_binding_handler(), initial_sync_mode)

    def unbind_selected_option_from_observable(self, observable: CarriesDistinctSingleValueHook[T]) -> None:
        """
        Remove the bidirectional binding for the selected option with another observable.
        
        This method removes the binding between this observable's selected option
        and another observable, preventing further automatic synchronization.
        
        Args:
            observable: The observable to unbind the selected option from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        self._get_single_value_hook().remove_binding(observable._get_single_value_hook())

    def unbind_options_from_observable(self, observable: CarriesDistinctSetHook[T]) -> None:
        """
        Remove the bidirectional binding for the options set with another observable.
        
        This method removes the binding between this observable's options set
        and another observable, preventing further automatic synchronization.
        
        Args:
            observable: The observable to unbind the options from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        self._get_set_hook().remove_binding(observable._get_set_hook())

    def unbind_from(self, observable: "ObservableSelectionOption[T]") -> None:
        """
        Remove the bidirectional binding for the selected option with another instance of this class.
        
        This method removes the binding between this observable's selected option
        and another instance of this class, preventing further automatic synchronization.
        """

        self._get_set_binding_handler().remove_binding(observable._get_set_binding_handler())
        self._get_single_value_binding_handler().remove_binding(observable._get_single_value_binding_handler())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        """
        Check the consistency of the binding system.
        
        This method performs comprehensive checks on both the selected option
        and options bindings to ensure they are in a consistent state and
        values are properly synchronized.
        
        Returns:
            Tuple of (is_consistent, message) where is_consistent is a boolean
            indicating if the system is consistent, and message provides details
            about any inconsistencies found.
        """
        binding_state_consistent, binding_state_consistent_message = self._get_single_value_hook().check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        binding_state_consistent, binding_state_consistent_message = self._get_set_hook().check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._get_single_value_hook().check_values_synced()
        if not values_synced:
            return False, values_synced_message
        values_synced, values_synced_message = self._get_set_hook().check_values_synced()
        if not values_synced:
            return False, values_synced_message
        return True, "Binding system is consistent"
    
    def add(self, item: T) -> None:
        """
        Add an item to the options set.
        
        This method adds a new item to the available options, using
        set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            item: The item to add to the options set
        """
        new_options = self._get_set().copy()
        if item not in new_options:
            new_options.add(item)
        self._set_component_values({"selected_option": self._get_single_value(), "options": new_options})
    
    def __str__(self) -> str:
        return f"OSO(options={self._get_set()}, selected={self._get_single_value()})"
    
    def __repr__(self) -> str:
        return f"ObservableSelectionOption({self._get_set()}, {self._get_single_value()})"
    
    def __len__(self) -> int:
        """
        Get the number of available options.
        
        Returns:
            The number of available options
        """
        return len(self._get_set())
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an item is in the available options.
        
        Args:
            item: The item to check for
            
        Returns:
            True if the item is in the options set, False otherwise
        """
        return item in self._get_set()
    
    def __iter__(self):
        """
        Get an iterator over the available options.
        
        Returns:
            An iterator that yields each option in the set
        """
        return iter(self._get_set())
    
    def __eq__(self, other) -> bool:
        """
        Check equality with another selection option or observable.
        
        Args:
            other: Another ObservableSelectionOption to compare with
            
        Returns:
            True if both options sets and selected options are equal, False otherwise
        """
        if isinstance(other, ObservableSelectionOption):
            return (self._get_set() == other._get_set() and 
                   self._get_single_value() == other._get_single_value())
        return False
    
    def __ne__(self, other) -> bool:
        """
        Check inequality with another selection option or observable.
        
        Args:
            other: Another ObservableSelectionOption to compare with
            
        Returns:
            True if the objects are not equal, False otherwise
        """
        return not (self == other)
    
    def __hash__(self) -> int:
        """
        Get the hash value based on the current options and selected option.
        
        Returns:
            Hash value based on the options set and selected option
        """
        return hash((frozenset(self._get_set()), self._get_single_value()))
    
    def __bool__(self) -> bool:
        """
        Convert the selection option to a boolean.
        
        Returns:
            True if there is a selected option, False if selected_option is None
        """
        return bool(self._get_single_value())
    
    @property
    def is_none_selection_allowed(self) -> bool:
        """
        Check if none selection is allowed.
        
        Returns:
            True if none selection is allowed, False otherwise
        """
        return self._allow_none
    
    def set_allow_none_selection(self, allow_none: bool) -> None:
        """
        Set if none selection is allowed.
        
        Args:
            allow_none: True if none selection is allowed, False otherwise

        Raises:
            ValueError: If trying to set allow_none to False if selected option is None
        """
        if self._get_single_value() is None and not allow_none:
            raise ValueError("Cannot set allow_none to False if selected option is None")
        self._allow_none = allow_none
    
    def _get_set_hook(self) -> Hook[set[T]]:
        """
        Get the set hook for options.
        
        Returns:
            The hook for the options set
        """
        return self._component_hooks["options"]
    
    def get_set_value(self) -> set[T]:
        """
        Get the current value of the options set as a copy.
        
        Returns:
            A copy of the current options set value
        """
        return self._component_values["options"].copy()
    
    def _get_single_value_hook(self) -> Hook[Optional[T]]:
        """
        Get the single value hook for the selected option.
        
        Returns:
            The hook for the selected option
        """
        return self._component_hooks["selected_option"]
    
    def get_single_value(self) -> Optional[T]:
        """
        Get the current selected option value.
        
        Returns:
            The current selected option value
        """
        return self._component_values["selected_option"]