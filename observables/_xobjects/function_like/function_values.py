"""
Function Values - Parameter object for observable functions

This module provides a typed parameter object that standardizes how values
are passed to function callables in observable functions.
"""

from typing import Generic, Mapping, TypeVar
from dataclasses import dataclass

K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type


@dataclass(frozen=True, slots=True)
class FunctionValues(Generic[K, V]):
    """
    Immutable container for values passed to observable function callables.
    
    This provides a clean, typed interface for accessing both submitted (changed)
    values and current (complete state) values in function callables.
    
    Attributes:
        submitted: The values that were just changed/submitted.
                   This is a subset of all values, containing only the keys
                   that triggered the function call.
        current: The complete current state of all values.
                 This contains all keys with their current values, providing
                 full context for the function callable.
    
    Example:
        >>> def my_function(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
        ...     # Access what changed
        ...     if 'field1' in values.submitted:
        ...         new_value = values.submitted['field1']
        ...         # Access complete current state
        ...         other_field = values.current.get('field2', 0)
        ...         return (True, {'field2': 100 - new_value})
        ...     return (True, {})
    """
    
    submitted: Mapping[K, V]
    current: Mapping[K, V]
    
    def __repr__(self) -> str:
        """Return a readable representation."""
        return f"FunctionValues(submitted={dict(self.submitted)}, current={dict(self.current)})"

