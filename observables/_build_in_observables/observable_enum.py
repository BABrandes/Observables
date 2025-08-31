from typing import Any, Generic, TypeVar, Optional, overload, Protocol, runtime_checkable, Literal, Mapping
from enum import Enum
from logging import Logger
from .._utils.hook import HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.base_observable import BaseObservable
from .._utils.carries_collective_hooks import CarriesCollectiveHooks
from .._utils.observable_serializable import ObservableSerializable

E = TypeVar("E", bound=Enum)

@runtime_checkable
class ObservableEnumLikeBase(CarriesCollectiveHooks[Any], Protocol[E]):
    """
    Base protocol for observable enum objects.
    """
    
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

    def get_value(self, key: Literal["enum_value", "enum_options"]) -> Any:
        """
        Get the value of the enum value or options.
        """
        ...

    def change_enum_options(self, new_options: set[E]) -> None:
        """
        Change the enum options.
        """
        ...

@runtime_checkable
class ObservableOptionalEnumLike(ObservableEnumLikeBase[E], Protocol[E]):
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

    def change_enum_value(self, new_value: Optional[E]) -> None:
        """
        Change the enum value.
        """
        ...

    def set_enum_value_and_options(self, enum_value: Optional[E], enum_options: set[E]) -> None:
        """
        Set the enum value and options.
        """
        ...

@runtime_checkable
class ObservableEnumLike(ObservableEnumLikeBase[E], Protocol[E]):
    """
    Protocol for observable enum objects.
    """
    
    @property
    def enum_value(self) -> E:
        """
        Get the enum value.
        """
        ...
    
    @enum_value.setter
    def enum_value(self, value: E) -> None:
        """
        Set the enum value.
        """
        ...

    def change_enum_value(self, new_value: E) -> None:
        """
        Change the enum value.
        """
        ...

    @property
    def enum_value_hook(self) -> HookLike[E]:
        """
        Get the hook for the enum value.
        """
        ...

    def set_enum_value_and_options(self, enum_value: E, enum_options: set[E]) -> None:
        """
        Set the enum value and options.
        """
        ...

# ObservableEnum implements the Observable protocol for type safety and polymorphism
class ObservableEnumBase(BaseObservable[Literal["enum_value", "enum_options"], Any], ObservableEnumLikeBase[E], Generic[E]):

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
    
    def change_enum_options(self, new_options: set[E]) -> None:
        """
        Change the enum options.
        """
        self._set_component_values({"enum_options": new_options}, notify_binding_system=True)

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
    
    def __ne__(self, other: Any) -> bool:
        """
        Compare inequality with another observable enum or enum value.
        
        Args:
            other: ObservableEnum or enum value to compare with
            
        Returns:
            True if values are not equal, False otherwise
        """
        return not (self == other)

    def __bool__(self) -> bool:
        """
        Convert the observable enum to boolean based on its value.
        
        Returns:
            Boolean representation of the stored enum value
        """
        return bool(self._component_hooks["enum_value"].value)

