
from typing import TypeVar, Protocol, runtime_checkable
from .hook import HookLike
from .carries_distinct_hook import CarriesDistinctHook

T = TypeVar("T")

@runtime_checkable
class CarriesDistinctTupleHook(CarriesDistinctHook, Protocol[T]):
    """
    Protocol for observables that carry a tuple and can participate in bindings via. a hook.
    
    This protocol defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for tuples via. a hook.
    It extends the base BaseCarriesDistinctHook protocol with specific methods for
    tuple management.
    
    Classes implementing this protocol must provide:
    - Methods to get and set tuples
    - Validation logic for tuple changes
    - Access to the internal hook
    
    This protocol is implemented by:
    - ObservableTuple
    
    Note:
        This protocol can be used directly by end users for type hints and
        interface definitions when working with tuple observables.
        The individual methods remain internal implementation details.
    """

    @property
    def distinct_tuple_hook(self) -> HookLike[tuple[T, ...]]:
        """
        Method to get the hook for tuple.
        
        This method provides access to the internal hook that
        manages bidirectional bindings for this observable. The binding
        system uses this hook to establish and manage connections.
        
        Returns:
            The internal hook for tuple
            
        Note:
            This is an internal method called by the hook system.
            It should not be called directly by users.
        """
        ...

    @property
    def distinct_tuple_reference(self) -> tuple[T, ...]:
        """
        Method to get the current value of the tuple.
        
        Returns:
            The current value of the tuple
        """
        ...