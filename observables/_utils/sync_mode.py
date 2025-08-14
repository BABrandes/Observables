from enum import Enum

class SyncMode(Enum):
    """
    Synchronization modes for establishing bidirectional bindings between observables.
    
    This enum defines how two observables should synchronize their values when
    establishing a bidirectional binding. The initial sync mode determines which
    observable's value is used as the source of truth during binding establishment.
    
    Attributes:
        UPDATE_SELF_FROM_OBSERVABLE: Use the target observable's value for initial sync
        UPDATE_OBSERVABLE_FROM_SELF: Use this observable's value for initial sync
    
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
    UPDATE_SELF_FROM_OBSERVABLE = "update_self_from_observable"
    UPDATE_OBSERVABLE_FROM_SELF = "update_observable_from_self"