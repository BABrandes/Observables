from typing import Protocol, runtime_checkable, TypeVar
from .carries_hooks import CarriesHooks

HK = TypeVar("HK", contravariant=True)

@runtime_checkable
class CarriesDistinctHook(CarriesHooks[HK], Protocol[HK]):
    """
    Protocol for objects that can participate in bidirectional bindings.
    
    Classes implementing this protocol can:
    - Participate in bidirectional bindings with other observables
    - Automatically synchronize their values with bound observables
    - Maintain consistency across a network of interconnected objects
    
    This protocol is implemented by:
    - CarriesBindableSingleValue
    - CarriesBindableList
    - CarriesBindableSet
    - CarriesBindableDict
    - ObservableSingleValue
    - ObservableList
    - ObservableSet
    - ObservableDict
    - ObservableSelectionOption
    
    Note:
        This protocol can be used directly by end users for type hints and
        interface definitions when working with observable objects.
    """

    pass