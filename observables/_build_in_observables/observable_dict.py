from typing import Generic, TypeVar, Dict, Optional
from .._utils._listening_base import ListeningBase
from .._utils._internal_binding_handler import InternalBindingHandler, SyncMode
from .._utils._carries_bindable_dict import CarriesBindableDict

K = TypeVar("K")
V = TypeVar("V")

class ObservableDict(ListeningBase, CarriesBindableDict[K, V], Generic[K, V]):

    def __init__(self, initial_dict: Optional[Dict[K, V]] = None):
        super().__init__()
        self._dict: Dict[K, V] = initial_dict.copy() if initial_dict is not None else {}
        self._binding_handler: InternalBindingHandler[Dict[K, V]] = InternalBindingHandler(
            self, self._get_dict, self._set_dict, self._check_dict
        )

    @property
    def dict(self) -> Dict[K, V]:
        """Get the current dictionary value"""
        return self._dict.copy()  # Return a copy to prevent external modification
    
    def _get_dict(self) -> Dict[K, V]:
        return self._dict
    
    def _set_dict(self, dict_to_set: Dict[K, V]) -> None:
        self.change_dict(dict_to_set)
    
    def _get_dict_binding_handler(self) -> InternalBindingHandler[Dict[K, V]]:
        return self._binding_handler
    
    def _check_dict(self, dict_to_check: Dict[K, V]) -> bool:
        return True  # Always accept any dictionary
    
    def change_dict(self, new_dict: Dict[K, V]) -> None:
        """Change the entire dictionary"""
        if new_dict == self._dict:
            return
        self._dict = new_dict.copy()  # Store a copy to prevent external modification
        self._binding_handler.notify_bindings(new_dict)
        self._notify_listeners()
    
    def set_item(self, key: K, value: V) -> None:
        """Set a single key-value pair"""
        if key in self._dict and self._dict[key] == value:
            return  # No change
        self._dict[key] = value
        self._binding_handler.notify_bindings(self._dict)
        self._notify_listeners()
    
    def get_item(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Get a value by key with optional default"""
        return self._dict.get(key, default)
    
    def has_key(self, key: K) -> bool:
        """Check if a key exists"""
        return key in self._dict
    
    def remove_item(self, key: K) -> None:
        """Remove a key-value pair"""
        if key not in self._dict:
            return  # No change
        del self._dict[key]
        self._binding_handler.notify_bindings(self._dict)
        self._notify_listeners()
    
    def clear(self) -> None:
        """Clear all items from the dictionary"""
        if not self._dict:
            return  # No change
        self._dict.clear()
        self._binding_handler.notify_bindings(self._dict)
        self._notify_listeners()
    
    def update(self, other_dict: Dict[K, V]) -> None:
        """Update the dictionary with items from another dictionary"""
        if not other_dict:
            return  # No change
        # Check if any values would actually change
        has_changes = False
        for key, value in other_dict.items():
            if key not in self._dict or self._dict[key] != value:
                has_changes = True
                break
        
        if not has_changes:
            return  # No change
        
        self._dict.update(other_dict)
        self._binding_handler.notify_bindings(self._dict)
        self._notify_listeners()
    
    def keys(self) -> set[K]:
        """Get all keys as a set"""
        return set(self._dict.keys())
    
    def values(self) -> list[V]:
        """Get all values as a list"""
        return list(self._dict.values())
    
    def items(self) -> list[tuple[K, V]]:
        """Get all key-value pairs as a list of tuples"""
        return list(self._dict.items())
    
    def __len__(self) -> int:
        return len(self._dict)
    
    def __contains__(self, key: K) -> bool:
        return key in self._dict
    
    def __getitem__(self, key: K) -> V:
        if key not in self._dict:
            raise KeyError(f"Key '{key}' not found in dictionary")
        return self._dict[key]
    
    def __setitem__(self, key: K, value: V) -> None:
        self.set_item(key, value)
    
    def __delitem__(self, key: K) -> None:
        self.remove_item(key)
    
    def __str__(self) -> str:
        return f"OD(dict={self._dict})"
    
    def __repr__(self) -> str:
        return f"ObservableDict({self._dict})"

    def bind_to_observable(self, observable: CarriesBindableDict[K, V], initial_sync_mode: SyncMode = SyncMode.UPDATE_VALUE_FROM_OBSERVABLE) -> None:
        if observable is None:
            raise ValueError("Cannot bind to None observable")
        self._binding_handler.establish_binding(observable._get_dict_binding_handler(), initial_sync_mode)

    def unbind_from_observable(self, observable: CarriesBindableDict[K, V]) -> None:
        self._binding_handler.remove_binding(observable._get_dict_binding_handler())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        binding_state_consistent, binding_state_consistent_message = self._binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._binding_handler.check_values_synced()
        if not values_synced:
            return False, values_synced_message
        return True, "Binding system is consistent"
