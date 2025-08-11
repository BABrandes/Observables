from typing import Generic, TypeVar, Optional, overload
from .._utils._listening_base import ListeningBase
from .._utils._internal_binding_handler import InternalBindingHandler, SyncMode, DEFAULT_SYNC_MODE
from .._utils._carries_bindable_dict import CarriesBindableDict
from .._utils.observable import Observable

K = TypeVar("K")
V = TypeVar("V")

class ObservableDict(ListeningBase, Observable, CarriesBindableDict[K, V], Generic[K, V]):
    """
    An observable wrapper around a dictionary that supports bidirectional bindings and reactive updates.
    
    This class provides a reactive wrapper around Python dictionaries, allowing other objects to
    observe changes and establish bidirectional bindings. It implements the full dict interface
    while maintaining reactivity and binding capabilities.
    
    Features:
    - Bidirectional bindings with other ObservableDict instances
    - Full dict interface compatibility (get, set, update, clear, etc.)
    - Listener notification system for change events
    - Automatic copying to prevent external modification
    - Type-safe generic implementation for keys and values
    
    Example:
        >>> # Create an observable dictionary
        >>> config = ObservableDict({"theme": "dark", "language": "en"})
        >>> config.add_listeners(lambda: print("Config changed!"))
        >>> config["theme"] = "light"  # Triggers listener
        Config changed!
        
        >>> # Create bidirectional binding
        >>> config_copy = ObservableDict(config)
        >>> config_copy["timezone"] = "UTC"  # Updates both dicts
        >>> print(config.value, config_copy.value)
        {'theme': 'light', 'language': 'en', 'timezone': 'UTC'} {'theme': 'light', 'language': 'en', 'timezone': 'UTC'}
    
    Args:
        initial_dict: Initial dictionary, another ObservableDict to bind to, or None for empty dict
    """
    
    @overload
    def __init__(self, initial_dict: dict[K, V]):
        """Initialize with a direct dictionary value."""
        ...
    
    @overload
    def __init__(self, initial_dict: CarriesBindableDict[K, V]):
        """Initialize with another observable dictionary, establishing a bidirectional binding."""
        ...
    
    @overload
    def __init__(self, initial_dict: None):
        """Initialize with an empty dictionary."""
        ...
    
    def __init__(self, initial_dict: dict[K, V] | CarriesBindableDict[K, V] | None = None):
        """
        Initialize the ObservableDict.
        
        Args:
            initial_dict: Initial dictionary, observable dictionary to bind to, or None for empty dict
        """
        super().__init__()
        
        if initial_dict is None:
            initial_dict_value: dict[K, V] = {}
            bindable_dict_carrier: Optional[CarriesBindableDict[K, V]] = None
        elif isinstance(initial_dict, CarriesBindableDict):
            initial_dict_value: dict[K, V] = initial_dict._get_dict().copy()
            bindable_dict_carrier: Optional[CarriesBindableDict[K, V]] = initial_dict
        else:
            initial_dict_value: dict[K, V] = initial_dict.copy()
            bindable_dict_carrier: Optional[CarriesBindableDict[K, V]] = None

        self._binding_handler: InternalBindingHandler[dict[K, V]] = InternalBindingHandler(self, self._get_dict, self._set_dict, self._check_dict)

        self._dict: dict[K, V] = initial_dict_value

        if bindable_dict_carrier is not None:
            self.bind_to_observable(bindable_dict_carrier)

    @property
    def value(self) -> dict[K, V]:
        """
        Get a copy of the current dictionary value.
        
        Returns:
            A copy of the current dictionary to prevent external modification
        """
        return self._dict.copy()  # Return a copy to prevent external modification
    
    def _get_dict(self) -> dict[K, V]:
        """Internal method to get dictionary for binding system."""
        return self._dict
    
    def _set_dict(self, dict_to_set: dict[K, V]) -> None:
        """Internal method to set dictionary from binding system."""
        self.change_dict(dict_to_set)
    
    def _get_dict_binding_handler(self) -> InternalBindingHandler[dict[K, V]]:
        """Internal method to get binding handler for binding system."""
        return self._binding_handler
    
    def _check_dict(self, dict_to_check: dict[K, V]) -> bool:
        """Internal method to check dictionary validity for binding system."""
        return True  # Always accept any dictionary
    
    def change_dict(self, new_dict: dict[K, V]) -> None:
        """
        Change the entire dictionary to a new value.
        
        This method replaces the current dictionary with a new one, triggering binding updates
        and listener notifications. If the new dictionary is identical to the current one,
        no action is taken.
        
        Args:
            new_dict: The new dictionary to set
        """
        if new_dict == self._dict:
            return
        self._dict = new_dict.copy()  # Store a copy to prevent external modification
        self._binding_handler.notify_bindings(self._dict)
        self._notify_listeners()
    
    def set_item(self, key: K, value: V) -> None:
        """
        Set a single key-value pair.
        
        This method sets or updates a key-value pair in the dictionary, triggering
        binding updates and listener notifications. If the key already exists with
        the same value, no action is taken.
        
        Args:
            key: The key to set or update
            value: The value to associate with the key
        """
        if key in self._dict and self._dict[key] == value:
            return  # No change
        self._dict[key] = value
        self._binding_handler.notify_bindings(self._dict)
        self._notify_listeners()
    
    def get_item(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        Get a value by key with optional default.
        
        Args:
            key: The key to look up
            default: Default value to return if key is not found
            
        Returns:
            The value associated with the key, or the default value if key not found
        """
        return self._dict.get(key, default)
    
    def has_key(self, key: K) -> bool:
        """
        Check if a key exists in the dictionary.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._dict
    
    def remove_item(self, key: K) -> None:
        """
        Remove a key-value pair from the dictionary.
        
        This method removes a key-value pair if it exists, triggering binding updates
        and listener notifications. If the key doesn't exist, no action is taken.
        
        Args:
            key: The key to remove
        """
        if key not in self._dict:
            return  # No change
        del self._dict[key]
        self._binding_handler.notify_bindings(self._dict)
        self._notify_listeners()
    
    def clear(self) -> None:
        """
        Clear all items from the dictionary.
        
        This method removes all key-value pairs from the dictionary, triggering
        binding updates and listener notifications. If the dictionary is already
        empty, no action is taken.
        """
        if not self._dict:
            return  # No change
        self._dict.clear()
        self._binding_handler.notify_bindings(self._dict)
        self._notify_listeners()
    
    def update(self, other_dict: dict[K, V]) -> None:
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

    def bind_to_observable(self, observable: CarriesBindableDict[K, V], initial_sync_mode: SyncMode = DEFAULT_SYNC_MODE) -> None:
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

    def get_observed_values(self) -> tuple[dict[K, V]]:
        return tuple(self._dict)
    
    def set_observed_values(self, values: tuple[dict[K, V]]) -> None:
        self.change_dict(values[0])