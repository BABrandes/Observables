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

from typing import Generic, Optional, TypeVar, overload, runtime_checkable, Protocol, Any, Literal, Mapping
from logging import Logger

from .._hooks.hook_aliases import Hook
from .._hooks.hook_protocols.owned_full_hook_protocol import OwnedFullHookProtocol
from .._carries_hooks.complex_observable_base import ComplexObservableBase
from .._carries_hooks.carries_hooks_protocol import CarriesHooksProtocol

T = TypeVar("T")

@runtime_checkable
class ObservableWithOptionsProtocol(CarriesHooksProtocol[Any, Optional[T]|set[T]|int], Protocol[T]):

    @property
    def available_options(self) -> set[T]:
        ...
    
    @available_options.setter
    def available_options(self, options: set[T]) -> None:
        ...

    @property
    def available_options_hook(self) -> Hook[set[T]]:
        ...

    def change_available_options(self, available_options: set[T]) -> None:
        ...

@runtime_checkable
class ObservableSelectionOptionProtocol(ObservableWithOptionsProtocol[T], Protocol[T]):

    @property
    def selected_option(self) -> T:
        ...
    
    @selected_option.setter
    def selected_option(self, selected_option: T) -> None:
        ...

    @property
    def selected_option_hook(self) -> OwnedFullHookProtocol[T]:
        ...

    def change_selected_option(self, selected_option: T) -> None:
        ...

    def change_selected_option_and_available_options(self, selected_option: T, available_options: set[T]) -> None:
        ...

@runtime_checkable
class ObservableOptionalSelectionOptionProtocol(ObservableWithOptionsProtocol[T], Protocol[T]):

    @property
    def selected_option(self) -> Optional[T]:
        ...
    
    @selected_option.setter
    def selected_option(self, selected_option: Optional[T]) -> None:
        ...

    @property
    def selected_option_hook(self) -> OwnedFullHookProtocol[Optional[T]]:
        ...

    def change_selected_option(self, selected_option: Optional[T]) -> None:
        ...

    def change_selected_option_and_available_options(self, selected_option: Optional[T], available_options: set[T]) -> None:
        ...

O = TypeVar("O", bound="ObservableSelectionOptionBase[Any, Any]")

class ObservableSelectionOptionBase(ComplexObservableBase[Literal["selected_option", "available_options"], Literal["number_of_available_options"], Optional[T]|set[T], int, O], ObservableWithOptionsProtocol[T], Generic[T, O]):

    @property
    def available_options(self) -> set[T]:
        value = self._primary_hooks["available_options"].value
        if isinstance(value, set):
            return value.copy() # type: ignore
        else:
            raise ValueError("Available options is not a set")
    
    @available_options.setter
    def available_options(self, options: set[T]) -> None:
        if options == self._primary_hooks["available_options"].value:
            return

        success, msg = self.submit_values({"available_options": options})
        if not success:
            raise ValueError(msg)
    
    def change_available_options(self, available_options: set[T]) -> None:
        if available_options == self._primary_hooks["available_options"].value:
            return
        
        success, msg = self.submit_values({"available_options": available_options})
        if not success:
            raise ValueError(msg)

    @property
    def available_options_hook(self) -> Hook[set[T]]:
        return self._primary_hooks["available_options"] # type: ignore

    def _get_set_hook(self) -> Hook[set[T]]:
        return self._primary_hooks["available_options"] # type: ignore

    def add(self, item: T) -> None:
        available_options = self._primary_hooks["available_options"].value
        if isinstance(available_options, set):
            new_options: set[T] = available_options.copy() # type: ignore
        else:
            raise ValueError("Available options is not a set")

        if item not in new_options:
            new_options.add(item)
            self.submit_values({"available_options": new_options})
    
    def add_available_option(self, item: T) -> None:
        self.add(item)
    
    def remove_available_option(self, item: T) -> None:
        if item == self._primary_hooks["selected_option"].value:
            raise ValueError(f"Cannot remove {item} as it is the currently selected option")
        
        available_options = self._primary_hooks["available_options"].value
        if isinstance(available_options, set):
            new_options: set[T] = available_options.copy() # type: ignore
        else:
            raise ValueError("Available options is not a set")

        if item in new_options:
            new_options.remove(item)
            self.submit_values({"available_options": new_options})
    
    def __str__(self) -> str:
        available_options = self._primary_hooks["available_options"].value
        if isinstance(available_options, set):
            sorted_options: list[T] = sorted(available_options) # type: ignore
        else:
            raise ValueError("Available options is not a set")

        return f"OSO(selected_option={self._primary_hooks['selected_option'].value}, available_options={{{', '.join(repr(opt) for opt in sorted_options)}}})"
    
    def __repr__(self) -> str:
        available_options = self._primary_hooks["available_options"].value
        if isinstance(available_options, set):
            sorted_options: list[T] = sorted(available_options) # type: ignore
        else:
            raise ValueError("Available options is not a set")

        return f"OSO(selected_option={self._primary_hooks['selected_option'].value}, available_options={{{', '.join(repr(opt) for opt in sorted_options)}}})"
    
    def __len__(self) -> int:
        available_options = self._primary_hooks["available_options"].value
        if isinstance(available_options, set):
            return len(available_options) # type: ignore
        else:
            raise ValueError("Available options is not a set")
    
    def __contains__(self, item: T) -> bool:
        available_options = self._primary_hooks["available_options"].value
        if isinstance(available_options, set):
            return item in available_options # type: ignore
        else:
            raise ValueError("Available options is not a set")
    
    def __iter__(self):
        available_options = self._primary_hooks["available_options"].value
        if isinstance(available_options, set):
            return iter(available_options) # type: ignore
        else:
            raise ValueError("Available options is not a set")

