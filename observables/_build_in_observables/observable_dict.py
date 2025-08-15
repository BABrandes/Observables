from typing import Generic, TypeVar, Optional, overload, Any, Callable, Protocol, runtime_checkable
from .._utils.hook import Hook
from .._utils.sync_mode import SyncMode
from .._utils.carries_distinct_dict_hook import CarriesDistinctDictHook
from .._utils.base_observable import BaseObservable

K = TypeVar("K")
V = TypeVar("V")

@runtime_checkable
class ObservableDictLike(CarriesDistinctDictHook[K, V], Protocol[K, V]):
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

    def bind_to(self, observable_or_hook: CarriesDistinctDictHook[K, V]|Hook[dict[K, V]], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding with another observable dictionary.
        """
        ...

    def unbind_from(self, observable_or_hook: CarriesDistinctDictHook[K, V]|Hook[dict[K, V]]) -> None:
        """
        Remove the bidirectional binding with another observable dictionary.
        """
        ...

class ObservableDict(BaseObservable, ObservableDictLike[K, V], Generic[K, V]):
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

    @classmethod
    def _mandatory_component_value_keys(cls) -> set[str]:
        """
        Get the mandatory component value keys.
        """
        return {"value"}

    @overload
    def __init__(self, hook: CarriesDistinctDictHook[K, V]|Hook[dict[K, V]], validator: Optional[Callable[[dict[K, V]], bool]] = None):
        """Initialize with a direct dictionary value."""
        ...
    
    @overload
    def __init__(self, dict_value: dict[K, V]):
        """Initialize with another observable dictionary, establishing a bidirectional binding."""
        ...
    
    @overload
    def __init__(self, dict_value: None):
        """Initialize with an empty dictionary."""
        ...
    
    def __init__(self, hook_or_value: dict[K, V] | CarriesDistinctDictHook[K, V] | Hook[dict[K, V]] | None = None):
        """
        Initialize the ObservableDict.
        
        Args:
            initial_dict: Initial dictionary, observable dictionary to bind to, or None for empty dict

        Raises:
            ValueError: If the initial dictionary is not a dictionary
        """

        if hook_or_value is None:
            initial_dict_value: dict[K, V] = {}
            hook: Optional[Hook[dict[K, V]]] = None
        elif isinstance(hook_or_value, CarriesDistinctDictHook):
            initial_dict_value: dict[K, V] = hook_or_value._get_dict_value()
            hook: Optional[Hook[dict[K, V]]] = hook_or_value._get_dict_hook()
        elif isinstance(hook_or_value, Hook):
            initial_dict_value: dict[K, V] = hook_or_value._get_callback()
            hook: Optional[Hook[dict[K, V]]] = hook_or_value
        else:
            initial_dict_value: dict[K, V] = hook_or_value.copy()
            hook: Optional[Hook[dict[K, V]]] = None

        def verification_method(x: dict[str, Any]) -> tuple[bool, str]:
            if not isinstance(x["value"], dict):
                return False, "Value is not a dictionary"
            return True, "Verification method passed"

        super().__init__(
            {
                "value": initial_dict_value
            },
            {
                "value": Hook(self, self._get_dict_value, self._set_dict_value)
            },
            verification_method=verification_method
        )

        if hook is not None:
            self.bind_to(hook)

    @property
    def dict_value(self) -> dict[K, V]:
        """
        Get the current value of the dictionary as a copy.
        
        Returns:
            A copy of the current dictionary value
        """
        return self._get_dict_value().copy()
    
    @dict_value.setter
    def dict_value(self, value: dict[K, V]) -> None:
        """
        Set the current value of the dictionary.
        """
        self.change_dict(value)

    def _get_dict_value(self) -> dict[K, V]:
        """
        INTERNAL. Do not use this method directly.

        Method to get dictionary for binding system. No copy is made!
        
        Returns:
            The current dictionary value
        """
        return self._component_values["value"]
    
    def _set_dict_value(self, dict_to_set: dict[K, V]) -> None:
        """
        INTERNAL. Do not use this method directly.

        Method to set dictionary from binding system.
        
        Args:
            dict_to_set: The new dictionary to set
        """
        self.change_dict(dict_to_set)
    
    def _get_dict_hook(self) -> Hook[dict[K, V]]:
        """
        INTERNAL. Do not use this method directly.

        Method to get hook for binding system.
        
        Returns:
            The hook for the dictionary
        """
        return self._component_hooks["value"]
    
    def change_dict(self, new_dict: dict[K, V]) -> None:
        """
        Change the entire dictionary to a new value.
        
        This method replaces the current dictionary with a new one, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            new_dict: The new dictionary to set
        """
        if new_dict == self._get_dict_value():
            return
        # Use the protocol method to set the value
        self.set_observed_values((new_dict,))
    
    def set_item(self, key: K, value: V) -> None:
        """
        Set a single key-value pair.
        
        This method sets or updates a key-value pair in the dictionary, using
        set_observed_values to ensure all changes go through the centralized protocol method.
        
        Args:
            key: The key to set or update
            value: The value to associate with the key
        """
        if key in self._get_dict_value() and self._get_dict_value()[key] == value:
            return  # No change
        new_dict = self._get_dict_value().copy()
        new_dict[key] = value
        self.set_observed_values((new_dict,))
    
    def get_item(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        Get a value by key with optional default.
        
        Args:
            key: The key to look up
            default: Default value to return if key is not found
            
        Returns:
            The value associated with the key, or the default value if key not found
        """
        return self._get_dict_value().get(key, default)
    
    def has_key(self, key: K) -> bool:
        """
        Check if a key exists in the dictionary.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._get_dict_value()
    
    def remove_item(self, key: K) -> None:
        """
        Remove a key-value pair from the dictionary.
        
        This method removes a key-value pair if it exists, using set_observed_values
        to ensure all changes go through the centralized protocol method.
        
        Args:
            key: The key to remove
        """
        if key not in self._get_dict_value():
            return  # No change
        new_dict = self._get_dict_value().copy()
        del new_dict[key]
        self.set_observed_values((new_dict,))
    
    def clear(self) -> None:
        """
        Clear all items from the dictionary.
        
        This method removes all key-value pairs from the dictionary, using
        set_observed_values to ensure all changes go through the centralized protocol method.
        """
        if not self._get_dict_value():
            return  # No change
        new_dict = {}
        self.set_observed_values((new_dict,))
    
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
            if key not in self._get_dict_value() or self._get_dict_value()[key] != value:
                has_changes = True
                break
        
        if not has_changes:
            return  # No change
        
        new_dict = self._get_dict_value().copy()
        new_dict.update(other_dict)
        self.set_observed_values((new_dict,))
    
    def keys(self) -> set[K]:
        """
        Get all keys from the dictionary as a set.
        
        Returns:
            A set containing all keys in the dictionary
        """
        return set(self._get_dict_value())
    
    def values(self) -> list[V]:
        """
        Get all values from the dictionary as a list.
        
        Returns:
            A list containing all values in the dictionary
        """
        return list(self._get_dict_value().values())
    
    def items(self) -> list[tuple[K, V]]:
        """
        Get all key-value pairs from the dictionary as a list of tuples.
        
        Returns:
            A list of tuples, each containing a key-value pair
        """
        return list(self._get_dict_value().items())
    
    def __len__(self) -> int:
        """
        Get the number of key-value pairs in the dictionary.
        
        Returns:
            The number of key-value pairs
        """
        return len(self._component_values["value"])
    
    def __contains__(self, key: K) -> bool:
        """
        Check if a key exists in the dictionary.
        
        Args:
            key: The key to check for
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._get_dict_value()
    
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
        if key not in self._get_dict_value():
            raise KeyError(f"Key '{key}' not found in dictionary")
        return self._get_dict_value()[key]
    
    def __setitem__(self, key: K, value: V) -> None:
        """
        Set a key-value pair in the dictionary.
        
        This method sets or updates a key-value pair, triggering binding updates
        and listener notifications if the value changes.
        
        Args:
            key: The key to set or update
            value: The value to associate with the key
        """
        self.set_item(key, value)
    
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
        self.remove_item(key)
    
    def __str__(self) -> str:
        return f"OD(dict={self._get_dict_value()})"
    
    def __repr__(self) -> str:
        return f"ObservableDict({self._get_dict_value()})"

    def bind_to(self, hook: CarriesDistinctDictHook[K, V]|Hook[dict[K, V]], initial_sync_mode: SyncMode = SyncMode.UPDATE_SELF_FROM_OBSERVABLE) -> None:
        """
        Establish a bidirectional binding with another observable dictionary via. a hook.
        
        This method creates a bidirectional binding between this observable dictionary and another,
        ensuring that changes to either observable are automatically propagated to the other.
        The binding can be configured with different initial synchronization modes.
        
        Args:
            hook: The hook to bind to
            initial_sync_mode: How to synchronize values initially
            
        Raises:
            ValueError: If observable is None
        """
        if hook is None:
            raise ValueError("Cannot bind to None observable")
        if isinstance(hook, CarriesDistinctDictHook):
            hook = hook._get_dict_hook()
        self._get_dict_hook().establish_binding(hook, initial_sync_mode)

    def unbind_from(self, hook: CarriesDistinctDictHook[K, V]|Hook[dict[K, V]]) -> None:
        """
        Remove the bidirectional binding with another observable dictionary.
        
        This method removes the binding between this observable dictionary and another,
        preventing further automatic synchronization of changes.
        
        Args:
            hook: The hook to unbind from
            
        Raises:
            ValueError: If there is no binding to remove
        """
        if isinstance(hook, CarriesDistinctDictHook):
            hook = hook._get_dict_hook()
        self._get_dict_hook().remove_binding(hook)

    def get_observed_component_values(self) -> tuple[dict[K, V]]:
        """
        Get the values of all observables that are bound to this observable.
        
        This method is part of the Observable protocol and provides access to
        the current values of all bound observables.
        
        Returns:
            A tuple containing the current dictionary value
        """
        return tuple(self._get_dict_value())
    
    def set_observed_values(self, values: tuple[dict[K, V]]) -> None:
        """
        Set the values of all observables that are bound to this observable.
        
        The order of the values is important and should not be changed - it is characteristic to this observable.
        
        This method is part of the Observable protocol and allows external
        systems to update this observable's value. It handles all internal
        state changes, binding updates, and listener notifications.
        
        Args:
            values: A tuple containing the new dictionary value to set
        """
 
        self._set_component_values_from_dict(
            {"value": values[0]}
        )