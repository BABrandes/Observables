from typing import Protocol

class BaseCarriesDistinctHook(Protocol):
    """
    Base protocol for objects that can participate in bidirectional bindings.
    
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