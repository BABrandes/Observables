from typing import Literal, TypeVar, Generic, Optional, Mapping, Any, Callable
from logging import Logger
from abc import ABC, abstractmethod
from types import MappingProxyType

from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._carries_hooks.complex_observable_base import ComplexObservableBase
from ..._auxiliary.listening_base import ListeningBase

K = TypeVar("K")
V = TypeVar("V")
KT = TypeVar("KT")  # Key type (can be Optional[K] for optional variants)
VT = TypeVar("VT")  # Value type (can be Optional[V] for optional variants)

class ObservableDictBase(
    ComplexObservableBase[
        Literal["dict", "key", "value"], 
        Literal["keys", "values", "length"], 
        Any, 
        frozenset[K]|tuple[V, ...]|int, 
        "ObservableDictBase[K, V, KT, VT]"
    ], 
    ListeningBase, 
    Generic[K, V, KT, VT], 
    ABC
):
    """
    Abstract base class for all dictionary-based observables.
    
    This base class provides common functionality for observables that manage:
    - dict: The dictionary to select from
    - key: The selected key in the dictionary
    - value: The value at the selected key
    
    Plus three read-only secondary hooks:
    - keys: Immutable frozenset of dictionary keys
    - values: Immutable tuple of dictionary values
    - length: Dictionary length (int)
    
    Four Variants (see their specific docs for behavior matrices):
    ┌────────────────────────────────────┬───────────────┬────────────────────┐
    │ Variant                            │ if key is None│ if key not in dict │
    ├────────────────────────────────────┼───────────────┼────────────────────┤
    │ ObservableSelectionDict            │     error     │       error        │
    │ ObservableOptionalSelectionDict    │     None      │       error        │
    │ ObservableDefaultSelectionDict     │     error     │      default       │
    │ ObservableOptionalDefaultSelection │     None      │      default       │
    └────────────────────────────────────┴───────────────┴────────────────────┘
    
    Type Parameters:
        K: Dictionary key type
        V: Dictionary value type
        KT: Actual key type (K or Optional[K] for optional variants)
        VT: Actual value type (V or Optional[V] for optional variants)
    
    Subclasses must implement:
        - _create_add_values_callback(): Creates the add_values_to_be_updated_callback
        - _create_validation_callback(): Creates the validate_complete_values_in_isolation_callback
        - _compute_initial_value(): Computes the initial value from dict and key
    """

    def __init__(
        self,
        dict_hook: Mapping[K, V] | Hook[Mapping[K, V]],
        key_hook: KT | Hook[KT],
        value_hook: Optional[Hook[VT]] = None,
        invalidate_callback: Optional[Callable[[], None]] = None,
        logger: Optional[Logger] = None
    ):
        """
        Initialize the ObservableDictBase.
        
        Args:
            dict_hook: The mapping or hook containing the mapping
            key_hook: The initial key or hook
            value_hook: Optional hook for the value (if None, will be computed)
            logger: Optional logger for debugging
            invalidate_callback: Optional callback called after value changes
        """
        
        # Extract initial values and wrap in MappingProxyType
        if isinstance(dict_hook, Hook):
            _initial_dict_value: Mapping[K, V] = dict_hook.value
            # If hook contains non-MappingProxyType, wrap it
            if not isinstance(_initial_dict_value, MappingProxyType):
                _initial_dict_value = MappingProxyType(dict(_initial_dict_value))
        else:
            _initial_dict_value = dict_hook
            # Wrap in MappingProxyType for immutability
            if not isinstance(_initial_dict_value, MappingProxyType):
                # Convert to dict first to ensure it's a mutable copy, then wrap
                _dict_copy = dict(_initial_dict_value)
                _initial_dict_value = MappingProxyType(_dict_copy)

        if isinstance(key_hook, Hook):
            _initial_key_value: KT = key_hook.value  # type: ignore
        else:
            _initial_key_value = key_hook  # type: ignore

        # Compute initial value if not provided
        if value_hook is None:
            _initial_value_value: VT = self._compute_initial_value(
                _initial_dict_value, 
                _initial_key_value  # type: ignore
            )
        else:
            if not isinstance(value_hook, Hook):  # type: ignore
                raise ValueError("value_hook must be a Hook or None")
            _initial_value_value = value_hook.value  # type: ignore

        # Initialize ListeningBase
        ListeningBase.__init__(self, logger)
        
        # Initialize ComplexObservableBase
        ComplexObservableBase.__init__(  # type: ignore
            self,
            initial_component_values_or_hooks={
                "dict": dict_hook if isinstance(dict_hook, Hook) else _initial_dict_value,
                "key": key_hook if not (key_hook is None or (isinstance(key_hook, type(None)))) else _initial_key_value,
                "value": value_hook if value_hook is not None else _initial_value_value
            },
            secondary_hook_callbacks={
                "keys": lambda values: frozenset(values["dict"].keys()) if values["dict"] is not None else frozenset(),  # type: ignore
                "values": lambda values: tuple(values["dict"].values()) if values["dict"] is not None else (),  # type: ignore
                "length": lambda values: len(values["dict"]) if values["dict"] is not None else 0  # type: ignore
            },
            verification_method=self._create_validation_callback(),
            add_values_to_be_updated_callback=self._create_add_values_callback(),
            invalidate_callback=invalidate_callback,
            logger=logger
        )

    @abstractmethod
    def _create_add_values_callback(self) -> Callable[
        [Any, Mapping[Literal["dict", "key", "value"], Any], Mapping[Literal["dict", "key", "value"], Any]], 
        Mapping[Literal["dict", "key", "value"], Any]
    ]:
        """
        Create the add_values_to_be_updated_callback for this observable.
        
        This callback is responsible for completing partial value submissions.
        Each subclass implements its own logic for handling different combinations
        of dict/key/value submissions.
        
        Returns:
            A callback function that takes (self, current_values, submitted_values)
            and returns additional values to be updated.
        """
        ...

    @abstractmethod
    def _create_validation_callback(self) -> Callable[
        [Mapping[Literal["dict", "key", "value"], Any]], 
        tuple[bool, str]
    ]:
        """
        Create the validate_complete_values_in_isolation_callback for this observable.
        
        This callback validates that a complete set of values (dict, key, value)
        represents a valid state. Each subclass can implement its own validation logic.
        
        Returns:
            A callback function that takes (values) and returns (is_valid, message).
        """
        ...

    @abstractmethod
    def _compute_initial_value(self, initial_dict: Mapping[K, V], initial_key: KT) -> VT:
        """
        Compute the initial value from the dict and key.
        
        Args:
            initial_dict: The initial dictionary
            initial_key: The initial key
            
        Returns:
            The computed initial value
        """
        ...

    ########################################################
    # Common properties
    ########################################################

    @property
    def dict_hook(self) -> Hook[MappingProxyType[K, V]]:
        """
        Get the dictionary hook.
        
        Returns:
            The hook managing the dictionary value as MappingProxyType (immutable).
            
        Note:
            Returns MappingProxyType to enforce immutability. Attempting to mutate
            the returned dict will raise TypeError. All modifications should go
            through change_dict() or submit_values().
        """
        return self._primary_hooks["dict"]  # type: ignore

    def change_dict(self, value: Mapping[K, V]) -> None:
        """
        Change the dictionary behind this hook.
        
        Args:
            value: The new mapping (will be wrapped in MappingProxyType)
        """
        # Wrap in MappingProxyType for immutability
        if not isinstance(value, MappingProxyType):
            value = MappingProxyType(dict(value))
        success, msg = self.submit_value("dict", value)
        if not success:
            raise ValueError(msg)

    @property
    def key_hook(self) -> Hook[KT]:
        """
        Get the key hook.
        
        Returns:
            The hook managing the dictionary key.
        """
        return self.get_hook("key")  # type: ignore

    @property
    def key(self) -> KT:
        """
        Get the key behind this hook.
        """
        return self.get_value_of_hook("key")  # type: ignore
    
    @key.setter
    def key(self, value: KT) -> None:
        """
        Set the key behind this hook.
        """
        success, msg = self.submit_value("key", value)
        if not success:
            raise ValueError(msg)

    def change_key(self, value: KT) -> None:
        """
        Change the key behind this hook.
        """
        success, msg = self.submit_value("key", value)
        if not success:
            raise ValueError(msg)

    @property
    def value_hook(self) -> Hook[VT]:
        """
        Get the value hook.
        
        Returns:
            The hook managing the retrieved value.
        """
        return self.get_hook("value")  # type: ignore

    @property
    def value(self) -> VT:
        """
        Get the value behind this hook.
        """
        return self.get_value_of_hook("value")  # type: ignore

    @value.setter
    def value(self, value: VT) -> None:
        """
        Set the value behind this hook.
        """
        success, msg = self.submit_value("value", value)
        if not success:
            raise ValueError(msg)

    def change_value(self, value: VT) -> None:
        """
        Change the value behind this hook.
        """
        success, msg = self.submit_value("value", value)
        if not success:
            raise ValueError(msg)

    # ------------------------- Secondary hooks -------------------------

    @property
    def keys_hook(self) -> ReadOnlyHook[frozenset[K]]:
        """
        Get the keys hook (read-only).
        
        Returns:
            A read-only hook containing a frozenset of dictionary keys.
        """
        return self.get_hook("keys")  # type: ignore

    @property
    def keys(self) -> frozenset[K]:
        """
        Get the keys behind this hook as an immutable frozenset.
        
        Returns:
            A frozenset of all keys in the dictionary.
        """
        return self.get_value_of_hook("keys")  # type: ignore

    @property
    def values_hook(self) -> ReadOnlyHook[tuple[V, ...]]:
        """
        Get the values hook (read-only).
        """
        return self.get_hook("values")  # type: ignore

    @property
    def values(self) -> tuple[V, ...]:
        """
        Get the values behind this hook.
        """
        return self.get_value_of_hook("values")  # type: ignore

    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the length hook (read-only).
        """
        return self.get_hook("length")  # type: ignore

    @property
    def length(self) -> int:
        """
        Get the length behind this hook.
        """
        return self.get_value_of_hook("length")  # type: ignore

    ########################################################
    # Utility method
    ########################################################

    def set_dict_and_key(self, dict_value: Mapping[K, V], key_value: KT) -> None:
        """
        Set the dictionary and key behind this hook.
        
        This method must be implemented by subclasses as the value computation
        logic differs (e.g., handling None keys in optional variants).
        """
        raise NotImplementedError("Subclasses must implement set_dict_and_key")

