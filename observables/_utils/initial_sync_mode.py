from enum import Enum

class InitialSyncMode(Enum):
    """
    Synchronization modes for establishing bidirectional bindings between observables.
    
    This enum defines how two observables should synchronize their values when
    establishing a bidirectional binding. The initial sync mode determines which
    observable's value is used as the source of truth during binding establishment.
    
    Attributes:
        SELF_IS_UPDATED: The self observable is updated from the other observable
        SELF_UPDATES: The self observable updates the other observable
    
    Example:
        >>> from observables import ObservableSingleValue, SyncMode
        
        >>> # Create observables with different values
        >>> source = ObservableSingleValue(10)
        >>> target = ObservableSingleValue(20)
        
        >>> # Bind with different sync modes
        >>> # This will set target to 10 (source's value)
        >>> source.bind_to_observable(target, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        >>> print(target.value)  # Output: 10
        
        >>> # This would set source to 20 (target's value)
        >>> # source.bind_to_observable(target, SyncMode.UPDATE_VALUE_FROM_OBSERVABLE)
    """
    SELF_IS_UPDATED = "self_is_updated"
    SELF_UPDATES = "self_updates"