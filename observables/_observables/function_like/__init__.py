"""
Function-like Observables Module

This module provides function-like observables that transform values between inputs and outputs.

Available classes:
- ObservableFunction: Synchronizes multiple values with custom validation logic
- ObservableOneWayFunction: One-way transformation from inputs to outputs
- ObservableTransfer: Bidirectional transformation (deprecated, use ObservableOneWayFunction instead)
"""

from .observable_function import ObservableFunction
from .observable_one_way_function import ObservableOneWayFunction
from .observable_transfer import ObservableTransfer

__all__ = [
    'ObservableFunction',
    'ObservableOneWayFunction',
    'ObservableTransfer',
]

