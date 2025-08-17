
from typing import TypeVar, runtime_checkable, Protocol
from .hook import HookLike
from .carries_distinct_hook import CarriesDistinctHook

T = TypeVar("T")

@runtime_checkable
class CarriesDistinctSingleValueHook(CarriesDistinctHook, Protocol[T]):
    """
    Protocol for observables that carry a single value and can participate in bindings via. a hook.
    
    This protocol defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for single values.
    It extends the base BaseCarriesDistinctHook protocol with specific methods for
    single value management.
    
    Classes implementing this protocol must provide:
    - Methods to get and set single values
    - Validation logic for value changes
    - Access to the internal binding handler
    
    This protocol is implemented by:
    - ObservableSingleValue
    - ObservableSelectionOption (for selected_option binding)
    
    Note:
        This protocol can be used directly by end users for type hints and
        interface definitions when working with single value observables.
        The individual methods remain internal implementation details.
    """

    @property
    def distinct_single_value_hook(self) -> HookLike[T]:
        """
        Method to get the hook for the single value.
        
        Returns:
            The hook for the single value
        """
        ...

    @property
    def distinct_single_value_reference(self) -> T:
        """
        Method to get the current value of the single value.
        
        Returns:
            The current value of the single value
        """
        ...