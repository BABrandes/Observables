from logging import Logger
from typing import Any, Callable, Generic, Optional, TypeVar, overload, Protocol, runtime_checkable, Literal, Mapping
from .._utils.hook import HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.carries_hooks import CarriesHooks
from .._utils.base_observable import BaseObservable
from .._utils.observable_serializable import ObservableSerializable

T = TypeVar("T")

@runtime_checkable
class ObservableSingleValueLike(CarriesHooks[Any], Protocol[T]):
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

    def change_value(self, new_value: T) -> None:
        """
        Change the value (lambda-friendly method).
        """
        ...

    @property
    def value_hook(self) -> HookLike[T]:
        """
        Get the hook for the value.
        """
        ...
    

class ObservableSingleValue(BaseObservable[Literal["value"], Any], ObservableSerializable[Literal["value"], "ObservableSingleValue"], ObservableSingleValueLike[T], Generic[T]):
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
        >>> age.value = 30  # Triggers listener and validation
        Age changed!
        
        >>> # Create bidirectional binding
        >>> age_copy = ObservableSingleValue(age)
        >>> age_copy.value = 35  # Updates both observables
        >>> print(age.value, age_copy.value)
        35 35
        
        >>> # Lambda-friendly method for event handlers
        >>> button.on_click(lambda: age.change_value(40))
    
    Args:
        value: The initial value or another ObservableSingleValue to bind to
        validator: Optional function to validate values before setting them
    
    Raises:
        ValueError: If the initial value fails validation
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
        Initialize the ObservableSingleValue.
        
        Args:
            value: Initial value or observable to bind to
            validator: Optional validation function

        Raises:
            ValueError: If the initial value fails validation
        """

        if isinstance(observable_or_hook_or_value, HookLike):
            initial_value: T = observable_or_hook_or_value.value # type: ignore
            hook: Optional[HookLike[T]] = observable_or_hook_or_value
        elif isinstance(observable_or_hook_or_value, ObservableSingleValueLike):
            initial_value: T = observable_or_hook_or_value.value # type: ignore
            hook: Optional[HookLike[T]] = observable_or_hook_or_value.value_hook # type: ignore
        else:
            # Assume the value is T
            initial_value: T = observable_or_hook_or_value
            hook: Optional[HookLike[T]] = None

        self._internal_construct_from_values(
            initial_values={"value": initial_value}, # type: ignore
            logger=logger,
            validator=validator,
        )
        
        if hook is not None:
            self.connect(hook, "value", InitialSyncMode.USE_TARGET_VALUE)

    def _internal_construct_from_values(
        self,
        initial_values: Mapping[Literal["value"], T],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """
        Construct an ObservableSingleValue instance.
        """

        validator: Optional[Callable[[T], tuple[bool, str]]] = kwargs.get("validator")

        super().__init__(
            initial_values,
            verification_method= lambda x: (True, "Verification method passed") if validator is None else validator(x["value"]),
            secondary_hook_callbacks={},
            logger=logger
        )

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
        if value == self._primary_hooks["value"].value:
            return
        self._set_component_values({"value": value}, notify_binding_system=True)

    def change_value(self, new_value: T) -> None:
        """
        Change the value (lambda-friendly method).
        
        This method is equivalent to setting the .value property but can be used
        in lambda expressions and other contexts where property assignment isn't suitable.
        
        Args:
            new_value: The new value to set
        """
        if new_value == self._primary_hooks["value"].value:
            return
        self._set_component_values({"value": new_value}, notify_binding_system=True)
    
    @property
    def value_hook(self) -> HookLike[T]:
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
            return self._primary_hooks["value"].value < other._primary_hooks["value"].value
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
            return self._primary_hooks["value"].value <= other._primary_hooks["value"].value
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
            return self._primary_hooks["value"].value > other._primary_hooks["value"].value
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
            return self._primary_hooks["value"].value >= other._primary_hooks["value"].value
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