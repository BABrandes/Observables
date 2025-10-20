"""
ObservableSelectionSet Module

This module provides the ObservableSelectionSet class, a sophisticated observable
that combines the functionality of an observable set (for available options) and an
observable single value (for the selected option).

The ObservableSelectionSet is designed for scenarios where you need to:
- Maintain a dynamic set of valid options
- Track a currently selected option from that set
- Ensure data consistency and validation
- Synchronize with other observables through linking
- React to changes through listeners and notifications

Key Features:
- Bidirectional linking for both options and selected values
- Automatic validation ensuring selected option is always valid
- Comprehensive listener notification system
- Full set interface for options management
- Type-safe generic implementation
- Configurable None selection handling
- Atomic operations for consistency

Architecture:
The class implements multiple interfaces:
- Observable: Base observable pattern with listeners and component management
- CarriesDistinctSingleValueHook: Interface for single value linking operations
- CarriesDistinctSetHook: Interface for set linking operations

The internal structure uses a component-based approach where:
- selected_option: Manages the currently selected value
- available_options: Manages the set of valid options
- Each component has its own hook for linking management

Linking System:
The linking system supports:
- Linking between ObservableSelectionSet instances (comprehensive linking)
- Linking to ObservableSingleValue instances (selected option only)
- Linking to ObservableSet instances (options only)
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
- Linking operations are O(1) but may trigger cascading updates

Thread Safety:
This module is not thread-safe. If used in multi-threaded environments,
external synchronization is required.

Example Usage:
    >>> # Basic usage
    >>> selector = ObservableSelectionSet("Apple", {"Apple", "Banana", "Cherry"})
    >>> print(selector.selected_option)  # "Apple"

    >>> # Add listener
    >>> selector.add_listeners(lambda: print("Changed!"))
    >>> selector.selected_option = "Banana"  # Triggers listener

    >>> # Linking
    >>> source = ObservableSet({"Red", "Green", "Blue"})
    >>> selector.link_options_to_observable(source)
    >>> source.add("Yellow")  # Automatically updates selector

Dependencies:
- typing: For type hints and generic support
- .._utils.hook: For linking mechanism
- .._utils.sync_mode: For synchronization modes
- .._utils.carries_distinct_single_value_hook: For single value linking interface
- .._utils.carries_distinct_set_hook: For set linking interface
- .._utils.observable: For base observable functionality

See Also:
- Observable: Base observable class
- ObservableSet: For managing observable sets
- ObservableSingleValue: For managing observable single values
- Hook: For custom linking mechanisms
- SyncMode: For linking synchronization modes
"""

from typing import Generic, Optional, TypeVar, Any, Literal, Mapping
from collections.abc import Iterable
from logging import Logger

from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ..._carries_hooks.x_complex_base import ComplexObservableBase
from ..._nexus_system.submission_error import SubmissionError
from .protocols import ObservableSelectionOptionsProtocol
from .utils import likely_settable

T = TypeVar("T")

