"""

"""

from typing import Literal, TypeVar, Generic, Optional, Mapping, Any
from .._hooks.hook_like import HookLike
from .._hooks.owned_hook_like import OwnedHookLike
from .._hooks.owned_hook import OwnedHook
from logging import Logger
from .._utils.base_carries_hooks import BaseCarriesHooks
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.hook_nexus import HookNexus
from .._utils.base_listening import BaseListening

K = TypeVar("K")
V = TypeVar("V")

class ObservableSelectionDict(BaseCarriesHooks[Literal["dict", "key", "value"], Any], BaseListening, Generic[K, V]):
    """

    """

    def __init__(
        self,
        dict_hook: dict[K, V] | HookLike[dict[K, V]],
        key_hook: K | HookLike[K],
        value_hook: Optional[HookLike[V]] = None,
        logger: Optional[Logger] = None):
        """

        """

        def add_values_to_be_updated_callback(
            current_values: Mapping[Literal["dict", "key", "value"], Any],
            submitted_values: Mapping[Literal["dict", "key", "value"], Any]) -> Mapping[Literal["dict", "key", "value"], Any]:
            """
            Add values to be updated if the submitted values are not complete.
            """

            match ("dict" in submitted_values, "key" in submitted_values, "value" in submitted_values):
                case (True, True, True):
                    return {}
                case (True, True, False):
                    return {
                        "value": submitted_values["dict"][submitted_values["key"]]}
                case (True, False, True):
                    if submitted_values["value"] != submitted_values["dict"][current_values["key"]]:
                        raise ValueError(f"Value {submitted_values['value']} is not the same as the value in the dictionary {submitted_values['dict'][self._key_hook.value]}")
                case (True, False, False):
                    return {
                    "value": submitted_values["dict"][current_values["key"]]}
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

        def validation_of_complete_value_set_in_isolation_callback(values: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:
            """
            Validate the values in isolation.
            """

            if values["key"] not in values["dict"]:
                return False, "Key not in dictionary"
            if values["value"] != values["dict"][values["key"]]:
                return False, "Value not equal to value in dictionary"

            return True, "Validation of complete value set in isolation passed"

        BaseListening.__init__(self, logger)
        BaseCarriesHooks[Literal["dict", "key", "value"], Any].__init__(
            self,
            invalidate_callback=None,
            validation_of_complete_value_set_in_isolation_callback=validation_of_complete_value_set_in_isolation_callback,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback,
            logger=logger)

        if isinstance(dict_hook, HookLike):
            _initial_dict_value: dict[K, V] = dict_hook.value
        else:
            _initial_dict_value = dict_hook

        if isinstance(key_hook, HookLike):
            _initial_key_value: K = key_hook.value # type: ignore
        else:
            _initial_key_value = key_hook

        if value_hook is not None:
            assert isinstance(value_hook, HookLike)
            _initial_value_value: V = value_hook.value
        else:
            _initial_value_value = _initial_dict_value[_initial_key_value]

        self._ignore_invalidation_flag: bool = False

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, logger)
        self._key_hook: OwnedHook[K] = OwnedHook[K](self, _initial_key_value, logger) # type: ignore
        self._value_hook: OwnedHook[V] = OwnedHook[V](self, _initial_value_value, logger) # type: ignore

        if isinstance(dict_hook, HookLike):
            self._dict_hook.connect(dict_hook, InitialSyncMode.USE_TARGET_VALUE)
        if isinstance(key_hook, HookLike):
            self._key_hook.connect(key_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore
        if isinstance(value_hook, HookLike):
            self._value_hook.connect(value_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore

    ########################################################
    # CarriesHooks interface
    ########################################################

    def _get_hook(self, key: Literal["dict", "key", "value"]) -> "OwnedHookLike[Any]":
        if key == "dict":
            return self._dict_hook
        elif key == "key":
            return self._key_hook
        elif key == "value":
            return self._value_hook
        else:
            raise ValueError(f"Invalid key: {key}")

    def _get_hook_value_as_reference(self, key: Literal["dict", "key", "value"]) -> Any:
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

    def _get_hook_key(self, hook_or_nexus: "HookLike[Any]|HookNexus[Any]") -> Literal["dict", "key", "value"]:
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
    def dict_hook(self) -> HookLike[dict[K, V]]:
        """
        Get the dictionary hook.
        
        Returns:
            The hook managing the dictionary value.
        """
        return self._dict_hook

    @property
    def key_hook(self) -> HookLike[K]:
        """
        Get the key hook.
        
        Returns:
            The hook managing the dictionary key.
        """
        return self._key_hook

    @property
    def value_hook(self) -> HookLike[V]:
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
        self._value_hook.invalidate()

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
        success, msg = self._key_hook.submit_value(value)
        if not success:
            raise ValueError(msg)
        self._key_hook.invalidate()

    ################################################################################

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: K) -> None:
        """
        Set the dictionary and key behind this hook.
        """

        _inferred_value = dict_value[key_value]
        OwnedHookLike[Any].submit_values(
            {
                self._dict_hook: dict_value, 
                self._key_hook: key_value,
                self._value_hook: _inferred_value
            }
        )

class ObservableOptionalSelectionDict(BaseCarriesHooks[Literal["dict", "key", "value"], Any], BaseListening, Generic[K, V]):
    """
    An observable that allows for an optional key and value.

    if the key is None, the value is None

    """

    def __init__(
        self,
        dict_hook: dict[K, V] | HookLike[dict[K, V]],
        key_hook: Optional[K] | HookLike[Optional[K]] = None,
        value_hook: Optional[HookLike[Optional[V]]] = None,
        logger: Optional[Logger] = None):
        """

        """

        def add_values_to_be_updated_callback(
            current_values: Mapping[Literal["dict", "key", "value"], Any],
            submitted_values: Mapping[Literal["dict", "key", "value"], Any]) -> Mapping[Literal["dict", "key", "value"], Any]:
            """
            Add values to be updated if the submitted values are not complete.
            """

            match ("dict" in submitted_values, "key" in submitted_values, "value" in submitted_values):
                case (True, True, True):
                    return {}
                case (True, True, False):
                    if submitted_values["key"] is None:
                        return {"value": None}
                    else:
                        return {"value": submitted_values["dict"][submitted_values["key"]]}
                case (True, False, True):
                    if current_values["key"] is None:
                        if submitted_values["value"] != None:
                            raise ValueError(f"Value {submitted_values['value']} is not None when key is None")
                    else:
                        if submitted_values["value"] != submitted_values["dict"][current_values["key"]]:
                            raise ValueError(f"Value {submitted_values['value']} is not the same as the value in the dictionary {submitted_values['dict'][self._key_hook.value]}")
                case (True, False, False):
                    if current_values["key"] is None:
                        return {"value": None}
                    else:
                        return {"value": submitted_values["dict"][current_values["key"]]}
                case (False, True, True):
                    if submitted_values["key"] is None:
                        return {}
                    else:
                        _dict = current_values["dict"].copy()
                        _dict[submitted_values["key"]] = submitted_values["value"]
                    return {"dict": _dict}
                case (False, True, False):
                    if submitted_values["key"] is None:
                        return {"value": None}
                    else:
                        return {"value": current_values["dict"][submitted_values["key"]]}
                case (False, False, True):
                    if submitted_values["key"] is None:
                        if submitted_values["value"] != None:
                            raise ValueError(f"Value {submitted_values['value']} is not None when key is None")
                        else:
                            return {}
                    else:
                        _dict = current_values["dict"].copy()
                        _dict[current_values["key"]] = submitted_values["value"]
                    return {"dict": _dict}
                case (False, False, False):
                    return {}

            raise ValueError("Invalid keys")

        def validation_of_complete_value_set_in_isolation_callback(values: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:
            """
            Validate the values in isolation.
            """

            if values["key"] not in values["dict"]:
                return False, "Key not in dictionary"
            if values["key"] is None:
                if not values["value"] is None:
                    return False, "Value is not None when key is None"
            else:
                if values["value"] != values["dict"][values["key"]]:
                    return False, "Value not equal to value in dictionary"

            return True, "Validation of complete value set in isolation passed"

        BaseListening.__init__(self, logger)
        BaseCarriesHooks[Literal["dict", "key", "value"], Any].__init__(
            self,
            invalidate_callback=None,
            validation_of_complete_value_set_in_isolation_callback=validation_of_complete_value_set_in_isolation_callback,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback,
            logger=logger
        )

        if isinstance(dict_hook, HookLike):
            _initial_dict_value: dict[K, V] = dict_hook.value
        else:
            _initial_dict_value = dict_hook

        if key_hook is None:
            _initial_key_value: Optional[K] = None
        elif isinstance(key_hook, HookLike):
            _initial_key_value = key_hook.value # type: ignore
        else:
            # key_hook is a K
            _initial_key_value = key_hook

        if value_hook is None:
            if _initial_key_value is None:
                _initial_value_value: Optional[V] = None
            else:
                _initial_value_value = _initial_dict_value[_initial_key_value]
        elif isinstance(value_hook, HookLike): # type: ignore
            _initial_value_value = value_hook.value # type: ignore
        else:
            raise ValueError("value_hook parameter must either be None or a HookLike")

        self._ignore_invalidation_flag: bool = False

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, logger)
        self._key_hook: OwnedHook[Optional[K]] = OwnedHook[K](self, _initial_key_value, logger) # type: ignore
        self._value_hook: OwnedHook[Optional[V]] = OwnedHook[V](self, _initial_value_value, logger) # type: ignore

        if isinstance(dict_hook, HookLike):
            self._dict_hook.connect(dict_hook, InitialSyncMode.USE_TARGET_VALUE)
        if isinstance(key_hook, HookLike):
            self._key_hook.connect(key_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore
        if isinstance(value_hook, HookLike):
            self._value_hook.connect(value_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore

    ########################################################
    # CarriesHooks interface
    ########################################################

    def _get_hook_value_as_reference(self, key: Literal["dict", "key", "value"]) -> Any:
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

    def _get_hook(self, key: Literal["dict", "key", "value"]) -> "OwnedHookLike[Any]":
        if key == "dict":
            return self._dict_hook
        elif key == "key":
            return self._key_hook
        elif key == "value":
            return self._value_hook
        else:
            raise ValueError(f"Invalid key: {key}")

    def _get_hook_key(self, hook_or_nexus: "HookLike[Any]|HookNexus[Any]") -> Literal["dict", "key", "value"]:
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
    def dict_hook(self) -> HookLike[dict[K, V]]:
        """
        Get the dictionary hook.
        
        Returns:
            The hook managing the dictionary value.
        """
        return self._dict_hook

    @property
    def key_hook(self) -> HookLike[Optional[K]]:
        """
        Get the key hook.
        
        Returns:
            The hook managing the dictionary key.
        """
        return self._key_hook

    @property
    def value_hook(self) -> HookLike[Optional[V]]:
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
        self._value_hook.invalidate()

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
        self._key_hook.invalidate()

    ######################################################################

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: Optional[K]) -> None:
        """
        Set the dictionary and key behind this hook.
        """

        if key_value is None:
            _inferred_value = None
        else:
            _inferred_value = dict_value[key_value]

        OwnedHookLike[Any].submit_values(
            {
                self._dict_hook: dict_value,
                self._key_hook: key_value,
                self._value_hook: _inferred_value
            }
        )

class ObservableDefaultSelectionDict(BaseCarriesHooks[Literal["dict", "key", "value"], Any], BaseListening, Generic[K, V]):
    """
    An observable that allows for a default value and a selection of a key and value.

    This means, if the key is None, the value is the default value.
    If the key is not None, the value is the value in the dictionary at the key.

    """

    def __init__(
        self,
        dict_hook: dict[K, V] | HookLike[dict[K, V]],
        key_hook: Optional[K] | HookLike[Optional[K]],
        value_hook: Optional[HookLike[V]],
        default_value: V,
        logger: Optional[Logger] = None):
        """

        """

        def add_values_to_be_updated_callback(
            current_values: Mapping[Literal["dict", "key", "value"], Any],
            submitted_values: Mapping[Literal["dict", "key", "value"], Any]) -> Mapping[Literal["dict", "key", "value"], Any]:
            """
            Add values to be updated if the submitted values are not complete.
            """

            match ("dict" in submitted_values, "key" in submitted_values, "value" in submitted_values):
                case (True, True, True):
                    return {}
                case (True, True, False):
                    if submitted_values["key"] is None:
                        return {"value": default_value}
                    else:
                        return {"value": submitted_values["dict"][submitted_values["key"]]}
                case (True, False, True):
                    if current_values["key"] is None:
                        if submitted_values["value"] != default_value:
                            raise ValueError(f"Value {submitted_values['value']} is not the default value {default_value} when key is None")
                    else:
                        if submitted_values["value"] != submitted_values["dict"][current_values["key"]]:
                            raise ValueError(f"Value {submitted_values['value']} is not the same as the value in the dictionary {submitted_values['dict'][self._key_hook.value]}")
                case (True, False, False):
                    if current_values["key"] is None:
                        return {"value": default_value}
                    else:
                        return {"value": submitted_values["dict"][current_values["key"]]}
                case (False, True, True):
                    if submitted_values["key"] is None:
                        return {}
                    else:
                        _dict = current_values["dict"].copy()
                        _dict[submitted_values["key"]] = submitted_values["value"]
                    return {"dict": _dict}
                case (False, True, False):
                    if submitted_values["key"] is None:
                        return {"value": default_value}
                    else:
                        return {"value": current_values["dict"][submitted_values["key"]]}
                case (False, False, True):
                    if submitted_values["key"] is None:
                        if submitted_values["value"] != default_value:
                            raise ValueError(f"Value {submitted_values['value']} is not None when key is None")
                        else:
                            return {}
                    else:
                        _dict = current_values["dict"].copy()
                        _dict[current_values["key"]] = submitted_values["value"]
                    return {"dict": _dict}
                case (False, False, False):
                    return {}

            raise ValueError("Invalid keys")

        def validation_of_complete_value_set_in_isolation_callback(values: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:
            """
            Validate the values in isolation.
            """

            if values["key"] not in values["dict"]:
                return False, "Key not in dictionary"
            if values["key"] is None:
                if values["value"] != default_value:
                    return False, f"Value is not the default value {default_value} when key is None"
            else:
                if values["value"] != values["dict"][values["key"]]:
                    return False, "Value not equal to value in dictionary"

            return True, "Validation of complete value set in isolation passed"

        BaseListening.__init__(self, logger)
        BaseCarriesHooks[Literal["dict", "key", "value"], Any].__init__(
            self,
            invalidate_callback=None,
            validation_of_complete_value_set_in_isolation_callback=validation_of_complete_value_set_in_isolation_callback,
            add_values_to_be_updated_callback=add_values_to_be_updated_callback,
            logger=logger
        )

        self._default_value: V = default_value

        if isinstance(dict_hook, HookLike):
            _initial_dict_value: dict[K, V] = dict_hook.value
        else:
            _initial_dict_value = dict_hook

        if isinstance(key_hook, HookLike):
            _initial_key_value: Optional[K] = key_hook.value # type: ignore
        else:
            _initial_key_value = key_hook

        if value_hook is None:
            if _initial_key_value is None:
                _initial_value_value: V = default_value
            else:
                _initial_value_value = _initial_dict_value[_initial_key_value]
        elif isinstance(value_hook, HookLike): # type: ignore
            _initial_value_value = value_hook.value # type: ignore
        else:
            raise ValueError("value_hook parameter must either be None or a HookLike")

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, logger)
        self._key_hook: OwnedHook[Optional[K]] = OwnedHook[Optional[K]](self, _initial_key_value, logger) # type: ignore
        self._value_hook: OwnedHook[V] = OwnedHook[V](self, _initial_value_value, logger) # type: ignore

        if isinstance(dict_hook, HookLike):
            self._dict_hook.connect(dict_hook, InitialSyncMode.USE_TARGET_VALUE)
        if isinstance(key_hook, HookLike):
            self._key_hook.connect(key_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore
        if isinstance(value_hook, HookLike):
            self._value_hook.connect(value_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore

    ########################################################
    # CarriesHooks interface
    ########################################################

    def _get_hook_value_as_reference(self, key: Literal["dict", "key", "value"]) -> Any:
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

    def _get_hook(self, key: Literal["dict", "key", "value"]) -> "OwnedHookLike[Any]":
        if key == "dict":
            return self._dict_hook
        elif key == "key":
            return self._key_hook
        elif key == "value":
            return self._value_hook
        else:
            raise ValueError(f"Invalid key: {key}")

    def _get_hook_key(self, hook_or_nexus: "HookLike[Any]|HookNexus[Any]") -> Literal["dict", "key", "value"]:
        if isinstance(hook_or_nexus, HookNexus):
            if hook_or_nexus == self._dict_hook.hook_nexus:
                return "dict"
            elif hook_or_nexus == self._key_hook.hook_nexus:
                return "key"
            elif hook_or_nexus == self._value_hook.hook_nexus:
                return "value"
            else:
                raise ValueError(f"Invalid hook or nexus: {hook_or_nexus}")
        elif isinstance(hook_or_nexus, HookLike): # type: ignore
            if hook_or_nexus == self._dict_hook:
                return "dict"
            elif hook_or_nexus == self._key_hook:
                return "key"
            elif hook_or_nexus == self._value_hook:
                return "value"
            else:
                raise ValueError(f"Invalid hook or nexus: {hook_or_nexus}")
        else:
            raise ValueError(f"Invalid hook or nexus: {hook_or_nexus}")

########################################################
# Specific properties
########################################################

    @property
    def dict_hook(self) -> HookLike[dict[K, V]]:
        """
        Get the dictionary hook.
        
        Returns:
            The hook managing the dictionary value.
        """
        return self._dict_hook

    @property
    def key_hook(self) -> HookLike[Optional[K]]:
        """
        Get the key hook.
        
        Returns:
            The hook managing the dictionary key.
        """
        return self._key_hook

    @property
    def value_hook(self) -> HookLike[V]:
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
        self._value_hook.invalidate()

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
        self._key_hook.invalidate()

    ######################################################################

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: Optional[K]) -> None:
        """
        Set the dictionary and key behind this hook.
        """

        if key_value is None:
            inferred_value = self._default_value
        else:
            inferred_value = dict_value[key_value]

        OwnedHookLike[Any].submit_values(
            {
                self._dict_hook: dict_value,
                self._key_hook: key_value,
                self._value_hook: inferred_value
            }
        )