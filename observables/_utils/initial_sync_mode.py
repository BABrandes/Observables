from enum import Enum

class InitialSyncMode(Enum):
    """
    Synchronization modes for establishing bidirectional bindings between observables.
    
    This enum defines how two observables should synchronize their values when
    establishing a bidirectional binding. The initial sync mode determines which
    observable's value is used as the source of truth during binding establishment.
    
    Attributes:
        PUSH_TO_TARGET: The caller pushes its value to the target observable
        PULL_FROM_TARGET: The caller pulls value from the target observable
    
    Example:
        >>> from observables import ObservableSingleValue, InitialSyncMode
        
        >>> # Create observables with different values
        >>> source = ObservableSingleValue(10)
        >>> target = ObservableSingleValue(20)
        
        >>> # Bind with different sync modes
        >>> # This will set target to 10 (source's value)
        >>> source.attach(target.single_value_hook, "value", InitialSyncMode.PUSH_TO_TARGET)
        >>> print(target.single_value)  # Output: 10
        
        >>> # This would set source to 20 (target's value)
        >>> source.attach(target.single_value_hook, "value", InitialSyncMode.PULL_FROM_TARGET)
        >>> print(source.single_value)  # Output: 20
    """
    PUSH_TO_TARGET = "push_to_target"
    PULL_FROM_TARGET = "pull_from_target"