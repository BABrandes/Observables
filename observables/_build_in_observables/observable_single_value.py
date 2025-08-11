from abc import ABC, abstractmethod
from typing import Callable, Generic, Literal, Optional, TypeVar, overload
from .._utils._listening_base import ListeningBase
from .._utils._internal_binding_handler import InternalBindingHandler, SyncMode
from .._utils._carries_bindable_single_value import CarriesBindableSingleValue

T = TypeVar("T")

class ObservableSingleValue(ListeningBase, CarriesBindableSingleValue[T], Generic[T]):

    def __init__(self, value: T):
        super().__init__()
        self._value: T = value
        self._binding_handler: InternalBindingHandler[T] = InternalBindingHandler(self, self._get_single_value, self._set_single_value, self._check_single_value)

    @property
    def value(self) -> T:
        return self._value
    
    def set_value(self, new_value: T) -> None:
        if new_value == self._value:
            return

        self._value = new_value
        if not self._binding_handler._is_updating_from_binding:
            self._binding_handler.notify_bindings(new_value)
        self._notify_listeners()
    
    def _get_single_value(self) -> T:
        return self._value
    
    def _set_single_value(self, single_value_to_set: T) -> None:
        self.set_value(single_value_to_set)
    
    def _check_single_value(self, single_value_to_check: T) -> bool:
        return True
    
    def _get_single_value_binding_handler(self) -> InternalBindingHandler[T]:
        return self._binding_handler
        
    def __str__(self) -> str:
        return f"OSV(value={self._value})"
    
    def __repr__(self) -> str:
        return f"OSV(value={self._value})"
    
    def __eq__(self, other) -> bool:
        """Compare with another value or observable"""
        if isinstance(other, ObservableSingleValue):
            return self._value == other._value
        return self._value == other
    
    def __ne__(self, other) -> bool:
        """Compare with another value or observable"""
        return not (self == other)
    
    def __lt__(self, other) -> bool:
        """Compare with another value or observable"""
        if isinstance(other, ObservableSingleValue):
            return self._value < other._value
        return self._value < other
    
    def __le__(self, other) -> bool:
        """Compare with another value or observable"""
        if isinstance(other, ObservableSingleValue):
            return self._value <= other._value
        return self._value <= other
    
    def __gt__(self, other) -> bool:
        """Compare with another value or observable"""
        if isinstance(other, ObservableSingleValue):
            return self._value > other._value
        return self._value > other
    
    def __ge__(self, other) -> bool:
        """Compare with another value or observable"""
        if isinstance(other, ObservableSingleValue):
            return self._value >= other._value
        return self._value >= other
    
    def __hash__(self) -> int:
        """Hash based on the current value"""
        return hash(self._value)
    
    def __bool__(self) -> bool:
        """Boolean conversion"""
        return bool(self._value)
    
    def __int__(self) -> int:
        """Integer conversion"""
        return int(self._value) # type: ignore
    
    def __float__(self) -> float:
        """Float conversion"""
        return float(self._value) # type: ignore
    
    def __complex__(self) -> complex:
        """Complex conversion"""
        return complex(self._value) # type: ignore
    
    def __abs__(self) -> float:
        """Absolute value"""
        return abs(self._value) # type: ignore
    
    def __round__(self, ndigits=None):
        """Round the value"""
        return round(self._value, ndigits) # type: ignore
    
    def __floor__(self):
        """Floor division"""
        import math
        return math.floor(self._value) # type: ignore
    
    def __ceil__(self):
        """Ceiling division"""
        import math
        return math.ceil(self._value) # type: ignore
    
    def __trunc__(self):
        """Truncate the value"""
        import math
        return math.trunc(self._value) # type: ignore
    
    def bind_to_observable(self, observable: CarriesBindableSingleValue[T], initial_sync_mode: SyncMode = SyncMode.UPDATE_VALUE_FROM_OBSERVABLE) -> None:
        if observable is None:
            raise ValueError("Cannot bind to None observable")
        self._binding_handler.establish_binding(observable._get_single_value_binding_handler(), initial_sync_mode)

    def unbind_from_observable(self, observable: "ObservableSingleValue[T]") -> None:
        self._binding_handler.remove_binding(observable._get_single_value_binding_handler())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        binding_state_consistent, binding_state_consistent_message = self._binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._binding_handler.check_values_synced()
        if not values_synced:
            return False, values_synced_message
        return True, "Binding system is consistent"