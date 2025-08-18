
from typing import TypeVar, Protocol, runtime_checkable
from .hook import HookLike
from .carries_distinct_hook import CarriesDistinctHook

T = TypeVar("T")
HK = TypeVar("HK", contravariant=True)
    
@runtime_checkable
class CarriesDistinctSetHook(CarriesDistinctHook[HK], Protocol[T, HK]):
    """
    Protocol for observables that carry a set and can participate in bindings via. a hook.
    
    This protocol defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for sets via. a hook.
    It extends the base CarriesDistinctHook protocol with specific methods for
    set management.
    
    Classes implementing this protocol must provide:
    - Methods to get and set sets
    - Validation logic for set changes
    - Access to the internal hook
    
    This protocol is implemented by:
    - ObservableSet
    - ObservableSelectionOption (for options binding)
    
    Note:
        This protocol can be used directly by end users for type hints and
        interface definitions when working with set observables.
        The individual methods remain internal implementation details.
    """

    @property
    def distinct_set_hook(self) -> HookLike[set[T]]:
        """
        Method to get the hook for set.
        
        This method provides access to the internal hook that
        manages bidirectional bindings for this observable. The binding
        system uses this hook to establish and manage connections.
        
        Returns:
            The internal hook for set
            
        Note:
            This is an internal method called by the hook system.
            It should not be called directly by users.
        """
        ...

    @property
    def distinct_set_reference(self) -> set[T]:
        """
        Method to get the current value of the set.
        
        Returns:
            The current value of the set
        """
        ...