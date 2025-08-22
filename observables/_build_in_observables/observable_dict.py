from logging import Logger
from typing import Generic, TypeVar, Optional, overload, Callable, Protocol, runtime_checkable, Any, Literal
from .._utils.hook import HookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.base_observable import BaseObservable
from .._utils.carries_hooks import CarriesHooks

K = TypeVar("K")
V = TypeVar("V")

@runtime_checkable
class ObservableDictLike(CarriesHooks[Any], Protocol[K, V]):
    """
    Protocol for observable dictionary objects.
    """
    
    @property
    def dict_value(self) -> dict[K, V]:
        """
        Get the dictionary value.
        """
        ...
    
    @dict_value.setter
    def dict_value(self, value: dict[K, V]) -> None:
        """
        Set the dictionary value.
        """
        ...

    @property
    def dict_value_hook(self) -> HookLike[dict[K, V]]:
        """
        Get the hook for the dictionary.
        """
        ...

class ObservableDict(BaseObservable[Literal["value"]], ObservableDictLike[K, V], Generic[K, V]):
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
    def __init__(self, observable_or_hook: HookLike[dict[K, V]], validator: Optional[Callable[[dict[K, V]], bool]] = None, logger: Optional[Logger] = None) -> None:
        """Initialize with a direct dictionary value."""
        ...
    
    @overload
    def __init__(self, dict_value: dict[K, V], logger: Optional[Logger] = None) -> None:
        """Initialize with another observable dictionary, establishing a bidirectional binding."""
        ...

    @overload
    def __init__(self, observable: ObservableDictLike[K, V], logger: Optional[Logger] = None) -> None:
        """Initialize from another ObservableDictLike object."""
        ...
    
    @overload
    def __init__(self, dict_value: None) -> None:
        """Initialize with an empty dictionary."""
        ...
    
    def __init__(self, observable_or_hook_or_value: dict[K, V] | HookLike[dict[K, V]] | None = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize the ObservableDict.
        
        Args:
            initial_dict: Initial dictionary, observable dictionary to bind to, or None for empty dict

        Raises:
            ValueError: If the initial dictionary is not a dictionary
        """

        if observable_or_hook_or_value is None:
            initial_dict_value: dict[K, V] = {}
            hook: Optional[HookLike[dict[K, V]]] = None
        elif isinstance(observable_or_hook_or_value, ObservableDictLike):
            initial_dict_value: dict[K, V] = observable_or_hook_or_value.dict_value # type: ignore
            hook: Optional[HookLike[dict[K, V]]] = observable_or_hook_or_value.dict_value_hook # type: ignore
        elif isinstance(observable_or_hook_or_value, HookLike):
            initial_dict_value: dict[K, V] = observable_or_hook_or_value.value
            hook: Optional[HookLike[dict[K, V]]] = observable_or_hook_or_value
        else:
            initial_dict_value: dict[K, V] = observable_or_hook_or_value.copy()
            hook: Optional[HookLike[dict[K, V]]] = None

        super().__init__(
            {"value": initial_dict_value},
            verification_method=lambda x: (True, "Verification method passed") if isinstance(x["value"], dict) else (False, "Value is not a dictionary"),
            logger=logger
        )

        if hook is not None:
            self.attach(hook, "value", InitialSyncMode.PULL_FROM_TARGET)

    @property
    def dict_value_hook(self) -> HookLike[dict[K, V]]:
        """
        Get the hook for the dictionary.
        """
        return self._component_hooks["value"]

    @property
    def dict_value(self) -> dict[K, V]:
        """
        Get the current value of the dictionary as a copy.
        
        Returns:
            A copy of the current dictionary value
        """
        return self._component_hooks["value"].value.copy()
    
    @dict_value.setter
    def dict_value(self, value: dict[K, V]) -> None:
        """
        Set the current value of the dictionary.
        """
        self._set_component_values({"value": value}, notify_binding_system=True)
    
    def change_dict(self, new_dict: dict[K, V]) -> None:
        """
        Change the entire dictionary to a new value.
        
        This method replaces the current dictionary with a new one, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            new_dict: The new dictionary to set
        """
        if new_dict == self._component_hooks["value"].value:
            return
        # Use the protocol method to set the value
        self._set_component_values({"value": new_dict}, notify_binding_system=True)
    
    def set_item(self, key: K, value: V) -> None:
        """
        Set a single key-value pair.
        
        This method sets or updates a key-value pair in the dictionary, using
        set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            key: The key to set or update
            value: The value to associate with the key
        """
        if key in self.dict_value and self.dict_value[key] == value:
            return  # No change
        new_dict = self.dict_value.copy()
        new_dict[key] = value
        self._set_component_values({"value": new_dict}, notify_binding_system=True)
    
    def get_item(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        Get a value by key with optional default.
        
        Args:
            key: The key to look up
            default: Default value to return if key is not found
            
        Returns:
            The value associated with the key, or the default value if key not found
        """
        return self._component_hooks["value"].value.get(key, default)
    
    def has_key(self, key: K) -> bool:
        """
        Check if a key exists in the dictionary.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._component_hooks["value"].value
    
    def remove_item(self, key: K) -> None:
        """
        Remove a key-value pair from the dictionary.
        
        This method removes a key-value pair if it exists, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            key: The key to remove
        """
        if key not in self._component_hooks["value"].value:
            return  # No change
        new_dict: dict[K, V] = self._component_hooks["value"].value.copy()
        del new_dict[key]
        self._set_component_values({"value": new_dict}, notify_binding_system=True)
    
    def clear(self) -> None:
        """
        Clear all items from the dictionary.
        
        This method removes all key-value pairs from the dictionary, using
        set_observed_values to ensure all changes go through the centralized protocol method.
        """
        if not self._component_hooks["value"].value:
            return  # No change
        new_dict: dict[K, V] = {}
        self._set_component_values({"value": new_dict}, notify_binding_system=True)
    
    def update(self, other_dict: dict[K, V]) -> None:
        """
        Update the dictionary with items from another dictionary.
        
        This method adds or updates key-value pairs from the provided dictionary,
        using set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            other_dict: Dictionary containing items to add or update
        """
        if not other_dict:
            return  # No change
        # Check if any values would actually change
        has_changes = False
        for key, value in other_dict.items():
            if key not in self._component_hooks["value"].value or self._component_hooks["value"].value[key] != value:
                has_changes = True
                break
        
        if not has_changes:
            return  # No change
        
        new_dict = self._component_hooks["value"].value.copy()
        new_dict.update(other_dict)
        self._set_component_values({"value": new_dict}, notify_binding_system=True)
    
    def keys(self) -> set[K]:
        """
        Get all keys from the dictionary as a set.

        Returns:
            A set containing all keys in the dictionary
        """
        return set(self._component_hooks["value"].value.keys())
    
    def values(self) -> list[V]:
        """
        Get all values from the dictionary as a list.
        
        Returns:
            A list containing all values in the dictionary
        """
        return list(self._component_hooks["value"].value.values())
    
    def items(self) -> list[tuple[K, V]]:
        """
        Get all key-value pairs from the dictionary as a list of tuples.
        
        Returns:
            A list of tuples, each containing a key-value pair
        """
        return list(self._component_hooks["value"].value.items())
    
    def __len__(self) -> int:
        """
        Get the number of key-value pairs in the dictionary.
        
        Returns:
            The number of key-value pairs
        """
        return len(self._component_hooks["value"].value)
    
    def __contains__(self, key: K) -> bool:
        """
        Check if a key exists in the dictionary.
        
        Args:
            key: The key to check for
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._component_hooks["value"].value
    
    def __getitem__(self, key: K) -> V:
        """
        Get a value by key.
        
        Args:
            key: The key to look up
            
        Returns:
            The value associated with the key
            
        Raises:
            KeyError: If the key is not found in the dictionary
        """
        if key not in self._component_hooks["value"].value:
            raise KeyError(f"Key '{key}' not found in dictionary")
        return self._component_hooks["value"].value[key]
    
    def __setitem__(self, key: K, value: V) -> None:
        """
        Set a key-value pair in the dictionary.
        
        This method sets or updates a key-value pair, triggering binding updates
        and listener notifications if the value changes.
        
        Args:
            key: The key to set or update
            value: The value to associate with the key
        """
        self._set_component_values({"value": {**self._component_hooks["value"].value, key: value}}, notify_binding_system=True)
    
    def __delitem__(self, key: K) -> None:
        """
        Remove a key-value pair from the dictionary.
        
        This method removes a key-value pair if it exists, triggering binding updates
        and listener notifications.
        
        Args:
            key: The key to remove
            
        Raises:
            KeyError: If the key is not found in the dictionary
        """
        self._set_component_values({"value": {k: v for k, v in self._component_hooks["value"].value.items() if k != key}}, notify_binding_system=True)
    
    def __str__(self) -> str:
        return f"OD(dict={self._component_hooks['value'].value})"
    
    def __repr__(self) -> str:
        return f"ObservableDict({self._component_hooks['value'].value})"