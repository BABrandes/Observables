from enum import Enum

class InitialSyncMode(Enum):
    """
    Synchronization modes for establishing bidirectional bindings between observables.
    
    This enum defines how two observables should synchronize their values when
    establishing a bidirectional binding. The initial sync mode determines which
    observable's value is used as the source of truth during binding establishment.
    
    Attributes:
        USE_CALLER_VALUE: Use the caller's value for initial synchronization
        USE_TARGET_VALUE: Use the target's value for initial synchronization
    
    Example:
        >>> from observables import ObservableSingleValue, InitialSyncMode
        
        >>> # Create observables with different values
        >>> source = ObservableSingleValue(10)
        >>> target = ObservableSingleValue(20)
        
        >>> # Bind with different sync modes
        >>> # This will set target to 10 (source's value)
        >>> source.attach(target.single_value_hook, "value", InitialSyncMode.USE_CALLER_VALUE)
        >>> print(target.single_value)  # Output: 10
        
        >>> # This would set source to 20 (target's value)
        >>> source.attach(target.single_value_hook, "value", InitialSyncMode.USE_TARGET_VALUE)
        >>> print(source.single_value)  # Output: 20
    """
    USE_CALLER_VALUE = "use_caller_value"
    USE_TARGET_VALUE = "use_target_value"