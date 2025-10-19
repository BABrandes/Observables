from typing import Literal, TypeVar, Generic, Optional, Mapping, Any, Callable, Protocol
from logging import Logger
from abc import ABC, abstractmethod

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
        tuple[K, ...]|tuple[V, ...]|int, 
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
    - keys: Tuple of dictionary keys
    - values: Tuple of dictionary values
    - length: Dictionary length
    
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
        dict_hook: dict[K, V] | Hook[dict[K, V]],
        key_hook: KT | Hook[KT],
        value_hook: Optional[Hook[VT]],
        logger: Optional[Logger] = None,
        invalidate_callback: Optional[Callable[..., tuple[bool, str]]] = None
    ):
        """
        Initialize the ObservableDictBase.
        
        Args:
            dict_hook: The dictionary or hook containing the dictionary
            key_hook: The initial key or hook
            value_hook: Optional hook for the value (if None, will be computed)
            logger: Optional logger for debugging
            invalidate_callback: Optional callback called after value changes
        """
        
        # Extract initial values
        if isinstance(dict_hook, Hook):
            _initial_dict_value: dict[K, V] = dict_hook.value
        else:
            _initial_dict_value = dict_hook

        if isinstance(key_hook, Hook):
            _initial_key_value: KT = key_hook.value
        else:
            _initial_key_value = key_hook

        # Compute initial value if not provided
        if value_hook is None:
            _initial_value_value: VT = self._compute_initial_value(
                _initial_dict_value, 
                _initial_key_value
            )
        else:
            if not isinstance(value_hook, Hook):
                raise ValueError("value_hook must be a Hook or None")
            _initial_value_value = value_hook.value

        # Initialize ListeningBase
        ListeningBase.__init__(self, logger)
        
        # Initialize ComplexObservableBase
        ComplexObservableBase.__init__(
            self,
            initial_component_values_or_hooks={
                "dict": dict_hook,
                "key": key_hook if not (key_hook is None or (isinstance(key_hook, type(None)))) else _initial_key_value,
                "value": value_hook if value_hook is not None else _initial_value_value
            },
            secondary_hook_callbacks={
                "keys": lambda values: tuple(values["dict"].keys()) if values["dict"] is not None else (),
                "values": lambda values: tuple(values["dict"].values()) if values["dict"] is not None else (),
                "length": lambda values: len(values["dict"]) if values["dict"] is not None else 0
            },
            verification_method=self._create_validation_callback(),
            add_values_to_be_updated_callback=self._create_add_values_callback(),
            invalidate_callback=invalidate_callback,
            logger=logger
        )

    @abstractmethod
    def _create_add_values_callback(self) -> Callable[
        ["ObservableDictBase[K, V, KT, VT]", Mapping[Literal["dict", "key", "value"], Any], Mapping[Literal["dict", "key", "value"], Any]], 
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
    def _compute_initial_value(self, initial_dict: dict[K, V], initial_key: KT) -> VT:
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
    def dict_hook(self) -> Hook[dict[K, V]]:
        """
        Get the dictionary hook.
        
        Returns:
            The hook managing the dictionary value.
        """
        return self._primary_hooks["dict"]  # type: ignore

    def change_dict(self, value: dict[K, V]) -> None:
        """
        Change the dictionary behind this hook.
        """
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
    def keys_hook(self) -> ReadOnlyHook[tuple[K, ...]]:
        """
        Get the keys hook (read-only).
        """
        return self.get_hook("keys")  # type: ignore

    @property
    def keys(self) -> tuple[K, ...]:
        """
        Get the keys behind this hook.
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

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: KT) -> None:
        """
        Set the dictionary and key behind this hook.
        
        This method must be implemented by subclasses as the value computation
        logic differs (e.g., handling None keys in optional variants).
        """
        raise NotImplementedError("Subclasses must implement set_dict_and_key")