class ObservableSelectionSet(ComplexObservableBase[Literal["selected_option", "available_options"], Literal["number_of_available_options"], T | Iterable[T], int, "ObservableSelectionSet"], ObservableSelectionOptionsProtocol[T], Generic[T]):
    """
    Observable for selecting one option from a set of available options.
    
    ObservableSelectionOption manages a selection state where exactly one option must
    be selected from a set of available options. It enforces validation ensuring the
    selected option is always in the available options set.
    
    Type Parameters:
        T: The type of options. Can be any hashable type - str, int, Enum, custom objects
           with __hash__ and __eq__, etc. Must be hashable to work in a set.
    
    Hooks:
        - **selected_option_hook**: Primary hook for the currently selected option (type T)
        - **available_options_hook**: Primary hook for the set of available options (type set[T])
        - **number_of_available_options_hook**: Secondary hook for count (type int, read-only)
    
    Validation:
        The observable automatically validates that:
        - Selected option must be in available options
        - Available options must be a non-empty set
        - Changes that would violate these rules are rejected with ValueError
    
    Key Features:
        - **Enforced Validity**: Selected option always exists in available options
        - **Atomic Updates**: Change both selection and options atomically
        - **Bidirectional Linking**: Link selection to other observables
        - **Secondary Hooks**: Automatically computed number of options
        - **Type Safety**: Generic type ensures type consistency
    
    Example:
        Basic usage::
        
            from observables import ObservableSelectionOption
            
            # Create selector
            theme = ObservableSelectionOption("dark", {"dark", "light", "auto"})
            
            # Access selected value
            print(theme.selected_option)  # "dark"
            
            # Change selection
            theme.selected_option = "light"  # ✓ Valid
            
            # Invalid selection raises error
            try:
                theme.selected_option = "rainbow"  # ✗ Not in options
            except ValueError as e:
                print(f"Validation error: {e}")
        
        Atomic updates::
        
            # Change both selection and options together
            theme.change_selected_option_and_available_options(
                "blue",
                {"blue", "red", "green"}
            )
        
        With linking::
        
            user_theme = ObservableSelectionOption("dark", {"dark", "light"})
            display_theme = ObservableSelectionOption("light", {"dark", "light"})
            
            # Link them - both must have same options for validation
            user_theme.connect_hooks({
                "selected_option": display_theme.selected_option_hook,
                "available_options": display_theme.available_options_hook
            }, "use_caller_value")
    """

    def __init__(self, selected_option: T | Hook[T] | ReadOnlyHook[T] | ObservableSelectionOptionsProtocol[T], available_options: Iterable[T] | Hook[Iterable[T]] | ReadOnlyHook[Iterable[T]] | None = None, logger: Optional[Logger] = None) -> None:
        """
        Initialize an ObservableSelectionOption.
        
        This constructor supports multiple initialization patterns with flexible combinations
        of values and hooks for both selected_option and available_options.
        
        Args:
            selected_option: The initial selected option. Can be:
                - T: A direct value (must be in available_options)
                - Hook[T]: A hook to link the selection to
                - ObservableSelectionOptionProtocol[T]: Another observable to link to (copies both hooks)
            available_options: The set of options to choose from. Can be:
                - set[T]: A direct set of options (selected_option must be in this set)
                - Hook[set[T]]: A hook to link the available options to
                - None: If selected_option is an ObservableSelectionOptionProtocol, options are copied from it
            logger: Optional logger for debugging operations. Default is None.
        
        Raises:
            ValueError: If selected_option is not in available_options during initialization.
        
        Note:
            When linking to hooks or observables, both selected_option and available_options
            are bound. This ensures validation consistency - the selected option will always
            be valid for the current set of available options.
        
        Example:
            Multiple initialization patterns::
            
                # 1. Direct values
                color = ObservableSelectionOption("red", {"red", "green", "blue"})
                
                # 2. From another observable (links both hooks)
                color_copy = ObservableSelectionOption(color)
                color.selected_option = "blue"  # Both update
                
                # 3. Mixed: direct selection, hook for options
                options_source = ObservableSelectionOption("A", {"A", "B"})
                mixed = ObservableSelectionOption(
                    "A", 
                    options_source.available_options_hook
                )
                
                # 4. With logging
                import logging
                logger = logging.getLogger(__name__)
                logged = ObservableSelectionOption(
                    "option1",
                    {"option1", "option2", "option3"},
                    logger=logger
                )
        """
        
        if isinstance(selected_option, ObservableSelectionOptionsProtocol):
            initial_selected_option: T = selected_option.selected_option # type: ignore
            initial_available_options: Iterable[T] = selected_option.available_options # type: ignore
            hook_selected_option: Optional[Hook[T]] = selected_option.selected_option_hook # type: ignore
            hook_available_options: Optional[Hook[Iterable[T]]] = selected_option.available_options_hook # type: ignore

        else:
            if selected_option is None:
                raise ValueError("selected_option parameter is required when selected_option is not an ObservableSelectionOptionProtocol")
            
            elif isinstance(selected_option, ManagedHookProtocol):
                initial_selected_option: T = selected_option.value # type: ignore
                hook_selected_option = selected_option # type: ignore

            else:
                # selected_option is a T
                initial_selected_option = selected_option # type: ignore
                hook_selected_option = None

            if available_options is None:
                initial_available_options = set()
                hook_available_options = None

            elif isinstance(available_options, ManagedHookProtocol):
                initial_available_options = available_options.value # type: ignore
                hook_available_options = available_options # type: ignore

            else:
                # available_options is an Iterable[T]
                initial_available_options: Iterable[T] = set(available_options) # type: ignore
                hook_available_options = None
                
        def is_valid_value(x: Mapping[Literal["selected_option", "available_options"], Any]) -> tuple[bool, str]:
            selected_option = x["selected_option"]
            available_options = x["available_options"]

            if not likely_settable(available_options):
                return False, f"Available options '{available_options}' cannot be used as a set!"

            if selected_option not in available_options:
                return False, f"Selected option '{selected_option}' not in available options '{available_options}'!"

            return True, "Verification method passed"

        super().__init__(
            initial_hook_values={"selected_option": initial_selected_option, "available_options": initial_available_options}, # type: ignore
            verification_method=is_valid_value,
            secondary_hook_callbacks={"number_of_available_options": lambda x: len(x["available_options"])}, # type: ignore
            logger=logger
        )

        if hook_selected_option is not None:
            self._join(hook_selected_option, "selected_option", "use_target_value") # type: ignore
        if hook_available_options is not None:
            self._join(hook_available_options, "available_options", "use_target_value") # type: ignore

    #########################################################
    # ObservableSelectionOptionsProtocol implementation
    #########################################################

    #-------------------------------- available options --------------------------------
    
    @property
    def available_options_hook(self) -> Hook[Iterable[T]]:
        return self._primary_hooks["available_options"] # type: ignore

    @property
    def available_options(self) -> set[T]: # type: ignore
        return self._primary_hooks["available_options"].value # type: ignore

    @available_options.setter
    def available_options(self, available_options: Iterable[T]) -> None:
        self.change_available_options(available_options)

    def change_available_options(self, available_options: Iterable[T]) -> None:        
        success, msg = self._submit_value("available_options", set(available_options))
        if not success:
            raise SubmissionError(msg, available_options, "available_options")

    #-------------------------------- selected option --------------------------------

    @property
    def selected_option_hook(self) -> Hook[T]:
        return self._primary_hooks["selected_option"] # type: ignore

    @property
    def selected_option(self) -> T: # type: ignore
        return self._primary_hooks["selected_option"].value # type: ignore
    
    @selected_option.setter
    def selected_option(self, selected_option: T) -> None:
        self.change_selected_option(selected_option)

    def change_selected_option(self, selected_option: T) -> None:
        if selected_option == self._primary_hooks["selected_option"].value:
            return
        
        success, msg = self._submit_values({"selected_option": selected_option})
        if not success:
            raise ValueError(msg)
        
        success, msg = self._submit_values({"selected_option": selected_option})
        if not success:
            raise ValueError(msg)
    
    def change_selected_option_and_available_options(self, selected_option: T, available_options: Iterable[T]) -> None:
        if selected_option == self._primary_hooks["selected_option"].value and available_options == self._primary_hooks["available_options"].value:
            return
        
        success, msg = self._submit_values({"selected_option": selected_option, "available_options": frozenset(available_options)})
        if not success:
            raise ValueError(msg)

    #-------------------------------- number of available options --------------------------------

    @property
    def number_of_available_options_hook(self) -> ReadOnlyHook[int]:
        return self._secondary_hooks["number_of_available_options"] # type: ignore

    @property
    def number_of_available_options(self) -> int:
        return len(self._primary_hooks["available_options"].value) # type: ignore

    #-------------------------------- convenience methods --------------------------------

    def add_available_option(self, option: T) -> None:
        """Add an option to the available options set."""
        success, msg = self._submit_values({"available_options": self._primary_hooks["available_options"].value | frozenset([option])}) # type: ignore
        if not success:
            raise ValueError(msg)

    def add_available_options(self, options: Iterable[T]) -> None:
        """Add an option to the available options set."""
        success, msg = self._submit_values({"available_options": self._primary_hooks["available_options"].value | frozenset(options)}) # type: ignore
        if not success:
            raise ValueError(msg)

    def remove_available_option(self, option: T) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_values({"available_options": self._primary_hooks["available_options"].value - frozenset([option])}) # type: ignore
        if not success:
            raise ValueError(msg)

    def remove_available_options(self, options: Iterable[T]) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_values({"available_options": self._primary_hooks["available_options"].value - frozenset(options)}) # type: ignore
        if not success:
            raise ValueError(msg)