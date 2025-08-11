from typing import Generic, TypeVar, Optional, overload
from enum import Enum
from .._utils._carries_enum import CarriesEnum
from .._utils._carries_bindable_set import CarriesBindableSet
from .._utils._internal_binding_handler import InternalBindingHandler, SyncMode, DEFAULT_SYNC_MODE
from .._utils.observable import Observable

E = TypeVar("E", bound=Enum)

# ObservableEnum implements the Observable protocol for type safety and polymorphism
class ObservableEnum(Observable, CarriesEnum[E], CarriesBindableSet[E], Generic[E]):
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
    def __init__(self, value: E, enum_options: Optional[set[E]] = None):
        """Initialize with a direct enum value."""
        ...

    @overload
    def __init__(self, value: CarriesEnum[E], enum_options: Optional[set[E]] = None):
        """Initialize with another observable enum, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, value: E, enum_options: CarriesBindableSet[E]):
        """Initialize with a set of enum options."""
        ...

    @overload
    def __init__(self, value: CarriesEnum[E], enum_options: set[E]):
        """Initialize with another observable enum, establishing a bidirectional binding."""
        ...

    def __init__(self, value: E | CarriesEnum[E], enum_options: Optional[set[E]] | CarriesBindableSet[E] = None):
        """
        Initialize the ObservableEnum.
        
        Args:
            value: Initial enum value or observable enum to bind to
            enum_options: Set of valid enum options or observable set to bind to
            
        Raises:
            ValueError: If the initial enum value is not in the options set
        """
        super().__init__()

        if isinstance(value, CarriesEnum):
            initial_enum_value: E = value._get_enum()
            bindable_enum_carrier: Optional[CarriesEnum[E]] = value
        else:
            initial_enum_value: E = value
            bindable_enum_carrier: Optional[CarriesEnum[E]] = None

        if enum_options is None:
            initial_enum_options: set[E] = set(initial_enum_value.__class__.__members__.values())
            bindable_set_carrier: Optional[CarriesBindableSet[E]] = None
        elif isinstance(enum_options, CarriesBindableSet):
            initial_enum_options: set[E] = enum_options._get_set().copy()
            bindable_set_carrier: Optional[CarriesBindableSet[E]] = enum_options
        else:
            initial_enum_options: set[E] = enum_options.copy()
            bindable_set_carrier: Optional[CarriesBindableSet[E]] = None

        # Validate that the initial enum value is in the options set
        if initial_enum_value not in initial_enum_options:
            raise ValueError(f"Enum value {initial_enum_value} not in options {initial_enum_options}")

        self._enum_value = initial_enum_value
        self._enum_options = initial_enum_options

        self._enum_value_binding_handler: InternalBindingHandler[E] = InternalBindingHandler(self, self._get_enum, self._set_enum, self._check_enum)
        self._enum_options_binding_handler: InternalBindingHandler[set[E]] = InternalBindingHandler(self, self._get_set, self._set_set, self._check_set)

        # Establish bindings if carriers were provided
        if bindable_enum_carrier is not None:
            self.bind_enum_value_to_observable(bindable_enum_carrier, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
        if bindable_set_carrier is not None:
            self.bind_enum_options_to_observable(bindable_set_carrier, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)

    @property
    def enum_options(self) -> set[E]:
        """
        Get a copy of the available enum options.
        
        Returns:
            A copy of the available enum options set to prevent external modification
        """
        return self._enum_options.copy()
    
    @enum_options.setter
    def enum_options(self, value: set[E]) -> None:
        """
        Set the available enum options.
        
        This setter automatically calls change_enum_options() to ensure proper validation
        and notification.
        
        Args:
            value: New set of available enum options
        """
        self.change_enum_options(value)
    
    @property
    def enum_value(self) -> E:
        """
        Get the currently selected enum value.
        
        Returns:
            The currently selected enum value
        """
        return self._enum_value
    
    @enum_value.setter
    def enum_value(self, value: E) -> None:
        """
        Set the selected enum value.
        
        This setter automatically calls change_enum_value() to ensure proper validation
        and notification.
        
        Args:
            value: New selected enum value
        """
        self.change_enum_value(value)
    
    def _get_enum(self) -> E:
        """Internal method to get enum value for binding system."""
        return self._enum_value
    
    def _set_enum(self, value: E) -> None:
        """Internal method to set enum value from binding system."""
        self.change_enum_value(value)
    
    def _check_enum(self, value: E) -> bool:
        """
        Internal method to check enum value validity for binding system.
        
        Ensures the enum value is always in the available options set.
        """
        return value in self._enum_options
    
    def _get_set(self) -> set[E]:
        """Internal method to get enum options for binding system."""
        return self._enum_options.copy()
    
    def _set_set(self, value: set[E]) -> None:
        """Internal method to set enum options from binding system."""
        self.change_enum_options(value)
    
    def _check_set(self, value: set[E]) -> bool:
        """
        Internal method to check set validity for binding system.
        
        Always accepts any set of enum options.
        """
        return True

    def _get_enum_binding_handler(self) -> InternalBindingHandler[E]:
        """Internal method to get enum value binding handler."""
        return self._enum_value_binding_handler

    def _get_set_binding_handler(self) -> InternalBindingHandler[set[E]]:
        """Internal method to get set binding handler for CarriesBindableSet interface."""
        return self._enum_options_binding_handler

    def change_enum_value(self, new_value: E) -> None:
        """
        Change the enum value to a new value.
        
        This method validates the new enum value, updates the internal state,
        notifies all bound observables, and triggers listener callbacks.
        If the new value is identical to the current one, no action is taken.
        
        Args:
            new_value: The new enum value to set
            
        Raises:
            ValueError: If the new enum value is not in the available options
        """
        if new_value == self._enum_value:
            return

        # Validate that the new value is in the options set
        if new_value not in self._enum_options:
            raise ValueError(f"Enum value {new_value} not in options {self._enum_options}")

        self._enum_value = new_value
        self._enum_value_binding_handler.notify_bindings(new_value)
        self._notify_listeners()

    def change_enum_options(self, new_options: set[E]) -> None:
        """
        Change the available enum options.
        
        This method validates that the current enum value is still valid
        with the new options, updates the internal state, notifies all
        bound observables, and triggers listener callbacks.
        
        Args:
            new_options: The new set of available enum options
            
        Raises:
            ValueError: If the current enum value is not in the new options set
        """
        if new_options == self._enum_options:
            return

        # Validate that the current enum value is still valid
        if self._enum_value not in new_options:
            raise ValueError(f"Current enum value {self._enum_value} not in new options {new_options}")

        self._enum_options = new_options.copy()
        self._enum_options_binding_handler.notify_bindings(self._enum_options)
        self._notify_listeners()

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
        if enum_value not in enum_options:
            raise ValueError(f"Enum value {enum_value} not in options {enum_options}")
        
        if enum_options == self._enum_options and enum_value == self._enum_value:
            return
        
        self._enum_options = enum_options.copy()
        self._enum_value = enum_value
        
        self._enum_options_binding_handler.notify_bindings(enum_options)
        self._enum_value_binding_handler.notify_bindings(enum_value)
        self._notify_listeners()

    def bind_enum_value_to_observable(self, observable: CarriesEnum[E], initial_sync_mode: SyncMode = DEFAULT_SYNC_MODE) -> None:
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
        if observable is None:
            raise ValueError("Cannot bind to None observable")
        self._enum_value_binding_handler.establish_binding(observable._get_enum_binding_handler(), initial_sync_mode)

    def bind_enum_options_to_observable(self, observable: CarriesBindableSet[E], initial_sync_mode: SyncMode = DEFAULT_SYNC_MODE) -> None:
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
        if observable is None:
            raise ValueError("Cannot bind to None observable")
        self._enum_options_binding_handler.establish_binding(observable._get_set_binding_handler(), initial_sync_mode)

    def unbind_enum_value_from_observable(self, observable: CarriesEnum[E]) -> None:
        """
        Remove the bidirectional binding for the enum value with another observable.
        
        This method removes the binding between this observable's enum value and another,
        preventing further automatic synchronization of changes.
        
        Args:
            observable: The observable enum to unbind from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        self._enum_value_binding_handler.remove_binding(observable._get_enum_binding_handler())

    def unbind_enum_options_from_observable(self, observable: CarriesBindableSet[E]) -> None:
        """
        Remove the bidirectional binding for the enum options with another observable.
        
        This method removes the binding between this observable's enum options and another,
        preventing further automatic synchronization of changes.
        
        Args:
            observable: The observable set to unbind from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        self._enum_options_binding_handler.remove_binding(observable._get_set_binding_handler())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        """
        Check the consistency of the binding system.
        
        This method performs comprehensive checks on the binding system to ensure
        that all bindings are in a consistent state and values are properly synchronized.
        
        Returns:
            Tuple of (is_consistent, message) where is_consistent is a boolean
            indicating if the system is consistent, and message provides details
            about any inconsistencies found.
        """
        # Check enum value binding consistency
        binding_state_consistent, binding_state_consistent_message = self._enum_value_binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, f"Enum value binding state inconsistent: {binding_state_consistent_message}"
        
        # Check enum options binding consistency
        binding_state_consistent, binding_state_consistent_message = self._enum_options_binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, f"Enum options binding state inconsistent: {binding_state_consistent_message}"
        
        # Check enum value synchronization
        values_synced, values_synced_message = self._enum_value_binding_handler.check_values_synced()
        if not values_synced:
            return False, f"Enum values not synced: {values_synced_message}"
        
        # Check enum options synchronization
        values_synced, values_synced_message = self._enum_options_binding_handler.check_values_synced()
        if not values_synced:
            return False, f"Enum options not synced: {values_synced_message}"
        
        return True, "Binding system is consistent"

    def add_enum_option(self, option: E) -> None:
        """
        Add a new enum option to the available options.
        
        This method adds a new enum option to the available options set,
        triggering binding updates and listener notifications.
        
        Args:
            option: The new enum option to add
        """
        if option not in self._enum_options:
            self._enum_options.add(option)
            self._enum_options_binding_handler.notify_bindings(self._enum_options)
            self._notify_listeners()

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
        if option == self._enum_value:
            raise ValueError(f"Cannot remove currently selected enum value {option}")
        
        if option in self._enum_options:
            self._enum_options.remove(option)
            self._enum_options_binding_handler.notify_bindings(self._enum_options)
            self._notify_listeners()

    def __str__(self) -> str:
        """String representation of the observable enum."""
        return f"OE(value={self._enum_value}, options={self._enum_options})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the observable enum."""
        return f"ObservableEnum(value={self._enum_value}, options={self._enum_options})"
    
    def __eq__(self, other) -> bool:
        """
        Compare equality with another observable enum or enum value.
        
        Args:
            other: ObservableEnum or enum value to compare with
            
        Returns:
            True if values are equal, False otherwise
        """
        if isinstance(other, ObservableEnum):
            return (self._enum_value == other._enum_value and 
                   self._enum_options == other._enum_options)
        elif isinstance(other, Enum):
            return self._enum_value == other
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
        return hash((self._enum_value, frozenset(self._enum_options)))
    
    def __bool__(self) -> bool:
        """
        Convert the observable enum to boolean based on its value.
        
        Returns:
            Boolean representation of the stored enum value
        """
        return bool(self._enum_value)
    
    def get_observed_values(self) -> tuple[E, set[E]]:
        return (self._enum_value, self._enum_options)
    
    def set_observed_values(self, values: tuple[E, set[E]]) -> None:
        self.set_enum_value_and_options(values[0], values[1])