from typing import Literal, TypeVar, Generic, Optional, Mapping, Any
from logging import Logger

from ..._hooks.hook_aliases import Hook
from ..._hooks.owned_hook import OwnedHook
from ..._hooks.hook_protocols.owned_hook_protocol import OwnedHookProtocol
from ..._carries_hooks.carries_hooks_base import CarriesHooksBase
from ..._nexus_system.hook_nexus import HookNexus
from ..._auxiliary.listening_base import ListeningBase
from .protocols import ObservableOptionalSelectionDictProtocol

K = TypeVar("K")
V = TypeVar("V")

class ObservableOptionalSelectionDict(CarriesHooksBase[Literal["dict", "key", "value"], Any, "ObservableOptionalSelectionDict[K, V]"], ObservableOptionalSelectionDictProtocol[K, V], ListeningBase, Generic[K, V]):
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
            self_ref: "ObservableOptionalSelectionDict[K, V]",
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

        ListeningBase.__init__(self, logger)
        CarriesHooksBase.__init__( # type: ignore
            self,
            invalidate_callback=None,
            validate_complete_values_in_isolation_callback=validate_complete_values_in_isolation_callback,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback,
            logger=logger
        )

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

        self._ignore_invalidation_flag: bool = False

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, logger)
        self._key_hook: OwnedHook[Optional[K]] = OwnedHook[K](self, _initial_key_value, logger) # type: ignore
        self._value_hook: OwnedHook[Optional[V]] = OwnedHook[V](self, _initial_value_value, logger) # type: ignore

        if isinstance(dict_hook, Hook):
            self._dict_hook.connect_hook(dict_hook, "use_target_value")
        if isinstance(key_hook, Hook):
            self._key_hook.connect_hook(key_hook, "use_target_value") # type: ignore
        if isinstance(value_hook, Hook):
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

    def _get_hook(self, key: Literal["dict", "key", "value"]) -> OwnedHookProtocol[Any]:
        if key == "dict":
            return self._dict_hook
        elif key == "key":
            return self._key_hook
        elif key == "value":
            return self._value_hook
        else:
            raise ValueError(f"Invalid key: {key}")

    def _get_hook_key(self, hook_or_nexus: "Hook[Any]|HookNexus[Any]") -> Literal["dict", "key", "value"]:
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
    def dict_hook(self) -> Hook[dict[K, V]]:
        """
        Get the dictionary hook.
        
        Returns:
            The hook managing the dictionary value.
        """
        return self._dict_hook

    @property
    def key_hook(self) -> Hook[Optional[K]]:
        """
        Get the key hook.
        
        Returns:
            The hook managing the dictionary key.
        """
        return self._key_hook

    @property
    def value_hook(self) -> Hook[Optional[V]]:
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
        if value is not None and value not in self._dict_hook.value:
            raise KeyError(f"Key {value} not in dictionary")
        success, msg = self._key_hook.submit_value(value)
        if not success:
            raise ValueError(msg)

    ######################################################################

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: Optional[K]) -> None:
        """
        Set the dictionary and key behind this hook.
        """

        if key_value is None:
            _inferred_value = None
        else:
            _inferred_value = dict_value[key_value]

        OwnedHook[Any].submit_values(
            {
                self._dict_hook: dict_value,
                self._key_hook: key_value,
                self._value_hook: _inferred_value
            }
        )
