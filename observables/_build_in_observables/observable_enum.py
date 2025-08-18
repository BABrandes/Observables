from typing import Any, Generic, TypeVar, Optional, overload, Protocol, runtime_checkable, Literal
from enum import Enum
from .._utils.hook import HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.base_observable import BaseObservable
from .._utils.carries_collective_hooks import CarriesCollectiveHooks

E = TypeVar("E", bound=Enum)

@runtime_checkable
class ObservableEnumLike(CarriesCollectiveHooks[Any], Protocol[E]):
    """
    Protocol for observable enum objects.
    """
    
    @property
    def enum_value(self) -> Optional[E]:
        """
        Get the enum value.
        """
        ...
    
    @enum_value.setter
    def enum_value(self, value: Optional[E]) -> None:
        """
        Set the enum value.
        """
        ...

    @property
    def enum_value_hook(self) -> HookLike[Optional[E]]:
        """
        Get the hook for the enum value.
        """
        ...

    @property
    def enum_options(self) -> set[E]:
        """
        Get the enum options.
        """
        ...
    
    @enum_options.setter
    def enum_options(self, value: set[E]) -> None:
        """
        Set the enum options.
        """
        ...

    @property
    def enum_options_hook(self) -> HookLike[set[E]]:
        """
        Get the hook for the enum options.
        """
        ...

    def set_enum_value_and_options(self, enum_value: Optional[E], enum_options: set[E]) -> None:
        """
        Set the enum value and options.
        """
        ...

