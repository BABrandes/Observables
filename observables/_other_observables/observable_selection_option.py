from typing import Generic, Optional, TypeVar, overload
from .._utils._internal_binding_handler import InternalBindingHandler, SyncMode, DEFAULT_SYNC_MODE
from .._utils._carries_bindable_single_value import CarriesBindableSingleValue
from .._utils._carries_bindable_set import CarriesBindableSet
from .._utils.observable import Observable

T = TypeVar("T")

class ObservableSelectionOption(Observable, CarriesBindableSingleValue[T], CarriesBindableSet[T], Generic[T]):
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
    
    Example:
        >>> # Create a selection with available options
        >>> country_selector = ObservableSelectionOption(
        ...     options=["USA", "Canada", "UK", "Germany"],
        ...     selected_option="USA"
        ... )
        >>> country_selector.add_listeners(lambda: print("Selection changed!"))
        >>> country_selector.selected_option = "Canada"  # Triggers listener
        Selection changed!
        
        >>> # Create bidirectional binding for options
        >>> options_source = ObservableSet(["A", "B", "C"])
        >>> selector = ObservableSelectionOption(options_source, "A")
        >>> options_source.add("D")  # Updates selector options
        >>> print(selector.options)
        {'A', 'B', 'C', 'D'}
    
    Args:
        options: Set of available options or observable set to bind to
        selected_option: Initially selected option or observable value to bind to
    """
    
    @overload
    def __init__(self, options: CarriesBindableSet[T], selected_option: CarriesBindableSingleValue[T]):
        """Initialize with observable options and observable selected option."""
        ...

    @overload
    def __init__(self, options: CarriesBindableSet[T], selected_option: T):
        """Initialize with observable options and direct selected option."""
        ...

    @overload
    def __init__(self, options: set[T], selected_option: CarriesBindableSingleValue[T]):
        """Initialize with direct options and observable selected option."""
        ...
    
    @overload
    def __init__(self, options: set[T], selected_option: T):
        """Initialize with direct options and direct selected option."""
        ...

    def __init__(self, options: set[T] | CarriesBindableSet[T], selected_option: T | CarriesBindableSingleValue[T]):
        """
        Initialize the ObservableSelectionOption.
        
        Args:
            options: Set of available options or observable set to bind to
            selected_option: Initially selected option or observable value to bind to
            
        Raises:
            ValueError: If selected_option is not in options set
        """
        super().__init__()  # Initialize ListeningBase
        
        if isinstance(options, CarriesBindableSet):
            initial_options: set[T] = options._get_set().copy()
            bindable_set_carrier: Optional[CarriesBindableSet[T]] = options
        else:
            initial_options: set[T] = options.copy()
            bindable_set_carrier: Optional[CarriesBindableSet[T]] = None

        if isinstance(selected_option, CarriesBindableSingleValue):
            initial_selected_option: T = selected_option._get_single_value()
            bindable_single_value_carrier: Optional[CarriesBindableSingleValue[T]] = selected_option
        else:
            initial_selected_option: T = selected_option
            bindable_single_value_carrier: Optional[CarriesBindableSingleValue[T]] = None

        self._options_binding_handler: InternalBindingHandler[set[T]] = InternalBindingHandler(self, self._get_set, self._set_set, self._check_set)
        self._selected_option_binding_handler: InternalBindingHandler[T] = InternalBindingHandler(self, self._get_single_value, self._set_single_value, self._check_single_value)

        self._options = initial_options
        self._selected_option = initial_selected_option

        if bindable_set_carrier is not None:
            self.bind_options_to_observable(bindable_set_carrier)
        if bindable_single_value_carrier is not None:
            self.bind_selected_option_to_observable(bindable_single_value_carrier)

    @property
    def options(self) -> set[T]:
        """
        Get a copy of the available options.
        
        Returns:
            A copy of the available options set to prevent external modification
        """
        return self._options.copy()
    
    @options.setter
    def options(self, value: set[T]) -> None:
        """
        Set the available options.
        
        This setter automatically calls change_options() to ensure proper validation
        and notification.
        
        Args:
            value: New set of available options
        """
        self.change_options(value)
    
    @property
    def selected_option(self) -> T:
        """
        Get the currently selected option.
        
        Returns:
            The currently selected option
        """
        return self._selected_option
    
    @selected_option.setter
    def selected_option(self, value: T) -> None:
        """
        Set the selected option.
        
        This setter automatically calls change_selected_option() to ensure proper validation
        and notification.
        
        Args:
            value: New selected option
        """
        self.change_selected_option(value)
    
    def _get_set(self) -> set[T]:
        """Internal method to get options set for binding system."""
        return self._options
    
    def _get_single_value(self) -> T:
        """Internal method to get selected option for binding system."""
        return self._selected_option
    
    def _set_set(self, value: set[T]) -> None:
        """Internal method to set options from binding system."""
        self.change_options(value)
    
    def _set_single_value(self, value: T) -> None:
        """Internal method to set selected option from binding system."""
        self.change_selected_option(value)
    
    def _get_single_value_binding_handler(self) -> InternalBindingHandler[T]:
        """Internal method to get selected option binding handler."""
        return self._selected_option_binding_handler
    
    def _get_set_binding_handler(self) -> InternalBindingHandler[set[T]]:
        """Internal method to get options binding handler."""
        return self._options_binding_handler
    
    def _check_set(self, set_to_check: set[T]) -> bool:
        """
        Internal method to check options validity for binding system.
        
        Allows empty sets during initialization and ensures selected option
        is always in the options set.
        """
        # Allow empty sets during initialization
        if not set_to_check:
            return True
        # If we have a selected option, it must be in the set
        if hasattr(self, '_selected_option') and self._selected_option is not None:
            return self._selected_option in set_to_check
        return True
    
    def _check_single_value(self, single_value_to_check: T) -> bool:
        """
        Internal method to check selected option validity for binding system.
        
        Allows None values during initialization and ensures the selected option
        is always in the available options set.
        """
        # Allow None values during initialization
        if single_value_to_check is None:
            return True
        # If we have options, the value must be in them
        if hasattr(self, '_options') and self._options:
            return single_value_to_check in self._options
        return True
    
    def set_selected_option_and_available_options(self, selected_option: T, options: set[T]) -> None:

        if selected_option not in options:
            raise ValueError(f"Selected option {selected_option} not in options {options}")
        
        if options == self._options and selected_option == self._selected_option:
            return
        
        self._options = options
        self._selected_option = selected_option
        self._options_binding_handler.notify_bindings(options)
        self._selected_option_binding_handler.notify_bindings(selected_option)

        self._notify_listeners()
    
    def change_options(self, options: set[T]) -> None:
        if options == self._options:
            return
        
        self.raise_if_selected_option_not_in_options(self._selected_option, options)

        self._options = options.copy()
        self._options_binding_handler.notify_bindings(self._options)
        self._notify_listeners()

    def change_selected_option(self, selected_option: T) -> None:
        if selected_option == self._selected_option:
            return

        self.raise_if_selected_option_not_in_options(selected_option, self._options)

        self._selected_option = selected_option
        self._selected_option_binding_handler.notify_bindings(selected_option)
        self._notify_listeners()

    def raise_if_selected_option_not_in_options(self, selected_option: T, options: set[T]) -> None:
        if selected_option not in options:
            raise ValueError(f"Selected option {selected_option} not in options {options}")

    def bind_selected_option_to_observable(self, observable: CarriesBindableSingleValue[T], initial_sync_mode: SyncMode = DEFAULT_SYNC_MODE) -> None:
        if observable is None:
            raise ValueError("Observable is None")
        self._selected_option_binding_handler.establish_binding(observable._get_single_value_binding_handler(), initial_sync_mode)

    def bind_options_to_observable(self, observable: CarriesBindableSet[T], initial_sync_mode: SyncMode = DEFAULT_SYNC_MODE) -> None:        
        if observable is None:
            raise ValueError("Observable is None")
        self._options_binding_handler.establish_binding(observable._get_set_binding_handler(), initial_sync_mode)

    def unbind_selected_option_from_observable(self, observable: CarriesBindableSingleValue[T]) -> None:
        self._selected_option_binding_handler.remove_binding(observable._get_single_value_binding_handler())

    def unbind_options_from_observable(self, observable: CarriesBindableSet[T]) -> None:
        self._options_binding_handler.remove_binding(observable._get_set_binding_handler())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        binding_state_consistent, binding_state_consistent_message = self._selected_option_binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        binding_state_consistent, binding_state_consistent_message = self._options_binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._selected_option_binding_handler.check_values_synced()
        if not values_synced:
            return False, values_synced_message
        values_synced, values_synced_message = self._options_binding_handler.check_values_synced()
        if not values_synced:
            return False, values_synced_message
        return True, "Binding system is consistent"
    
    def add(self, item: T) -> None:
        """Add an item to the options set"""
        if item not in self._options:
            self._options.add(item)
            self._options_binding_handler.notify_bindings(self._options)
            self._notify_listeners()
    
    def __str__(self) -> str:
        return f"OSO(options={self._options}, selected={self._selected_option})"
    
    def __repr__(self) -> str:
        return f"ObservableSelectionOption({self._options}, {self._selected_option})"
    
    def __len__(self) -> int:
        return len(self._options)
    
    def __contains__(self, item: T) -> bool:
        return item in self._options
    
    def __iter__(self):
        """Iterate over the options"""
        return iter(self._options)
    
    def __eq__(self, other) -> bool:
        """Compare with another selection option or observable"""
        if isinstance(other, ObservableSelectionOption):
            return (self._options == other._options and 
                   self._selected_option == other._selected_option)
        return False
    
    def __ne__(self, other) -> bool:
        """Compare with another selection option or observable"""
        return not (self == other)
    
    def __hash__(self) -> int:
        """Hash based on the current options and selected option"""
        return hash((frozenset(self._options), self._selected_option))
    
    def __bool__(self) -> bool:
        """Boolean conversion based on selected option"""
        return bool(self._selected_option)
    
    def get_observed_values(self) -> tuple[T, set[T]]:
        return (self._selected_option, self._options)
    
    def set_observed_values(self, values: tuple[T, set[T]]) -> None:    
        self.set_selected_option_and_available_options(values[0], values[1])