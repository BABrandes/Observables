from typing import TypeVar, Protocol, runtime_checkable
from .hook import HookLike
from .base_carries_distinct_hook import BaseCarriesDistinctHook

K = TypeVar("K")
V = TypeVar("V")

@runtime_checkable
class CarriesDistinctDictHook(BaseCarriesDistinctHook, Protocol[K, V]):
    """
    Protocol for observables that carry a dictionary and can participate in bindings via. a hook.
    
    This protocol defines the interface that must be implemented by any
    observable class that wants to support bidirectional bindings for dictionaries via. a hook.
    It extends the base BaseCarriesDistinctHook protocol with specific methods for
    dictionary management.
    
    Classes implementing this protocol must provide:
    - Methods to get and set dictionaries
    - Validation logic for dictionary changes
    - Access to the internal hook
    
    This protocol is implemented by:
    - ObservableDict
    
    Note:
        This protocol can be used directly by end users for type hints and
        interface definitions when working with dictionary observables.
        The individual methods remain internal implementation details.
    """

    @property
    def distinct_dict_hook(self) -> HookLike[dict[K, V]]:
        """
        Method to get the hook for dictionary.
        
        This method provides access to the internal hook that
        manages bidirectional bindings for this observable. The binding
        system uses this hook to establish and manage connections.
        
        Returns:
            The internal hook for dictionary
            
        Note:
            This is an internal method called by the hook system.
            It should not be called directly by users.
        """
        ...

    @property
    def distinct_dict_reference(self) -> dict[K, V]:
        """
        Get the current value of the dictionary.
        """
        ...