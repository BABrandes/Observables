"""
Function-like Observables Module

This module provides function-like observables that transform values between inputs and outputs.

Available classes:
- ObservableFunction: Synchronizes multiple values with custom validation logic
- ObservableOneWayFunction: One-way transformation from inputs to outputs
"""

from .x_function import ObservableFunction
from .x_one_way_function import ObservableOneWayFunction

__all__ = [
    'ObservableFunction',
    'ObservableOneWayFunction',
]

