from logging import Logger
from typing import Any, Callable, Generic, Optional, TypeVar, overload, Protocol, runtime_checkable, Literal, Mapping
from .._hooks.hook_like import HookLike
from .._utils.carries_hooks_like import CarriesHooksLike
from .._utils.base_observable import BaseObservable
from .._utils.observable_serializable import ObservableSerializable
from .._utils.submission_error import SubmissionError

T = TypeVar("T")

@runtime_checkable
class ObservableSingleValueLike(CarriesHooksLike[Any, T], Protocol[T]):
    """
    Protocol for observable single value objects.
    """
    
    @property
    def value(self) -> T:
        """
        Get the value.
        """
        ...
    
    @value.setter
    def value(self, value: T) -> None:
        """
        Set the value.
        """
        ...

    def change_value(self, value: T) -> None:
        """
        Change the value (lambda-friendly method).
        """
        ...

    @property
    def hook(self) -> HookLike[T]:
        """
        Get the hook for the value.
        """
        ...
    
class ObservableSingleValue(BaseObservable[Literal["value"], Any, T, Any, "ObservableSingleValue"], ObservableSingleValueLike[T], ObservableSerializable[Literal["value"], T], Generic[T]):
    """
    Observable wrapper for a single value with validation and bidirectional binding.
    
    ObservableSingleValue wraps any value type in a reactive container that supports
    listeners, validation, and bidirectional synchronization. It's the simplest and
    most commonly used observable type.
    
    Type Parameters:
        T: The type of value being stored. Can be any Python type - int, str, float,
           list, dict, custom objects, etc. The type is preserved through binding and
           validated through the validator function if provided.
    
    Multiple Inheritance:
        - BaseObservable: Core observable functionality with hook management
        - ObservableSingleValueLike[T]: Protocol for single value interface
        - ObservableSerializable: Support for serialization callbacks
        - Generic[T]: Type-safe value storage and operations
    
    Three Notification Mechanisms:
        1. **Listeners**: Synchronous callbacks via `add_listeners()`
        2. **Subscribers**: Async notifications via `add_subscriber()` (if Publisher mixin)
        3. **Connected Hooks**: Bidirectional sync via `connect_hook()`
    
    Key Features:
        - **Type Safety**: Full generic type support with type checking
        - **Validation**: Optional validator function called before value changes
        - **Bidirectional Binding**: Changes propagate in both directions
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
        
        Bidirectional binding::
        
            # Create two observables
            celsius = ObservableSingleValue(25.0)
            display = ObservableSingleValue(0.0)
            
            # Bind them - display adopts celsius value
            celsius.connect_hook(display.hook, "value", "use_caller_value")
            
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

    @overload
    def __init__(self, single_value: T, validator: Optional[Callable[[T], tuple[bool, str]]] = None, logger: Optional[Logger] = None) -> None:
        """Initialize with a direct value."""
        ...
    
    @overload
    def __init__(self, hook: HookLike[T], validator: Optional[Callable[[T], tuple[bool, str]]] = None, logger: Optional[Logger] = None) -> None:
        """Initialize with another observable, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, observable: ObservableSingleValueLike[T], validator: Optional[Callable[[T], tuple[bool, str]]] = None, logger: Optional[Logger] = None) -> None:
        """Initialize with another observable, establishing a bidirectional binding."""
        ...

    def __init__(self, observable_or_hook_or_value: T | HookLike[T], validator: Optional[Callable[[T], tuple[bool, str]]] = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize an ObservableSingleValue.
        
        This constructor supports three initialization patterns:
        
        1. **Direct value**: Pass a value directly
        2. **From hook**: Pass a HookLike to bind to
        3. **From observable**: Pass another ObservableSingleValue to bind to
        
        Args:
            observable_or_hook_or_value: Can be one of three types:
                - T: A direct value (int, str, list, custom object, etc.)
                - HookLike[T]: A hook to bind to (establishes bidirectional connection)
                - ObservableSingleValueLike[T]: Another observable to bind to
            validator: Optional validation function that takes a value and returns
                (success: bool, message: str). Called before any value change.
                If validation fails (success=False), the change is rejected with
                ValueError. Default is None (no validation).
            logger: Optional logger for debugging observable operations. If provided,
                hook connections, value changes, and errors will be logged.
                Default is None.
        
        Raises:
            ValueError: If validator is provided and the initial value fails validation.
        
        Example:
            Three initialization patterns::
            
                # 1. Direct value
                age = ObservableSingleValue(25)
                
                # 2. From another observable (creates binding)
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

        if isinstance(observable_or_hook_or_value, HookLike):
            initial_value: T = observable_or_hook_or_value.value # type: ignore
            hook: Optional[HookLike[T]] = observable_or_hook_or_value #type: ignore
        elif isinstance(observable_or_hook_or_value, ObservableSingleValueLike):
            initial_value: T = observable_or_hook_or_value.value # type: ignore
            hook = observable_or_hook_or_value.hook # type: ignore
        else:
            # Assume the value is T
            initial_value: T = observable_or_hook_or_value
            hook = None

        validator: Optional[Callable[[T], tuple[bool, str]]] = validator

        initial_component_values_or_hooks: dict[Literal["value"], T] = {"value": initial_value}
        super().__init__(
            initial_component_values_or_hooks=initial_component_values_or_hooks,
            verification_method= lambda x: (True, "Verification method passed") if validator is None else validator(x["value"]),
            secondary_hook_callbacks={},
            logger=logger
        )
        
        if hook is not None:
            self.connect_hook(hook, "value", "use_target_value") # type: ignore

    @property
    def value(self) -> T:
        """
        Get the current value.
        """
        return self._primary_hooks["value"].value
    
    @value.setter
    def value(self, value: T) -> None:
        """
        Set a new value, triggering validation, binding updates, and listener notifications.
        
        Args:
            value: The new value to set
            
        Raises:
            ValueError: If the new value fails validation
        """
        success, msg = self.submit_value("value", value)
        if not success:
            raise SubmissionError(msg, value, "value")

    def change_value(self, value: T) -> None:
        """
        Change the value (lambda-friendly method).
        
        This method is equivalent to setting the .value property but can be used
        in lambda expressions and other contexts where property assignment isn't suitable.
        
        Args:
            new_value: The new value to set
        """
        if value == self._primary_hooks["value"].value:
            return
        self.value = value
    
    @property
    def hook(self) -> HookLike[T]:
        """
        Get the hook for the value.
        
        This hook can be used for binding operations with other observables.
        """
        return self._primary_hooks["value"]
    
    
    def __str__(self) -> str:
        return f"OSV(value={self._primary_hooks['value'].value})"
    
    def __repr__(self) -> str:
        """Return a string representation of the observable."""
        return f"ObservableSingleValue({self._primary_hooks['value'].value!r})"
    
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
            return self._primary_hooks["value"].value < other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value < other
    
    def __le__(self, other: Any) -> bool:
        """
        Compare if this value is less than or equal to another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is less than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self._primary_hooks["value"].value <= other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value <= other
    
    def __gt__(self, other: Any) -> bool:
        """
        Compare if this value is greater than another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is greater than the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self._primary_hooks["value"].value > other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value > other
    
    def __ge__(self, other: Any) -> bool:
        """
        Compare if this value is greater than or equal to another value or observable.
        
        Args:
            other: Value or ObservableSingleValue to compare with
            
        Returns:
            True if this value is greater than or equal to the other, False otherwise
        """
        if isinstance(other, ObservableSingleValue):
            return self._primary_hooks["value"].value >= other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value >= other
    
    def __bool__(self) -> bool:
        """
        Convert the value to a boolean.
        
        Returns:
            Boolean representation of the current value
        """
        return bool(self._primary_hooks["value"].value)
    
    def __int__(self) -> int:
        """
        Convert the value to an integer.
        
        Returns:
            Integer representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to an integer
        """
        return int(self._primary_hooks["value"].value) # type: ignore
    
    def __float__(self) -> float:
        """
        Convert the value to a float.
        
        Returns:
            Float representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to a float
        """
        return float(self._primary_hooks["value"].value) # type: ignore
    
    def __complex__(self) -> complex:
        """
        Convert the value to a complex number.
        
        Returns:
            Complex representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to a complex number
        """
        return complex(self._primary_hooks["value"].value) # type: ignore
    
    def __abs__(self) -> float:
        """
        Get the absolute value.
        
        Returns:
            Absolute value of the current value
            
        Raises:
            TypeError: If the value doesn't support absolute value operation
        """
        return abs(self._primary_hooks["value"].value) # type: ignore
    
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
        return round(self._primary_hooks["value"].value, ndigits) # type: ignore
    
    def __floor__(self) -> int:
        """
        Get the floor value (greatest integer less than or equal to the value).
        
        Returns:
            Floor value
            
        Raises:
            TypeError: If the value doesn't support floor operation
        """
        import math
        return math.floor(self._primary_hooks["value"].value) # type: ignore
    
    def __ceil__(self) -> int:
        """
        Get the ceiling value (smallest integer greater than or equal to the value).
        
        Returns:
            Ceiling value
            
        Raises:
            TypeError: If the value doesn't support ceiling operation
        """
        import math
        return math.ceil(self._primary_hooks["value"].value) # type: ignore
    
    def __trunc__(self) -> int:
        """
        Get the truncated value (integer part of the value).
        
        Returns:
            Truncated value
            
        Raises:
            TypeError: If the value doesn't support truncation
        """
        import math
        return math.trunc(self._primary_hooks["value"].value) # type: ignore

    #### ObservableSerializable implementation ####

    def get_value_references_for_serialization(self) -> Mapping[Literal["value"], T]:
        return {"value": self._primary_hooks["value"].value}

    def set_value_references_from_serialization(self, values: Mapping[Literal["value"], T]) -> None:
        self.value = values["value"]