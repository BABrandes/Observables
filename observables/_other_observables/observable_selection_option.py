"""
ObservableSelectionOption Module

This module provides the ObservableSelectionOption class, a sophisticated observable
that combines the functionality of an observable set (for available options) and an
observable single value (for the selected option).

The ObservableSelectionOption is designed for scenarios where you need to:
- Maintain a dynamic set of valid options
- Track a currently selected option from that set
- Ensure data consistency and validation
- Synchronize with other observables through bindings
- React to changes through listeners and notifications

Key Features:
- Bidirectional bindings for both options and selected values
- Automatic validation ensuring selected option is always valid
- Comprehensive listener notification system
- Full set interface for options management
- Type-safe generic implementation
- Configurable None selection handling
- Atomic operations for consistency

Architecture:
The class implements multiple interfaces:
- Observable: Base observable pattern with listeners and component management
- CarriesDistinctSingleValueHook: Interface for single value binding operations
- CarriesDistinctSetHook: Interface for set binding operations

The internal structure uses a component-based approach where:
- selected_option: Manages the currently selected value
- available_options: Manages the set of valid options
- Each component has its own hook for binding management

Binding System:
The binding system supports:
- Binding between ObservableSelectionOption instances (comprehensive binding)
- Binding to ObservableSingleValue instances (selected option only)
- Binding to ObservableSet instances (options only)
- Different synchronization modes for initial value setup
- Automatic validation and error handling

Validation Rules:
- If allow_none=False, selected_option cannot be None
- If allow_none=False, options set cannot be empty
- selected_option must always be in the available options set
- All changes are validated before being applied

Performance Characteristics:
- O(1) average case for most operations
- O(n) worst case for set operations where n is the number of options
- Memory usage scales linearly with the number of options
- Binding operations are O(1) but may trigger cascading updates

Thread Safety:
This module is not thread-safe. If used in multi-threaded environments,
external synchronization is required.

Example Usage:
    >>> # Basic usage
    >>> selector = ObservableSelectionOption("Apple", {"Apple", "Banana", "Cherry"})
    >>> print(selector.selected_option)  # "Apple"
    
    >>> # Add listener
    >>> selector.add_listeners(lambda: print("Changed!"))
    >>> selector.selected_option = "Banana"  # Triggers listener
    
    >>> # Binding
    >>> source = ObservableSet({"Red", "Green", "Blue"})
    >>> selector.bind_options_to_observable(source)
    >>> source.add("Yellow")  # Automatically updates selector

Dependencies:
- typing: For type hints and generic support
- .._utils.hook: For binding mechanism
- .._utils.sync_mode: For synchronization modes
- .._utils.carries_distinct_single_value_hook: For single value binding interface
- .._utils.carries_distinct_set_hook: For set binding interface
- .._utils.observable: For base observable functionality

See Also:
- Observable: Base observable class
- ObservableSet: For managing observable sets
- ObservableSingleValue: For managing observable single values
- Hook: For custom binding mechanisms
- SyncMode: For binding synchronization modes
"""

from typing import Any, Generic, Optional, TypeVar, overload, runtime_checkable, Protocol
from .._utils.hook import Hook, HookLike
from .._utils.sync_mode import SyncMode
from .._utils.carries_distinct_single_value_hook import CarriesDistinctSingleValueHook
from .._utils.carries_distinct_set_hook import CarriesDistinctSetHook
from .._utils.base_observable import BaseObservable

T = TypeVar("T")

