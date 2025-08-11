
from typing import Callable, Generic, Literal, Optional , TypeVar
from ..utils._listening_base import ListeningBase
from ..utils._internal_binding_handler import InternalBindingHandler, SyncMode
from ..utils._carries_bindable_set import CarriesBindableSet

T = TypeVar("T")

class ObservableSet(ListeningBase, CarriesBindableSet[T], Generic[T]):

    def __init__(self, options: set[T]):
        super().__init__()
        self._options: set[T] = options
        self._binding_handler: InternalBindingHandler[set[T]] = InternalBindingHandler(self, self._get_set, self._set_set, self._check_set)

    @property
    def options(self) -> set[T]:
        return self._options
    
    def _get_set(self) -> set[T]:
        return self._options
    
    def _set_set(self, set_to_set: set[T]) -> None:
        self.change_options(set_to_set)
    
    def _get_set_binding_handler(self) -> InternalBindingHandler[set[T]]:
        return self._binding_handler
    
    def _check_set(self, set_to_check: set[T]) -> bool:
        return True
    
    def change_options(self, options: set[T]) -> None:
        if options == self._options:
            return
        self._options = options
        self._binding_handler.notify_bindings(options)
        self._notify_listeners()

    def bind_to_observable(self, observable: CarriesBindableSet[T], initial_sync_mode: SyncMode = SyncMode.UPDATE_VALUE_FROM_OBSERVABLE) -> None:
        if observable is None:
            raise ValueError("Cannot bind to None observable")
        self._binding_handler.establish_binding(observable._get_set_binding_handler(), initial_sync_mode)

    def unbind_from_observable(self, observable: CarriesBindableSet[T]) -> None:
        self._binding_handler.remove_binding(observable._get_set_binding_handler())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        binding_state_consistent, binding_state_consistent_message = self._binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._binding_handler.check_values_synced()
        if not values_synced:
            return False, values_synced_message
        return True, "Binding system is consistent"
    
    def __str__(self) -> str:
        return f"OS(options={self._options})"
    
    def __repr__(self) -> str:
        return f"ObservableSet({self._options})"
    
    def __len__(self) -> int:
        return len(self._options)
    
    def __contains__(self, item: T) -> bool:
        return item in self._options
    
    def __iter__(self):
        """Iterate over the options"""
        return iter(self._options)
    
    def __eq__(self, other) -> bool:
        """Compare with another set or observable"""
        if isinstance(other, ObservableSet):
            return self._options == other._options
        return self._options == other
    
    def __ne__(self, other) -> bool:
        """Compare with another set or observable"""
        return not (self == other)
    
    def __le__(self, other) -> bool:
        """Check if this set is a subset of another"""
        if isinstance(other, ObservableSet):
            return self._options <= other._options
        return self._options <= other
    
    def __lt__(self, other) -> bool:
        """Check if this set is a proper subset of another"""
        if isinstance(other, ObservableSet):
            return self._options < other._options
        return self._options < other
    
    def __ge__(self, other) -> bool:
        """Check if this set is a superset of another"""
        if isinstance(other, ObservableSet):
            return self._options >= other._options
        return self._options >= other
    
    def __gt__(self, other) -> bool:
        """Check if this set is a proper superset of another"""
        if isinstance(other, ObservableSet):
            return self._options > other._options
        return self._options > other
    
    def __and__(self, other):
        """Set intersection"""
        if isinstance(other, ObservableSet):
            return self._options & other._options
        return self._options & other
    
    def __or__(self, other):
        """Set union"""
        if isinstance(other, ObservableSet):
            return self._options | other._options
        return self._options | other
    
    def __sub__(self, other):
        """Set difference"""
        if isinstance(other, ObservableSet):
            return self._options - other._options
        return self._options - other
    
    def __xor__(self, other):
        """Set symmetric difference"""
        if isinstance(other, ObservableSet):
            return self._options ^ other._options
        return self._options ^ other
    
    def __hash__(self) -> int:
        """Hash based on the current options"""
        return hash(frozenset(self._options))