# ObservableEnum implements the Observable protocol for type safety and polymorphism
class ObservableEnum(BaseObservable[Literal["enum_value", "enum_options"]], ObservableEnumLike[E], Generic[E]):
    """
    An observable wrapper around an enum that supports bidirectional bindings and reactive updates.
    
    This class implements the Observable protocol, which provides a standardized interface
    for all observable objects in the library. The Observable protocol ensures consistency
    across different observable types and enables polymorphic usage.
    
    **Observable Protocol Benefits:**
    - **Type Safety**: Enables static type checking and IDE support for observable operations
    - **Polymorphism**: Can be used interchangeably with other observable types in generic contexts
    - **Interface Consistency**: Guarantees that all observables implement the same core methods
    - **Future Extensibility**: Allows for protocol-based features and utilities
    
    **Core Features:**
    - **Enum Value Management**: Stores and manages a single enum value with validation
    - **Options Management**: Maintains a set of valid enum options that can be dynamically updated
    - **Bidirectional Bindings**: Supports two-way synchronization with other observables
    - **Listener System**: Notifies registered callbacks when values change
    - **Validation**: Ensures enum values are always within the valid options set
    
    **Binding Capabilities:**
    - **Value Binding**: Bind enum values between multiple ObservableEnum instances
    - **Options Binding**: Bind enum options to ObservableSet instances
    - **Sync Modes**: Control binding direction with explicit SyncMode specification
    - **Chain Binding**: Create complex binding chains across multiple observables
    
    **Example Usage:**
        from enum import Enum
        from observables import ObservableEnum, SyncMode
        
        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"
        
        # Create observable enums
        color1 = ObservableEnum(Color.RED)
        color2 = ObservableEnum(Color.BLUE)
        
        # Bind them together
        color1.bind_enum_value_to_observable(color2, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        
        # Changes propagate automatically
        color1.enum_value = Color.GREEN
        assert color2.enum_value == Color.GREEN
        
        # Add listeners for reactive programming
        def on_color_change():
            print(f"Color changed to: {color1.enum_value}")
        
        color1.add_listener(on_color_change)
        
        # Dynamic options management
        color1.change_enum_options({Color.GREEN, Color.BLUE})
        # This will fail if current value (GREEN) is not in new options
        # color1.change_enum_options({Color.RED, Color.BLUE})  # ValueError!
    
    **Protocol Compliance:**
    This class fully implements the Observable protocol, ensuring it can be used
    anywhere an Observable is expected. This includes:
    - Generic collections of observables
    - Protocol-based function parameters
    - Type-safe observable factories and utilities
    
    **Thread Safety:**
    The class is not thread-safe by default. If used in multi-threaded environments,
    external synchronization should be applied.
    
    **Performance Characteristics:**
    - O(1) for value and options access
    - O(n) for binding operations where n is the number of bound observables
    - O(m) for listener notifications where m is the number of registered listeners
    - Memory usage scales linearly with the number of bindings and listeners
    """

    @overload
    def __init__(self, enum_value: Optional[E], enum_options: Optional[set[E]] = None, *, allow_none: bool = True) -> None:
        """Initialize with a direct enum value."""
        ...

    @overload
    def __init__(self, enum_value: HookLike[Optional[E]], enum_options: Optional[set[E]] = None, *, allow_none: bool = True) -> None:
        """Initialize with another observable enum, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, enum_value: Optional[E], enum_options: HookLike[set[E]], *, allow_none: bool = True) -> None:
        """Initialize with a set of enum options."""
        ...

    @overload
    def __init__(self, enum_value: HookLike[Optional[E]], enum_options: HookLike[set[E]], *, allow_none: bool = True) -> None:
        """Initialize with another observable enum, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, observable: ObservableEnumLike[E], enum_options: Optional[set[E]] = None, *, allow_none: bool = True) -> None:
        """Initialize from another ObservableEnumLike object."""
        ...

    def __init__(self, enum_value: Optional[E] | HookLike[Optional[E]] | ObservableEnumLike[E], enum_options: Optional[set[E]] | HookLike[set[E]] = None, *, allow_none: bool = True) -> None: # type: ignore
        """
        Initialize the ObservableEnum.
        
        Args:
            value: Initial enum value or observable enum to bind to
            enum_options: Set of valid enum options or observable set to bind to
            allow_none: Whether to allow None as an enum value
        Raises:
            ValueError: If the initial enum value is not in the options set
        """

        self._allow_none = allow_none
        
        # Flag to track if we've already set enum_options from the hook
        skip_enum_options_processing = False
        
        # Initialize variables
        initial_enum_options: set[E] = set()
        bindable_set_carrier: Optional[HookLike[set[E]]] = None

        if enum_value is None:
            if not allow_none:
                raise ValueError("None is not allowed as an enum value, if allow_none is False")
            initial_enum_value: Optional[E] = None # type: ignore
            bindable_enum_carrier: Optional[HookLike[Optional[E]]] = None
        elif isinstance(enum_value, HookLike):
            # Check if this hook is from an ObservableEnum-like object
            if hasattr(enum_value, 'owner') and hasattr(enum_value.owner, 'enum_options'):
                # This is a hook from an ObservableEnum, extract both value and options
                initial_enum_value = enum_value.value
                initial_enum_options = enum_value.owner.enum_options # type: ignore
                bindable_enum_carrier = enum_value
                # Skip the enum_options processing below
                skip_enum_options_processing = True
            else:
                # This is just a value hook
                initial_enum_value: Optional[E] = enum_value.value # type: ignore
                bindable_enum_carrier: Optional[HookLike[Optional[E]]] = None
        else:
            initial_enum_value: Optional[E] = enum_value # type: ignore
            bindable_enum_carrier: Optional[HookLike[Optional[E]]] = None

        # Only process enum_options if we haven't already set them from the hook
        if not skip_enum_options_processing:
            if isinstance(enum_options, HookLike):
                initial_enum_options: set[E] = enum_options.value
                bindable_set_carrier: Optional[HookLike[set[E]]] = None
            elif enum_options is None:
                if enum_value is None:
                    raise ValueError("enum_value is None, but enum_options is None")
                # When no enum_options provided, create it from the enum class
                # Get the actual enum class from the value, not the protocol class
                if hasattr(enum_value, '__class__') and hasattr(enum_value.__class__, '__members__'):
                    initial_enum_options: set[E] = set(enum_value.__class__.__members__.values()) # type: ignore
                else:
                    # Fallback: create an empty set
                    initial_enum_options: set[E] = set()
                bindable_set_carrier: Optional[HookLike[set[E]]] = None
            elif isinstance(enum_options, ObservableEnumLike):
                initial_enum_options: set[E] = enum_options.enum_options # type: ignore
                bindable_set_carrier: Optional[HookLike[set[E]]] = enum_options.enum_options_hook # type: ignore
            elif isinstance(enum_options, HookLike):
                initial_enum_options: set[E] = set()
                bindable_set_carrier: Optional[HookLike[set[E]]] = None
            elif enum_options == set() and not allow_none:
                raise ValueError("An empty set of options is not allowed, if allow_none is False")
            elif enum_options == set() and allow_none:
                initial_enum_options: set[E] = set()
                bindable_set_carrier: Optional[HookLike[set[E]]] = None
            else:
                initial_enum_options: set[E] = enum_options.copy() # type: ignore
                bindable_set_carrier: Optional[HookLike[set[E]]] = None
        # End of conditional enum_options processing

        # Validate that the initial enum value is in the options set
        # Skip validation for None when allow_none=True
        if initial_enum_value is not None and initial_enum_value not in initial_enum_options:
            raise ValueError(f"Enum value {initial_enum_value} not in options {initial_enum_options}")

        def is_valid_value(dict_of_values: dict[str, Any]) -> tuple[bool, str]:

            if "enum_value" in dict_of_values:
                enum_value: Optional[E] = dict_of_values["enum_value"] # type: ignore
            else:
                enum_value: Optional[E] = self._component_hooks["enum_value"].value
            
            if "enum_options" in dict_of_values:
                enum_options: set[E] = dict_of_values["enum_options"]
            else:
                enum_options: set[E] = self._component_hooks["enum_options"].value

            if enum_value is None:
                if not allow_none:
                    return False, "Enum value is None, but allow_none is False"
            if enum_options == set():
                if not allow_none:
                    return False, "An empty set of options is not allowed, if allow_none is False"
                if enum_value is not None:
                    return False, f"Enum value {enum_value} is not None, but options are empty"
            if enum_value is not None and enum_value not in enum_options:
                return False, f"Enum value {enum_value} not in options {enum_options}"

            return True, "Verification method passed"

        super().__init__(
            {
                "enum_value": initial_enum_value,
                "enum_options": initial_enum_options
            },
            verification_method=is_valid_value
        )

        # Establish bindings if carriers were provided
        if bindable_enum_carrier is not None:
            self.attach(bindable_enum_carrier, "enum_value", InitialSyncMode.PULL_FROM_TARGET)
        if bindable_set_carrier is not None:
            self.attach(bindable_set_carrier, "enum_options", InitialSyncMode.PULL_FROM_TARGET)

    @property
    def enum_options(self) -> set[E]:
        """
        Get a copy of the available enum options.
        
        Returns:
            A copy of the available enum options set to prevent external modification
        """
        return self._component_hooks["enum_options"].value.copy()
    
    @enum_options.setter
    def enum_options(self, value: set[E]) -> None:
        """
        Set the available enum options.
        
        This setter automatically calls change_enum_options() to ensure proper validation
        and notification.
        
        Args:
            value: New set of available enum options
        """
        self._set_component_values({"enum_options": value}, notify_binding_system=True)

    @property
    def enum_options_hook(self) -> HookLike[set[E]]:
        """
        Get the hook for the enum options.
        """
        return self._component_hooks["enum_options"]
    
    @property
    def enum_value(self) -> Optional[E]:
        """
        Get the currently selected enum value.
        
        Returns:
            The currently selected enum value
        """
        return self._component_hooks["enum_value"].value
    
    @enum_value.setter
    def enum_value(self, value: Optional[E]) -> None:
        """
        Set the selected enum value.
        
        This setter automatically calls set_enum_value() to ensure proper validation
        and notification.
        
        Args:
            value: New selected enum value
        """
        self._set_component_values({"enum_value": value}, notify_binding_system=True)

    @property
    def enum_value_hook(self) -> HookLike[Optional[E]]:
        """
        Get the hook for the enum value.
        """
        return self._component_hooks["enum_value"]

    @property
    def enum_value_not_none(self) -> E:
        """
        Get the current enum value if it is not None.
        
        Returns:
            The current enum value

        Raises:
            ValueError: If the enum value is None
        """
        enum_value = self.enum_value

        if enum_value is None:
            raise ValueError("Enum value is None")

        return enum_value

    def set_enum_value_and_options(self, enum_value: Optional[E], enum_options: set[E]) -> None:
        """
        Set both the enum value and options simultaneously.
        
        This method is useful when you need to update both values atomically
        to maintain consistency. It validates both values and triggers
        appropriate notifications.
        
        Args:
            enum_value: The new enum value to set
            enum_options: The new set of available enum options
            
        Raises:
            ValueError: If the enum value is not in the options set
        """
        self._set_component_values({"enum_value": enum_value, "enum_options": enum_options}, notify_binding_system=True)


    def add_enum_option(self, option: E) -> None:
        """
        Add a new enum option to the available options.
        
        This method adds a new enum option to the available options set,
        using _set_component_values to ensure all changes go through the centralized protocol method.
        
        Args:
            option: The new enum option to add
        """
        if option not in self._component_values["enum_options"]:
            new_options = self._component_values["enum_options"].copy()
            new_options.add(option)
            self._set_component_values({"enum_options": new_options}, notify_binding_system=True)

    def remove_enum_option(self, option: E) -> None:
        """
        Remove an enum option from the available options.
        
        This method removes an enum option from the available options set.
        If the current enum value is the one being removed, it will raise
        a ValueError to maintain consistency.
        
        Args:
            option: The enum option to remove
            
        Raises:
            ValueError: If trying to remove the currently selected enum value
        """
        if option == self._component_values["enum_value"]:
            raise ValueError(f"Cannot remove currently selected enum value {option}")
        
        if option in self._component_values["enum_options"]:
            new_options = self._component_values["enum_options"].copy()
            new_options.remove(option)
            self._set_component_values({"enum_options": new_options}, notify_binding_system=True)

    def __str__(self) -> str:
        """String representation of the observable enum."""
        # Sort options for consistent string representation
        sorted_options = sorted(self._component_hooks['enum_options'].value, key=lambda x: x.value if x is not None else '')
        return f"OE(enum_value={self._component_hooks['enum_value'].value}, enum_options={{{', '.join(str(opt) for opt in sorted_options)}}})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the observable enum."""
        return f"ObservableEnum(enum_value={self._component_hooks['enum_value'].value}, enum_options={self._component_hooks['enum_options'].value})"
    
    def __eq__(self, other: Any) -> bool:
        """
        Compare equality with another observable enum or enum value.
        
        Args:
            other: ObservableEnum or enum value to compare with
            
        Returns:
            True if values are equal, False otherwise
        """
        if isinstance(other, ObservableEnum):
            return (self._component_hooks["enum_value"].value == other._component_hooks["enum_value"].value and 
                   self._component_hooks["enum_options"].value == other._component_hooks["enum_options"].value)
        elif isinstance(other, Enum):
            return self._component_hooks["enum_value"].value == other
        return False
    
    def __ne__(self, other: Any) -> bool:
        """
        Compare inequality with another observable enum or enum value.
        
        Args:
            other: ObservableEnum or enum value to compare with
            
        Returns:
            True if values are not equal, False otherwise
        """
        return not (self == other)
    
    def __hash__(self) -> int:
        """
        Get hash value based on the stored enum value and options.
        
        Returns:
            Hash value of the stored enum value and options
        """
        return hash((self._component_hooks["enum_value"].value, frozenset(self._component_hooks["enum_options"].value)))
    
    def __bool__(self) -> bool:
        """
        Convert the observable enum to boolean based on its value.
        
        Returns:
            Boolean representation of the stored enum value
        """
        return bool(self._component_hooks["enum_value"].value)
    
    @property
    def is_none_enum_value_allowed(self) -> bool:
        """
        Check if None enum value is allowed.
        
        Returns:
            True if None enum value is allowed, False otherwise
        """
        return self._allow_none
    
    def set_allow_none_enum_value(self, allow_none: bool) -> None:
        """
        Set if None enum value is allowed.
        
        Args:
            allow_none: True if None enum value is allowed, False otherwise

        Raises:
            ValueError: If trying to set allow_none to False if enum value is None
        """
        if self._component_hooks["enum_value"].value is None and not allow_none:
            raise ValueError("Cannot set allow_none to False if enum value is None")

        self._allow_none = allow_none