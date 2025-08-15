from typing import Any, Generic, TypeVar, Optional, overload, Protocol, runtime_checkable
from enum import Enum
from .._utils.carries_distinct_enum_hook import CarriesDistinctEnumHook
from .._utils.carries_distinct_set_hook import CarriesDistinctSetHook
from .._utils.hook import Hook, HookLike
from .._utils.sync_mode import SyncMode
from .._utils.base_observable import BaseObservable

E = TypeVar("E", bound=Enum)

@runtime_checkable
class ObservableEnumLike(CarriesDistinctEnumHook[E], CarriesDistinctSetHook[E], Protocol[E]):
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

    def set_enum_value_and_options(self, enum_value: Optional[E], enum_options: set[E]) -> None:
        """
        Set the enum value and options.
        """
        ...

    def bind_enum_value_to_observable(self, observable_or_hook: CarriesDistinctEnumHook[E]|HookLike[E], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding for the enum value with another observable.
        """
        ...

    def bind_enum_options_to_observable(self, observable_or_hook: CarriesDistinctSetHook[E], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding for the enum options with another observable.
        """
        ...

    def unbind_enum_value_from_observable(self, observable_or_hook: CarriesDistinctEnumHook[E]|HookLike[E]) -> None:
        """
        Remove the bidirectional binding for the enum value with another observable.
        """
        ...
        
    def unbind_enum_options_from_observable(self, observable_or_hook: CarriesDistinctSetHook[E]) -> None:
        """
        Remove the bidirectional binding for the enum options with another observable.
        """
        ...

    def bind_to(self, observable: "ObservableEnumLike[E]", initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding with another observable enum.
        """
        ...
        
    def unbind_from(self, observable: "ObservableEnumLike[E]") -> None:
        """
        Remove the bidirectional binding with another observable enum.
        """
        ...

# ObservableEnum implements the Observable protocol for type safety and polymorphism
class ObservableEnum(BaseObservable, ObservableEnumLike[E], Generic[E]):
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

    @classmethod
    def _mandatory_component_value_keys(cls) -> set[str]:
        """
        Get the mandatory component value keys.
        """
        return {"enum_value", "enum_options"}

    @overload
    def __init__(self, enum_value: Optional[E], enum_options: Optional[set[E]] = None, allow_none: bool = True):
        """Initialize with a direct enum value."""
        ...

    @overload
    def __init__(self, enum_value: CarriesDistinctEnumHook[E], enum_options: Optional[set[E]] = None, allow_none: bool = True):
        """Initialize with another observable enum, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, enum_value: Optional[E], enum_options: CarriesDistinctSetHook[E], allow_none: bool = True):
        """Initialize with a set of enum options."""
        ...

    @overload
    def __init__(self, enum_value: CarriesDistinctEnumHook[E], enum_options: set[E], allow_none: bool = True):
        """Initialize with another observable enum, establishing a bidirectional binding."""
        ...

    def __init__(self, enum_value: Optional[E] | CarriesDistinctEnumHook[E], enum_options: Optional[set[E]] | CarriesDistinctSetHook[E] = None, allow_none: bool = True):
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

        if enum_value is None:
            if not allow_none:
                raise ValueError("None is not allowed as an enum value, if allow_none is False")
            initial_enum_value: Optional[E] = None
            bindable_enum_carrier: Optional[CarriesDistinctEnumHook[E]] = None
        elif isinstance(enum_value, CarriesDistinctEnumHook):
            initial_enum_value: E = enum_value._get_enum_value()
            bindable_enum_carrier: Optional[CarriesDistinctEnumHook[E]] = enum_value
        else:
            initial_enum_value: E = enum_value
            bindable_enum_carrier: Optional[CarriesDistinctEnumHook[E]] = None

        if enum_options is None:
            initial_enum_options: set[E] = set(initial_enum_value.__class__.__members__.values())
            bindable_set_carrier: Optional[CarriesDistinctSetHook[E]] = None
        elif isinstance(enum_options, CarriesDistinctSetHook):
            initial_enum_options: set[E] = enum_options._get_set_value().copy()
            bindable_set_carrier: Optional[CarriesDistinctSetHook[E]] = enum_options
        else:
            if enum_options == set() and not allow_none:
                raise ValueError("An empty set of options is not allowed, if allow_none is False")
            elif enum_options == set() and allow_none:
                initial_enum_options: set[E] = set()
                bindable_set_carrier: Optional[CarriesDistinctSetHook[E]] = None
            else:
                initial_enum_options: set[E] = enum_options.copy()
                bindable_set_carrier: Optional[CarriesDistinctSetHook[E]] = None

        # Validate that the initial enum value is in the options set
        if initial_enum_value not in initial_enum_options:
            raise ValueError(f"Enum value {initial_enum_value} not in options {initial_enum_options}")

        def verification_method(x: dict[str, Any]) -> tuple[bool, str]:

            enum_value = x["enum_value"]
            enum_options = x["enum_options"]

            if enum_value is None:
                if not allow_none:
                    return False, "Enum value is None, but allow_none is False"
            if enum_options == set():
                if not allow_none:
                    return False, "An empty set of options is not allowed, if allow_none is False"
                if enum_value is not None:
                    return False, f"Enum value {enum_value} is not None, but options are empty"
            if not isinstance(enum_options, set):
                return False, "Enum options is not a set"
            if not enum_value in enum_options:
                return False, f"Enum value {enum_value} not in options {enum_options}"

            return True, "Verification method passed"

        super().__init__(
            {
                "enum_value": initial_enum_value,
                "enum_options": initial_enum_options
            },
            {
                "enum_value": Hook(self, self._get_enum_value, self._set_enum_value),
                "enum_options": Hook(self, self._get_set_value, self._set_set_value)
            },
            verification_method=verification_method
        )

        # Establish bindings if carriers were provided
        if bindable_enum_carrier is not None:
            self.bind_enum_value_to(bindable_enum_carrier, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        if bindable_set_carrier is not None:
            self.bind_enum_options_to(bindable_set_carrier, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)

    @property
    def enum_options(self) -> set[E]:
        """
        Get a copy of the available enum options.
        
        Returns:
            A copy of the available enum options set to prevent external modification
        """
        return self._component_values["enum_options"].copy()
    
    @enum_options.setter
    def enum_options(self, value: set[E]) -> None:
        """
        Set the available enum options.
        
        This setter automatically calls change_enum_options() to ensure proper validation
        and notification.
        
        Args:
            value: New set of available enum options
        """
        self.set_enum_options(value)
    
    @property
    def enum_value(self) -> Optional[E]:
        """
        Get the currently selected enum value.
        
        Returns:
            The currently selected enum value
        """
        return self._component_values["enum_value"]
    
    @enum_value.setter
    def enum_value(self, value: Optional[E]) -> None:
        """
        Set the selected enum value.
        
        This setter automatically calls set_enum_value() to ensure proper validation
        and notification.
        
        Args:
            value: New selected enum value
        """
        self.set_enum_value(value)

    @property
    def enum_value_not_none(self) -> E:
        """
        Get the current enum value if it is not None.
        
        Returns:
            The current enum value

        Raises:
            ValueError: If the enum value is None
        """

        enum_value = self._component_values["enum_value"]

        if enum_value is None:
            raise ValueError("Enum value is None")

        return enum_value

    
    def _get_enum_value(self) -> Optional[E]:
        """
        INTERNAL. Do not use this method directly.

        Method to get enum value for binding system. No copy is made!
        
        Returns:
            The current enum value
        """
        return self._component_values["enum_value"]
    
    def _set_enum_value(self, value: Optional[E]) -> None:
        """
        INTERNAL. Do not use this method directly.

        Method to set enum value from binding system.
        
        Args:
            value: The new enum value to set
        """
        self.set_enum_value(value)
    
    def _get_set_value(self) -> set[E]:
        """
        INTERNAL. Do not use this method directly.

        Method to get enum options for binding system. No copy is made!
        
        Returns:
            The current enum options
        """
        return self._component_values["enum_options"]
    
    def _set_set_value(self, value: set[E]) -> None:
        """
        INTERNAL. Do not use this method directly.

        Method to set enum options from binding system.
        
        Args:
            value: The new enum options to set
        """
        self.set_enum_options(value)
    
    def set_enum_value(self, new_value: Optional[E]) -> None:
        """
        Set the enum value to a new value.
        
        This method updates the enum value, ensuring that it's valid
        according to the current available options and allow_none setting.
        
        Args:
            new_value: The new enum value to set
            
        Raises:
            ValueError: If the new enum value is not in the available options
        """
        self.set_observed_values((new_value, self._get_set_value()))

    def set_enum_options(self, new_options: set[E]) -> None:
        """
        Set the available enum options.
        
        This method validates that the current enum value is still valid
        with the new options, updates the internal state, notifies all
        bound observables, and triggers listener callbacks.
        
        Args:
            new_options: The new set of available enum options
            
        Raises:
            ValueError: If the current enum value is not in the new options set
            ValueError: If the new options set is empty
        """
        self.set_observed_values((self._get_enum_value(), new_options))

    def _get_set_hook(self) -> Hook[set[E]]:
        """
        Get the hook for the enum options.
        """
        return self._component_hooks["enum_options"]
    
    def get_set_value(self) -> set[E]:
        """
        Get the current value of the enum options set as a copy.
        
        Returns:
            A copy of the current enum options set value
        """
        return self._component_values["enum_options"].copy()
    
    def _get_enum_hook(self) -> Hook[E]:
        """
        Get the hook for the enum value.
        """
        return self._component_hooks["enum_value"]
    
    def get_enum_value(self) -> Optional[E]:
        """
        Get the current enum value.
        
        Returns:
            The current enum value
        """
        return self._component_values["enum_value"]

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
        self.set_observed_values((enum_value, enum_options))

    def bind_enum_value_to(self, hook: CarriesDistinctEnumHook[E]|Hook[E], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding for the enum value with another observable.
        
        This method creates a bidirectional binding between this observable's enum value
        and another observable's enum value, ensuring that changes to either observable
        are automatically propagated to the other.
        
        Args:
            observable: The observable enum to bind to
            initial_sync_mode: How to synchronize values initially
            
        Raises:
            ValueError: If observable is None
        """
        if hook is None:
            raise ValueError("Cannot bind to None hook")
        if isinstance(hook, CarriesDistinctEnumHook):
            hook = hook._get_enum_hook()
        self._get_enum_hook().establish_binding(hook, initial_sync_mode)

    def bind_enum_options_to(self, hook: CarriesDistinctSetHook[E]|Hook[set[E]], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding for the enum options with another observable.
        
        This method creates a bidirectional binding between this observable's enum options
        and another observable's set, ensuring that changes to either observable
        are automatically propagated to the other.
        
        Args:
            observable: The observable set to bind to
            initial_sync_mode: How to synchronize values initially
            
        Raises:
            ValueError: If observable is None
        """
        if hook is None:
            raise ValueError("Cannot bind to None hook")
        if isinstance(hook, CarriesDistinctSetHook):
            hook = hook._get_set_hook()
        self._get_set_hook().establish_binding(hook, initial_sync_mode)

    def bind_to(self, observable: ObservableEnumLike[E], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding with another observable enum.
        """
        self.bind_enum_value_to(observable._get_enum_hook(), initial_sync_mode)
        self.bind_enum_options_to(observable._get_set_hook(), initial_sync_mode)

    def unbind_enum_value_from(self, hook: CarriesDistinctEnumHook[E]|Hook[E]) -> None:
        """
        Remove the bidirectional binding for the enum value with another observable.
        
        This method removes the binding between this observable's enum value and another,
        preventing further automatic synchronization of changes.
        
        Args:
            observable: The observable enum to unbind from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        if isinstance(hook, CarriesDistinctEnumHook):
            hook = hook._get_enum_hook()
        self._get_enum_hook().remove_binding(hook)

    def unbind_enum_options_from(self, hook: CarriesDistinctSetHook[E]|Hook[set[E]]) -> None:
        """
        Remove the bidirectional binding for the enum options with another observable.
        
        This method removes the binding between this observable's enum options and another,
        preventing further automatic synchronization of changes.
        
        Args:
            observable: The observable set to unbind from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        if isinstance(hook, CarriesDistinctSetHook):
            hook = hook._get_set_hook()
        self._get_set_hook().remove_binding(hook)

    def unbind_from(self, observable: ObservableEnumLike[E]) -> None:
        """
        Remove the bidirectional binding with another observable enum.
        """
        self.unbind_enum_value_from(observable._get_enum_hook())
        self.unbind_enum_options_from(observable._get_set_hook())

    def add_enum_option(self, option: E) -> None:
        """
        Add a new enum option to the available options.
        
        This method adds a new enum option to the available options set,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            option: The new enum option to add
        """
        if option not in self._get_set_value():
            new_options = self._get_set_value().copy()
            new_options.add(option)
            self.set_observed_values((self._get_enum_value(), new_options))

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
        if option == self._get_enum_value():
            raise ValueError(f"Cannot remove currently selected enum value {option}")
        
        if option in self._get_set_value():
            new_options = self._get_set_value().copy()
            new_options.remove(option)
            self.set_observed_values((self._get_enum_value(), new_options))

    def __str__(self) -> str:
        """String representation of the observable enum."""
        return f"OE(value={self._get_enum_value()}, options={self._get_set_value()})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the observable enum."""
        return f"ObservableEnum(value={self._get_enum_value()}, options={self._get_set_value()})"
    
    def __eq__(self, other) -> bool:
        """
        Compare equality with another observable enum or enum value.
        
        Args:
            other: ObservableEnum or enum value to compare with
            
        Returns:
            True if values are equal, False otherwise
        """
        if isinstance(other, ObservableEnum):
            return (self._get_enum_value() == other._get_enum_value() and 
                   self._get_set_value() == other._get_set_value())
        elif isinstance(other, Enum):
            return self._get_enum_value() == other
        return False
    
    def __ne__(self, other) -> bool:
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
        return hash((self._get_enum_value(), frozenset(self._get_set_value())))
    
    def __bool__(self) -> bool:
        """
        Convert the observable enum to boolean based on its value.
        
        Returns:
            Boolean representation of the stored enum value
        """
        return bool(self._get_enum_value())
    
    def get_observed_component_values(self) -> tuple[E, set[E]]:
        """
        Get the values of all observables that are bound to this observable.
        
        This method is part of the Observable protocol and provides access to
        the current values of all bound observables.
        
        Returns:
            A tuple containing (enum_value, enum_options)
        """
        return (self._get_enum_value(), self._get_set_value())
    
    def set_observed_values(self, values: tuple[E, set[E]]) -> None:
        """
        Set the values of all observables that are bound to this observable.
        
        This method is part of the Observable protocol and allows external
        systems to update this observable's values. It handles all internal
        state changes, binding updates, and listener notifications.
        
        Args:
            values: A tuple containing (enum_value, enum_options)
        """

        # Update internal state
        self._set_component_values_from_dict({"enum_value": values[0], "enum_options": values[1]})

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
        if self._get_enum_value() is None and not allow_none:
            raise ValueError("Cannot set allow_none to False if enum value is None")

        self._allow_none = allow_none