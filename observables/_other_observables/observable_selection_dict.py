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
        value_hook: V | HookLike[V],
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

        if isinstance(value_hook, HookLike):
            _initial_value_value: V = value_hook.value # type: ignore
        else:
            _initial_value_value = value_hook

        self._ignore_invalidation_flag: bool = False

        def dict_or_key_invalidated() -> tuple[bool, str]:
            if self._ignore_invalidation_flag:
                return True, "Invalidation already on its way"
            if self._key_hook.value in self._dict_hook.value:
                self._ignore_invalidation_flag = True
                self._value_hook.submit_single_value(self._dict_hook.value[self._key_hook.value])
                self._ignore_invalidation_flag = False
            return True, "Successfully invalidated"

        def value_invalidated() -> tuple[bool, str]:
            if self._ignore_invalidation_flag:
                return True, "Invalidation already on its way"
            if self._key_hook.value is not None:
                dict_value: dict[K, V] = self._dict_hook.value
                dict_value[self._key_hook.value] = self._value_hook.value
                self._ignore_invalidation_flag = True
                self._dict_hook.submit_single_value(dict_value)
                self._ignore_invalidation_flag = False
            return True, "Successfully invalidated"

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, lambda _: dict_or_key_invalidated(), logger)
        self._key_hook: OwnedHook[K] = OwnedHook[K](self, _initial_key_value, lambda _: dict_or_key_invalidated(), logger) # type: ignore
        self._value_hook: OwnedHook[V] = OwnedHook[V](self, _initial_value_value, lambda _: value_invalidated(), logger) # type: ignore

        def verification_method(x: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:

            # All three keys must be present!
            if "dict" not in x or "key" not in x or "value" not in x:
                return False, "All three keys must be present"

            if x["value"] is None:
                return False, "Value is None"
            if x["key"] is None:
                return False, "Key is None"
            if x["dict"] is None:
                return False, "Dictionary is None"

            if x["key"] not in x["dict"]:
                return False, "Key is not in dictionary"

            return True, "Verification method passed"

        self._verification_method = verification_method

        if isinstance(dict_hook, HookLike):
            self._dict_hook.connect(dict_hook, InitialSyncMode.USE_TARGET_VALUE)
        if isinstance(key_hook, HookLike):
            self._key_hook.connect(key_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore
        if isinstance(value_hook, HookLike):
            self._value_hook.connect(value_hook, InitialSyncMode.USE_TARGET_VALUE) # type: ignore

    def verify_values(self, values: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:
        """
        Verify the values.

        Args:
            values: The values to verify.

        Returns:
            A tuple containing a boolean indicating if the values are valid and a string describing the result.
        """
        values = {**self.get_hook_value_as_reference_dict(), **values}
        return self._verification_method(values)

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
        if hook_or_nexus == self._dict_hook:
            return "dict"
        elif hook_or_nexus == self._key_hook:
            return "key"
        elif hook_or_nexus == self._value_hook:
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

    def is_valid_hook_value(self, hook_key: Literal["dict", "key", "value"], value: Any) -> tuple[bool, str]:
        values = self.get_hook_value_as_reference_dict()
        values[hook_key] = value
        return self._verification_method(values)

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

    def is_valid_hook_values(self, values: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:
        values = {**self.get_hook_value_as_reference_dict(), **values}
        return self._verification_method(values)

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
        
        success, message = self._verification_method({"dict": dict_value, "key": key_value})
        if not success:
            raise ValueError(message)
        
        OwnedHookLike[Any].submit_multiple_values(
            (self._dict_hook, dict_value),
            (self._key_hook, key_value)
        )

class ObservableOptionalSelectionDict(CarriesCollectiveHooks[Literal["dict", "key", "value"], Any], BaseListening, Generic[K, V]):
    """

    """

    def __init__(
        self,
        dict_hook: dict[K, V] | HookLike[dict[K, V]],
        key_hook: Optional[K] | HookLike[Optional[K]] = None,
        value_hook: Optional[V] | HookLike[Optional[V]] = None,
        logger: Optional[Logger] = None):
        """

        """

        BaseListening.__init__(self, logger)

        if isinstance(dict_hook, HookLike):
            _initial_dict_value: dict[K, V] = dict_hook.value
        else:
            _initial_dict_value = dict_hook

        if isinstance(key_hook, HookLike):
            _initial_key_value: Optional[K] = key_hook.value # type: ignore
        else:
            _initial_key_value = key_hook

        if isinstance(value_hook, HookLike):
            _initial_value_value: Optional[V] = value_hook.value # type: ignore
        else:
            _initial_value_value = value_hook

        self._ignore_invalidation_flag: bool = False

        def dict_or_key_invalidated() -> tuple[bool, str]:
            if self._ignore_invalidation_flag:
                return True, "Invalidation already on its way"
            key_value: Optional[K] = self._key_hook.value
            if key_value is None:
                self._ignore_invalidation_flag = True
                self._value_hook.submit_single_value(None)
                self._ignore_invalidation_flag = False
            else:
                if key_value in self._dict_hook.value:
                    self._ignore_invalidation_flag = True
                    self._value_hook.submit_single_value(self._dict_hook.value[key_value])
                    self._ignore_invalidation_flag = False
            return True, "Successfully invalidated"

        def value_invalidated() -> tuple[bool, str]:
            if self._ignore_invalidation_flag:
                return True, "Invalidation already on its way"
            dict_value: dict[K, V] = self._dict_hook.value
            key_value: Optional[K] = self._key_hook.value
            if key_value is None:
                if self._value_hook.value is not None:
                    raise ValueError("Cannot set value when key is None")
            else:
                dict_value[key_value] = self._value_hook.value # type: ignore
            self._ignore_invalidation_flag = True
            self._dict_hook.submit_single_value(dict_value)
            self._ignore_invalidation_flag = False
            return True, "Successfully invalidated"

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, lambda _: dict_or_key_invalidated(), logger)
        self._key_hook: OwnedHook[Optional[K]] = OwnedHook[K](self, _initial_key_value, lambda _: dict_or_key_invalidated(), logger) # type: ignore
        self._value_hook: OwnedHook[Optional[V]] = OwnedHook[V](self, _initial_value_value, lambda _: value_invalidated(), logger) # type: ignore

        def verification_method(x: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:

            # All three keys must be present!
            if "dict" not in x or "key" not in x or "value" not in x:
                return False, "All three keys must be present"

            if x["dict"] is None:
                return False, "Dictionary is None"
            if x["key"] is None and x["value"] is None:
                return True, "Verification method passed"
            if x["key"] is None:
                return False, "Key is None but value is not None"
            if x["value"] is None:
                return False, "Value is None but key is not None"
            if x["key"] not in x["dict"]:
                return False, "Key is not in dictionary"

            return True, "Verification method passed"

        self._verification_method = verification_method

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
        if hook_or_nexus == self._dict_hook:
            return "dict"
        elif hook_or_nexus == self._key_hook:
            return "key"
        elif hook_or_nexus == self._value_hook:
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

    def is_valid_hook_value(self, hook_key: Literal["dict", "key", "value"], value: Any) -> tuple[bool, str]:
        values = self.get_hook_value_as_reference_dict()
        values[hook_key] = value
        return self._verification_method(values)

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

    def is_valid_hook_values(self, values: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:
        values = {**self.get_hook_value_as_reference_dict(), **values}
        return self._verification_method(values)

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

        success, msg = self.is_valid_hook_values({"dict": dict_value, "key": key_value})
        if not success:
            raise ValueError(msg)

        OwnedHookLike[Any].submit_multiple_values(
            (self._dict_hook, dict_value),
            (self._key_hook, key_value)
        )

class ObservableDefaultSelectionDict(CarriesCollectiveHooks[Literal["dict", "key", "value"], Any], BaseListening, Generic[K, V]):
    """

    """

    def __init__(
        self,
        dict_hook: dict[K, V] | HookLike[dict[K, V]],
        key_hook: Optional[K] | HookLike[Optional[K]],
        value_hook: V | HookLike[V],
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

        if isinstance(value_hook, HookLike):
            _initial_value_value: V = value_hook.value # type: ignore
        else:
            _initial_value_value = value_hook

        self._ignore_invalidation_flag: bool = False

        def dict_or_key_invalidated() -> tuple[bool, str]:
            if self._ignore_invalidation_flag:
                return True, "Invalidation already on its way"
            key_value: Optional[K] = self._key_hook.value
            if key_value is None:
                self._ignore_invalidation_flag = True
                self._value_hook.submit_single_value(self._default_value)
                self._ignore_invalidation_flag = False
            else:
                if key_value in self._dict_hook.value:
                    self._ignore_invalidation_flag = True
                    self._value_hook.submit_single_value(self._dict_hook.value[key_value])
                    self._ignore_invalidation_flag = False
            return True, "Successfully invalidated"

        def value_invalidated() -> tuple[bool, str]:
            if self._ignore_invalidation_flag:
                return True, "Invalidation already on its way"
            dict_value: dict[K, V] = self._dict_hook.value
            key_value: Optional[K] = self._key_hook.value
            if key_value is None:
                if self._value_hook.value != self._default_value:
                    raise ValueError("Cannot set value when key is None and value is not the default value")
            else:
                dict_value[key_value] = self._value_hook.value # type: ignore
            self._ignore_invalidation_flag = True
            self._dict_hook.submit_single_value(dict_value)
            self._ignore_invalidation_flag = False
            return True, "Successfully invalidated"

        self._dict_hook: OwnedHook[dict[K, V]] = OwnedHook[dict[K, V]](self, _initial_dict_value, lambda _: dict_or_key_invalidated(), logger)
        self._key_hook: OwnedHook[Optional[K]] = OwnedHook[K](self, _initial_key_value, lambda _: dict_or_key_invalidated(), logger) # type: ignore
        self._value_hook: OwnedHook[V] = OwnedHook[V](self, _initial_value_value, lambda _: value_invalidated(), logger) # type: ignore

        def verification_method(x: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:

            # All three keys must be present!
            if "dict" not in x or "key" not in x or "value" not in x:
                return False, "All three keys must be present"

            if x["dict"] is None:
                return False, "Dictionary is None"
            if x["key"] is None and x["value"] == self._default_value:
                return True, "Verification method passed"
            if x["key"] is None:
                return False, "Key is None but value is not the default value"
            if x["value"] == self._default_value:
                return False, "Value is default but key is not None"
            if x["key"] not in x["dict"]:
                return False, "Key is not in dictionary"

            return True, "Verification method passed"

        self._verification_method = verification_method

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
        if hook_or_nexus == self._dict_hook:
            return "dict"
        elif hook_or_nexus == self._key_hook:
            return "key"
        elif hook_or_nexus == self._value_hook:
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

    def is_valid_hook_value(self, hook_key: Literal["dict", "key", "value"], value: Any) -> tuple[bool, str]:
        values = self.get_hook_value_as_reference_dict()
        values[hook_key] = value
        return self._verification_method(values)

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

    def is_valid_hook_values(self, values: Mapping[Literal["dict", "key", "value"], Any]) -> tuple[bool, str]:
        values = {**self.get_hook_value_as_reference_dict(), **values}
        return self._verification_method(values)

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

        success, msg = self.is_valid_hook_values({"dict": dict_value, "key": key_value})
        if not success:
            raise ValueError(msg)

        OwnedHookLike[Any].submit_multiple_values(
            (self._dict_hook, dict_value),
            (self._key_hook, key_value)
        )