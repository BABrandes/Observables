from typing import Any, Callable, Generic, Optional, TypeVar
from logging import Logger

from .._hooks.hook_aliases import Hook, ReadOnlyHook
from .._carries_hooks.x_single_value_base import XValueBase
from .._carries_hooks.carries_single_hook_protocol import CarriesSingleHookProtocol
from .._nexus_system.submission_error import SubmissionError

T = TypeVar("T")

class ObservableSingleValue(XValueBase[T], CarriesSingleHookProtocol[T], Generic[T]):
    """
    Observable wrapper for a single value with transitive synchronization via Nexus fusion.

    ObservableSingleValue exposes a hook that references a Nexus. When observables are joined,
    their Nexuses undergo fusion, creating transitive synchronization networks:
    
        obs_a.join(obs_b)  # Creates fusion domain AB
        obs_c.join(obs_d)  # Creates fusion domain CD
        obs_b.join(obs_c)  # Fuses domains → ABCD
        # All four observables now share one Nexus and synchronize transitively
    
    This is the simplest and most commonly used observable type, supporting validation,
    listeners, and bidirectional synchronization through Nexus fusion.

    Type Parameters:
        T: The type of value being stored. Can be any Python type - int, str, float,
           list, dict, custom objects, etc. The type is preserved through linking and
           validated through the validator function if provided.

    Multiple Inheritance:
        - BaseObservable: Core observable functionality with hook management
        - ObservableSingleValueProtocol[T]: Protocol for single value interface
        - ObservableSerializable: Support for serialization callbacks
        - Generic[T]: Type-safe value storage and operations

    Three Notification Mechanisms:
        1. **Listeners**: Synchronous callbacks via `add_listeners()`
        2. **Subscribers**: Async notifications via `add_subscriber()` (if Publisher mixin)
        3. **Connected Hooks**: Bidirectional sync via `link()`

    Key Features:
        - **Type Safety**: Full generic type support with type checking
        - **Validation**: Optional validator function called before value changes
        - **Bidirectional Linking**: Changes propagate in both directions
        - **Listener Notifications**: Callbacks triggered on value changes
        - **Thread Safety**: All operations protected by NexusManager's lock
        - **Memory Efficient**: Shares centralized storage via HookNexus
    
    Example:
        Basic usage::
        
            from observables import ObservableSingleValue
            
            # Simple observable
            name = ObservableSingleValue("John")
            print(name.value)  # "John"
            
            # With validation
            def validate_age(age):
                if 0 <= age <= 150:
                    return True, "Valid age"
                return False, "Age must be between 0 and 150"
            
            age = ObservableSingleValue(25, validator=validate_age)
            age.value = 30  # ✓ Valid
            
            try:
                age.value = 200  # ✗ Raises ValueError
            except ValueError as e:
                print(f"Validation failed: {e}")
        
        Bidirectional linking::

            # Create two observables
            celsius = ObservableSingleValue(25.0)
            display = ObservableSingleValue(0.0)

            # Link them - display adopts celsius value
            celsius.join(display.hook, "value", "use_caller_value")

            # Changes propagate bidirectionally
            celsius.value = 30.0
            print(display.value)  # 30.0

            display.value = 20.0
            print(celsius.value)  # 20.0
        
        With listeners::
        
            counter = ObservableSingleValue(0)
            counter.add_listeners(lambda: print(f"Count: {counter.value}"))
            
            counter.value = 1  # Prints: "Count: 1"
            counter.value = 2  # Prints: "Count: 2"
    """

    def __init__(self, value_or_hook: T | Hook[T] | ReadOnlyHook[T] | CarriesSingleHookProtocol[T], validator: Optional[Callable[[T], tuple[bool, str]]] = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize an ObservableSingleValue.
        
        This constructor supports three initialization patterns:
        
        1. **Direct value**: Pass a value directly
        2. **From hook**: Pass a Hook to join to
        3. **From observable**: Pass another ObservableSingleValue to join to
        
        Args:
            observable_or_hook_or_value: Can be one of three types:
                - T: A direct value (int, str, list, custom object, etc.)
                - Hook[T]: A hook to join to (establishes bidirectional connection)
                - ObservableSingleValueProtocol[T]: Another observable to join to
            validator: Optional validation function that takes a value and returns
                (success: bool, message: str). Called before any value change.
                If validation fails (success=False), the change is rejected with
                SubmissionError. Default is None (no validation).
            logger: Optional logger for debugging observable operations. If provided,
                hook connections, value changes, and errors will be logged.
                Default is None.
        
        Raises:
            SubmissionError: If validator is provided and the initial value fails validation.
        
        Example:
            Three initialization patterns::
            
                # 1. Direct value
                age = ObservableSingleValue(25)
                
                # 2. From another observable (creates join)
                age_copy = ObservableSingleValue(age)
                age_copy.value = 30  # Both update to 30
                
                # 3. With validation
                def validate_positive(x):
                    return (x > 0, "Must be positive")
                
                count = ObservableSingleValue(
                    10,
                    validator=validate_positive,
                    logger=my_logger
                )
        """

        # Initialize the base class
        super().__init__(
            value_or_hook=value_or_hook,
            verification_method=validator,
            invalidate_callback=None,
            logger=logger
        )

    #########################################################
    # Access
    #########################################################

    @property
    def hook(self) -> Hook[T]:
        """
        Get the hook for the value (thread-safe).
        
        This hook can be used for joining operations with other observables.
        """
        with self._lock:
            return self._get_single_hook()

    @property
    def value(self) -> T:
        """
        Get the current value (thread-safe).
        """
        with self._lock:
            return self._get_single_value()

    @value.setter
    def value(self, value: T) -> None:
        """
        Set a new value (thread-safe).
        
        Args:
            new_value: The new value to set
            
        Raises:
            SubmissionError: If validation fails or value cannot be set
        """
        success, msg = self.change_value(value, raise_submission_error_flag=False)
        if not success:
            raise SubmissionError(msg, value, "value")

    def change_value(self, new_value: T, *, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Change the value (lambda-friendly method).
        
        This method is equivalent to setting the .value property but can be used
        in lambda expressions and other contexts where property assignment isn't suitable.
        
        Args:
            new_value: The new value to set
            
        Raises:
            SubmissionError: If the new value fails validation
        """
        success, msg = self._submit_value("value", new_value)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, new_value, "value")
        return success, msg

    #########################################################
    # Standard object methods
    #########################################################
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"OSV(value={self.value})"
    
    def __repr__(self) -> str:
        """Return a string representation of the observable."""
        return f"ObservableSingleValue({self.value!r})"
    
    def __hash__(self) -> int:
        """Make the observable hashable for use in sets and as dictionary keys."""
        return hash(id(self))
    
    def __eq__(self, other: object) -> bool:
        """Check if this observable equals another object."""
        if isinstance(other, ObservableSingleValue):
            return id(self) == id(other) # type: ignore
        return False
    
    def __ne__(self, other: Any) -> bool:
        """
        Compare inequality with another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if values are not equal, False otherwise
        """
        return not (self == other)
    
    def __lt__(self, other: Any) -> bool:
        """
        Compare if this value is less than another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is less than the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self.value < other.value # type: ignore
        return self.value < other
    
    def __le__(self, other: Any) -> bool:
        """
        Compare if this value is less than or equal to another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is less than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self.value <= other.value # type: ignore
        return self.value <= other
    
    def __gt__(self, other: Any) -> bool:
        """
        Compare if this value is greater than another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is greater than the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self.value > other.value # type: ignore
        return self.value > other
    
    def __ge__(self, other: Any) -> bool:
        """
        Compare if this value is greater than or equal to another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is greater than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self.value >= other.value # type: ignore
        return self.value >= other
    
    def __bool__(self) -> bool:
        """
        Convert the value to a boolean.
        
        Returns:
            Boolean representation of the current value
        """
        return bool(self.value)
    
    def __int__(self) -> int:
        """
        Convert the value to an integer.
        
        Returns:
            Integer representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to an integer
        """
        return int(self.value) # type: ignore
    
    def __float__(self) -> float:
        """
        Convert the value to a float.
        
        Returns:
            Float representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to a float
        """
        return float(self.value) # type: ignore
    
    def __complex__(self) -> complex:
        """
        Convert the value to a complex number.
        
        Returns:
            Complex representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to a complex number
        """
        return complex(self.value) # type: ignore
    
    def __abs__(self) -> float:
        """
        Get the absolute value.
        
        Returns:
            Absolute value of the current value
            
        Raises:
            TypeError: If the value doesn't support absolute value operation
        """
        return abs(self.value) # type: ignore
    
    def __round__(self, ndigits: Optional[int] = None) -> float:
        """
        Round the value to the specified number of decimal places.
        
        Args:
            ndigits: Number of decimal places to round to (default: 0)
            
        Returns:
            Rounded value
            
        Raises:
            TypeError: If the value doesn't support rounding
        """
        return round(self.value, ndigits) # type: ignore
    
    def __floor__(self) -> int:
        """
        Get the floor value (greatest integer less than or equal to the value).
        
        Returns:
            Floor value
            
        Raises:
            TypeError: If the value doesn't support floor operation
        """
        import math
        return math.floor(self.value) # type: ignore
    
    def __ceil__(self) -> int:
        """
        Get the ceiling value (smallest integer greater than or equal to the value).
        
        Returns:
            Ceiling value
            
        Raises:
            TypeError: If the value doesn't support ceiling operation
        """
        import math
        return math.ceil(self.value) # type: ignore
    
    def __trunc__(self) -> int:
        """
        Get the truncated value (integer part of the value).
        
        Returns:
            Truncated value
            
        Raises:
            TypeError: If the value doesn't support truncation
        """
        import math
        return math.trunc(self.value) # type: ignore