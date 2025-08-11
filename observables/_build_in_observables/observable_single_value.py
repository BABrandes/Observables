from typing import Callable, Generic, Optional, TypeVar, overload
from .._utils._listening_base import ListeningBase
from .._utils._internal_binding_handler import InternalBindingHandler, SyncMode, DEFAULT_SYNC_MODE
from .._utils._carries_bindable_single_value import CarriesBindableSingleValue
from .._utils.observable import Observable

T = TypeVar("T")

class ObservableSingleValue(ListeningBase, Observable, CarriesBindableSingleValue[T], Generic[T]):
    """
    An observable wrapper around a single value that supports bidirectional bindings and validation.
    
    This class provides a reactive wrapper around any value type, allowing other objects to
    observe changes and establish bidirectional bindings. It supports custom validation,
    listener notifications, and automatic synchronization with other observables.
    
    Features:
    - Bidirectional bindings with other ObservableSingleValue instances
    - Custom validation through validator functions
    - Listener notification system for change events
    - Rich comparison and arithmetic operations
    - Type-safe generic implementation
    
    Example:
        >>> # Create an observable with validation
        >>> age = ObservableSingleValue(25, validator=lambda x: 0 <= x <= 150)
        >>> age.add_listeners(lambda: print("Age changed!"))
        >>> age.set_value(30)  # Triggers listener and validation
        Age changed!
        
        >>> # Create bidirectional binding
        >>> age_copy = ObservableSingleValue(age)
        >>> age_copy.set_value(35)  # Updates both observables
        >>> print(age.value, age_copy.value)
        35 35
    
    Args:
        value: The initial value or another ObservableSingleValue to bind to
        validator: Optional function to validate values before setting them
    
    Raises:
        ValueError: If the initial value fails validation
    """
    
    @overload
    def __init__(self, value: CarriesBindableSingleValue[T], validator: Optional[Callable[[T], bool]] = None):
        """Initialize with another observable, establishing a bidirectional binding."""
        ...
    
    @overload
    def __init__(self, value: T, validator: Optional[Callable[[T], bool]] = None):
        """Initialize with a direct value."""
        ...

    def __init__(self, value: T | CarriesBindableSingleValue[T], validator: Optional[Callable[[T], bool]] = None):
        """
        Initialize the ObservableSingleValue.
        
        Args:
            value: Initial value or observable to bind to
            validator: Optional validation function
        """
        super().__init__()
        self._validator: Optional[Callable[[T], bool]] = validator
        if isinstance(value, CarriesBindableSingleValue):
            initial_value: T = value._get_single_value()
            bindable_single_value_carrier: Optional[CarriesBindableSingleValue[T]] = value
        else:
            initial_value: T = value
            bindable_single_value_carrier: Optional[CarriesBindableSingleValue[T]] = None
        # Validate initial value
        if self._validator and not self._validator(initial_value):
            raise ValueError(f"Invalid value: {initial_value}")
        self._value = initial_value
        self._binding_handler: InternalBindingHandler[T] = InternalBindingHandler(self, self._get_single_value, self._set_single_value, self._check_single_value)
        if bindable_single_value_carrier is not None:
            self.bind_to_observable(bindable_single_value_carrier)

    @property
    def value(self) -> T:
        """
        Get the current value.
        
        Returns:
            The current value stored in this observable.
        """
        return self._value
    
    def set_value(self, new_value: T) -> None:
        """
        Set a new value, triggering validation, binding updates, and listener notifications.
        
        This method validates the new value, updates the internal state, notifies
        all bound observables, and triggers listener callbacks. If the new value
        is identical to the current value, no action is taken.
        
        Args:
            new_value: The new value to set
            
        Raises:
            ValueError: If the new value fails validation
        """
        if new_value == self._value:
            return

        # Validate the new value
        if self._validator and not self._validator(new_value):
            raise ValueError(f"Invalid value: {new_value}")

        self._value = new_value
        self._binding_handler.notify_bindings(new_value)
        self._notify_listeners()
    
    def _get_single_value(self) -> T:
        """Internal method to get the current value for binding system."""
        return self._value
    
    def _set_single_value(self, single_value_to_set: T) -> None:
        """Internal method to set value from binding system."""
        self.set_value(single_value_to_set)
    
    def _check_single_value(self, single_value_to_check: T) -> bool:
        """Internal method to check value validity for binding system."""
        if self._validator:
            return self._validator(single_value_to_check)
        return True
    
    def _get_single_value_binding_handler(self) -> InternalBindingHandler[T]:
        """Internal method to get binding handler for binding system."""
        return self._binding_handler
        
    def __str__(self) -> str:
        """String representation of the observable."""
        return f"OSV(value={self._value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the observable."""
        return f"OSV(value={self._value})"
    
    def __eq__(self, other) -> bool:
        """
        Compare equality with another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if values are equal, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self._value == other._value
        return self._value == other
    
    def __ne__(self, other) -> bool:
        """
        Compare inequality with another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if values are not equal, False otherwise
        """
        return not (self == other)
    
    def __lt__(self, other) -> bool:
        """
        Compare if this value is less than another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is less than the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self._value < other._value
        return self._value < other
    
    def __le__(self, other) -> bool:
        """
        Compare if this value is less than or equal to another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is less than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self._value <= other._value
        return self._value <= other
    
    def __gt__(self, other) -> bool:
        """
        Compare if this value is greater than another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is greater than the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self._value > other._value
        return self._value > other
    
    def __ge__(self, other) -> bool:
        """Compare with another value or observable"""
        if isinstance(other, ObservableSingleValue):
            return self._value >= other._value
        return self._value >= other
    
    def __hash__(self) -> int:
        """Hash based on the current value"""
        return hash(self._value)
    
    def __bool__(self) -> bool:
        """Boolean conversion"""
        return bool(self._value)
    
    def __int__(self) -> int:
        """Integer conversion"""
        return int(self._value) # type: ignore
    
    def __float__(self) -> float:
        """Float conversion"""
        return float(self._value) # type: ignore
    
    def __complex__(self) -> complex:
        """Complex conversion"""
        return complex(self._value) # type: ignore
    
    def __abs__(self) -> float:
        """Absolute value"""
        return abs(self._value) # type: ignore
    
    def __round__(self, ndigits=None):
        """Round the value"""
        return round(self._value, ndigits) # type: ignore
    
    def __floor__(self):
        """Floor division"""
        import math
        return math.floor(self._value) # type: ignore
    
    def __ceil__(self):
        """Ceiling division"""
        import math
        return math.ceil(self._value) # type: ignore
    
    def __trunc__(self):
        """Truncate the value"""
        import math
        return math.trunc(self._value) # type: ignore
    
    def bind_to_observable(self, observable: CarriesBindableSingleValue[T], initial_sync_mode: SyncMode = DEFAULT_SYNC_MODE) -> None:
        if observable is None:
            raise ValueError("Cannot bind to None observable")
        self._binding_handler.establish_binding(observable._get_single_value_binding_handler(), initial_sync_mode)

    def unbind_from_observable(self, observable: "ObservableSingleValue[T]") -> None:
        self._binding_handler.remove_binding(observable._get_single_value_binding_handler())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        binding_state_consistent, binding_state_consistent_message = self._binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._binding_handler.check_values_synced()
        if not values_synced:
            return False, values_synced_message
        return True, "Binding system is consistent"
    
    def get_observed_values(self) -> tuple[T]:
        return (self._value,)
    
    def set_observed_values(self, values: tuple[T]) -> None:
        self.set_value(values[0])