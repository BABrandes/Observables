"""

"""

from typing import Literal, TypeVar, Generic, Optional, Mapping, Any
from .._hooks.hook_like import HookLike
from .._hooks.owned_hook_like import OwnedHookLike
from .._hooks.owned_hook import OwnedHook
from logging import Logger
from .._utils.carries_collective_hooks import CarriesCollectiveHooks
from .._utils.initial_sync_mode import InitialSyncMode
from .._utils.hook_nexus import HookNexus
from .._utils.base_listening import BaseListening

K = TypeVar("K")
V = TypeVar("V")

class ObservableSelectionDict(CarriesCollectiveHooks[Literal["dict", "key", "value"], Any], BaseListening, Generic[K, V]):
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

        BaseListening.__init__(self, logger)

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

        def dict_invalidated(submitted_value: dict[K, V]) -> None:
            """
            This function is called when the dictionary is invalidated.
            """

            # Check if the value_hook carries the correct value
            if self._value_hook.value != submitted_value[self._key_hook.value]:
                # Submit the correct value
                self._value_hook.submit_single_value(submitted_value[self._key_hook.value])

        def key_invalidated(submitted_value: K) -> None:
            """
            This function is called when the key is invalidated.
            """

            current_dict: dict[K, V] = self._dict_hook.value
            current_value: V = self._value_hook.value

            if current_value != current_dict[submitted_value]:
                inferred_value: V = current_dict[submitted_value]
                # Submit the correct value
                self._value_hook.submit_single_value(inferred_value)

        def value_invalidated(submitted_value: V) -> None:
            """
            This function is called when the value is invalidated.
            """

            _key: Optional[K] = self._key_hook.value

            # Check if the value_hook carries the correct value
            if _key is not None:
                if self._dict_hook.value[_key] != submitted_value:
                    # Submit the correct value
                    _new_dict_value: dict[K, V] = self._dict_hook.value.copy()
                    _new_dict_value[_key] = submitted_value
                    self._dict_hook.submit_single_value(_new_dict_value)

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, None, dict_invalidated, logger)
        self._key_hook: OwnedHook[K] = OwnedHook[K](self, _initial_key_value, None, key_invalidated, logger) # type: ignore
        self._value_hook: OwnedHook[V] = OwnedHook[V](self, _initial_value_value, None, value_invalidated, logger) # type: ignore

        if isinstance(dict_hook, HookLike):
            self._dict_hook.connect(dict_hook, InitialSyncMode.USE_TARGET_VALUE)
        if isinstance(key_hook, HookLike):
            self._key_hook.connect(key_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore
        if isinstance(value_hook, HookLike):
            self._value_hook.connect(value_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore

    ########################################################
    # CarriesHooks interface
    ########################################################

    def get_hook(self, key: Literal["dict", "key", "value"]) -> "OwnedHookLike[Any]":
        if key == "dict":
            return self._dict_hook
        elif key == "key":
            return self._key_hook
        elif key == "value":
            return self._value_hook
        else:
            raise ValueError(f"Invalid key: {key}")

    def get_hook_value_as_reference(self, key: Literal["dict", "key", "value"]) -> Any:
        if key == "dict":
            return self._dict_hook.value
        elif key == "key":
            return self._key_hook.value
        elif key == "value":
            return self._value_hook.value
        else:
            raise ValueError(f"Invalid key: {key}")

    def get_hook_keys(self) -> set[Literal["dict", "key", "value"]]:
        """Get all keys managed by this observable."""
        return {"dict", "key", "value"}

    def get_hook_key(self, hook_or_nexus: "HookLike[Any]|HookNexus[Any]") -> Literal["dict", "key", "value"]:
        # Handle both hooks and their associated nexuses
        if hook_or_nexus == self._dict_hook or (hasattr(self._dict_hook, 'hook_nexus') and hook_or_nexus == self._dict_hook.hook_nexus):
            return "dict"
        elif hook_or_nexus == self._key_hook or (hasattr(self._key_hook, 'hook_nexus') and hook_or_nexus == self._key_hook.hook_nexus):
            return "key"
        elif hook_or_nexus == self._value_hook or (hasattr(self._value_hook, 'hook_nexus') and hook_or_nexus == self._value_hook.hook_nexus):
            return "value"
        else:
            raise ValueError(f"Invalid hook or nexus: {hook_or_nexus}")

    def connect(self, hook: "HookLike[Any]", to_key: Literal["dict", "key", "value"], initial_sync_mode: InitialSyncMode) -> None:
        if to_key == "dict":
            self._dict_hook.connect(hook, initial_sync_mode)
        elif to_key == "key":
            self._key_hook.connect(hook, initial_sync_mode)
        elif to_key == "value":
            self._value_hook.connect(hook, initial_sync_mode)
        else:
            raise ValueError(f"Invalid key: {to_key}")

    def disconnect(self, key: Optional[Literal["dict", "key", "value"]]) -> None:
        if key == "dict":
            self._dict_hook.disconnect()
        elif key == "key":
            self._key_hook.disconnect()
        elif key == "value":
            self._value_hook.disconnect()
        else:
            raise ValueError(f"Invalid key: {key}")

    def invalidate_hooks(self) -> tuple[bool, str]:
        return True, "No invalidation needed"

    def _internal_invalidate_hooks(self, submitted_values: dict[Literal["dict", "key", "value"], Any]) -> None:
        """
        Internal invalidate for the nexus to use before the hooks are invalidated.
        """
        pass

    def destroy(self) -> None:
        """
        Destroy the observable by disconnecting all hooks, removing listeners, and invalidating.
        """
        self.disconnect(None)
        self.remove_all_listeners()

########################################################
# CarriesCollectiveHooks interface
########################################################

    def get_collective_hook_keys(self) -> set[Literal["dict", "key", "value"]]:
        return {"dict", "key", "value"}

    def connect_multiple_hooks(self, hooks: Mapping[Literal["dict", "key", "value"], HookLike[Any]], initial_sync_mode: InitialSyncMode) -> None:
        self._dict_hook.connect(hooks["dict"], initial_sync_mode)
        self._key_hook.connect(hooks["key"], initial_sync_mode)
        self._value_hook.connect(hooks["value"], initial_sync_mode)

    def _is_valid_values_as_part_of_owner_impl(self, values: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[Literal[True, False, "InternalInvalidationNeeded"], str]:
        """
        Check if the values can be accepted, so that a subsequent invalidation will result in a valid state.
        """

        if len(values) == 3:
            _dict = values["dict"]
            _key = values["key"]
            _value = values["value"]

            if _dict is None:
                return False, "Dictionary is None"
            if _key not in _dict:
                return False, f"Key {_key} is not in dictionary"
            if _dict[_key] != _value:
                return False, f"Value {_value} is not the same as the value in the dictionary {_dict[_key]}"
            return True, "Everything is valid"

        elif len(values) == 2:

            if "dict" in values and "key" in values:
                _dict = values["dict"]
                _key = values["key"]
                if _dict is None:
                    return False, "Dictionary is None"
                if _key not in _dict:
                    return False, f"Key {_key} is not in dictionary"
                inferred_value: V = _dict[_key]
                if inferred_value != self._value_hook.value:
                    return "InternalInvalidationNeeded", f"Inferred value {inferred_value} is not the same as the value currently carried by the value hook {self._value_hook.value}"
                return True, "Everything is valid"

            elif "dict" in values and "value" in values:
                _dict = values["dict"]
                _value = values["value"]
                _current_key: K = self._key_hook.value

                if _dict is None:
                    return False, "Dictionary is None"
                if _dict[_current_key] != _value:
                    return False, f"Value {_value} is not the same as the value in the dictionary {_dict[_current_key]}"
                return True, "Everything is valid"

            elif "key" in values and "value" in values:
                _key = values["key"]
                _value = values["value"]
                _current_dict = self._dict_hook.value
                if _key not in _current_dict:
                    return False, f"Key {_key} is not in dictionary"
                if _current_dict[_key] != _value:
                    return "InternalInvalidationNeeded", f"Value {_value} is not the same as the value in the dictionary {_current_dict[_key]}"
                return True, "Everything is valid"

            else:
                return False, "Invalid number of keys"

        elif len(values) == 1:
            if "dict" in values:
                _dict = values["dict"]
                _current_key = self._key_hook.value
                _inferred_value = _dict[_current_key]

                if _dict is None:
                    return False, "Dictionary is None"
                if _current_key not in _dict:
                    return False, f"Key {_current_key} is not in dictionary"
                inferred_value = _dict[_current_key]
                if inferred_value != self._value_hook.value:
                    return "InternalInvalidationNeeded", f"Inferred value {inferred_value} is not the same as the value currently carried by the value hook {self._value_hook.value}"
                return True, "Everything is valid"

            elif "key" in values:
                _key = values["key"]
                _current_dict = self._dict_hook.value
                _inferred_value = _current_dict[_key]

                if _key not in _current_dict:
                    return False, f"Key {_key} is not in dictionary"
                if _inferred_value != self._value_hook.value:
                    return "InternalInvalidationNeeded", f"Inferred value {_inferred_value} is not the same as the value currently carried by the value hook {self._value_hook.value}"
                return True, "Everything is valid"

            elif "value" in values:
                _value = values["value"]
                _current_dict = self._dict_hook.value
                _current_key = self._key_hook.value
                if _current_key not in _current_dict:
                    return False, f"Key {_current_key} is not in dictionary"
                if _value != _current_dict[_current_key]:
                    return "InternalInvalidationNeeded", f"Value {_value} is not the same as the value in the dictionary {_current_dict[_current_key]}"
                return True, "Everything is valid"

            else:
                return False, "Invalid number of keys"
        else:
            return False, "Invalid number of keys"

        return True, "Everything is valid"

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
        success, msg = self._value_hook.submit_single_value(value)
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
        success, msg = self._key_hook.submit_single_value(value)
        if not success:
            raise ValueError(msg)
        self._key_hook.invalidate()

    ################################################################################

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: K) -> None:
        """
        Set the dictionary and key behind this hook.
        """

        _inferred_value = dict_value[key_value]
        OwnedHookLike[Any].submit_multiple_values(
            (self._dict_hook, dict_value),
            (self._key_hook, key_value),
            (self._value_hook, _inferred_value)
        )

class ObservableOptionalSelectionDict(CarriesCollectiveHooks[Literal["dict", "key", "value"], Any], BaseListening, Generic[K, V]):
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

        BaseListening.__init__(self, logger)

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

        def dict_invalidated() -> tuple[bool, str]:
            """
            This function is called when the dictionary is invalidated.
            """

            _key = self._key_hook.value

            # Check if the value_hook carries the correct value
            if _key is not None:
                if self._value_hook.value != self._dict_hook.value[_key]:
                    # Submit the correct value
                    success, msg = self._value_hook.submit_single_value(self._dict_hook.value[_key])
                    if not success:
                        raise ValueError(msg)
                    return True, "Successfully invalidated"
                else:
                    self._notify_listeners()
                    return True, "Successfully invalidated"
            else:
                self._notify_listeners()
                return True, "Successfully invalidated"

        def key_invalidated() -> tuple[bool, str]:
            """
            This function is called when the key is invalidated.
            """

            self._notify_listeners()
            return True, "Successfully invalidated"

        def value_invalidated() -> tuple[bool, str]:
            """
            This function is called when the value is invalidated.
            """

            _key: Optional[K] = self._key_hook.value

            # Check if the value_hook carries the correct value
            if _key is not None:
                if self._dict_hook.value[_key] != self._value_hook.value:
                    # Submit the correct value
                    _new_dict_value: dict[K, V] = self._dict_hook.value.copy()
                    _new_dict_value[_key] = self._value_hook.value # type: ignore
                    success, msg = self._dict_hook.submit_single_value(_new_dict_value)
                    if not success:
                        raise ValueError(msg)
                    return True, "Successfully invalidated"
                else:
                    self._notify_listeners()
                    return True, "Successfully invalidated"
            else:
                self._notify_listeners()
                return True, "Successfully invalidated"

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, lambda _: dict_invalidated(), logger)
        self._key_hook: OwnedHook[Optional[K]] = OwnedHook[K](self, _initial_key_value, lambda _: key_invalidated(), logger) # type: ignore
        self._value_hook: OwnedHook[Optional[V]] = OwnedHook[V](self, _initial_value_value, lambda _: value_invalidated(), logger) # type: ignore

        if isinstance(dict_hook, HookLike):
            self._dict_hook.connect(dict_hook, InitialSyncMode.USE_TARGET_VALUE)
        if isinstance(key_hook, HookLike):
            self._key_hook.connect(key_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore
        if isinstance(value_hook, HookLike):
            self._value_hook.connect(value_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore

    ########################################################
    # CarriesHooks interface
    ########################################################

    def get_hook_value_as_reference(self, key: Literal["dict", "key", "value"]) -> Any:
        if key == "dict":
            return self._dict_hook.value
        elif key == "key":
            return self._key_hook.value
        elif key == "value":
            return self._value_hook.value
        else:
            raise ValueError(f"Invalid key: {key}")

    def get_hook_keys(self) -> set[Literal["dict", "key", "value"]]:
        """Get all keys managed by this observable."""
        return {"dict", "key", "value"}

    def get_hook(self, key: Literal["dict", "key", "value"]) -> "OwnedHookLike[Any]":
        if key == "dict":
            return self._dict_hook
        elif key == "key":
            return self._key_hook
        elif key == "value":
            return self._value_hook
        else:
            raise ValueError(f"Invalid key: {key}")

    def get_hook_key(self, hook_or_nexus: "HookLike[Any]|HookNexus[Any]") -> Literal["dict", "key", "value"]:
        # Handle both hooks and their associated nexuses
        if hook_or_nexus == self._dict_hook or (hasattr(self._dict_hook, 'hook_nexus') and hook_or_nexus == self._dict_hook.hook_nexus):
            return "dict"
        elif hook_or_nexus == self._key_hook or (hasattr(self._key_hook, 'hook_nexus') and hook_or_nexus == self._key_hook.hook_nexus):
            return "key"
        elif hook_or_nexus == self._value_hook or (hasattr(self._value_hook, 'hook_nexus') and hook_or_nexus == self._value_hook.hook_nexus):
            return "value"
        else:
            raise ValueError(f"Invalid hook or nexus: {hook_or_nexus}")

    def connect(self, hook: "HookLike[Any]", to_key: Literal["dict", "key", "value"], initial_sync_mode: InitialSyncMode) -> None:
        if to_key == "dict":
            self._dict_hook.connect(hook, initial_sync_mode)
        elif to_key == "key":
            self._key_hook.connect(hook, initial_sync_mode)
        elif to_key == "value":
            self._value_hook.connect(hook, initial_sync_mode)
        else:
            raise ValueError(f"Invalid key: {to_key}")

    def disconnect(self, key: Optional[Literal["dict", "key", "value"]]) -> None:
        if key == "dict":
            self._dict_hook.disconnect()
        elif key == "key":
            self._key_hook.disconnect()
        elif key == "value":
            self._value_hook.disconnect()
        else:
            raise ValueError(f"Invalid key: {key}")

    def is_valid_value(self, hook_key: Literal["dict", "key", "value"], value: Any, value_check_mode: set[ValueCheckMode] = {ValueCheckMode.THIS_OWNER, ValueCheckMode.CONNECTED_HOOKS}) -> tuple[bool, str]:
        return self.is_valid_values({hook_key: value}, value_check_mode)

    def invalidate_hooks(self) -> tuple[bool, str]:
        self._notify_listeners()
        return True, "Successfully invalidated"

    def destroy(self) -> None:
        """
        Destroy the observable by disconnecting all hooks, removing listeners, and invalidating.
        """
        self.disconnect(None)
        self.remove_all_listeners()

########################################################
# CarriesCollectiveHooks interface
########################################################

    def get_collective_hook_keys(self) -> set[Literal["dict", "key", "value"]]:
        return {"dict", "key", "value"}

    def connect_multiple_hooks(self, hooks: Mapping[Literal["dict", "key", "value"], HookLike[Any]], initial_sync_mode: InitialSyncMode) -> None:
        self._dict_hook.connect(hooks["dict"], initial_sync_mode)
        self._key_hook.connect(hooks["key"], initial_sync_mode)
        self._value_hook.connect(hooks["value"], initial_sync_mode)

    def is_valid_values(self, values: Mapping[Literal["dict", "key", "value"], Any], value_check_mode: set[ValueCheckMode] = {ValueCheckMode.THIS_OWNER, ValueCheckMode.CONNECTED_HOOKS}) -> tuple[bool, str]:
        """
        Check if the values can be accepted, so that a subsequent invalidation will result in a valid state.
        """

        from .._utils.hook_nexus import ValueCheckMode as HookNexusValueCheckMode

        if ValueCheckMode.CONNECTED_HOOKS in value_check_mode:
            for hook_key in values:
                hook = self.get_hook(hook_key)
                value = values[hook_key]
                success, message = hook.is_valid_value(value, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                if not success:
                    return False, message

        if ValueCheckMode.THIS_OWNER in value_check_mode:

            if len(values) == 3:
                _dict = values["dict"]
                _key = values["key"]
                _value = values["value"]

                if _dict is None:
                    return False, "Dictionary is None"
                if not _key is None:
                    if _key not in _dict:
                        return False, f"Key {_key} is not in dictionary"
                    if _dict[_key] != _value:
                        return False, f"Value {_value} is not the same as the value in the dictionary {_dict[_key]}"
                else:
                    if _value is not None:
                        return False, "Key is None but value is not None"

            elif len(values) == 2:

                if "dict" in values and "key" in values:
                    _dict = values["dict"]
                    _key = values["key"]
                    inferred_value = _dict[_key]

                    if _dict is None:
                        return False, "Dictionary is None"
                    if not _key is None:
                        if _key not in _dict:
                            return False, f"Key {_key} is not in dictionary"
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._value_hook.is_valid_value(inferred_value, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message
                    else:
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._value_hook.is_valid_value(None, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message

                elif "dict" in values and "value" in values:
                    _dict = values["dict"]
                    _value = values["value"]
                    _current_key = self._key_hook.value

                    if not _current_key is None:
                        if _dict is None:
                            return False, "Dictionary is None"
                        if _dict[_current_key] != _value:
                            return False, f"Value {_value} is not the same as the value in the dictionary {_dict[_current_key]}"
                    else:
                        if _value is not None:
                            return False, "Key is None but value is not None"

                elif "key" in values and "value" in values:
                    _key = values["key"]
                    _value = values["value"]
                    _current_dict = self._dict_hook.value

                    if not _key is None:
                        if _key not in _current_dict:
                            return False, f"Key {_key} is not in dictionary"
                        if _current_dict[_key] != _value:
                            return False, f"Value {_value} is not the same as the value in the dictionary {_current_dict[_key]}"
                    else:
                        if _value is not None:
                            return False, "Key is None but value is not None"

                else:
                    return False, "Invalid number of keys"

            elif len(values) == 1:
                if "dict" in values:
                    _dict = values["dict"]
                    _current_key = self._key_hook.value
                    _inferred_value = _dict[_current_key]

                    if _dict is None:
                        return False, "Dictionary is None"
                    if not _current_key is None:
                        if _current_key not in _dict:
                            return False, f"Key {_current_key} is not in dictionary"
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._value_hook.is_valid_value(_inferred_value, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message
                    else:
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._value_hook.is_valid_value(None, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message

                elif "key" in values:
                    _key = values["key"]
                    _current_dict = self._dict_hook.value
                    _current_value = self._value_hook.value

                    if not _key is None:
                        if _key not in _current_dict:
                            return False, f"Key {_key} is not in dictionary"
                        # For Optional dict: if setting key to non-None, current value must not be None
                        if _current_value is None:
                            return False, f"Cannot set key to {_key} when current value is None"
                    else:
                        # For Optional dict: if setting key to None, current value must be None  
                        if _current_value is not None:
                            return False, f"Cannot set key to None when current value is {_current_value}"
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._value_hook.is_valid_value(None, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message

                elif "value" in values:
                    _value = values["value"]
                    _current_dict = self._dict_hook.value
                    _current_key = self._key_hook.value

                    if not _current_key is None:
                        if _current_key not in _current_dict:
                            return False, f"Key {_current_key} is not in dictionary"
                        # For Optional dict: if key is not None, value cannot be None
                        if _value is None:
                            return False, f"Cannot set value to None when current key is {_current_key}"
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._value_hook.is_valid_value(_value, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message
                    else:
                        if _value is not None:
                            return False, "Key is None but value is not None"

                else:
                    return False, "Invalid number of keys"

        return True, "Everything is valid"


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
        success, msg = self._value_hook.submit_single_value(value)
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
        success, msg = self._key_hook.submit_single_value(value)
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

        OwnedHookLike[Any].submit_multiple_values(
            (self._dict_hook, dict_value),
            (self._key_hook, key_value),
            (self._value_hook, _inferred_value)
        )

class ObservableDefaultSelectionDict(CarriesCollectiveHooks[Literal["dict", "key", "value"], Any], BaseListening, Generic[K, V]):
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

        BaseListening.__init__(self, logger)

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

        self._ignore_invalidation_flag: bool = False

        def dict_invalidated() -> tuple[bool, str]:
            """
            This function is called when the dictionary is invalidated.
            """

            _key: Optional[K] = self._key_hook.value
            if _key is not None:
                if self._dict_hook.value[_key] != self._value_hook.value:
                    # Submit the correct value
                    _new_value_value: V = self._dict_hook.value[_key]
                    success, msg = self._value_hook.submit_single_value(_new_value_value)
                    if not success:
                        raise ValueError(msg)
                    return True, "Successfully invalidated"
                else:
                    self._notify_listeners()
                    return True, "Successfully invalidated"
            else:
                self._notify_listeners()
                return True, "Successfully invalidated"

        def key_invalidated() -> tuple[bool, str]:
            """
            This function is called when the key is invalidated.
            """
            self._notify_listeners()
            return True, "Successfully invalidated"

        def value_invalidated() -> tuple[bool, str]:
            """
            This function is called when the value is invalidated.
            """

            _key: Optional[K] = self._key_hook.value

            if _key is not None:
                if self._dict_hook.value[_key] != self._value_hook.value:
                    # Submit the correct value
                    _new_dict_value: dict[K, V] = self._dict_hook.value.copy()
                    _new_dict_value[_key] = self._value_hook.value # type: ignore
                    success, msg = self._dict_hook.submit_single_value(_new_dict_value)
                    if not success:
                        raise ValueError(msg)
                    return True, "Successfully invalidated"
                else:
                    self._notify_listeners()
                    return True, "Successfully invalidated"
            else:
                self._notify_listeners()
                return True, "Successfully invalidated"

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, lambda _: dict_invalidated(), logger)
        self._key_hook: OwnedHook[Optional[K]] = OwnedHook[Optional[K]](self, _initial_key_value, lambda _: key_invalidated(), logger) # type: ignore
        self._value_hook: OwnedHook[V] = OwnedHook[V](self, _initial_value_value, lambda _: value_invalidated(), logger) # type: ignore

        if isinstance(dict_hook, HookLike):
            self._dict_hook.connect(dict_hook, InitialSyncMode.USE_TARGET_VALUE)
        if isinstance(key_hook, HookLike):
            self._key_hook.connect(key_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore
        if isinstance(value_hook, HookLike):
            self._value_hook.connect(value_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore

    ########################################################
    # CarriesHooks interface
    ########################################################

    def get_hook_value_as_reference(self, key: Literal["dict", "key", "value"]) -> Any:
        if key == "dict":
            return self._dict_hook.value
        elif key == "key":
            return self._key_hook.value
        elif key == "value":
            return self._value_hook.value
        else:
            raise ValueError(f"Invalid key: {key}")

    def get_hook_keys(self) -> set[Literal["dict", "key", "value"]]:
        """Get all keys managed by this observable."""
        return {"dict", "key", "value"}

    def get_hook(self, key: Literal["dict", "key", "value"]) -> "OwnedHookLike[Any]":
        if key == "dict":
            return self._dict_hook
        elif key == "key":
            return self._key_hook
        elif key == "value":
            return self._value_hook
        else:
            raise ValueError(f"Invalid key: {key}")

    def get_hook_key(self, hook_or_nexus: "HookLike[Any]|HookNexus[Any]") -> Literal["dict", "key", "value"]:
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

    def connect(self, hook: "HookLike[Any]", to_key: Literal["dict", "key", "value"], initial_sync_mode: InitialSyncMode) -> None:
        if to_key == "dict":
            self._dict_hook.connect(hook, initial_sync_mode)
        elif to_key == "key":
            self._key_hook.connect(hook, initial_sync_mode)
        elif to_key == "value":
            self._value_hook.connect(hook, initial_sync_mode)
        else:
            raise ValueError(f"Invalid key: {to_key}")

    def disconnect(self, key: Optional[Literal["dict", "key", "value"]]) -> None:
        if key == "dict":
            self._dict_hook.disconnect()
        elif key == "key":
            self._key_hook.disconnect()
        elif key == "value":
            self._value_hook.disconnect()
        else:
            raise ValueError(f"Invalid key: {key}")

    def is_valid_value(self, hook_key: Literal["dict", "key", "value"], value: Any, value_check_mode: set[ValueCheckMode] = {ValueCheckMode.THIS_OWNER, ValueCheckMode.CONNECTED_HOOKS}) -> tuple[bool, str]:
        return self.is_valid_values({hook_key: value}, value_check_mode)

    def invalidate_hooks(self) -> tuple[bool, str]:
        self._notify_listeners()
        return True, "Successfully invalidated"

    def destroy(self) -> None:
        """
        Destroy the observable by disconnecting all hooks, removing listeners, and invalidating.
        """
        self.disconnect(None)
        self.remove_all_listeners()

########################################################
# CarriesCollectiveHooks interface
########################################################

    def get_collective_hook_keys(self) -> set[Literal["dict", "key", "value"]]:
        return {"dict", "key", "value"}

    def connect_multiple_hooks(self, hooks: Mapping[Literal["dict", "key", "value"], HookLike[Any]], initial_sync_mode: InitialSyncMode) -> None:
        self._dict_hook.connect(hooks["dict"], initial_sync_mode)
        self._key_hook.connect(hooks["key"], initial_sync_mode)
        self._value_hook.connect(hooks["value"], initial_sync_mode)

    def is_valid_values(self, values: Mapping[Literal["dict", "key", "value"], Any], value_check_mode: set[ValueCheckMode] = {ValueCheckMode.THIS_OWNER, ValueCheckMode.CONNECTED_HOOKS}) -> tuple[bool, str]:
        """
        Check if the values can be accepted, so that a subsequent invalidation will result in a valid state.
        """

        from .._utils.hook_nexus import ValueCheckMode as HookNexusValueCheckMode

        if ValueCheckMode.CONNECTED_HOOKS in value_check_mode:
            for hook_key in values:
                hook = self.get_hook(hook_key)
                value = values[hook_key]
                success, message = hook.is_valid_value(value, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                if not success:
                    return False, message

        if ValueCheckMode.THIS_OWNER in value_check_mode:

            if len(values) == 3:
                _dict = values["dict"]
                _key = values["key"]
                _value = values["value"]

                if _dict is None:
                    return False, "Dictionary is None"
                if not _key is None:
                    if _key not in _dict:
                        return False, f"Key {_key} is not in dictionary"
                    if _dict[_key] != _value:
                        return False, f"Value {_value} is not the same as the value in the dictionary {_dict[_key]}"
                else:
                    if _value is not self._default_value:
                        return False, f"Key is None but value is not the default value {self._default_value}"

            elif len(values) == 2:

                if "dict" in values and "key" in values:
                    _dict = values["dict"]
                    _key = values["key"]
                    inferred_value = _dict[_key]

                    if _dict is None:
                        return False, "Dictionary is None"
                    if not _key is None:
                        if _key not in _dict:
                            return False, f"Key {_key} is not in dictionary"
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._value_hook.is_valid_value(inferred_value, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message
                    else:
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._value_hook.is_valid_value(self._default_value, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message
                        return True, "Everything is valid"


                elif "dict" in values and "value" in values:
                    _dict = values["dict"]
                    _value = values["value"]
                    _current_key = self._key_hook.value

                    if not _current_key is None:
                        if _dict is None:
                            return False, "Dictionary is None"
                        if _dict[_current_key] != _value:
                            return False, f"Value {_value} is not the same as the value in the dictionary {_dict[_current_key]}"
                    else:
                        if _value is not self._default_value:
                            return False, f"Key is None but value is not the default value {self._default_value}"

                elif "key" in values and "value" in values:
                    _key = values["key"]
                    _value = values["value"]
                    _current_dict = self._dict_hook.value

                    if not _key is None:
                        if _key not in _current_dict:
                            return False, f"Key {_key} is not in dictionary"
                        if _current_dict[_key] != _value:
                            return False, f"Value {_value} is not the same as the value in the dictionary {_current_dict[_key]}"
                        _current_dict = _current_dict.copy()
                        _current_dict[_key] = _value
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._dict_hook.is_valid_value(_current_dict, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message
                    else:
                        if _value is not self._default_value:
                            return False, f"Key is None but value is not the default value {self._default_value}"

                else:
                    return False, "Invalid number of keys"

            elif len(values) == 1:
                if "dict" in values:
                    _dict = values["dict"]
                    _current_key = self._key_hook.value
                    _inferred_value = _dict[_current_key]

                    if _dict is None:
                        return False, "Dictionary is None"
                    if not _current_key is None:
                        if _current_key not in _dict:
                            return False, f"Key {_current_key} is not in dictionary"
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._value_hook.is_valid_value(_inferred_value, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message
                    else:
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._value_hook.is_valid_value(self._default_value, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message

                elif "key" in values:
                    _key = values["key"]
                    _current_dict = self._dict_hook.value
                    _current_value = self._value_hook.value

                    if not _key is None:
                        if _key not in _current_dict:
                            return False, f"Key {_key} is not in dictionary"
                        # For Optional dict: if setting key to non-None, current value must not be None
                        if _current_value is None:
                            return False, f"Cannot set key to {_key} when current value is None"
                    else:
                        # For Default dict: if setting key to None, current value must be None  
                        if _current_value != self._default_value:
                            if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                                success, message = self._value_hook.is_valid_value(self._default_value, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                                if not success:
                                    return False, message
                    return True, "Everything is valid"

                elif "value" in values:
                    _value = values["value"]
                    _current_dict = self._dict_hook.value
                    _current_key = self._key_hook.value

                    if not _current_key is None:
                        if _current_key not in _current_dict:
                            return False, f"Key {_current_key} is not in dictionary"
                        _new_dict_value: dict[K, V] = _current_dict.copy()
                        _new_dict_value[_current_key] = _value
                        if value_check_mode == {ValueCheckMode.CONNECTED_HOOKS}:
                            success, message = self._dict_hook.is_valid_value(_new_dict_value, {HookNexusValueCheckMode.CONNECTED_HOOKS})
                            if not success:
                                return False, message
                    else:
                        if _value != self._default_value:
                            return False, f"Key is None but value is not the default value {self._default_value}"

                else:
                    return False, "Invalid number of keys"
            else:
                return False, "Invalid number of keys"

        return True, "Everything is valid"

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
        success, msg = self._value_hook.submit_single_value(value)
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
        success, msg = self._key_hook.submit_single_value(value)
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

        OwnedHookLike[Any].submit_multiple_values(
            (self._dict_hook, dict_value),
            (self._key_hook, key_value),
            (self._value_hook, inferred_value)
        )