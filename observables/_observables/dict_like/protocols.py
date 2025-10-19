from typing import TypeVar, Optional, Protocol, Mapping, runtime_checkable
from types import MappingProxyType

from ..._hooks.hook_aliases import Hook, ReadOnlyHook

K = TypeVar("K")
V = TypeVar("V")

@runtime_checkable
class ObservableDictProtocol(Protocol[K, V]):
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

@runtime_checkable
class ObservableSelectionDictProtocol(Protocol[K, V]):
    """
    Protocol for observable selection dictionary functionality.
    
    This protocol defines the interface for observables that manage a selection
    from a dictionary, maintaining synchronization between:
    - dict: The dictionary to select from (immutable MappingProxyType)
    - key: The selected key in the dictionary
    - value: The value at the selected key
    
    Note:
        The dict_hook returns MappingProxyType for immutability. Do not attempt
        to mutate it. Use change_dict() or set_dict_and_key() for modifications.
    """
    
    @property
    def dict_hook(self) -> "Hook[MappingProxyType[K, V]]":
        """Get the dictionary hook (returns MappingProxyType for immutability)."""
        ...
    
    @property
    def key_hook(self) -> "Hook[K]":
        """Get the key hook."""
        ...
    
    @property
    def value_hook(self) -> "Hook[V]":
        """Get the value hook."""
        ...
    
    @property
    def value(self) -> V:
        """Get the current value."""
        ...
    
    @value.setter
    def value(self, value: V) -> None:
        """Set the current value."""
        ...
    
    @property
    def key(self) -> K:
        """Get the current key."""
        ...
    
    @key.setter
    def key(self, value: K) -> None:
        """Set the current key."""
        ...
    
    def set_dict_and_key(self, dict_value: Mapping[K, V], key_value: K) -> None:
        """Set the dictionary and key behind this hook."""
        ...

@runtime_checkable
class ObservableOptionalSelectionDictProtocol(Protocol[K, V]):
    """
    Protocol for observable optional selection dictionary functionality.
    
    This protocol extends ObservableSelectionDictProtocol to allow None values:
    - dict: The dictionary to select from (immutable MappingProxyType)
    - key: The selected key in the dictionary (can be None)
    - value: The value at the selected key (can be None)
    
    Note:
        The dict_hook returns MappingProxyType for immutability. Do not attempt
        to mutate it. Use change_dict() or set_dict_and_key() for modifications.
    """
    
    @property
    def dict_hook(self) -> "Hook[MappingProxyType[K, V]]":
        """Get the dictionary hook (returns MappingProxyType for immutability)."""
        ...
    
    @property
    def key_hook(self) -> "Hook[Optional[K]]":
        """Get the key hook."""
        ...
    
    @property
    def value_hook(self) -> "Hook[Optional[V]]":
        """Get the value hook."""
        ...
    
    @property
    def value(self) -> Optional[V]:
        """Get the current value."""
        ...
    
    @value.setter
    def value(self, value: Optional[V]) -> None:
        """Set the current value."""
        ...
    
    @property
    def key(self) -> Optional[K]:
        """Get the current key."""
        ...
    
    @key.setter
    def key(self, value: Optional[K]) -> None:
        """Set the current key."""
        ...
    
    def set_dict_and_key(self, dict_value: Mapping[K, V], key_value: Optional[K]) -> None:
        """Set the dictionary and key behind this hook."""
        ...

@runtime_checkable
class ObservableDefaultSelectionDictProtocol(Protocol[K, V]):
    """
    Protocol for observable default selection dictionary functionality.
    
    This protocol extends ObservableSelectionDictProtocol to automatically
    create default entries when keys are not present in the dictionary.
    
    Note:
        The dict_hook returns MappingProxyType for immutability. Do not attempt
        to mutate it. Use change_dict() or set_dict_and_key() for modifications.
    """
    
    @property
    def dict_hook(self) -> "Hook[MappingProxyType[K, V]]":
        """Get the dictionary hook (returns MappingProxyType for immutability)."""
        ...
    
    @property
    def key_hook(self) -> "Hook[K]":
        """Get the key hook."""
        ...
    
    @property
    def value_hook(self) -> "Hook[V]":
        """Get the value hook."""
        ...
    
    @property
    def value(self) -> V:
        """Get the current value."""
        ...
    
    @value.setter
    def value(self, value: V) -> None:
        """Set the current value."""
        ...
    
    @property
    def key(self) -> K:
        """Get the current key."""
        ...
    
    @key.setter
    def key(self, value: K) -> None:
        """Set the current key."""
        ...
    
    def set_dict_and_key(self, dict_value: Mapping[K, V], key_value: K) -> None:
        """Set the dictionary and key behind this hook."""
        ...

@runtime_checkable
class ObservableOptionalDefaultSelectionDictProtocol(Protocol[K, V]):
    """
    Protocol for observable optional default selection dictionary functionality.
    
    This protocol combines optional selection with automatic default entry creation.
    
    Note:
        The dict_hook returns MappingProxyType for immutability. Do not attempt
        to mutate it. Use change_dict() or set_dict_and_key() for modifications.
    """
    
    @property
    def dict_hook(self) -> "Hook[MappingProxyType[K, V]]":
        """Get the dictionary hook (returns MappingProxyType for immutability)."""
        ...
    
    @property
    def key_hook(self) -> "Hook[Optional[K]]":
        """Get the key hook."""
        ...
    
    @property
    def value_hook(self) -> "Hook[Optional[V]]":
        """Get the value hook."""
        ...
    
    @property
    def value(self) -> Optional[V]:
        """Get the current value."""
        ...
    
    @value.setter
    def value(self, value: Optional[V]) -> None:
        """Set the current value."""
        ...
    
    @property
    def key(self) -> Optional[K]:
        """Get the current key."""
        ...
    
    @key.setter
    def key(self, value: Optional[K]) -> None:
        """Set the current key."""
        ...
    
    def set_dict_and_key(self, dict_value: Mapping[K, V], key_value: Optional[K]) -> None:
        """Set the dictionary and key behind this hook."""
        ...
