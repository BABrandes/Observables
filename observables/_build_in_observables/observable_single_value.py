from typing import Any, Callable, Generic, Optional, TypeVar, overload
from .._utils.hook import Hook
from .._utils.sync_mode import SyncMode
from .._utils.carries_distinct_single_value_hook import CarriesDistinctSingleValueHook
from .._utils.base_observable import BaseObservable

T = TypeVar("T")

class ObservableSingleValue(BaseObservable, CarriesDistinctSingleValueHook[T], Generic[T]):
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
    
    @classmethod
    def _mandatory_component_value_keys(cls) -> set[str]:
        """
        Get the mandatory component value keys.
        """
        return {"value"}

    @overload
    def __init__(self, hook: CarriesDistinctSingleValueHook[T]|Hook[T], validator: Optional[Callable[[T], bool]] = None):
        """Initialize with another observable, establishing a bidirectional binding."""
        ...
    
    @overload
    def __init__(self, value: T, validator: Optional[Callable[[T], bool]] = None):
        """Initialize with a direct value."""
        ...

    def __init__(self, hook_or_value: T | CarriesDistinctSingleValueHook[T] | Hook[T], validator: Optional[Callable[[T], bool]] = None):
        """
        Initialize the ObservableSingleValue.
        
        Args:
            value: Initial value or observable to bind to
            validator: Optional validation function

        Raises:
            ValueError: If the initial value fails validation
        """

        if isinstance(hook_or_value, CarriesDistinctSingleValueHook):
            initial_value: T = hook_or_value._get_single_value()
            hook: Optional[Hook[T]] = hook_or_value._get_single_value_hook()
        elif isinstance(hook_or_value, Hook):
            initial_value: T = hook_or_value._get_callback()
            hook: Optional[Hook[T]] = hook_or_value
        else:
            initial_value: T = hook_or_value
            hook: Optional[Hook[T]] = None

        if validator is not None:
            def verification_method(x: dict[str, Any]) -> tuple[bool, str]:
                if validator(x["value"]) is False:
                    return False, "Value does not pass validation"
                return True, "Verification method passed"
        else:
            def verification_method(x: dict[str, Any]) -> tuple[bool, str]:
                return True, "Verification method passed"
        
        super().__init__(
            {
                "value": initial_value
            },
            {
                "value": Hook(self, self._get_single_value, self._set_single_value)
            },
            verification_method=verification_method,
        )
        
        if hook is not None:
            self.bind_to(hook)

    @property
    def single_value(self) -> T:
        """
        Get the current value.
        
        Returns:
            The current value stored in this observable.
        """
        return self._component_values["value"]
    
    @single_value.setter
    def single_value(self, new_value: T) -> None:
        """
        Set a new value, triggering validation, binding updates, and listener notifications.
        
        Args:
            new_value: The new value to set
            
        Raises:
            ValueError: If the new value fails validation
        """
        self._set_component_values_from_dict({"value": new_value})
    
    def _get_single_value(self) -> T:
        """
        INTERNAL. Do not use this method directly.

        Method to get the current value for binding system.
        
        Returns:
            The current value
        """
        return self._component_values["value"]
    
    def _set_single_value(self, single_value_to_set: T) -> None:
        """
        INTERNAL. Do not use this method directly.

        Method to set value from binding system.
        
        Args:
            single_value_to_set: The new value to set
        """
        self.single_value = single_value_to_set
    
    def _get_single_value_hook(self) -> Hook[T]:
        """
        INTERNAL. Do not use this method directly.

        Method to get hook for binding system. No copy is made!
        
        Returns:
            The hook for the single value
        """
        return self._component_hooks["value"]
    
    def __str__(self) -> str:
        return f"OSV(value={self._get_single_value()})"
    
    def __repr__(self) -> str:
        return f"OSV(value={self._get_single_value()})"
    
    def __eq__(self, other) -> bool:
        """
        Compare equality with another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if values are equal, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self._get_single_value() == other._get_single_value()
        return self._get_single_value() == other
    
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
            return self._get_single_value() < other._get_single_value()
        return self._get_single_value() < other
    
    def __le__(self, other) -> bool:
        """
        Compare if this value is less than or equal to another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is less than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self._get_single_value() <= other._get_single_value()
        return self._get_single_value() <= other
    
    def __gt__(self, other) -> bool:
        """
        Compare if this value is greater than another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is greater than the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self._get_single_value() > other._get_single_value()
        return self._get_single_value() > other
    
    def __ge__(self, other) -> bool:
        """
        Compare if this value is greater than or equal to another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is greater than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self._get_single_value() >= other._get_single_value()
        return self._get_single_value() >= other
    
    def __hash__(self) -> int:
        """
        Get the hash value based on the current value.
        
        Returns:
            Hash value of the current value
        """
        return hash(self._get_single_value())
    
    def __bool__(self) -> bool:
        """
        Convert the value to a boolean.
        
        Returns:
            Boolean representation of the current value
        """
        return bool(self._get_single_value())
    
    def __int__(self) -> int:
        """
        Convert the value to an integer.
        
        Returns:
            Integer representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to an integer
        """
        return int(self._get_single_value()) # type: ignore
    
    def __float__(self) -> float:
        """
        Convert the value to a float.
        
        Returns:
            Float representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to a float
        """
        return float(self._get_single_value()) # type: ignore
    
    def __complex__(self) -> complex:
        """
        Convert the value to a complex number.
        
        Returns:
            Complex representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to a complex number
        """
        return complex(self._get_single_value()) # type: ignore
    
    def __abs__(self) -> float:
        """
        Get the absolute value.
        
        Returns:
            Absolute value of the current value
            
        Raises:
            TypeError: If the value doesn't support absolute value operation
        """
        return abs(self._get_single_value()) # type: ignore
    
    def __round__(self, ndigits=None):
        """
        Round the value to the specified number of decimal places.
        
        Args:
            ndigits: Number of decimal places to round to (default: 0)
            
        Returns:
            Rounded value
            
        Raises:
            TypeError: If the value doesn't support rounding
        """
        return round(self._get_single_value(), ndigits) # type: ignore
    
    def __floor__(self):
        """
        Get the floor value (greatest integer less than or equal to the value).
        
        Returns:
            Floor value
            
        Raises:
            TypeError: If the value doesn't support floor operation
        """
        import math
        return math.floor(self._get_single_value()) # type: ignore
    
    def __ceil__(self):
        """
        Get the ceiling value (smallest integer greater than or equal to the value).
        
        Returns:
            Ceiling value
            
        Raises:
            TypeError: If the value doesn't support ceiling operation
        """
        import math
        return math.ceil(self._get_single_value()) # type: ignore
    
    def __trunc__(self):
        """
        Get the truncated value (integer part of the value).
        
        Returns:
            Truncated value
            
        Raises:
            TypeError: If the value doesn't support truncation
        """
        import math
        return math.trunc(self._get_single_value()) # type: ignore
    
    def bind_to(self, hook: CarriesDistinctSingleValueHook[T]|Hook[T], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Create a bidirectional binding with another observable.
        
        This method establishes a bidirectional binding between this observable and
        another observable. When either observable's value changes, the other will
        automatically update to maintain synchronization.
        
        Args:
            observable: The observable to bind to
            initial_sync_mode: Determines which value is used for initial synchronization
            
        Raises:
            ValueError: If the observable is None
        """
        if hook is None:
            raise ValueError("Cannot bind to None observable")
        if isinstance(hook, CarriesDistinctSingleValueHook):
            hook = hook._get_single_value_hook()
        self._get_single_value_hook().establish_binding(hook, initial_sync_mode)

    def unbind_from(self, hook: CarriesDistinctSingleValueHook[T]|Hook[T]) -> None:
        """
        Remove the bidirectional binding with another observable.
        
        This method removes the bidirectional binding between this observable and
        another observable. After unbinding, changes in one observable will no longer
        affect the other.
        
        Args:
            hook: The hook to unbind from
        """
        if isinstance(hook, CarriesDistinctSingleValueHook):
            hook = hook._get_single_value_hook()
        self._get_single_value_hook().remove_binding(hook)