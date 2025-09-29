from logging import Logger
from typing import Generic, TypeVar, Optional, overload, Callable, Protocol, runtime_checkable, Literal, Any, Mapping
from .._hooks.hook_like import HookLike
from .._hooks.owned_hook_like import OwnedHookLike
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.base_observable import BaseObservable
from .._utils.observable_serializable import ObservableSerializable
from .._utils.carries_hooks_like import CarriesHooksLike

K = TypeVar("K")
V = TypeVar("V")

@runtime_checkable
class ObservableDictLike(CarriesHooksLike[Any, Any], Protocol[K, V]):
    """
    Protocol for observable dictionary objects.
    """
    
    @property
    def value(self) -> dict[K, V]:
        """
        Get the dictionary value.
        """
        ...
    
    @value.setter
    def value(self, value: dict[K, V]) -> None:
        """
        Set the dictionary value.
        """
        ...

    @property
    def value_hook(self) -> OwnedHookLike[dict[K, V]]:
        """
        Get the hook for the dictionary.
        """
        ...

    def change_value(self, new_dict: dict[K, V]) -> None:
        """
        Change the dictionary value (lambda-friendly method).
        """
        ...
    
    @property
    def length(self) -> int:
        """
        Get the current length of the dictionary.
        """
        ...
    
    @property
    def length_hook(self) -> OwnedHookLike[int]:
        """
        Get the hook for the dictionary length.
        """
        ...
    
