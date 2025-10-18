from typing import Literal, TypeVar, Generic, Optional, Mapping, Any, Callable
from logging import Logger

from ..._hooks.hook_protocol import HookProtocol
from ..._hooks.hook_with_owner_protocol import HookWithOwnerProtocol
from ..._hooks.owned_hook import OwnedHook
from ..._carries_hooks.carries_hooks_base import CarriesHooksBase
from ..._nexus_system.hook_nexus import HookNexus
from ..._auxiliary.listening_base import ListeningBase
from .protocols import ObservableSelectionDictProtocol

K = TypeVar("K")
V = TypeVar("V")

class ObservableSelectionDict(CarriesHooksBase[Literal["dict", "key", "value"], Any, "ObservableSelectionDict"], ObservableSelectionDictProtocol[K, V], ListeningBase, Generic[K, V]):
    """
    An observable that manages a selection from a dictionary in the new hook-based architecture.
    
    This observable maintains three components:
    - dict: The dictionary to select from
    - key: The selected key in the dictionary
    - value: The value at the selected key
    
    The observable ensures that these three components stay synchronized:
    - When dict or key changes, value is automatically updated
    - When value changes, the dictionary is updated at the current key
    - When key changes, value is updated to match the new key
    
    **New Architecture Features:**
    - Uses add_values_to_be_updated_callback to complete missing values
    - Uses validation callbacks to ensure consistency
    - Integrates with NexusManager for value submission
    - Supports custom invalidation callbacks
    """

    def __init__(
        self,
        dict_hook: dict[K, V] | HookProtocol[dict[K, V]],
        key_hook: K | HookProtocol[K],
        value_hook: Optional[HookProtocol[V]] = None,
        logger: Optional[Logger] = None,
        invalidate_callback: Optional[Callable[["ObservableSelectionDict[K, V]"], tuple[bool, str]]] = None):
        """

        """

        def add_values_to_be_updated_callback(
            self_ref: "ObservableSelectionDict[K, V]",
            current_values: Mapping[Literal["dict", "key", "value"], Any],
            submitted_values: Mapping[Literal["dict", "key", "value"], Any]) -> Mapping[Literal["dict", "key", "value"], Any]:
            """
            Add values to be updated if the submitted values are not complete.
            """

            match ("dict" in submitted_values, "key" in submitted_values, "value" in submitted_values):
                case (True, True, True):
                    return {}
                case (True, True, False):
                    # Dict and key provided - get value from dict
                    if submitted_values["key"] not in submitted_values["dict"]:
                        raise ValueError(f"Key {submitted_values['key']} not in dictionary")
                    return {"value": submitted_values["dict"][submitted_values["key"]]}
                case (True, False, True):
                    if submitted_values["value"] != submitted_values["dict"][current_values["key"]]:
                        raise ValueError(f"Value {submitted_values['value']} is not the same as the value in the dictionary {submitted_values['dict'][current_values['key']]}")
                    return {}
                case (True, False, False):
                    # Dict provided - get value for current key
                    return {"value": submitted_values["dict"][current_values["key"]]}
                case (False, True, True):
                    _dict = current_values["dict"].copy()
                    _dict[submitted_values["key"]] = submitted_values["value"]
                    return {
                        "dict": _dict}
                case (False, True, False):
                    return {
                        "value": current_values["dict"][submitted_values["key"]]}
                case (False, False, True):
                    _dict = current_values["dict"].copy()
                    _dict[current_values["key"]] = submitted_values["value"]
                    return {
                        "dict": _dict}
                case (False, False, False):
                    return {}

            raise ValueError("Invalid keys")

        def validate_complete_values_in_isolation_callback(
            self_ref: "ObservableSelectionDict[K, V]",
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

            # Check that the key is in the dictionary
            if values["key"] not in values["dict"]:
                raise KeyError(f"Key {values['key']} not in dictionary")

            # Check that the value is equal to the value in the dictionary
            if values["value"] != values["dict"][values["key"]]:
                return False, "Value not equal to value in dictionary"

            return True, "Validation of complete value set in isolation passed"

        ListeningBase.__init__(self, logger)
        CarriesHooksBase.__init__( # type: ignore
            self,
            invalidate_callback=invalidate_callback,
            validate_complete_values_in_isolation_callback=validate_complete_values_in_isolation_callback,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback,
            logger=logger)

        if isinstance(dict_hook, HookProtocol):
            _initial_dict_value: dict[K, V] = dict_hook.value
        else:
            _initial_dict_value = dict_hook

        if isinstance(key_hook, HookProtocol):
            _initial_key_value: K = key_hook.value # type: ignore
        else:
            _initial_key_value = key_hook

        if value_hook is not None:
            assert isinstance(value_hook, HookProtocol)
            _initial_value_value: V = value_hook.value
        else:
            _initial_value_value = _initial_dict_value[_initial_key_value]

        self._ignore_invalidation_flag: bool = False

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, logger)
        self._key_hook: OwnedHook[K] = OwnedHook[K](self, _initial_key_value, logger) # type: ignore
        self._value_hook: OwnedHook[V] = OwnedHook[V](self, _initial_value_value, logger) # type: ignore

        if isinstance(dict_hook, HookProtocol):
            self._dict_hook.connect_hook(dict_hook, "use_target_value")
        if isinstance(key_hook, HookProtocol):
            self._key_hook.connect_hook(key_hook, "use_target_value") # type: ignore
        if isinstance(value_hook, HookProtocol):
            self._value_hook.connect_hook(value_hook, "use_target_value") # type: ignore

    ########################################################
    # CarriesHooks interface
    ########################################################

    def _get_hook(self, key: Literal["dict", "key", "value"]) -> HookWithOwnerProtocol[Any]:
        if key == "dict":
            return self._dict_hook
        elif key == "key":
            return self._key_hook
        elif key == "value":
            return self._value_hook
        else:
            raise ValueError(f"Invalid key: {key}")

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
    def key_hook(self) -> HookProtocol[K]:
        """
        Get the key hook.
        
        Returns:
            The hook managing the dictionary key.
        """
        return self._key_hook

    @property
    def value_hook(self) -> HookProtocol[V]:
        """
        Get the value hook.
        
        Returns:
            The hook managing the retrieved value.
        """
        return self._value_hook

    @property
    def value(self) -> V:
        """
        Get the value behind this hook.
        """
        return self._value_hook.value

    @value.setter
    def value(self, value: V) -> None:
        """
        Set the value behind this hook.
        """
        success, msg = self._value_hook.submit_value(value)
        if not success:
            raise ValueError(msg)

    @property
    def key(self) -> K:
        """
        Get the key behind this hook.
        """
        return self._key_hook.value
    
    @key.setter
    def key(self, value: K) -> None:
        """
        Set the key behind this hook.
        """
        if value not in self._dict_hook.value:
            raise KeyError(f"Key {value} not in dictionary")
        success, msg = self._key_hook.submit_value(value)
        if not success:
            raise ValueError(msg)

    ################################################################################

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: K) -> None:
        """
        Set the dictionary and key behind this hook.
        """

        _inferred_value = dict_value[key_value]
        HookWithOwnerProtocol[Any].submit_values(
            {
                self._dict_hook: dict_value, 
                self._key_hook: key_value,
                self._value_hook: _inferred_value
            }
        )