# ObservableEnum implements the Observable protocol for type safety and polymorphism
class ObservableOptionalEnum(ObservableEnumBase[E], ObservableSerializable[Literal["enum_value", "enum_options"], "ObservableOptionalEnum"], ObservableOptionalEnumLike[E], Generic[E]):
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
    def __init__(self, enum_value: Optional[E], enum_options: Optional[set[E]] = None, *, logger: Optional[Logger] = None) -> None:
        """Initialize with a direct enum value."""
        ...

    @overload
    def __init__(self, enum_value: HookLike[Optional[E]], enum_options: Optional[set[E]] = None, *, logger: Optional[Logger] = None) -> None:
        """Initialize with another observable enum, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, enum_value: Optional[E], enum_options: HookLike[set[E]], *, logger: Optional[Logger] = None) -> None:
        """Initialize with a set of enum options."""
        ...

    @overload
    def __init__(self, enum_value: HookLike[Optional[E]], enum_options: HookLike[set[E]], *, logger: Optional[Logger] = None) -> None:
        """Initialize with another observable enum, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, observable: ObservableOptionalEnumLike[E], enum_options: None = None, *, logger: Optional[Logger] = None) -> None:
        """Initialize from another ObservableEnumLike object."""
        ...

    def __init__(self, enum_value: Optional[E] | HookLike[Optional[E]] | ObservableOptionalEnumLike[E], enum_options: Optional[set[E]] | HookLike[set[E]] = None, *, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize the ObservableEnum.
        
        Args:
            value: Initial enum value or observable enum to bind to
            enum_options: Set of valid enum options or observable set to bind to
        Raises:
            ValueError: If the initial enum value is not in the options set
        """

        # Flag to track if we've already set enum_options from the hook
        skip_enum_options_processing = False
        
        # Initialize variables
        initial_enum_options: set[E] = set()
        hook_enum_options: Optional[HookLike[set[E]]] = None

        if enum_value is None:
            initial_enum_value: Optional[E] = None
            hook_selected_enum: Optional[HookLike[Optional[E]]] = None

        elif isinstance(enum_value, HookLike):
            initial_enum_value: Optional[E] = enum_value.value
            hook_selected_enum: Optional[HookLike[Optional[E]]] = enum_value

        elif isinstance(enum_value, ObservableOptionalEnumLike):
            initial_enum_value: Optional[E] = enum_value.enum_value
            hook_selected_enum: Optional[HookLike[Optional[E]]] = enum_value.enum_value_hook
            skip_enum_options_processing = True

        else:
            initial_enum_value: Optional[E] = enum_value
            hook_selected_enum: Optional[HookLike[Optional[E]]] = None

        # Only process enum_options if we haven't already set them from the hook
        if not skip_enum_options_processing:
            if enum_options is None:
                if initial_enum_value is None:
                    raise ValueError("initial_enum_value is None and enum_options is None - no way to determine enum options")
                else:
                    if hasattr(initial_enum_value, '__class__') and hasattr(initial_enum_value.__class__, '__members__'):
                        initial_enum_options: set[E] = set(initial_enum_value.__class__.__members__.values()) # type: ignore
                    else:
                        raise ValueError("enum_value is not a valid enum value and enum_options is None - no way to determine enum options")
                hook_enum_options: Optional[HookLike[set[E]]] = None

            elif isinstance(enum_options, HookLike):
                initial_enum_options: set[E] = enum_options.value
                hook_enum_options: Optional[HookLike[set[E]]] = enum_options

            elif isinstance(enum_options, ObservableOptionalEnumLike):
                initial_enum_options: set[E] = enum_options.enum_options # type: ignore
                hook_enum_options: Optional[HookLike[set[E]]] = enum_options.enum_options_hook # type: ignore

            elif isinstance(enum_options, set): # type: ignore
                initial_enum_options: set[E] = enum_options.copy() # type: ignore
                hook_enum_options: Optional[HookLike[set[E]]] = None

            else:
                raise ValueError("enum_options is not a valid set of enum options")
            
        # End of conditional enum_options processing

        if logger is not None:
            logger.debug(f"initial_enum_value: {initial_enum_value}")
            logger.debug(f"initial_enum_options: {initial_enum_options}")
            logger.debug(f"hook_selected_enum: {hook_selected_enum}")
            logger.debug(f"hook_enum_options: {hook_enum_options}")

        self._internal_construct_from_values(
            {
                "enum_value": initial_enum_value,
                "enum_options": initial_enum_options
            },
            logger=logger,
        )

        # Establish bindings if carriers were provided
        if hook_selected_enum is not None:
            self.attach(hook_selected_enum, "enum_value", InitialSyncMode.PULL_FROM_TARGET)
        if hook_enum_options is not None:
            self.attach(hook_enum_options, "enum_options", InitialSyncMode.PULL_FROM_TARGET)

    def _internal_construct_from_values(
        self,
        initial_values: Mapping[Literal["enum_value", "enum_options"], Any],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """
        Construct an ObservableEnum instance.
        """

        def is_valid_value(x: Mapping[Literal["enum_value", "enum_options"], Any]) -> tuple[bool, str]:

            if "enum_value" in x:
                enum_value: Optional[E] = x["enum_value"] # type: ignore
            else:
                enum_value: Optional[E] = self._component_hooks["enum_value"].value
            
            if "enum_options" in x:
                enum_options: set[E] = x["enum_options"]
            else:
                enum_options: set[E] = self._component_hooks["enum_options"].value

            if enum_value is not None and enum_value not in enum_options:
                return False, f"Enum value {enum_value} not in options {enum_options}"

            return True, "Verification method passed"

        super().__init__(
            initial_values,
            verification_method=is_valid_value,
            logger=logger
        )

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

    def change_enum_value(self, new_value: Optional[E]) -> None:
        """
        Change the enum value.
        """
        self._set_component_values({"enum_value": new_value}, notify_binding_system=True)

    @property
    def enum_value_hook(self) -> HookLike[Optional[E]]:
        """
        Get the hook for the enum value.
        """
        return self._component_hooks["enum_value"]

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

    def __eq__(self, other: Any) -> bool:
        """
        Compare equality with another observable enum or enum value.
        
        Args:
            other: ObservableEnum or enum value to compare with
            
        Returns:
            True if values are equal, False otherwise
        """
        if isinstance(other, ObservableOptionalEnumLike):
            return (self.get_value("enum_value") == other.get_value("enum_value") and 
                   self.get_value("enum_options") == other.get_value("enum_options"))
        elif isinstance(other, Enum):
            return self.get_value("enum_value") == other
        return False
    
    def __hash__(self) -> int:
        """
        Get hash value based on the stored enum value and options.
        
        Returns:
            Hash value of the stored enum value and options
        """
        try:
            return hash((self.get_value("enum_value"), frozenset(self.get_value("enum_options"))))
        except (AttributeError, KeyError):
            # Fallback to object identity if not fully initialized
            return id(self)
    
    
# ObservableEnum implements the Observable protocol for type safety and polymorphism
class ObservableEnum(ObservableEnumBase[E], ObservableSerializable[Literal["enum_value", "enum_options"], "ObservableEnum"], ObservableEnumLike[E], Generic[E]):
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
    def __init__(self, enum_value: E, enum_options: Optional[set[E]] = None, *, logger: Optional[Logger] = None) -> None:
        """Initialize with a direct enum value."""
        ...

    @overload
    def __init__(self, enum_value: HookLike[E], enum_options: Optional[set[E]] = None, *, logger: Optional[Logger] = None) -> None:
        """Initialize with another observable enum, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, enum_value: E, enum_options: HookLike[set[E]], *, logger: Optional[Logger] = None) -> None:
        """Initialize with a set of enum options."""
        ...

    @overload
    def __init__(self, enum_value: HookLike[E], enum_options: HookLike[set[E]], *, logger: Optional[Logger] = None) -> None:
        """Initialize with another observable enum, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, observable: ObservableEnumLike[E], enum_options: None = None, *, logger: Optional[Logger] = None) -> None:
        """Initialize from another ObservableEnumLike object."""
        ...

    def __init__(self, enum_value: E | HookLike[E] | ObservableEnumLike[E], enum_options: Optional[set[E]] | HookLike[set[E]] = None, *, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize the ObservableEnum.
        
        Args:
            value: Initial enum value or observable enum to bind to
            enum_options: Set of valid enum options or observable set to bind to
        Raises:
            ValueError: If the initial enum value is not in the options set
        """

        # Initialize variables
        initial_enum_options: set[E] = set()
        hook_enum_options: Optional[HookLike[set[E]]] = None

        if enum_value is None: # type: ignore
            raise ValueError("enum_value is None")
        
        elif isinstance(enum_value, HookLike):
            initial_enum_value: E = enum_value.value
            hook_enum_value: Optional[HookLike[E]] = enum_value
            skip_enum_options_processing = False

        elif isinstance(enum_value, ObservableEnumLike):
            initial_enum_value: E = enum_value.enum_value
            hook_enum_value: Optional[HookLike[E]] = enum_value.enum_value_hook
            initial_enum_options: set[E] = enum_value.enum_options
            hook_enum_options: Optional[HookLike[set[E]]] = enum_value.enum_options_hook
            skip_enum_options_processing = True

        else:
            # This is a direct enum value
            initial_enum_value: E = enum_value
            hook_enum_value: Optional[HookLike[E]] = None
            skip_enum_options_processing = False

        # Only process enum_options if we haven't already set them from the hook
        if not skip_enum_options_processing:

            if enum_options is None:
                if hasattr(initial_enum_value, '__class__') and hasattr(initial_enum_value.__class__, '__members__'):
                    initial_enum_options: set[E] = set(initial_enum_value.__class__.__members__.values()) # type: ignore
                else:
                    raise ValueError("enum_value is not a valid enum value and enum_options is None - no way to determine enum options")
                hook_enum_options: Optional[HookLike[set[E]]] = None

            elif isinstance(enum_options, HookLike):
                initial_enum_options: set[E] = enum_options.value
                hook_enum_options: Optional[HookLike[set[E]]] = enum_options

            elif isinstance(enum_options, ObservableEnumLike):
                initial_enum_options: set[E] = enum_options.enum_options # type: ignore
                hook_enum_options: Optional[HookLike[set[E]]] = enum_options.enum_options_hook # type: ignore

            elif isinstance(enum_options, set): # type: ignore
                initial_enum_options: set[E] = enum_options.copy() # type: ignore
                hook_enum_options: Optional[HookLike[set[E]]] = None

            else:
                raise ValueError("enum_options is not a valid set of enum options")
        # End of conditional enum_options processing

        if logger is not None:
            logger.debug(f"initial_enum_value: {initial_enum_value}")
            logger.debug(f"initial_enum_options: {initial_enum_options}")
            logger.debug(f"hook_enum_value: {hook_enum_value}")
            logger.debug(f"hook_enum_options: {hook_enum_options}")

        self._internal_construct_from_values(
            {
                "enum_value": initial_enum_value,
                "enum_options": initial_enum_options
            },
            logger=logger
        )

        # Establish bindings if hooks were provided
        if hook_enum_value is not None:
            self.attach(hook_enum_value, "enum_value", InitialSyncMode.PULL_FROM_TARGET)
        if hook_enum_options is not None:
            self.attach(hook_enum_options, "enum_options", InitialSyncMode.PULL_FROM_TARGET)

    def _internal_construct_from_values(
        self,
        initial_values: Mapping[Literal["enum_value", "enum_options"], Any],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """
        Construct an ObservableEnum instance.
        """

        def is_valid_value(x: Mapping[Literal["enum_value", "enum_options"], Any]) -> tuple[bool, str]:

            if "enum_value" in x:
                enum_value: E = x["enum_value"] # type: ignore
            else:
                enum_value: E = self._component_hooks["enum_value"].value
            
            if "enum_options" in x:
                enum_options: set[E] = x["enum_options"]
            else:
                enum_options: set[E] = self._component_hooks["enum_options"].value

            if enum_value not in enum_options:
                return False, f"Enum value {enum_value} not in options {enum_options}"

            return True, "Verification method passed"

        super().__init__(
            initial_values,
            verification_method=is_valid_value,
            logger=logger
        )

    @property
    def enum_value(self) -> E:
        """
        Get the currently selected enum value.
        
        Returns:
            The currently selected enum value
        """
        return self._component_hooks["enum_value"].value
    
    @enum_value.setter
    def enum_value(self, value: E) -> None:
        """
        Set the selected enum value.
        
        This setter automatically calls set_enum_value() to ensure proper validation
        and notification.
        
        Args:
            value: New selected enum value
        """
        self._set_component_values({"enum_value": value}, notify_binding_system=True)

    def change_enum_value(self, new_value: E) -> None:
        """
        Change the enum value.
        """
        self._set_component_values({"enum_value": new_value}, notify_binding_system=True)

    @property
    def enum_value_hook(self) -> HookLike[E]:
        """
        Get the hook for the enum value.
        """
        return self._component_hooks["enum_value"]

    def set_enum_value_and_options(self, enum_value: E, enum_options: set[E]) -> None:
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

    def __eq__(self, other: Any) -> bool:
        """
        Compare equality with another observable enum or enum value.
        
        Args:
            other: ObservableEnum or enum value to compare with
            
        Returns:
            True if values are equal, False otherwise
        """
        if isinstance(other, ObservableEnumLike):
            return (self.get_value("enum_value") == other.get_value("enum_value") and 
                   self.get_value("enum_options") == other.get_value("enum_options"))
        elif isinstance(other, Enum):
            return self.get_value("enum_value") == other
        return False
    
    def __hash__(self) -> int:
        """
        Get hash value based on the stored enum value and options.
        
        Returns:
            Hash value of the stored enum value and options
        """
        try:
            return hash((self.get_value("enum_value"), frozenset(self.get_value("enum_options"))))
        except (AttributeError, KeyError):
            # Fallback to object identity if not fully initialized
            return id(self)