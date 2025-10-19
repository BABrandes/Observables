from typing import Generic, TypeVar, Optional, overload, Callable, Protocol, runtime_checkable, Literal, Any, Mapping
from logging import Logger
from types import MappingProxyType

from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._hooks.hook_protocols.managed_hook import ManagedHookProtocol
from ..._carries_hooks.complex_observable_base import ComplexObservableBase
from ..._carries_hooks.carries_hooks_protocol import CarriesHooksProtocol
from ..._carries_hooks.observable_serializable import ObservableSerializable
from ..._nexus_system.submission_error import SubmissionError

K = TypeVar("K")
V = TypeVar("V")

@runtime_checkable
class ObservableDictProtocol(CarriesHooksProtocol[Any, Any], Protocol[K, V]):
    """
    Protocol for observable dictionary objects.
    """
    
    @property
    def dict(self) -> MappingProxyType[K, V]:
        """
        Get the immutable dictionary value.
        """
        ...
    
    @dict.setter
    def dict(self, value: Mapping[K, V]) -> None:
        """
        Set the dictionary value.
        """
        ...

    @property
    def dict_hook(self) -> Hook[MappingProxyType[K, V]]:
        """
        Get the hook for the dictionary.
        """
        ...

    def change_dict(self, new_dict: Mapping[K, V]) -> None:
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
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the dictionary length.
        """
        ...

    @property
    def keys(self) -> frozenset[K]:
        """
        Get all keys from the dictionary as a frozenset.
        """
        ...
    
    @property
    def keys_hook(self) -> ReadOnlyHook[frozenset[K]]:
        """
        Get the hook for the dictionary keys.
        """
        ...

    @property
    def values(self) -> tuple[V, ...]:
        """
        Get all values from the dictionary as a tuple.
        """
        ...
    
    @property
    def values_hook(self) -> ReadOnlyHook[tuple[V, ...]]:
        """
        Get the hook for the dictionary values.
        """
        ...
    
class ObservableDict(ComplexObservableBase[Literal["dict"], Literal["length", "keys", "values"], MappingProxyType[K, V], int|frozenset[K]|tuple[V, ...], "ObservableDict"], ObservableDictProtocol[K, V], ObservableSerializable[Literal["dict"], MappingProxyType[K, V]], Generic[K, V]):
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
    def __init__(self, observable_or_hook: Hook[MappingProxyType[K, V]] | ReadOnlyHook[MappingProxyType[K, V]], validator: Optional[Callable[[MappingProxyType[K, V]], bool]] = None, logger: Optional[Logger] = None) -> None:
        """Initialize with a hook to a MappingProxyType."""
        ...
    
    @overload
    def __init__(self, dict_value: Mapping[K, V], logger: Optional[Logger] = None) -> None:
        """Initialize with a Mapping."""
        ...

    @overload
    def __init__(self, observable: ObservableDictProtocol[K, V], logger: Optional[Logger] = None) -> None:
        """Initialize from another ObservableDictProtocol object."""
        ...
    
    @overload
    def __init__(self, dict_value: None = None, logger: Optional[Logger] = None) -> None:
        """Initialize with an empty dictionary."""
        ...
    
    def __init__(self, observable_or_hook_or_value: Mapping[K, V] | Hook[MappingProxyType[K, V]] | ReadOnlyHook[MappingProxyType[K, V]] | None = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize the ObservableDict.
        
        Args:
            observable_or_hook_or_value: Initial dictionary (as Mapping), hook, observable, or None for empty dict
            logger: Optional logger for debugging

        Raises:
            ValueError: If the initial dictionary is not a valid mapping
        """

        if observable_or_hook_or_value is None:
            initial_dict_value: MappingProxyType[K, V] = MappingProxyType({})
            hook: Optional[ManagedHookProtocol[MappingProxyType[K, V]]] = None
        elif isinstance(observable_or_hook_or_value, ObservableDictProtocol):
            initial_dict_value = observable_or_hook_or_value.dict # type: ignore
            hook = observable_or_hook_or_value.dict_hook # type: ignore
        elif isinstance(observable_or_hook_or_value, ManagedHookProtocol):
            initial_dict_value = observable_or_hook_or_value.value # type: ignore
            hook = observable_or_hook_or_value # type: ignore
        else:
            # Convert Mapping to MappingProxyType
            initial_dict_value = MappingProxyType(dict(observable_or_hook_or_value)) # type: ignore
            hook = None

        def is_valid_value(x: Mapping[Literal["dict"], Any]) -> tuple[bool, str]:
            return (True, "Verification method passed") if isinstance(x["dict"], MappingProxyType) else (False, "Value is not a MappingProxyType")

        super().__init__(
            initial_component_values_or_hooks={"dict": initial_dict_value},
            verification_method=is_valid_value,
            secondary_hook_callbacks={
                "length": lambda x: len(x["dict"]),
                "keys": lambda x: frozenset(x["dict"].keys()),
                "values": lambda x: tuple(x["dict"].values())
            },
            logger=logger
        )

        if hook is not None:
            self.connect_hook(hook, "dict", "use_target_value") # type: ignore

    @property
    def dict(self) -> MappingProxyType[K, V]:
        """
        Get the current dictionary as an immutable MappingProxyType.
        
        Returns:
            The current dictionary as a MappingProxyType (immutable view)
        """
        return self._primary_hooks["dict"].value # type: ignore
    
    @dict.setter
    def dict(self, value: Mapping[K, V]) -> None:
        """
        Set the current value of the dictionary.
        
        Args:
            value: A Mapping to set as the new dictionary value
        """
        proxy_value = MappingProxyType(dict(value))
        success, msg = self.submit_value("dict", proxy_value)
        if not success:
            raise SubmissionError(msg, proxy_value, "dict")
    
    def change_dict(self, new_dict: Mapping[K, V]) -> None:
        """
        Change the dictionary value (lambda-friendly method).
        
        This method is equivalent to setting the .dict property but can be used
        in lambda expressions and other contexts where property assignment isn't suitable.
        
        Args:
            new_dict: The new dictionary to set (as a Mapping)
        """
        proxy_value = MappingProxyType(dict(new_dict))
        success, msg = self.submit_value("dict", proxy_value)
        if not success:
            raise SubmissionError(msg, proxy_value, "dict")

    @property
    def dict_hook(self) -> Hook[MappingProxyType[K, V]]:
        """
        Get the hook for the dictionary.
        
        This hook can be used for binding operations with other observables.
        """
        return self._primary_hooks["dict"] # type: ignore
    
    @property
    def length(self) -> int:
        """
        Get the current length of the dictionary.
        """
        return len(self._primary_hooks["dict"].value) # type: ignore
    
    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the dictionary length.
        
        This hook can be used for binding operations that react to length changes.
        """
        return self._secondary_hooks["length"] # type: ignore

    @property
    def keys(self) -> frozenset[K]:
        """
        Get all keys from the dictionary as a frozenset.

        Returns:
            A frozenset containing all keys in the dictionary
        """
        return frozenset(self._primary_hooks["dict"].value.keys()) # type: ignore
    
    @property
    def keys_hook(self) -> ReadOnlyHook[frozenset[K]]:
        """
        Get the hook for the dictionary keys.
        
        This hook can be used for binding operations that react to key changes.
        """
        return self._secondary_hooks["keys"] # type: ignore

    @property
    def values(self) -> tuple[V, ...]:
        """
        Get all values from the dictionary as a tuple.
        
        Returns:
            A tuple containing all values in the dictionary
        """
        return tuple(self._primary_hooks["dict"].value.values()) # type: ignore
    
    @property
    def values_hook(self) -> ReadOnlyHook[tuple[V, ...]]:
        """
        Get the hook for the dictionary values.
        
        This hook can be used for binding operations that react to value changes.
        """
        return self._secondary_hooks["values"] # type: ignore
    
    
    def set_item(self, key: K, value: V) -> None:
        """
        Set a single key-value pair.
        
        Creates a new MappingProxyType with the updated key-value pair.
        
        Args:
            key: The key to set or update
            value: The value to associate with the key
        """
        current = self._primary_hooks["dict"].value
        if key in current and current[key] == value:
            return  # No change
        new_dict = dict(current)
        new_dict[key] = value
        self.dict = MappingProxyType(new_dict)
    
    def get_item(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        Get a value by key with optional default.
        
        Args:
            key: The key to look up
            default: Default value to return if key is not found
            
        Returns:
            The value associated with the key, or the default value if key not found
        """
        return self._primary_hooks["dict"].value.get(key, default) # type: ignore
    
    def has_key(self, key: K) -> bool:
        """
        Check if a key exists in the dictionary.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._primary_hooks["dict"].value # type: ignore
    
    def remove_item(self, key: K) -> None:
        """
        Remove a key-value pair from the dictionary.
        
        Creates a new MappingProxyType without the specified key.
        
        Args:
            key: The key to remove
        """
        current = self._primary_hooks["dict"].value
        if key not in current:
            return  # No change
        new_dict = {k: v for k, v in current.items() if k != key}
        self.dict = MappingProxyType(new_dict)
    
    def clear(self) -> None:
        """
        Clear all items from the dictionary.
        
        Creates a new empty MappingProxyType.
        """
        if not self._primary_hooks["dict"].value:
            return  # No change
        self.dict = MappingProxyType({})
    
    def update(self, other_dict: Mapping[K, V]) -> None:
        """
        Update the dictionary with items from another mapping.
        
        Creates a new MappingProxyType with the updated items.
        
        Args:
            other_dict: Mapping containing items to add or update
        """
        if not other_dict:
            return  # No change
        # Check if any values would actually change
        current = self._primary_hooks["dict"].value
        has_changes = False
        for key, value in other_dict.items():
            if key not in current or current[key] != value:
                has_changes = True
                break
        
        if not has_changes:
            return  # No change
        
        new_dict = dict(current)
        new_dict.update(other_dict)
        self.dict = MappingProxyType(new_dict)
    
    def items(self) -> tuple[tuple[K, V], ...]:
        """
        Get all key-value pairs from the dictionary as a tuple of tuples.
        
        Returns:
            A tuple of tuples, each containing a key-value pair
        """
        return tuple(self._primary_hooks["dict"].value.items()) # type: ignore
    
    def __len__(self) -> int:
        """
        Get the number of key-value pairs in the dictionary.
        
        Returns:
            The number of key-value pairs
        """
        return len(self._primary_hooks["dict"].value) # type: ignore
    
    def __contains__(self, key: K) -> bool:
        """
        Check if a key exists in the dictionary.
        
        Args:
            key: The key to check for
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._primary_hooks["dict"].value # type: ignore
    
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
        current = self._primary_hooks["dict"].value
        if key not in current:
            raise KeyError(f"Key '{key}' not found in dictionary")
        return current[key] # type: ignore
    
    def __setitem__(self, key: K, value: V) -> None:
        """
        Set a key-value pair in the dictionary.
        
        Creates a new MappingProxyType with the updated key-value pair.
        
        Args:
            key: The key to set or update
            value: The value to associate with the key
        """
        current = self._primary_hooks["dict"].value
        new_dict = {**current, key: value}
        self.dict = MappingProxyType(new_dict)
    
    def __delitem__(self, key: K) -> None:
        """
        Remove a key-value pair from the dictionary.
        
        Creates a new MappingProxyType without the specified key.
        
        Args:
            key: The key to remove
            
        Raises:
            KeyError: If the key is not found in the dictionary
        """
        current = self._primary_hooks["dict"].value
        if key not in current:
            raise KeyError(f"Key '{key}' not found in dictionary")
        new_dict = {k: v for k, v in current.items() if k != key}
        self.dict = MappingProxyType(new_dict)
    
    def __str__(self) -> str:
        return f"OD(dict={dict(self._primary_hooks['dict'].value)})"
    
    def __repr__(self) -> str:
        return f"ObservableDict({dict(self._primary_hooks['dict'].value)})"

    #### ObservableSerializable implementation ####

    def get_value_references_for_serialization(self) -> Mapping[Literal["dict"], MappingProxyType[K, V]]:
        return {"dict": self._primary_hooks["dict"].value}

    def set_value_references_from_serialization(self, values: Mapping[Literal["dict"], MappingProxyType[K, V]]) -> None:
        self.dict = values["dict"]

    #########################################################
    # Deprecated Hook Aliases (for backwards compatibility)
    #########################################################

    @property
    def value(self) -> MappingProxyType[K, V]:
        """Deprecated: Use .dict instead."""
        return self.dict
    
    @value.setter
    def value(self, val: Mapping[K, V]) -> None:
        """Deprecated: Use .dict instead."""
        self.dict = val

    @property
    def value_hook(self) -> Hook[MappingProxyType[K, V]]:
        """Deprecated: Use .dict_hook instead."""
        return self.dict_hook

    def change_value(self, new_dict: Mapping[K, V]) -> None:
        """Deprecated: Use .change_dict instead."""
        self.change_dict(new_dict)