class ObservableSelectionOption(ObservableSelectionOptionBase[T, "ObservableSelectionOption"], ObservableSelectionOptionProtocol[T], Generic[T]):
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
        - **Bidirectional Binding**: Bind selection to other observables
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
        
        With binding::
        
            user_theme = ObservableSelectionOption("dark", {"dark", "light"})
            display_theme = ObservableSelectionOption("light", {"dark", "light"})
            
            # Bind them - both must have same options for validation
            user_theme.connect_hooks({
                "selected_option": display_theme.selected_option_hook,
                "available_options": display_theme.available_options_hook
            }, "use_caller_value")
    """

    @overload
    def __init__(self, selected_option: Hook[T], available_options: Hook[set[T]], *, logger: Optional[Logger] = None) -> None:
        ...

    @overload
    def __init__(self, selected_option: T, available_options: Hook[set[T]], *, logger: Optional[Logger] = None) -> None:
        ...

    @overload
    def __init__(self, selected_option: Hook[T], available_options: set[T], *, logger: Optional[Logger] = None) -> None:
        ...

    @overload
    def __init__(self, observable: ObservableSelectionOptionProtocol[T], available_options: None=None, *, logger: Optional[Logger] = None) -> None:
        ...
    
    @overload
    def __init__(self, selected_option: T, available_options: set[T], *, logger: Optional[Logger] = None) -> None:
        ...

    def __init__(self, selected_option: T | Hook[T] | ObservableSelectionOptionProtocol[T], available_options: set[T] | Hook[set[T]] | None = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize an ObservableSelectionOption.
        
        This constructor supports multiple initialization patterns with flexible combinations
        of values and hooks for both selected_option and available_options.
        
        Args:
            selected_option: The initial selected option. Can be:
                - T: A direct value (must be in available_options)
                - Hook[T]: A hook to bind the selection to
                - ObservableSelectionOptionProtocol[T]: Another observable to bind to (copies both hooks)
            available_options: The set of options to choose from. Can be:
                - set[T]: A direct set of options (selected_option must be in this set)
                - Hook[set[T]]: A hook to bind the available options to
                - None: If selected_option is an ObservableSelectionOptionProtocol, options are copied from it
            logger: Optional logger for debugging operations. Default is None.
        
        Raises:
            ValueError: If selected_option is not in available_options during initialization.
        
        Note:
            When binding to hooks or observables, both selected_option and available_options
            are bound. This ensures validation consistency - the selected option will always
            be valid for the current set of available options.
        
        Example:
            Multiple initialization patterns::
            
                # 1. Direct values
                color = ObservableSelectionOption("red", {"red", "green", "blue"})
                
                # 2. From another observable (binds both hooks)
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
        
        if isinstance(selected_option, ObservableSelectionOptionProtocol):
            initial_selected_option: T = selected_option.selected_option # type: ignore
            initial_available_options: set[T] = selected_option.available_options # type: ignore
            hook_selected_option: Optional[Hook[T]] = selected_option.selected_option_hook # type: ignore
            hook_available_options: Optional[Hook[set[T]]] = selected_option.available_options_hook # type: ignore

        else:
            if selected_option is None:
                raise ValueError("selected_option parameter is required when selected_option is not an ObservableSelectionOptionProtocol")
            
            elif isinstance(selected_option, Hook):
                initial_selected_option: T = selected_option.value # type: ignore
                hook_selected_option = selected_option # type: ignore

            else:
                # selected_option is a T
                initial_selected_option: T = selected_option
                hook_selected_option = None

            if available_options is None:
                initial_available_options = set()
                hook_available_options = None

            elif isinstance(available_options, Hook):
                initial_available_options = available_options.value # type: ignore
                hook_available_options = available_options

            elif isinstance(available_options, set): # type: ignore
                initial_available_options: set[T] = available_options.copy()
                hook_available_options: Optional[Hook[set[T]]] = None

            else:
                raise ValueError("available_options parameter is required when selected_option is not an ObservableSelectionOptionProtocol")
                
        def is_valid_value(x: Mapping[Literal["selected_option", "available_options"], Any]) -> tuple[bool, str]:
            if "selected_option" in x:
                selected_option: Optional[T] = x["selected_option"]
            else:
                selected_option = self._primary_hooks["selected_option"].value # type: ignore
                
            if "available_options" in x:
                available_options = x["available_options"]
            else:
                _available_options = self._primary_hooks["available_options"].value
                if isinstance(_available_options, set):
                    available_options: set[T] = _available_options # type: ignore
                else:
                    raise ValueError("Available options is not a set")

            if selected_option is None:
                return False, "Selected option is None"
            elif selected_option in available_options:
                return True, "Verification method passed"
            else:
                return False, f"Selected option {selected_option} not in options {available_options}"

        super().__init__(
            initial_component_values_or_hooks={"selected_option": initial_selected_option, "available_options": initial_available_options}, # type: ignore
            verification_method=is_valid_value,
            secondary_hook_callbacks={"number_of_available_options": lambda x: len(x["available_options"])}, # type: ignore
            logger=logger
        )

        if hook_selected_option is not None:
            self.connect_hook(hook_selected_option, "selected_option", "use_target_value") # type: ignore
        if hook_available_options is not None:
            self.connect_hook(hook_available_options, "available_options", "use_target_value") # type: ignore

    @property
    def selected_option(self) -> T:
        return self._primary_hooks["selected_option"].value # type: ignore
    
    @property
    def selected_option_not_none(self) -> T:
        selected_option: T = self._primary_hooks["selected_option"].value # type: ignore
        return selected_option
    
    @selected_option.setter
    def selected_option(self, selected_option: T) -> None:
        if selected_option == self._primary_hooks["selected_option"].value:
            return
        
        success, msg = self.submit_values({"selected_option": selected_option})
        if not success:
            raise ValueError(msg)

    @property
    def selected_option_hook(self) -> OwnedFullHookProtocol[T]:
        return self._primary_hooks["selected_option"] # type: ignore
    
    def change_selected_option(self, selected_option: T) -> None:
        if selected_option == self._primary_hooks["selected_option"].value:
            return
        
        success, msg = self.submit_values({"selected_option": selected_option})
        if not success:
            raise ValueError(msg)
 
    def change_selected_option_and_available_options(self, selected_option: T, available_options: set[T]) -> None:
        self.submit_values({"selected_option": selected_option, "available_options": available_options})

    def _get_single_value_hook(self) -> Hook[T]:
        return self._primary_hooks["selected_option"] # type: ignore

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ObservableSelectionOption):
            return (self._primary_hooks["available_options"].value == other._primary_hooks["available_options"].value and  # type: ignore
                   self._primary_hooks["selected_option"].value == other._primary_hooks["selected_option"].value) # type: ignore
        return False
    
    def __hash__(self) -> int:
        return hash((frozenset(self._primary_hooks["available_options"].value), self._primary_hooks["selected_option"].value)) # type: ignore
    
class ObservableOptionalSelectionOption(ObservableSelectionOptionBase[T, "ObservableOptionalSelectionOption"], ObservableOptionalSelectionOptionProtocol[T], Generic[T]):

    @overload
    def __init__(self, selected_option: Hook[Optional[T]], available_options: Hook[set[T]], *, logger: Optional[Logger] = None) -> None:
        ...

    @overload
    def __init__(self, selected_option: Optional[T], available_options: Hook[set[T]], *, logger: Optional[Logger] = None) -> None:
        ...

    @overload
    def __init__(self, selected_option: Hook[Optional[T]], available_options: set[T], *, logger: Optional[Logger] = None) -> None:
        ...

    @overload
    def __init__(self, observable: ObservableOptionalSelectionOptionProtocol[T], available_options: None=None, *, logger: Optional[Logger] = None) -> None:
        ...
    
    @overload
    def __init__(self, selected_option: Optional[T], available_options: set[T], *, logger: Optional[Logger] = None) -> None:
        ...

    def __init__(self, selected_option: Optional[T] | Hook[Optional[T]] | ObservableOptionalSelectionOptionProtocol[T], available_options: set[T] | Hook[set[T]] | None = None, *, logger: Optional[Logger] = None) -> None: # type: ignore
        
        if isinstance(selected_option, ObservableOptionalSelectionOptionProtocol):
            initial_selected_option: Optional[T] = selected_option.selected_option # type: ignore
            initial_available_options: set[T] = selected_option.available_options # type: ignore
            hook_selected_option: Optional[Hook[Optional[T]]] = selected_option.selected_option_hook # type: ignore
            hook_available_options: Optional[Hook[set[T]]] = selected_option.available_options_hook # type: ignore

        else:
            if selected_option is None:
                initial_selected_option: Optional[T] = None
                hook_selected_option: Optional[Hook[Optional[T]]] = None
            
            elif isinstance(selected_option, Hook):
                initial_selected_option = selected_option.value # type: ignore
                hook_selected_option = selected_option # type: ignore

            else:
                # selected_option is a T
                initial_selected_option = selected_option
                hook_selected_option = None

            if available_options is None:
                initial_available_options: set[T] = set()
                hook_available_options: Optional[Hook[set[T]]] = None

            elif isinstance(available_options, Hook):
                initial_available_options = available_options.value # type: ignore
                hook_available_options = available_options

            elif isinstance(available_options, set): # type: ignore
                initial_available_options = available_options.copy()
                hook_available_options = None

            else:
                raise ValueError("available_options parameter is required when selected_option is not an ObservableSelectionOptionProtocol")
                
        def is_valid_value(x: Mapping[Literal["selected_option", "available_options"], Any]) -> tuple[bool, str]:
            if "selected_option" in x:
                selected_option: Optional[T] = x["selected_option"]
            else:
                selected_option = self._primary_hooks["selected_option"].value # type: ignore
                
            if "available_options" in x:
                available_options: set[T] = x["available_options"] # type: ignore
            else:
                _available_options = self._primary_hooks["available_options"].value
                if isinstance(_available_options, set):
                    available_options: set[T] = _available_options # type: ignore
                else:
                    raise ValueError("Available options is not a set")

            if selected_option is None:
                return True, "Verification method passed"
            elif selected_option in available_options:
                return True, "Verification method passed"
            else:
                return False, f"Selected option {selected_option} not in options {available_options}"

        super().__init__(
            initial_component_values_or_hooks={"selected_option": initial_selected_option, "available_options": initial_available_options}, # type: ignore
            verification_method=is_valid_value,
            secondary_hook_callbacks={"number_of_available_options": lambda x: len(x["available_options"])}, # type: ignore
            logger=logger
        )

        if hook_selected_option is not None:
            self.connect_hook(hook_selected_option, "selected_option", "use_target_value") # type: ignore
        if hook_available_options is not None:
            self.connect_hook(hook_available_options, "available_options", "use_target_value") # type: ignore

    @property
    def selected_option(self) -> Optional[T]:
        return self.get_value_of_hook("selected_option") # type: ignore
    
    @property
    def selected_option_not_none(self) -> T:
        selected_option: T = self.get_value_of_hook("selected_option") # type: ignore
        if selected_option is None:
            raise ValueError("Selected option is None")
        return selected_option
    
    @selected_option.setter
    def selected_option(self, selected_option: Optional[T]) -> None:
        if selected_option == self._get_value_reference_of_hook("selected_option"):
            return
        
        self.submit_values({"selected_option": selected_option})

    @property
    def selected_option_hook(self) -> OwnedFullHookProtocol[Optional[T]]:
        return self.get_hook("selected_option") # type: ignore
    
    def change_selected_option(self, selected_option: Optional[T]) -> None:
        if selected_option == self._get_value_reference_of_hook("selected_option"):
            return
        
        self.submit_values({"selected_option": selected_option})
    
    def change_selected_option_and_available_options(self, selected_option: Optional[T], available_options: set[T]) -> None:
        self.submit_values({"selected_option": selected_option, "available_options": available_options})

    def _get_single_value_hook(self) -> OwnedFullHookProtocol[Optional[T]]:
        return self._primary_hooks["selected_option"] # type: ignore

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ObservableSelectionOption):
            return (self._get_value_reference_of_hook("available_options") == other._get_value_reference_of_hook("available_options") and  # type: ignore
                   self._get_value_reference_of_hook("selected_option") == other._get_value_reference_of_hook("selected_option")) # type: ignore
        return False
    
    def __hash__(self) -> int:
        return hash((frozenset(self.get_value_reference_of_hook("available_options")), self.get_value_reference_of_hook("selected_option"))) # type: ignore