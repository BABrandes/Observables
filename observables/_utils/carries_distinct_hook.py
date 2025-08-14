from abc import ABC

class CarriesDistinctHook(ABC):
    """
    Base abstract class for objects that can participate in bidirectional bindings.
    
    This is the root abstract base class that defines the common interface
    for all observable objects that support bidirectional bindings. It serves
    as a marker interface and common base for the more specific bindable
    interfaces.
    
    Classes implementing this interface can:
    - Participate in bidirectional bindings with other observables
    - Automatically synchronize their values with bound observables
    - Maintain consistency across a network of interconnected objects
    
    This interface is implemented by:
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
        This is an internal interface not intended for direct use by end users.
        Use the concrete observable classes instead.
    """
    pass