class ObservableDict(BaseObservable[Literal["value"], Literal["length"], K|V|dict[K, V], int], ObservableSerializable[Literal["value"], "ObservableDict"], ObservableDictLike[K, V], Generic[K, V]):
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
            initial_dict_value = observable_or_hook_or_value.value # type: ignore
            hook = observable_or_hook_or_value.value_hook # type: ignore
        elif isinstance(observable_or_hook_or_value, HookLike):
            initial_dict_value = observable_or_hook_or_value.value
            hook = observable_or_hook_or_value
        else:
            initial_dict_value = observable_or_hook_or_value.copy()
            hook = None

        self._internal_construct_from_values(
            {"value": initial_dict_value},
            logger=logger
        )

        if hook is not None:
            self.connect_hook(hook, "value", InitialSyncMode.USE_TARGET_VALUE) # type: ignore

    def _internal_construct_from_values(
        self,
        initial_values: Mapping[Literal["value"], dict[K, V]],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """
        Construct an ObservableDict instance.
        """

        def is_valid_value(x: Mapping[Literal["value"], Any]) -> tuple[bool, str]:
            return (True, "Verification method passed") if isinstance(x["value"], dict) else (False, "Value is not a dictionary")

        super().__init__(
            initial_values,
            verification_method=is_valid_value,
            secondary_hook_callbacks={"length": lambda x: len(x["value"])}, # type: ignore
            logger=logger
        )

    @property
    def value(self) -> dict[K, V]:
        """
        Get the current value of the dictionary as a copy.
        
        Returns:
            A copy of the current dictionary value
        """
        return self._primary_hooks["value"].value.copy() # type: ignore
    
    @value.setter
    def value(self, value: dict[K, V]) -> None:
        """
        Set the current value of the dictionary.
        """
        if value == self._primary_hooks["value"].value:
            return
        self.submit_values({"value": value})
    
    def change_value(self, new_dict: dict[K, V]) -> None:
        """
        Change the dictionary value (lambda-friendly method).
        
        This method is equivalent to setting the .value property but can be used
        in lambda expressions and other contexts where property assignment isn't suitable.
        
        Args:
            new_dict: The new dictionary to set
        """
        if new_dict == self._primary_hooks["value"].value:
            return
        self.submit_values({"value": new_dict})

    @property
    def value_hook(self) -> OwnedHookLike[dict[K, V]]:
        """
        Get the hook for the dictionary.
        
        This hook can be used for binding operations with other observables.
        """
        return self._primary_hooks["value"] # type: ignore
    
    @property
    def length(self) -> int:
        """
        Get the current length of the dictionary.
        """
        return len(self._primary_hooks["value"].value) # type: ignore
    
    @property
    def length_hook(self) -> OwnedHookLike[int]:
        """
        Get the hook for the dictionary length.
        
        This hook can be used for binding operations that react to length changes.
        """
        return self._secondary_hooks["length"] # type: ignore
    
    
    def set_item(self, key: K, value: V) -> None:
        """
        Set a single key-value pair.
        
        This method sets or updates a key-value pair in the dictionary, using
        set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            key: The key to set or update
            value: The value to associate with the key
        """
        if key in self.value and self.value[key] == value:
            return  # No change
        new_dict = self.value.copy()
        new_dict[key] = value
        self.submit_values({"value": new_dict})
    
    def get_item(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        Get a value by key with optional default.
        
        Args:
            key: The key to look up
            default: Default value to return if key is not found
            
        Returns:
            The value associated with the key, or the default value if key not found
        """
        return self._primary_hooks["value"].value.get(key, default) # type: ignore
    
    def has_key(self, key: K) -> bool:
        """
        Check if a key exists in the dictionary.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._primary_hooks["value"].value # type: ignore
    
    def remove_item(self, key: K) -> None:
        """
        Remove a key-value pair from the dictionary.
        
        This method removes a key-value pair if it exists, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            key: The key to remove
        """
        if key not in self._primary_hooks["value"].value: # type: ignore
            return  # No change
        new_dict: dict[K, V] = self._primary_hooks["value"].value.copy() # type: ignore
        del new_dict[key]
        self.submit_values({"value": new_dict}) # type: ignore
    
    def clear(self) -> None:
        """
        Clear all items from the dictionary.
        
        This method removes all key-value pairs from the dictionary, using
        set_observed_values to ensure all changes go through the centralized protocol method.
        """
        if not self._primary_hooks["value"].value: # type: ignore
            return  # No change
        new_dict: dict[K, V] = {}
        self.submit_values({"value": new_dict})
    
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
            if key not in self._primary_hooks["value"].value or self._primary_hooks["value"].value[key] != value: # type: ignore
                has_changes = True
                break
        
        if not has_changes:
            return  # No change
        
        new_dict = self._primary_hooks["value"].value.copy() # type: ignore
        new_dict.update(other_dict) # type: ignore
        self.submit_values({"value": new_dict}) # type: ignore
    
    def keys(self) -> set[K]:
        """
        Get all keys from the dictionary as a set.

        Returns:
            A set containing all keys in the dictionary
        """
        return set(self._primary_hooks["value"].value.keys()) # type: ignore
    
    def values(self) -> list[V]:
        """
        Get all values from the dictionary as a list.
        
        Returns:
            A list containing all values in the dictionary
        """
        return list(self._primary_hooks["value"].value.values()) # type: ignore
    
    def items(self) -> list[tuple[K, V]]:
        """
        Get all key-value pairs from the dictionary as a list of tuples.
        
        Returns:
            A list of tuples, each containing a key-value pair
        """
        return list(self._primary_hooks["value"].value.items()) # type: ignore
    
    def __len__(self) -> int:
        """
        Get the number of key-value pairs in the dictionary.
        
        Returns:
            The number of key-value pairs
        """
        return len(self._primary_hooks["value"].value) # type: ignore
    
    def __contains__(self, key: K) -> bool:
        """
        Check if a key exists in the dictionary.
        
        Args:
            key: The key to check for
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._primary_hooks["value"].value # type: ignore
    
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
        if key not in self._primary_hooks["value"].value: # type: ignore
            raise KeyError(f"Key '{key}' not found in dictionary")
        return self._primary_hooks["value"].value[key] # type: ignore
    
    def __setitem__(self, key: K, value: V) -> None:
        """
        Set a key-value pair in the dictionary.
        
        This method sets or updates a key-value pair, triggering binding updates
        and listener notifications if the value changes.
        
        Args:
            key: The key to set or update
            value: The value to associate with the key
        """
        self._set_component_values({"value": {**self._primary_hooks["value"].value, key: value}}, notify_binding_system=True) # type: ignore
    
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
        self._set_component_values({"value": {k: v for k, v in self._primary_hooks["value"].value.items() if k != key}}, notify_binding_system=True) # type: ignore
    
    def __str__(self) -> str:
        return f"OD(dict={self._primary_hooks['value'].value})"
    
    def __repr__(self) -> str:
        return f"ObservableDict({self._primary_hooks['value'].value})"