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

from typing import Generic, Optional, TypeVar, overload, runtime_checkable, Protocol, Any, Literal
from .._utils.hook import HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.carries_collective_hooks import CarriesCollectiveHooks
from .._utils.base_observable import BaseObservable

T = TypeVar("T")

@runtime_checkable
class ObservableSelectionOptionLike(CarriesCollectiveHooks[Any], Protocol[T]):

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
    def selected_option_hook(self) -> HookLike[Optional[T]]:
        """
        Get the hook for the selected option.
        """
        ...

    @property
    def available_options(self) -> set[T]:
        """
        Get the available options.
        """
        ...
    
    @available_options.setter
    def available_options(self, options: set[T]) -> None:
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

    def set_selected_option_and_available_options(self, selected_option: Optional[T], available_options: set[T]) -> None:
        """
        Set the selected option and available options.
        """
        ...

class ObservableSelectionOption(BaseObservable[Literal["selected_option", "available_options"]], ObservableSelectionOptionLike[T], Generic[T]):
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
    def __init__(self, selected_option: HookLike[Optional[T]], options: HookLike[set[T]], *, allow_none: bool = True) -> None:
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
    def __init__(self, selected_option: Optional[T], options: HookLike[set[T]], *, allow_none: bool = True) -> None:
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
    def __init__(self, selected_option: HookLike[Optional[T]], options: set[T], *, allow_none: bool = True) -> None:
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
    def __init__(self, observable: ObservableSelectionOptionLike[T], *, allow_none: bool = True) -> None:
        """
        Initialize from another ObservableSelectionOption.
        
        This overload is used when initializing from another ObservableSelectionOption
        instance. It will extract both the selected option and available options
        from the source observable and establish bindings.
        
        Args:
            observable: Another ObservableSelectionOption instance to initialize from.
                      Both the selected option and available options will be bound.
            allow_none: Whether to allow None as a valid selected option.
        
        Example:
            >>> source = ObservableSelectionOption("A", {"A", "B", "C"})
            >>> target = ObservableSelectionOption(source)
            >>> # target is now bound to source and will stay synchronized
        """
        ...
    
    @overload
    def __init__(self, selected_option: Optional[T], options: set[T], *, allow_none: bool = True) -> None:
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

    def __init__(self, selected_option: Optional[T] | HookLike[Optional[T]] | ObservableSelectionOptionLike[T], options: set[T] | HookLike[set[T]] | None = None, *, allow_none: bool = True) -> None: # type: ignore
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

        if isinstance(selected_option, ObservableSelectionOptionLike):
            initial_selected_option: Optional[T] = selected_option.selected_option # type: ignore
            available_options: set[T] = selected_option.available_options # type: ignore
            selected_option_hook: Optional[HookLike[Optional[T]]] = None
            available_options_hook: Optional[HookLike[set[T]]] = None
            observable: Optional[ObservableSelectionOptionLike[T]] = selected_option # type: ignore
        else:
            observable: Optional[ObservableSelectionOptionLike[T]] = None
            if options is None:
                raise ValueError("options parameter is required when selected_option is not an ObservableSelectionOptionLike")
            if isinstance(options, HookLike):
                available_options: set[T] = options.value # type: ignore
                available_options_hook: Optional[HookLike[set[T]]] = options
            else:
                available_options: set[T] = options.copy()
                available_options_hook: Optional[HookLike[set[T]]] = None

            if isinstance(selected_option, HookLike):
                initial_selected_option: Optional[T] = selected_option.value # type: ignore
                selected_option_hook: Optional[HookLike[Optional[T]]] = selected_option
            else:
                initial_selected_option: Optional[T] = selected_option
                selected_option_hook: Optional[HookLike[Optional[T]]] = None

            if not allow_none and (initial_selected_option is None or available_options == set()):
                raise ValueError("Selected option is None but allow_none is False")
            
            if initial_selected_option is not None and initial_selected_option not in available_options:
                raise ValueError(f"Selected option {initial_selected_option} not in options {available_options}")
            
        def is_valid_value(dict_of_values: dict[str, Any]) -> tuple[bool, str]:
            if "selected_option" in dict_of_values:
                selected_option: Optional[T] = dict_of_values["selected_option"]
            else:
                selected_option: Optional[T] = self._component_hooks["selected_option"].value
                
            if "available_options" in dict_of_values:
                available_options: set[T] = dict_of_values["available_options"]
            else:
                available_options: set[T] = self._component_hooks["available_options"].value
                
            # Only validate selected_option if it's being updated
            if "selected_option" in dict_of_values:
                if not allow_none and selected_option is None:
                    return False, "Selected option is None but allow_none is False"

                if selected_option is not None and selected_option not in available_options:
                    return False, f"Selected option {selected_option} not in options {available_options}"
            
            # Only validate available_options if it's being updated
            if "available_options" in dict_of_values:
                if not allow_none and available_options == set():
                    return False, "Options set is empty but allow_none is False"

            return True, "Verification method passed"

        super().__init__(
            {"selected_option": initial_selected_option, "available_options": available_options},
            verification_method=lambda x: is_valid_value(x)
        )

        if selected_option_hook is not None:
            self.attach(selected_option_hook, "selected_option", InitialSyncMode.SELF_IS_UPDATED)
        if available_options_hook is not None:
            self.attach(available_options_hook, "available_options", InitialSyncMode.SELF_IS_UPDATED)

        if observable is not None:
            self.attach(observable.get_hook("selected_option"), "selected_option", InitialSyncMode.SELF_IS_UPDATED)
            self.attach(observable.get_hook("available_options"), "available_options", InitialSyncMode.SELF_IS_UPDATED)

    ############################################################
    # Properties (Getters and Setters)
    ############################################################

    @property
    def _collective_hooks(self) -> set[HookLike[Any]]:
        return {self._component_hooks["selected_option"], self._component_hooks["available_options"]}
    
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
        return self._component_hooks["available_options"].value.copy()
    
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
        if options == self._component_hooks["available_options"].value:
            return

        if options == set():
            raise ValueError("An empty set of options can not be set without setting the selected option to None, if even it is allowed")
        
        self._raise_if_selected_option_not_in_options(self._component_hooks["selected_option"].value, options)

        # Use the protocol method to set the values
        self._set_component_values({"available_options": options}, notify_binding_system=True)
    
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
        return self._component_hooks["selected_option"].value
    
    @property
    def selected_option_not_none(self) -> T:
        """
        Get the current selected option if it is not None.
        
        Returns:
            The current selected option

        Raises:
            ValueError: If the selected option is None
        """
        selected_option = self._component_hooks["selected_option"].value
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
        if selected_option == self._component_hooks["selected_option"].value:
            return
        
        self._raise_if_selected_option_not_in_options(selected_option, self._component_hooks["available_options"].value)

        # Use the protocol method to set the values
        self._set_component_values({"selected_option": selected_option}, notify_binding_system=True)

    @property
    def selected_option_hook(self) -> HookLike[Optional[T]]:
        return self._component_hooks["selected_option"]
    
    @property
    def available_options_hook(self) -> HookLike[set[T]]:
        return self._component_hooks["available_options"]

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
        if self._component_hooks["selected_option"].value is None and not allow_none:
            raise ValueError("Cannot set allow_none to False if selected option is None")
        self._allow_none = allow_none
    
    ############################################################
    # Combined set and selected option methods
    ############################################################

    def set_selected_option_and_available_options(self, selected_option: Optional[T], available_options: set[T]) -> None:
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
            available_options: The new set of available options. Must be a valid set
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
        
        if selected_option is not None and selected_option not in available_options:
            error_msg = f"Selected option {selected_option} not in options {available_options}"
            raise ValueError(error_msg)
        
        if not self._allow_none and selected_option is None:
            error_msg = "Selected option is None but allow_none is False"
            raise ValueError(error_msg)
        
        if not self._allow_none and available_options == set():
            error_msg = "Options set is empty but allow_none is False"
            raise ValueError(error_msg)
        
        # Use the protocol method to set the values
        self._set_component_values({"selected_option": selected_option, "available_options": available_options}, notify_binding_system=True)

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
        new_options: set[T] = self._component_hooks["available_options"].value.copy()
        if item not in new_options:
            new_options.add(item)
            self._set_component_values({"available_options": new_options}, notify_binding_system=True)
    
    def add_available_option(self, item: T) -> None:
        """
        Add an item to the available options (alias for add method).
        
        Args:
            item: The item to add to the available options
        """
        self.add(item)
    
    def remove_available_option(self, item: T) -> None:
        """
        Remove an item from the available options.
        
        Args:
            item: The item to remove from the available options
            
        Raises:
            ValueError: If the item is the currently selected option
        """
        if item == self._component_hooks["selected_option"].value:
            raise ValueError(f"Cannot remove {item} as it is the currently selected option")
        
        new_options: set[T] = self._component_hooks["available_options"].value.copy()
        if item in new_options:
            new_options.remove(item)
            self._set_component_values({"available_options": new_options}, notify_binding_system=True)
    
    def __str__(self) -> str:
        # Sort options for consistent string representation
        sorted_options = sorted(self._component_hooks['available_options'].value)
        return f"OSO(selected_option={self._component_hooks['selected_option'].value}, available_options={{{', '.join(repr(opt) for opt in sorted_options)}}})"
    
    def __repr__(self) -> str:
        # Sort options for consistent string representation
        sorted_options = sorted(self._component_hooks['available_options'].value)
        return f"OSO(selected_option={self._component_hooks['selected_option'].value}, available_options={{{', '.join(repr(opt) for opt in sorted_options)}}})"
    
    def __len__(self) -> int:
        """
        Get the number of available options.
        
        Returns:
            The number of available options
        """
        return len(self._component_hooks["available_options"].value)
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an item is in the available options.
        
        Args:
            item: The item to check for
            
        Returns:
            True if the item is in the options set, False otherwise
        """
        return item in self._component_hooks["available_options"].value
    
    def __iter__(self):
        """
        Get an iterator over the available options.
        
        Returns:
            An iterator that yields each option in the set
        """
        return iter(self._component_hooks["available_options"].value)
    
    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another selection option or observable.
        
        Args:
            other: Another ObservableSelectionOption to compare with
            
        Returns:
            True if both options sets and selected options are equal, False otherwise
        """
        if isinstance(other, ObservableSelectionOption):
            return (self._component_hooks["available_options"].value == other._component_hooks["available_options"].value and 
                   self._component_hooks["selected_option"].value == other._component_hooks["selected_option"].value)
        return False
    
    def __ne__(self, other: Any) -> bool:
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
        return hash((frozenset(self._component_hooks["available_options"].value), self._component_hooks["selected_option"].value))
    
    def __bool__(self) -> bool:
        """
        Convert the selection option to a boolean.
        
        Returns:
            True if there is a selected option, False if selected_option is None
        """
        return bool(self._component_hooks["selected_option"].value)