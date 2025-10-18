from typing import Literal, TypeVar, Generic, Optional, Mapping, Any, Callable
from logging import Logger

from ..._hooks.hook_protocol import HookProtocol
from ..._hooks.hook_with_owner_protocol import HookWithOwnerProtocol
from ..._hooks.owned_hook import OwnedHook
from ..._carries_hooks.carries_hooks_base import CarriesHooksBase
from ..._nexus_system.hook_nexus import HookNexus
from ..._auxiliary.listening_base import ListeningBase
from .protocols import ObservableOptionalDefaultSelectionDictProtocol

K = TypeVar("K")
V = TypeVar("V")

class ObservableOptionalDefaultSelectionDict(CarriesHooksBase[Literal["dict", "key", "value"], Any, "ObservableOptionalDefaultSelectionDict[K, V]"], ObservableOptionalDefaultSelectionDictProtocol[K, V], ListeningBase, Generic[K, V]):
    """
    An observable that manages an optional selection from a dictionary with automatic default entry creation.
    
    This observable manages three components:
    - dict: The dictionary to select from
    - key: The selected key in the dictionary (can be None)
    - value: The value at the selected key (can be None when key is None)
    - default_value: The value or callable to use when key is not in the dictionary
    
    **Default Value Behavior:**
    - The key can be None, in which case value must be None
    - If the key is not None and not in the dictionary, a default entry is automatically added to the dictionary for this key
    - The default value can be a constant or a callable that takes the key and returns the value: Callable[[K], V]
    - This allows creating different default values based on which key is being accessed
    - The value will match the dictionary value at the key (after default entry creation if needed), or None if key is None
    
    **New Architecture Features:**
    - Uses add_values_to_be_updated_callback to complete missing values and add default entries
    - Uses validation callbacks to ensure consistency
    - Integrates with NexusManager for value submission
    - Supports custom invalidation callbacks
    """

    def __init__(
        self,
        dict_hook: dict[K, V] | HookProtocol[dict[K, V]],
        key_hook: Optional[K] | HookProtocol[Optional[K]],
        value_hook: Optional[HookProtocol[Optional[V]]],
        default_value: V | Callable[[K], V],
        logger: Optional[Logger] = None):
        """

        """

        def get_default_value(key: K) -> V:
            """Helper to get default value (call if callable, return if constant)."""
            if callable(default_value):
                return default_value(key)  # type: ignore
            return default_value  # type: ignore

        def add_values_to_be_updated_callback(
            self_ref: "ObservableOptionalDefaultSelectionDict[K, V]",
            current_values: Mapping[Literal["dict", "key", "value"], Any],
            submitted_values: Mapping[Literal["dict", "key", "value"], Any]) -> Mapping[Literal["dict", "key", "value"], Any]:
            """
            Add values to be updated if the submitted values are not complete.
            If key is not in dict (and key is not None), add a default entry to the dictionary.
            """

            match ("dict" in submitted_values, "key" in submitted_values, "value" in submitted_values):
                case (True, True, True):
                    return {}
                case (True, True, False):
                    # Dict and key provided - key MUST be in dict if not None
                    if submitted_values["key"] is None:
                        return {"value": None}
                    if submitted_values["key"] not in submitted_values["dict"]:
                        raise KeyError(f"Key {submitted_values['key']} not in submitted dictionary")
                    return {"value": submitted_values["dict"][submitted_values["key"]]}
                case (True, False, True):
                    # Dict and value provided - validate value matches current key
                    if current_values["key"] is None:
                        if submitted_values["value"] is not None:
                            raise ValueError(f"Value {submitted_values['value']} is not None when key is None")
                        return {}
                    if current_values["key"] not in submitted_values["dict"]:
                        raise KeyError(f"Current key {current_values['key']} not in submitted dictionary")
                    if submitted_values["value"] != submitted_values["dict"][current_values["key"]]:
                        raise ValueError(f"Value {submitted_values['value']} is not the same as the value in the dictionary {submitted_values['dict'][current_values['key']]}")
                    return {}
                case (True, False, False):
                    # Dict provided alone - current key must be in dict if not None
                    if current_values["key"] is None:
                        return {"value": None}
                    if current_values["key"] not in submitted_values["dict"]:
                        raise KeyError(f"Current key {current_values['key']} not in submitted dictionary")
                    return {"value": submitted_values["dict"][current_values["key"]]}
                case (False, True, True):
                    # Key and value provided - update dict with new value
                    if submitted_values["key"] is None:
                        return {}
                    _dict = current_values["dict"].copy()
                    _dict[submitted_values["key"]] = submitted_values["value"]
                    return {"dict": _dict}
                case (False, True, False):
                    # Key provided alone - add key to dict with default if not present (and key is not None)
                    if submitted_values["key"] is None:
                        return {"value": None}
                    if submitted_values["key"] not in current_values["dict"]:
                        _dict = current_values["dict"].copy()
                        _default_val = get_default_value(submitted_values["key"])
                        _dict[submitted_values["key"]] = _default_val
                        return {"dict": _dict, "value": _default_val}
                    return {"value": current_values["dict"][submitted_values["key"]]}
                case (False, False, True):
                    # Value provided alone - update dict at current key (if key is not None)
                    if current_values["key"] is None:
                        if submitted_values["value"] is not None:
                            raise ValueError(f"Value {submitted_values['value']} is not None when key is None")
                        return {}
                    _dict = current_values["dict"].copy()
                    _dict[current_values["key"]] = submitted_values["value"]
                    return {"dict": _dict}
                case (False, False, False):
                    return {}

            raise ValueError("Invalid keys")

        def validate_complete_values_in_isolation_callback(
            self_ref: "ObservableOptionalDefaultSelectionDict[K, V]",
            values: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:
            """
            Validate the values in isolation.
            If key is None, value must be None.
            Otherwise, value must match dict[key].
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

        ListeningBase.__init__(self, logger)
        CarriesHooksBase.__init__( # type: ignore
            self,
            invalidate_callback=None,
            validate_complete_values_in_isolation_callback=validate_complete_values_in_isolation_callback,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback,
            logger=logger
        )

        self._default_value: V | Callable[[K], V] = default_value

        if isinstance(dict_hook, HookProtocol):
            _initial_dict_value: dict[K, V] = dict_hook.value
        else:
            _initial_dict_value = dict_hook

        if isinstance(key_hook, HookProtocol):
            _initial_key_value: Optional[K] = key_hook.value # type: ignore
        else:
            _initial_key_value = key_hook

        # Add default entry to dict if key is not None and not in dict
        if _initial_key_value is not None and _initial_key_value not in _initial_dict_value:
            _initial_dict_value = _initial_dict_value.copy()
            _initial_dict_value[_initial_key_value] = get_default_value(_initial_key_value) # type: ignore

        if value_hook is None:
            if _initial_key_value is None:
                _initial_value_value: Optional[V] = None
            else:
                _initial_value_value = _initial_dict_value[_initial_key_value] # type: ignore
        elif isinstance(value_hook, HookProtocol): # type: ignore
            _initial_value_value = value_hook.value # type: ignore
        else:
            raise ValueError("value_hook parameter must either be None or a HookProtocol")

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, logger)
        self._key_hook: OwnedHook[Optional[K]] = OwnedHook[Optional[K]](self, _initial_key_value, logger) # type: ignore
        self._value_hook: OwnedHook[Optional[V]] = OwnedHook[Optional[V]](self, _initial_value_value, logger) # type: ignore

        if isinstance(dict_hook, HookProtocol):
            self._dict_hook.connect_hook(dict_hook, "use_target_value")
        if isinstance(key_hook, HookProtocol):
            self._key_hook.connect_hook(key_hook, "use_target_value") # type: ignore
        if isinstance(value_hook, HookProtocol):
            self._value_hook.connect_hook(value_hook, "use_target_value") # type: ignore

    ########################################################
    # CarriesHooks interface
    ########################################################

    def _get_value_reference_of_hook(self, key: Literal["dict", "key", "value"]) -> Any:
        if key == "dict":
            return self._dict_hook.value
        elif key == "key":
            return self._key_hook.value
        elif key == "value":
            return self._value_hook.value
        else:
            raise ValueError(f"Invalid key: {key}")

    def _get_hook_keys(self) -> set[Literal["dict", "key", "value"]]:
        """Get all keys managed by this observable."""
        return {"dict", "key", "value"}

    def _get_hook(self, key: Literal["dict", "key", "value"]) -> HookWithOwnerProtocol[Any]:
        if key == "dict":
            return self._dict_hook
        elif key == "key":
            return self._key_hook
        elif key == "value":
            return self._value_hook
        else:
            raise ValueError(f"Invalid key: {key}")

    def _get_hook_key(self, hook_or_nexus: "HookProtocol[Any]|HookNexus[Any]") -> Literal["dict", "key", "value"]:
        # Handle both hooks and their associated nexuses
        if hook_or_nexus == self._dict_hook or (hasattr(self._dict_hook, 'hook_nexus') and hook_or_nexus == self._dict_hook.hook_nexus):
            return "dict"
        elif hook_or_nexus == self._key_hook or (hasattr(self._key_hook, 'hook_nexus') and hook_or_nexus == self._key_hook.hook_nexus):
            return "key"
        elif hook_or_nexus == self._value_hook or (hasattr(self._value_hook, 'hook_nexus') and hook_or_nexus == self._value_hook.hook_nexus):
            return "value"
        else:
            raise ValueError(f"Invalid hook or nexus: {hook_or_nexus}")

########################################################
# Specific properties
########################################################

    @property
    def dict_hook(self) -> HookProtocol[dict[K, V]]:
        """
        Get the dictionary hook.
        
        Returns:
            The hook managing the dictionary value.
        """
        return self._dict_hook

    @property
    def key_hook(self) -> HookProtocol[Optional[K]]:
        """
        Get the key hook.
        
        Returns:
            The hook managing the dictionary key.
        """
        return self._key_hook

    @property
    def value_hook(self) -> HookProtocol[Optional[V]]:
        """
        Get the value hook.
        
        Returns:
            The hook managing the retrieved value.
        """
        return self._value_hook

    @property
    def value(self) -> Optional[V]:
        """
        Get the value behind this hook.
        """
        return self._value_hook.value

    @value.setter
    def value(self, value: Optional[V]) -> None:
        """
        Set the value behind this hook.
        """
        success, msg = self._value_hook.submit_value(value)
        if not success:
            raise ValueError(msg)

    @property
    def key(self) -> Optional[K]:
        """
        Get the key behind this hook.
        """
        return self._key_hook.value
    
    @key.setter
    def key(self, value: Optional[K]) -> None:
        """
        Set the key behind this hook.
        """
        success, msg = self._key_hook.submit_value(value)
        if not success:
            raise ValueError(msg)

    ######################################################################

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: Optional[K]) -> None:
        """
        Set the dictionary and key behind this hook.
        If key is not None and not in dict, add default entry.
        """

        # Add default entry if key is not None and not in dict
        if key_value is not None and key_value not in dict_value:
            dict_value = dict_value.copy()
            if callable(self._default_value):
                dict_value[key_value] = self._default_value(key_value)  # type: ignore
            else:
                dict_value[key_value] = self._default_value  # type: ignore

        if key_value is None:
            inferred_value = None
        else:
            inferred_value = dict_value[key_value]

        HookWithOwnerProtocol[Any].submit_values(
            {
                self._dict_hook: dict_value,
                self._key_hook: key_value,
                self._value_hook: inferred_value
            }
        )
