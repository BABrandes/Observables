from typing import Generic, TypeVar
from ..utils._listening_base import ListeningBase
from ..utils._internal_binding_handler import InternalBindingHandler, SyncMode
from ..utils._carries_bindable_list import CarriesBindableList

T = TypeVar("T")

class ObservableList(ListeningBase, CarriesBindableList[T], Generic[T]):

    def __init__(self, value: list[T]):
        super().__init__()
        self._value: list[T] = value
        self._binding_handler: InternalBindingHandler[list[T]] = InternalBindingHandler(self, self._get_list, self._set_list, self._check_list)

    @property
    def value(self) -> list[T]:
        return self._value
    
    def _set_list(self, list_to_set: list[T]) -> None:
        self.change_list(list_to_set)
    
    def _get_list(self) -> list[T]:
        return self._value
    
    def _check_list(self, list_to_check: list[T]) -> bool:
        return True

    def _get_list_binding_handler(self) -> InternalBindingHandler[list[T]]:
        return self._binding_handler
    
    def change_list(self, list_to_change: list[T]) -> None:
        if list_to_change == self._value:
            return
        self._value = list_to_change
        self._binding_handler.notify_bindings(list_to_change)
        self._notify_listeners()

    def bind_to_observable(self, observable: CarriesBindableList[T], initial_sync_mode: SyncMode = SyncMode.UPDATE_VALUE_FROM_OBSERVABLE) -> None:
        if observable is None:
            raise ValueError("Cannot bind to None observable")
        self._binding_handler.establish_binding(observable._get_list_binding_handler(), initial_sync_mode)

    def unbind_from_observable(self, observable: CarriesBindableList[T]) -> None:
        self._binding_handler.remove_binding(observable._get_list_binding_handler())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        binding_state_consistent, binding_state_consistent_message = self._binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._binding_handler.check_values_synced()
        if not values_synced:
            return False, values_synced_message
        return True, "Binding system is consistent"
    
    def __str__(self) -> str:
        return f"OL(value={self._value})"
    
    def __repr__(self) -> str:
        return f"ObservableList({self._value})"
    
    def __len__(self) -> int:
        return len(self._value)
    
    def __getitem__(self, index):
        """Get item at index or slice"""
        return self._value[index]
    
    def __setitem__(self, index, value):
        """Set item at index or slice"""
        if isinstance(index, slice):
            # Handle slice assignment
            old_value = self._value.copy()
            self._value[index] = value
            if old_value != self._value:
                self._binding_handler.notify_bindings(self._value)
                self._notify_listeners()
        else:
            # Handle single index assignment
            if self._value[index] != value:
                self._value[index] = value
                self._binding_handler.notify_bindings(self._value)
                self._notify_listeners()
    
    def __delitem__(self, index):
        """Delete item at index or slice"""
        old_value = self._value.copy()
        del self._value[index]
        if old_value != self._value:
            self._binding_handler.notify_bindings(self._value)
            self._notify_listeners()
    
    def __contains__(self, item: T) -> bool:
        return item in self._value
    
    def __iter__(self):
        """Iterate over the list"""
        return iter(self._value)
    
    def __reversed__(self):
        """Reverse iterate over the list"""
        return reversed(self._value)
    
    def __eq__(self, other) -> bool:
        """Compare with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value == other._value
        return self._value == other
    
    def __ne__(self, other) -> bool:
        """Compare with another list or observable"""
        return not (self == other)
    
    def __lt__(self, other) -> bool:
        """Compare with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value < other._value
        return self._value < other
    
    def __le__(self, other) -> bool:
        """Compare with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value <= other._value
        return self._value <= other
    
    def __gt__(self, other) -> bool:
        """Compare with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value > other._value
        return self._value > other
    
    def __ge__(self, other) -> bool:
        """Compare with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value >= other._value
        return self._value >= other
    
    def __add__(self, other):
        """Concatenate with another list or observable"""
        if isinstance(other, ObservableList):
            return self._value + other._value
        return self._value + other
    
    def __mul__(self, other):
        """Repeat the list"""
        return self._value * other
    
    def __rmul__(self, other):
        """Repeat the list (right multiplication)"""
        return other * self._value
    
    def __hash__(self) -> int:
        """Hash based on the current value"""
        return hash(tuple(self._value))