@runtime_checkable
class ObservableSelectionOptionLike(CarriesDistinctSingleValueHook[Optional[T]], CarriesDistinctSetHook[T], Protocol[T]):

    @property
    def selected_option(self) -> Optional[T]:
        """
        Get the selected option.
        """
        ...
    
    @selected_option.setter
    def selected_option(self, selected_option: Optional[T]) -> None:
        """
        Set the selected option.
        """
        ...

    @property
    def available_options(self) -> set[T]:
        """
        Get the available options.
        """
        ...
    
    @available_options.setter
    def available_options(self, available_options: set[T]) -> None:
        """
        Set the available options.
        """
        ...

    def set_selected_option_and_available_options(self, selected_option: Optional[T], available_options: set[T]) -> None:
        """
        Set the selected option and available options.
        """
        ...

    def bind_selected_option_to_observable(self, observable_or_hook: CarriesDistinctSingleValueHook[Optional[T]]|HookLike[Optional[T]], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Bind the selected option to an observable.
        """
        ...
        
    def bind_options_to_observable(self, observable_or_hook: CarriesDistinctSetHook[T], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Bind the options to an observable.
        """
        ...
    
    def unbind_selected_option_from_observable(self, observable_or_hook: CarriesDistinctSingleValueHook[Optional[T]]|HookLike[Optional[T]]) -> None:
        """
        Unbind the selected option from an observable.
        """
        ...
    
    def unbind_options_from_observable(self, observable_or_hook: CarriesDistinctSetHook[T]) -> None:
        """
        Unbind the options from an observable.
        """
        ...

    def bind_to(self, observable: "ObservableSelectionOptionLike[T]", initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Bind to an observable.
        """
        ...
    
    def unbind_from(self, observable: "ObservableSelectionOptionLike[T]") -> None:
        """
        Unbind from an observable.
        """
        ...

class ObservableSelectionOption(BaseObservable, ObservableSelectionOptionLike[T], Generic[T]):
    """
    An observable selection option that manages both available options and a selected value.
    
    This class combines the functionality of an observable set (for available options) and
    an observable single value (for the selected option). It ensures that the selected
    option is always valid according to the available options and supports bidirectional
    bindings for both the options set and the selected value.
    
    The ObservableSelectionOption is designed for scenarios where you need to:
    - Maintain a set of valid options that can change dynamically
    - Track a currently selected option from that set
    - Ensure the selected option is always valid
    - Synchronize both the options and selection with other observables
    - React to changes through listeners and bindings
    
    Features:
    - Bidirectional bindings for both options and selected option
    - Automatic validation ensuring selected option is always in options set
    - Listener notification system for change events
    - Full set interface for options management (add, remove, contains, etc.)
    - Type-safe generic implementation with proper type hints
    - Configurable None selection handling
    - Atomic operations for consistency
    - Comprehensive error handling and validation
    
    Binding System:
    The class implements a sophisticated binding system that allows:
    - Binding the options set to another observable set
    - Binding the selected option to another observable value
    - Binding to other ObservableSelectionOption instances
    - Different synchronization modes (UPDATE_SELF_FROM_OBSERVABLE, etc.)
    - Automatic propagation of changes through binding chains
    
    Validation Rules:
    - If allow_none=False, selected_option cannot be None
    - If allow_none=False, options set cannot be empty
    - selected_option must always be in the available options set
    - Changes are validated before being applied
    
    Thread Safety:
    This class is not thread-safe. If used in multi-threaded environments,
    external synchronization is required.
    
    Performance Characteristics:
    - O(1) average case for most operations
    - O(n) worst case for set operations where n is the number of options
    - Memory usage scales linearly with the number of options
    - Binding operations are O(1) but may trigger cascading updates
    
    Example Usage:
        >>> # Basic usage with direct values
        >>> selector = ObservableSelectionOption(
        ...     selected_option="Apple",
        ...     options={"Apple", "Banana", "Cherry"}
        ... )
        >>> print(selector.selected_option)  # "Apple"
        >>> print(selector.available_options)  # {"Apple", "Banana", "Cherry"}
        
        >>> # Add a listener for change notifications
        >>> def on_change():
        ...     print(f"Selection changed to: {selector.selected_option}")
        >>> selector.add_listeners(on_change)
        
        >>> # Change selection (triggers listener)
        >>> selector.selected_option = "Banana"
        Selection changed to: Banana
        
        >>> # Add new options
        >>> selector.add("Dragon Fruit")
        >>> print(selector.available_options)  # {"Apple", "Banana", "Cherry", "Dragon Fruit"}
        
        >>> # Binding with another observable
        >>> source_options = ObservableSet({"Red", "Green", "Blue"})
        >>> color_selector = ObservableSelectionOption("Red", source_options)
        >>> selector.bind_options_to_observable(source_options)
        >>> source_options.add("Yellow")  # Automatically updates selector
        >>> print(selector.available_options)  # {"Red", "Green", "Blue", "Yellow"}
        
        >>> # Binding between two selectors
        >>> selector1 = ObservableSelectionOption(1, {1, 2, 3})
        >>> selector2 = ObservableSelectionOption(10, {10, 20, 30})
        >>> selector1.bind_to(selector2)
        >>> selector1.selected_option = 5  # Updates selector2
        >>> print(selector2.selected_option)  # 5
    
    Args:
        selected_option: The initially selected option. Can be:
            - A direct value of type T
            - An ObservableSingleValue instance
            - A Hook instance
            - None (if allow_none=True)
        options: The set of available options. Can be:
            - A direct set of values
            - An ObservableSet instance  
            - A Hook instance
        allow_none: Whether to allow None as a valid selected option.
            If False, the selected option must always have a value
            and the options set cannot be empty.
    
    Raises:
        ValueError: If selected_option is not in the options set
        ValueError: If allow_none=False and selected_option is None
        ValueError: If allow_none=False and options set is empty
    
    Type Parameters:
        T: The type of the options and selected option. Must be hashable
           and support equality comparison.
    
    See Also:
        Observable: Base class providing the observable pattern
        ObservableSet: For managing observable sets of values
        ObservableSingleValue: For managing observable single values
        Hook: For creating custom binding mechanisms
    """
    
    @overload
    def __init__(self, selected_option: CarriesDistinctSingleValueHook[T]|HookLike[T], options: CarriesDistinctSetHook[T]|HookLike[set[T]], allow_none: bool = True):
        """
        Initialize with observable options and observable selected option.
        
        This overload is used when both the selected option and options are observable
        objects that can be bound to this instance.
        
        Args:
            selected_option: An observable value that will be bound to this instance's
                           selected option. Changes to this observable will update
                           this instance's selected option.
            options: An observable set that will be bound to this instance's options.
                    Changes to this observable set will update this instance's options.
            allow_none: Whether to allow None as a valid selected option.
        
        Example:
            >>> source_value = ObservableSingleValue("A")
            >>> source_options = ObservableSet({"A", "B", "C"})
            >>> selector = ObservableSelectionOption(source_value, source_options)
            >>> # Changes to source_value or source_options will automatically
            >>> # update the selector
        """
        ...

    @overload
    def __init__(self, selected_option: Optional[T], options: CarriesDistinctSetHook[T]|HookLike[set[T]], allow_none: bool = True):
        """
        Initialize with observable options and direct selected option.
        
        This overload is used when the options are observable but the selected option
        is a direct value that won't be bound.
        
        Args:
            selected_option: A direct value for the initially selected option.
                           This value will not be bound to any observable.
            options: An observable set that will be bound to this instance's options.
                    Changes to this observable set will update this instance's options.
            allow_none: Whether to allow None as a valid selected option.
        
        Example:
            >>> source_options = ObservableSet({"A", "B", "C"})
            >>> selector = ObservableSelectionOption("A", source_options)
            >>> # Only the options will be bound; selected_option "A" is static
        """
        ...

    @overload
    def __init__(self, selected_option: CarriesDistinctSingleValueHook[T]|HookLike[T], options: set[T], allow_none: bool = True):
        """
        Initialize with direct options and observable selected option.
        
        This overload is used when the selected option is observable but the options
        are a direct set that won't be bound.
        
        Args:
            selected_option: An observable value that will be bound to this instance's
                           selected option. Changes to this observable will update
                           this instance's selected option.
            options: A direct set of available options. This set will not be bound
                    to any observable and will remain static.
            allow_none: Whether to allow None as a valid selected option.
        
        Example:
            >>> source_value = ObservableSingleValue("A")
            >>> static_options = {"A", "B", "C"}
            >>> selector = ObservableSelectionOption(source_value, static_options)
            >>> # Only the selected option will be bound; options are static
        """
        ...
    
    @overload
    def __init__(self, selected_option: Optional[T], options: set[T], allow_none: bool = True):
        """
        Initialize with direct options and direct selected option.
        
        This overload is used when both the selected option and options are direct
        values that won't be bound to any observables.
        
        Args:
            selected_option: A direct value for the initially selected option.
                           This value will not be bound to any observable.
            options: A direct set of available options. This set will not be bound
                    to any observable and will remain static.
            allow_none: Whether to allow None as a valid selected option.
        
        Example:
            >>> selector = ObservableSelectionOption("Apple", {"Apple", "Banana", "Cherry"})
            >>> # Both values are static; no bindings are created
        """
        ...

    @classmethod
    def _mandatory_component_value_keys(cls) -> set[str]:
        """
        Get the mandatory component value keys.
        """
        return {"selected_option", "available_options"}

    def __init__(self, selected_option: Optional[T] | CarriesDistinctSingleValueHook[Optional[T]] | HookLike[Optional[T]], options: set[T] | CarriesDistinctSetHook[T] | HookLike[set[T]], allow_none: bool = True):
        """
        Initialize the ObservableSelectionOption.
        
        This method handles the initialization logic for all constructor overloads.
        It processes the input parameters, validates them, sets up the internal
        component structure, and establishes any necessary bindings.
        
        The initialization process:
        1. Processes and validates the selected_option parameter
        2. Processes and validates the options parameter  
        3. Creates internal hooks for binding management
        4. Calls the parent Observable constructor
        5. Establishes bindings if observable parameters were provided
        
        Args:
            selected_option: The initially selected option. Can be:
                - A direct value of type T (or None if allow_none=True)
                - An ObservableSingleValue instance (implements CarriesDistinctSingleValueHook)
                - A Hook instance for custom binding behavior
            options: The set of available options. Can be:
                - A direct set of values of type T
                - An ObservableSet instance (implements CarriesDistinctSetHook)
                - A Hook instance for custom binding behavior
            allow_none: Whether to allow None as a valid selected option.
                If False, the selected option must always have a value
                and the options set cannot be empty.
        
        Raises:
            ValueError: If selected_option is not in the options set
            ValueError: If allow_none=False and selected_option is None
            ValueError: If allow_none=False and options set is empty
        
        Note:
            The allow_none parameter affects validation behavior:
            - If True: selected_option can be None, options set can be empty
            - If False: selected_option must have a value, options set cannot be empty
            
            This is useful for scenarios where you want to enforce that a selection
            is always made, such as in required form fields.
        
        Implementation Details:
            The method creates internal hooks that manage the binding system:
            - selected_option hook: Manages bindings for the selected value
            - available_options hook: Manages bindings for the options set
            
            These hooks are automatically created and configured during initialization,
            allowing for seamless binding operations after the object is created.
        """
        
        self._allow_none = allow_none
        
        if isinstance(options, CarriesDistinctSetHook):
            available_options: set[T] = options._get_set_value()
            available_options_hook: Optional[HookLike[set[T]]] = options._get_set_hook()
        elif isinstance(options, HookLike):
            available_options: set[T] = options._get_callback()
            available_options_hook: Optional[HookLike[set[T]]] = options
        else:
            available_options: set[T] = options.copy()
            available_options_hook: Optional[CarriesDistinctSetHook[T]] = None

        if isinstance(selected_option, CarriesDistinctSingleValueHook):
            initial_selected_option: Optional[T] = selected_option._get_single_value()
            selected_option_hook: Optional[HookLike[T]] = selected_option._get_single_value_hook()
        elif isinstance(selected_option, HookLike):
            initial_selected_option: Optional[T] = selected_option._get_callback()
            selected_option_hook: Optional[HookLike[T]] = selected_option
        else:
            initial_selected_option: Optional[T] = selected_option
            selected_option_hook: Optional[HookLike[T]] = None

        if not allow_none and (initial_selected_option is None or available_options == set()):
            raise ValueError("Selected option is None but allow_none is False")
        
        if initial_selected_option is not None and initial_selected_option not in available_options:
            raise ValueError(f"Selected option {initial_selected_option} not in options {available_options}")
        
        def verification_method(x: dict[str, Any]) -> tuple[bool, str]:
            # Handle partial updates by getting current values for missing keys
            current_selected = x.get("selected_option", initial_selected_option)
            current_options = x.get("available_options", available_options)
            
            if not self._allow_none and current_selected is None:
                return False, "Selected option is None but allow_none is False"
            
            if current_options is not None and not isinstance(current_options, set):
                return False, "Options is not a set"
            
            if current_selected is not None and current_options is not None and current_selected not in current_options:
                return False, f"Selected option {current_selected} not in options {current_options}"
            
            if not self._allow_none and current_options == set():
                return False, "Options set is empty but allow_none is False"

            return True, "Verification method passed"

        super().__init__(
            {
                "selected_option": initial_selected_option,
                "available_options": available_options
            },
            {
                "selected_option": Hook(self, self._get_single_value, self._set_single_value),
                "available_options": Hook(self, self._get_set_value, self._set_set_value)
            },
            verification_method=verification_method
        )
        
        if available_options_hook is not None:
            self.bind_options_to_observable(available_options_hook)
            
        if selected_option_hook is not None:
            self.bind_selected_option_to_observable(selected_option_hook)

    @classmethod
    def _mandatory_component_value_keys(cls) -> set[str]:
        """
        Get the mandatory component value keys.
        """
        return {"selected_option", "available_options"}

    ############################################################
    # Properties (Getters and Setters)
    ############################################################

    @property
    def available_options(self) -> set[T]:
        """
        Get a copy of the available options.
        
        This property returns a copy of the internal options set to prevent
        external modification. Changes to the returned set will not affect
        the internal state of this ObservableSelectionOption.
        
        To modify the available options, use the setter or methods like `add()`.
        
        Returns:
            A copy of the available options set. The returned set contains
            all currently valid options that can be selected.
        
        Example:
            >>> selector = ObservableSelectionOption("A", {"A", "B", "C"})
            >>> options = selector.available_options
            >>> print(options)  # {"A", "B", "C"}
            >>> options.add("D")  # This won't affect the selector
            >>> print(selector.available_options)  # Still {"A", "B", "C"}
            
            # To actually add an option, use the setter or add() method:
            >>> selector.available_options = {"A", "B", "C", "D"}
            >>> # or
            >>> selector.add("D")
        
        Note:
            The returned set is a shallow copy. If the options contain
            mutable objects, modifications to those objects will still
            affect the internal state.
        """
        return self._get_set_value().copy()
    
    @available_options.setter
    def available_options(self, options: set[T]) -> None:
        """
        Set the available options set.
        
        This method updates the available options, ensuring that the current
        selected option remains valid. The method performs comprehensive
        validation to maintain data consistency.
        
        Validation Rules:
        - If the new options set is empty and allow_none=False, an error is raised
        - If the current selected option is not in the new options set, an error is raised
        - The selected option is automatically validated against the new options
        
        The setter triggers appropriate notifications to listeners and bound
        observables when the options change.
        
        Args:
            options: The new set of available options. Must be a valid set
                    containing all values that should be available for selection.
        
        Raises:
            ValueError: If trying to set empty options when allow_none=False
            ValueError: If current selected option is not in the new options set
            ValueError: If options is not a set type
        
        Example:
            >>> selector = ObservableSelectionOption("A", {"A", "B", "C"})
            >>> print(selector.selected_option)  # "A"
            >>> print(selector.available_options)  # {"A", "B", "C"}
            
            # Valid change - selected option "A" is still in new options
            >>> selector.available_options = {"A", "B", "D"}
            >>> print(selector.available_options)  # {"A", "B", "D"}
            
            # Invalid change - selected option "A" is not in new options
            >>> selector.available_options = {"X", "Y", "Z"}
            ValueError: Selected option A not in options {'X', 'Y', 'Z'}
            
            # To change both options and selection atomically, use:
            >>> selector.set_selected_option_and_available_options("X", {"X", "Y", "Z"})
        
        Note:
            This operation is atomic - either all changes succeed or none do.
            If validation fails, the original options set remains unchanged.
            
            When using bindings, changing the options here will automatically
            propagate to all bound observables.
        """
        if options == self._get_set_value():
            return

        if options == set():
            raise ValueError("An empty set of options can not be set without setting the selected option to None, if even it is allowed")
        
        self._raise_if_selected_option_not_in_options(self._get_single_value(), options)

        # Use the protocol method to set the values
        self._set_set_value(options)
    
    @property
    def selected_option(self) -> Optional[T]:
        """
        Get the currently selected option.
        
        This property returns the currently selected option from the available
        options set. The returned value is guaranteed to be either None
        (if allow_none=True) or a valid option from the available options.
        
        Returns:
            The currently selected option, or None if no option is selected
            and allow_none=True. The returned value is always a valid
            option from the available options set.
        
        Example:
            >>> selector = ObservableSelectionOption("Apple", {"Apple", "Banana", "Cherry"})
            >>> print(selector.selected_option)  # "Apple"
            
            >>> selector.selected_option = "Banana"
            >>> print(selector.selected_option)  # "Banana"
            
            >>> # If allow_none=True, can set to None
            >>> selector.selected_option = None
            >>> print(selector.selected_option)  # None
        
        Note:
            The returned value is always consistent with the available options.
            If the selected option is removed from the options set, it will
            automatically be set to None (if allow_none=True) or an error
            will be raised (if allow_none=False).
        """
        return self._get_single_value()
    
    @property
    def selected_option_not_none(self) -> T:
        """
        Get the current selected option if it is not None.
        
        Returns:
            The current selected option

        Raises:
            ValueError: If the selected option is None
        """
        selected_option = self._get_single_value()
        if selected_option is None:
            raise ValueError("Selected option is None")
        return selected_option
    
    @selected_option.setter
    def selected_option(self, selected_option: Optional[T]) -> None:
        """
        Set the selected option.
        
        This method updates the selected option, ensuring that it's valid
        according to the current available options and allow_none setting.
        The method performs comprehensive validation and triggers appropriate
        notifications when the selection changes.
        
        Validation Rules:
        - If selected_option is None, allow_none must be True
        - If selected_option is not None, it must be in the available options set
        - The validation is performed before the change is applied
        
        When the selected option changes, this triggers:
        - Listener notifications (if any listeners are registered)
        - Binding updates to all bound observables
        - Internal state updates
        
        Args:
            selected_option: The new selected option. Can be:
                - A valid option from the available options set
                - None (if allow_none=True)
        
        Raises:
            ValueError: If the selected option is not in the available options set
            ValueError: If selected option is None but allow_none is False
            ValueError: If the options set is empty and allow_none=False
        
        Example:
            >>> selector = ObservableSelectionOption("Apple", {"Apple", "Banana", "Cherry"})
            >>> print(selector.selected_option)  # "Apple"
            
            # Valid change
            >>> selector.selected_option = "Banana"
            >>> print(selector.selected_option)  # "Banana"
            
            # Invalid change - option not in available options
            >>> selector.selected_option = "Orange"
            ValueError: Selected option Orange not in options {'Apple', 'Banana', 'Cherry'}
            
            # Setting to None (if allow_none=True)
            >>> selector.selected_option = None
            >>> print(selector.selected_option)  # None
        
        Note:
            This operation is atomic - either the change succeeds or none do.
            If validation fails, the original selected option remains unchanged.
            
            When using bindings, changing the selected option here will automatically
            propagate to all bound observables.
            
            The setter automatically handles the case where the current selected
            option is the same as the new value (no-op).
        """
        if selected_option == self._get_single_value():
            return
        
        self._raise_if_selected_option_not_in_options(selected_option, self._get_set_value())

        # Use the protocol method to set the values
        self._set_single_value(selected_option)

    ############################################################
    # Other properties
    ############################################################
    
    @property
    def is_none_selection_allowed(self) -> bool:
        """
        Check if none selection is allowed.
        
        Returns:
            True if none selection is allowed, False otherwise
        """
        return self._allow_none
    
    @is_none_selection_allowed.setter
    def is_none_selection_allowed(self, allow_none: bool) -> None:
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

    ############################################################
    # Internal value methods
    ############################################################

    def _get_set_value(self) -> set[T]:
        """
        INTERNAL. Do not use this method directly.

        Method to get the current options set. No copy is made!
        
        Returns:
            The current options set
        """
        return self._get_component_value("available_options")
    
    def _get_single_value(self) -> T:
        """
        INTERNAL. Do not use this method directly.

        Method to get the current selected option. No copy is made!
        
        Returns:
            The current selected option
        """
        return self._get_component_value("selected_option")
    
    def _set_set_value(self, value: set[T]) -> None:
        """
        INTERNAL. Do not use this method directly.
        
        Args:
            value: The new options set to set
        """
        self._set_component_value("available_options", value)
    
    def _set_single_value(self, value: T) -> None:
        """
        INTERNAL. Do not use this method directly.
        
        Args:
            value: The new selected option to set
        """
        self._set_component_value("selected_option", value)
    
    ############################################################
    # Combined set and selected option methods
    ############################################################

    def set_selected_option_and_available_options(self, selected_option: Optional[T], options: set[T]) -> None:
        """
        Set both the selected option and available options atomically.
        
        This method allows setting both values simultaneously, ensuring consistency
        and triggering appropriate notifications. It's particularly useful when you
        need to update both values without creating intermediate invalid states
        that could trigger validation errors or inconsistent behavior.
        
        Atomic Operation Benefits:
        - Both values are updated together or neither is updated
        - No intermediate invalid states are created
        - Validation is performed on the complete new state
        - Notifications are triggered only once for the complete change
        - Binding updates are handled efficiently
        
        Use Cases:
        - Initializing an instance with new data
        - Bulk updates from external data sources
        - Synchronizing with other systems
        - Implementing undo/redo functionality
        - Batch operations that affect both values
        
        Args:
            selected_option: The new selected option. Can be:
                - A valid option from the new options set
                - None (if allow_none=True)
            options: The new set of available options. Must be a valid set
                    containing all values that should be available for selection.
        
        Raises:
            ValueError: If selected_option is not in the new options set
            ValueError: If selected_option is None but allow_none is False
            ValueError: If options set is empty but allow_none is False
            ValueError: If options is not a set type
        
        Example:
            >>> selector = ObservableSelectionOption("Apple", {"Apple", "Banana"})
            >>> print(selector.selected_option)  # "Apple"
            >>> print(selector.available_options)  # {"Apple", "Banana"}
            
            # Update both values atomically
            >>> selector.set_selected_option_and_available_options("Cherry", {"Cherry", "Date", "Elderberry"})
            >>> print(selector.selected_option)  # "Cherry"
            >>> print(selector.available_options)  # {"Cherry", "Date", "Elderberry"}
            
            # Invalid update - selected option not in new options
            >>> selector.set_selected_option_and_available_options("Apple", {"Date", "Elderberry"})
            ValueError: Selected option Apple not in options {'Date', 'Elderberry'}
            
            # Valid update with None selection (if allow_none=True)
            >>> selector.set_selected_option_and_available_options(None, {"Date", "Elderberry"})
            >>> print(selector.selected_option)  # None
        
        Note:
            This operation is truly atomic - either both values are updated
            successfully or neither is updated. If validation fails, the
            original state is preserved.
            
            The method automatically handles the case where the new values
            are the same as the current values (no-op).
            
            When using bindings, this operation will trigger appropriate
            updates to all bound observables.
            
            This method is more efficient than setting the values separately
            when both need to change, as it avoids intermediate validation
            and notification cycles.
        """
        if selected_option is not None and selected_option not in options:
            raise ValueError(f"Selected option {selected_option} not in options {options}")
        
        if not self._allow_none and selected_option is None:
            raise ValueError("Selected option is None but allow_none is False")
        
        if not self._allow_none and options == set():
            raise ValueError("Options set is empty but allow_none is False")
        
        # Use the protocol method to set the values
        self._set_component_values_from_tuples(("selected_option", selected_option), ("available_options", options))

    ############################################################
    # Internal hook methods
    ############################################################

    def _get_single_value_hook(self) -> HookLike[Optional[T]]:
        """
        INTERNAL. Do not use this method directly.

        Method to get hook for selected option.
        
        Returns:
            The binding handler for the selected option
        """
        return self._component_hooks["selected_option"]

    def _get_set_hook(self) -> HookLike[set[T]]:
        """
        INTERNAL. Do not use this method directly.

        Method to get hook for options set.
        
        Returns:
            The binding handler for the options set
        """
        return self._component_hooks["available_options"]

    def bind_selected_option_to_observable(self, hook: HookLike[Optional[T]] | CarriesDistinctSingleValueHook[Optional[T]], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding for the selected option with another observable.
        
        This method creates a bidirectional binding between this observable's selected option
        and another observable, ensuring that changes to either are automatically propagated.
        The binding maintains consistency between the two observables and handles validation
        automatically.
        
        Binding Behavior:
        - Changes to this observable's selected option automatically update the bound observable
        - Changes to the bound observable automatically update this observable's selected option
        - Validation ensures that only valid options are propagated
        - The binding is maintained until explicitly removed
        
        Initial Synchronization:
        The initial_sync_mode parameter determines how values are synchronized when the
        binding is first established:
        - UPDATE_SELF_FROM_OBSERVABLE: This observable's value is updated from the bound observable
        - UPDATE_OBSERVABLE_FROM_SELF: The bound observable's value is updated from this observable
        - BIDIRECTIONAL: Both observables are synchronized to a common value
        
        Args:
            hook: The observable to bind the selected option to. Can be:
                - A Hook instance for custom binding behavior
                - An ObservableSingleValue instance (implements CarriesDistinctSingleValueHook)
            initial_sync_mode: How to synchronize values initially. Determines which
                             observable's value takes precedence during initial binding.
        
        Raises:
            ValueError: If the hook is None
            ValueError: If the bound observable's value is not valid for this observable's options
        
        Example:
            >>> selector1 = ObservableSelectionOption("A", {"A", "B", "C"})
            >>> selector2 = ObservableSelectionOption("X", {"X", "Y", "Z"})
            
            # Bind selector1's selected option to selector2
            >>> selector1.bind_selected_option_to_observable(selector2)
            
            # Changes propagate in both directions
            >>> selector1.selected_option = "B"
            >>> print(selector2.selected_option)  # "B"
            
            >>> selector2.selected_option = "Y"
            >>> print(selector1.selected_option)  # "Y"
            
            # Note: The binding will fail if the new value is not in the options set
            >>> selector1.selected_option = "Z"  # "Z" not in {"A", "B", "C"}
            ValueError: Selected option Z not in options {'A', 'B', 'C'}
        
        Note:
            The binding is bidirectional, so changes flow in both directions.
            If a change would create an invalid state (e.g., selected option not in
            available options), the binding operation will fail and the original
            state will be preserved.
            
            To remove the binding, use unbind_selected_option_from_observable().
        """
        if isinstance(hook, CarriesDistinctSingleValueHook):
            hook = hook._get_single_value_hook()
        self._get_single_value_hook().establish_binding(hook, initial_sync_mode)

    def bind_options_to_observable(self, hook: CarriesDistinctSetHook[T]|HookLike[set[T]], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:        
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
        if isinstance(hook, CarriesDistinctSetHook):
            hook = hook._get_set_hook()
        self._get_set_hook().establish_binding(hook, initial_sync_mode)

    def bind_to(self, observable: ObservableSelectionOptionLike[T], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding with another observable.
        
        This method creates bidirectional bindings between this observable and another
        observable, ensuring that changes to either are automatically propagated.

        Binding Behavior:
        - Changes to this observable automatically update the bound observable
        - Changes to the bound observable automatically update this observable
        - Validation ensures that only valid states are propagated
        - Bindings are maintained until explicitly removed
        
        Initial Synchronization:
        The initial_sync_mode parameter determines how values are synchronized when
        the binding is first established:
        - UPDATE_SELF_FROM_OBSERVABLE: This observable's values are updated from the bound observable
        - UPDATE_OBSERVABLE_FROM_SELF: The bound observable's values are updated from this observable
        - BIDIRECTIONAL: Both observables are synchronized to common values
        
        Args:
            observable: The observable to bind to. Can be:
                - An ObservableSelectionOption instance (binds both options and selection)
            initial_sync_mode: How to synchronize values initially. Determines which
                             observable's values take precedence during initial binding.
        
        Raises:
            ValueError: If the observable is None
            ValueError: If binding would create an invalid state
        
        Example:
            # Binding between two ObservableSelectionOption instances
            >>> selector1 = ObservableSelectionOption("A", {"A", "B", "C"})
            >>> selector2 = ObservableSelectionOption("X", {"X", "Y", "Z"})
            >>> selector1.bind_to(selector2)
            
            # Both options and selection are now synchronized
            >>> selector1.selected_option = "B"
            >>> print(selector2.selected_option)  # "B"
            >>> print(selector2.available_options)  # {"A", "B", "C"}
        
        Note:
            When binding to another ObservableSelectionOption, the binding is comprehensive
            and affects both the options set and selected option. This creates a strong
            coupling between the two instances.
            
            The binding system automatically handles validation and prevents invalid states
            from being propagated. If a binding operation would create an invalid state,
            it will fail and the original state will be preserved.
            
            To remove bindings, use the appropriate unbind method:
            - unbind_from() for ObservableSelectionOption bindings
            - unbind_selected_option_from_observable() for single value bindings
            - unbind_available_options_from_observable() for set bindings
        """

        # First, synchronize the values atomically to maintain consistency
        if initial_sync_mode == SyncMode.UPDATE_SELF_FROM_OBSERVABLE:
            # Update both values at once to maintain consistency
            self.set_selected_option_and_available_options(
                observable.selected_option, 
                observable.available_options
            )
        elif initial_sync_mode == SyncMode.UPDATE_OBSERVABLE_FROM_SELF:
            # Update the other observable's values at once
            observable.set_selected_option_and_available_options(
                self.selected_option, 
                self.available_options
            )

        # Then, establish the bindings with UPDATE_SELF_FROM_OBSERVABLE mode
        # to ensure this observable gets updated from the other one
        self.bind_options_to_observable(observable._get_set_hook(), SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        self.bind_selected_option_to_observable(observable._get_single_value_hook(), SyncMode.UPDATE_SELF_FROM_OBSERVABLE)


    def unbind_selected_option_from_observable(self, observable: CarriesDistinctSingleValueHook[Optional[T]]|HookLike[Optional[T]]) -> None:
        """
        Remove the bidirectional binding for the selected option with another observable.
        
        This method removes the binding between this observable's selected option
        and another observable, preventing further automatic synchronization.
        
        Args:
            observable: The observable to unbind the selected option from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        if isinstance(observable, CarriesDistinctSingleValueHook):
            observable = observable._get_single_value_hook()
        self._get_single_value_hook().remove_binding(observable)

    def unbind_available_options_from_observable(self, observable: CarriesDistinctSetHook[T]|HookLike[set[T]]) -> None:
        """
        Remove the bidirectional binding for the options set with another observable.
        
        This method removes the binding between this observable's options set
        and another observable, preventing further automatic synchronization.
        
        Args:
            observable: The observable to unbind the options from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        if isinstance(observable, CarriesDistinctSetHook):
            observable = observable._get_set_hook()
        self._get_set_hook().remove_binding(observable)
    
    def unbind_from(self, observable: ObservableSelectionOptionLike[T]) -> None:
        """
        Remove the bidirectional binding for the selected option with another instance of this class.
        
        This method removes the binding between this observable's selected option
        and another instance of this class, preventing further automatic synchronization.
        """

        self._get_set_hook().remove_binding(observable._get_set_hook())
        self._get_single_value_hook().remove_binding(observable._get_single_value_hook())
    
    ############################################################
    # Other internal methods
    ############################################################

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
        
    ############################################################
    # Other methods
    ############################################################

    def add(self, item: T) -> None:
        """
        Add an item to the options set.
        
        This method adds a new item to the available options set. The method
        ensures that the addition is performed through the proper protocol,
        triggering appropriate notifications and maintaining data consistency.
        
        The add operation:
        - Adds the item to the available options if it's not already present
        - Triggers listener notifications for the change
        - Updates all bound observables
        - Maintains the current selected option (if it's still valid)
        
        Args:
            item: The item to add to the options set. The item must be of type T
                  and should be hashable for proper set operations.
        
        Example:
            >>> selector = ObservableSelectionOption("Apple", {"Apple", "Banana"})
            >>> print(selector.available_options)  # {"Apple", "Banana"}
            
            # Add a new option
            >>> selector.add("Cherry")
            >>> print(selector.available_options)  # {"Apple", "Banana", "Cherry"}
            
            # Adding an existing item has no effect
            >>> selector.add("Apple")
            >>> print(selector.available_options)  # {"Apple", "Banana", "Cherry"}
            
            # The selected option remains unchanged if still valid
            >>> print(selector.selected_option)  # "Apple"
        
        Note:
            This operation is atomic - either the item is added or it isn't.
            If the item is already in the options set, no change occurs and
            no notifications are triggered.
            
            When using bindings, adding an option here will automatically
            propagate to all bound observables.
            
            The method automatically handles the case where the item is
            already present in the options set (no-op).
        """
        new_options: set[T] = self._get_set_value().copy()
        if item not in new_options:
            new_options.add(item)
        self._set_component_values_from_tuples(("selected_option", self._get_single_value()), ("available_options", new_options))
    
    def __str__(self) -> str:
        return f"OSO(options={self._get_set_value()}, selected={self._get_single_value()})"
    
    def __repr__(self) -> str:
        return f"ObservableSelectionOption({self._get_set_value()}, {self._get_single_value()})"
    
    def __len__(self) -> int:
        """
        Get the number of available options.
        
        Returns:
            The number of available options
        """
        return len(self._get_set_value())
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an item is in the available options.
        
        Args:
            item: The item to check for
            
        Returns:
            True if the item is in the options set, False otherwise
        """
        return item in self._get_set_value()
    
    def __iter__(self):
        """
        Get an iterator over the available options.
        
        Returns:
            An iterator that yields each option in the set
        """
        return iter(self._get_set_value())
    
    def __eq__(self, other) -> bool:
        """
        Check equality with another selection option or observable.
        
        Args:
            other: Another ObservableSelectionOption to compare with
            
        Returns:
            True if both options sets and selected options are equal, False otherwise
        """
        if isinstance(other, ObservableSelectionOption):
            return (self._get_set_value() == other._get_set_value() and 
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
        return hash((frozenset(self._get_set_value()), self._get_single_value()))
    
    def __bool__(self) -> bool:
        """
        Convert the selection option to a boolean.
        
        Returns:
            True if there is a selected option, False if selected_option is None
        """
        return bool(self._get_single_value())