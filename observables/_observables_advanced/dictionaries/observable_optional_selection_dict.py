from typing import Literal, TypeVar, Generic, Optional, Mapping, Any
from logging import Logger

from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._carries_hooks.complex_observable_base import ComplexObservableBase
from ..._auxiliary.listening_base import ListeningBase
from .protocols import ObservableOptionalSelectionDictProtocol

K = TypeVar("K")
V = TypeVar("V")

class ObservableOptionalSelectionDict(ComplexObservableBase[Literal["dict", "key", "value"], Literal["keys", "values", "length"], Any, tuple[K, ...]|tuple[V, ...]|int, "ObservableOptionalSelectionDict[K, V]"], ObservableOptionalSelectionDictProtocol[K, V], ListeningBase, Generic[K, V]):
    """
    An observable that manages an optional selection from a dictionary in the new hook-based architecture.
    
    This observable extends ObservableSelectionDict to allow None values:
    - dict: The dictionary to select from
    - key: The selected key in the dictionary (can be None)
    - value: The value at the selected key (can be None)
    
    **Optional Behavior:**
    - If key is None, then value must be None
    - If key is not None, then value must match the dictionary value at that key
    - Allows setting value to None even when key is not None (for flexibility)
    
    **New Architecture Features:**
    - Uses add_values_to_be_updated_callback to complete missing values
    - Uses validation callbacks to ensure consistency with None handling
    - Integrates with NexusManager for value submission
    - Supports custom invalidation callbacks
    """

    def __init__(
        self,
        dict_hook: dict[K, V] | Hook[dict[K, V]],
        key_hook: Optional[K] | Hook[Optional[K]] = None,
        value_hook: Optional[Hook[Optional[V]]] = None,
        logger: Optional[Logger] = None):
        """
        Initialize an ObservableOptionalSelectionDict.
        
        Args:
            dict_hook: The dictionary or hook containing the dictionary
            key_hook: The initial key or hook (can be None)
            value_hook: Optional hook for the value (if None, will be derived from dict[key])
            logger: Optional logger for debugging
        """

        def add_values_to_be_updated_callback(
            self_ref: "ObservableOptionalSelectionDict[K, V]",
            current_values: Mapping[Literal["dict", "key", "value"], Any],
            submitted_values: Mapping[Literal["dict", "key", "value"], Any]) -> Mapping[Literal["dict", "key", "value"], Any]:
            """
            Add values to be updated if the submitted values are not complete.
            """

            match ("dict" in submitted_values, "key" in submitted_values, "value" in submitted_values):
                case (True, True, True):
                    # All three values provided
                    return {}
                case (True, True, False):
                    # Dict and key provided - get value from dict
                    if submitted_values["key"] is None:
                        return {"value": None}
                    else:
                        if submitted_values["key"] not in submitted_values["dict"]:
                            raise KeyError(f"Key {submitted_values['key']} not in dictionary")
                        return {"value": submitted_values["dict"][submitted_values["key"]]}
                case (True, False, True):
                    # Dict and value provided - validate value matches key
                    if current_values["key"] is None:
                        if submitted_values["value"] != None:
                            raise ValueError(f"Value {submitted_values['value']} is not None when key is None")
                        return {}
                    else:
                        if submitted_values["value"] != submitted_values["dict"][current_values["key"]]:
                            raise ValueError(f"Value {submitted_values['value']} is not the same as the value in the dictionary {submitted_values['dict'][current_values['key']]}")
                        return {}
                case (True, False, False):
                    # Dict provided - get value for current key
                    if current_values["key"] is None:
                        return {"value": None}
                    else:
                        return {"value": submitted_values["dict"][current_values["key"]]}
                case (False, True, True):
                    # Key and value provided - update dict with new value
                    if submitted_values["key"] is None:
                        return {}
                    else:
                        _dict = current_values["dict"].copy()
                        _dict[submitted_values["key"]] = submitted_values["value"]
                        return {"dict": _dict}
                case (False, True, False):
                    # Key provided - get value from current dict
                    if submitted_values["key"] is None:
                        return {"value": None}
                    else:
                        if submitted_values["key"] not in current_values["dict"]:
                            raise KeyError(f"Key {submitted_values['key']} not in dictionary")
                        return {"value": current_values["dict"][submitted_values["key"]]}
                case (False, False, True):
                    # Value provided - if current key is None, value must be None, otherwise update dict
                    if current_values["key"] is None:
                        if submitted_values["value"] != None:
                            raise ValueError(f"Value {submitted_values['value']} is not None when key is None")
                        else:
                            return {}
                    else:
                        _dict = current_values["dict"].copy()
                        _dict[current_values["key"]] = submitted_values["value"]
                        return {"dict": _dict}
                case (False, False, False):
                    # Nothing provided - no updates needed
                    return {}

            raise ValueError("Invalid keys")

        def validate_complete_values_in_isolation_callback(
            values: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:
            """
            Validate the values in isolation.
            """

            # Check that all three values are in the values
            if "dict" not in values:
                return False, "Dict not in values"
            if "key" not in values:
                return False, "Key not in values"
            if "value" not in values:
                return False, "Value not in values"

            
            # Check that the dictionary is not None
            if values["dict"] is None:
                return False, "Dictionary is None"

            if values["key"] is None:
                # Check that the value is None when the key is None
                if values["value"] is not None:
                    return False, "Value is not None when key is None"
            else:
                # Check that the key is in the dictionary
                if values["key"] not in values["dict"]:
                    return False, "Key not in dictionary"

                # Check that the value is equal to the value in the dictionary
                if values["value"] != values["dict"][values["key"]]:
                    return False, "Value not equal to value in dictionary"

            return True, "Validation of complete value set in isolation passed"

        # Compute initial values before passing to ComplexObservableBase
        if isinstance(dict_hook, Hook):
            _initial_dict_value: dict[K, V] = dict_hook.value
        else:
            _initial_dict_value = dict_hook

        if key_hook is None:
            _initial_key_value: Optional[K] = None
        elif isinstance(key_hook, Hook):
            _initial_key_value = key_hook.value # type: ignore
        else:
            # key_hook is a K
            _initial_key_value = key_hook

        if value_hook is None:
            if _initial_key_value is None:
                _initial_value_value: Optional[V] = None
            else:
                _initial_value_value = _initial_dict_value[_initial_key_value]
        elif isinstance(value_hook, Hook): # type: ignore
            _initial_value_value = value_hook.value # type: ignore
        else:
            raise ValueError("value_hook parameter must either be None or a Hook")

        ListeningBase.__init__(self, logger)
        ComplexObservableBase.__init__( # type: ignore
            self,
            initial_component_values_or_hooks={
                "dict": dict_hook,
                "key": key_hook if key_hook is not None else _initial_key_value,
                "value": value_hook if value_hook is not None else _initial_value_value
            },
            secondary_hook_callbacks={
                "keys": lambda values: tuple(values["dict"].keys()) if values["dict"] is not None else (), # type: ignore
                "values": lambda values: tuple(values["dict"].values()) if values["dict"] is not None else (), # type: ignore
                "length": lambda values: len(values["dict"]) if values["dict"] is not None else 0 # type: ignore
            },
            verification_method=validate_complete_values_in_isolation_callback,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback,
            invalidate_callback=None,
            logger=logger
        )

########################################################
# Specific properties
########################################################

    # ------------------------- dict hook and value -------------------------

    @property
    def dict_hook(self) -> Hook[dict[K, V]]:
        """
        Get the dictionary hook.
        
        Returns:
            The hook managing the dictionary value.
        """
        return self._primary_hooks["dict"] # type: ignore

    def change_dict(self, value: dict[K, V]) -> None:
        """
        Change the dictionary behind this hook.
        """
        success, msg = self.submit_value("dict", value)
        if not success:
            raise ValueError(msg)

    # ------------------------- key hook and value -------------------------

    @property
    def key_hook(self) -> Hook[Optional[K]]:
        """
        Get the key hook.
        
        Returns:
            The hook managing the dictionary key.
        """
        return self.get_hook("key") # type: ignore

    @property
    def key(self) -> Optional[K]:
        """
        Get the key behind this hook.
        """
        return self.get_value_of_hook("key") # type: ignore
    
    @key.setter
    def key(self, value: Optional[K]) -> None:
        """
        Set the key behind this hook.
        """

        success, msg = self.submit_value("key", value)
        if not success:
            raise ValueError(msg)

    def change_key(self, value: Optional[K]) -> None:
        """
        Change the key behind this hook.
        """
        success, msg = self.submit_value("key", value)
        if not success:
            raise ValueError(msg)

    # ------------------------- value hook and value -------------------------

    @property
    def value_hook(self) -> Hook[Optional[V]]:
        """
        Get the value hook.
        
        Returns:
            The hook managing the retrieved value.
        """
        return self.get_hook("value") # type: ignore

    @property
    def value(self) -> Optional[V]:
        """
        Get the value behind this hook.
        """
        return self.get_value_of_hook("value") # type: ignore

    @value.setter
    def value(self, value: Optional[V]) -> None:
        """
        Set the value behind this hook.
        """
        success, msg = self.submit_value("value", value)
        if not success:
            raise ValueError(msg)

    def change_value(self, value: Optional[V]) -> None:
        """
        Change the value behind this hook.
        """
        success, msg = self.submit_value("value", value)
        if not success:
            raise ValueError(msg)

    # ------------------------- keys hook and keys -------------------------

    @property
    def keys_hook(self) -> ReadOnlyHook[tuple[K, ...]]:
        """
        Get the keys hook.
        """
        return self.get_hook("keys") # type: ignore

    @property
    def keys(self) -> tuple[K, ...]:
        """
        Get the keys behind this hook.
        """
        return self.get_value_of_hook("keys") # type: ignore

    # ------------------------- values hook and values -------------------------

    @property
    def values_hook(self) -> ReadOnlyHook[tuple[V, ...]]:
        """
        Get the values hook.
        """
        return self.get_hook("values") # type: ignore

    @property
    def values(self) -> tuple[V, ...]:
        """
        Get the values behind this hook.
        """
        return self.get_value_of_hook("values") # type: ignore

    # ------------------------- length hook and length -------------------------

    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the length hook.
        """
        return self.get_hook("length") # type: ignore

    @property
    def length(self) -> int:
        """
        Get the length behind this hook.
        """
        return self.get_value_of_hook("length") # type: ignore

    ######################################################################

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: Optional[K]) -> None:
        """
        Set the dictionary and key behind this hook.
        """

        if key_value is None:
            _inferred_value = None
        else:
            _inferred_value = dict_value[key_value]

        self.submit_values({"dict": dict_value, "key": key_value, "value": _inferred_value})
