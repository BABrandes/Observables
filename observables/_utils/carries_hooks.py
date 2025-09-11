from typing import Protocol, TYPE_CHECKING, Any, runtime_checkable, TypeVar, Optional, final
from .initial_sync_mode import InitialSyncMode

if TYPE_CHECKING:
    from .hook_like import HookLike
    from .hook_nexus import HookNexus

HK = TypeVar("HK")

@runtime_checkable
class CarriesHooks(Protocol[HK]):
    """
    Protocol for observables that carry a set of hooks.
    """

    def get_hook(self, key: HK) -> "HookLike[Any]":
        ...

    def get_hook_value_as_reference(self, key: HK) -> Any:
        ...

    def get_hook_keys(self) -> set[HK]:
        ...

    def get_hook_key(self, hook_or_nexus: "HookLike[Any]|HookNexus[Any]") -> HK:
        ...

    def connect(self, hook: "HookLike[Any]", to_key: HK, initial_sync_mode: InitialSyncMode) -> None:
        ...

    def disconnect(self, key: Optional[HK]) -> None:
        ...

    def is_valid_hook_value(self, key: HK, value: Any) -> tuple[bool, str]:
        ...

    def invalidate_hooks(self) -> tuple[bool, str]:
        ...

    #########################################################

    @final
    def get_hook_value(self, key: HK) -> Any:
        value_as_reference = self.get_hook_value_as_reference(key)
        if hasattr(value_as_reference, "copy"):
            return value_as_reference.copy() # type: ignore
        else:
            return value_as_reference # type: ignore

    @final
    def get_hook_dict(self) ->  "dict[HK, HookLike[Any]]":
        hook_dict: dict[HK, "HookLike[Any]"] = {}
        for key in self.get_hook_keys():
            hook_dict[key] = self.get_hook(key)
        return hook_dict

    @final
    def get_hook_value_dict(self) -> Any:
        hook_value_dict: dict[HK, Any] = {}
        for key in self.get_hook_keys():
            hook_value_dict[key] = self.get_hook_value(key)
        return hook_value_dict

    @final
    def get_hook_value_as_reference_dict(self) -> Any:
        hook_value_as_reference_dict: dict[HK, Any] = {}
        for key in self.get_hook_keys():
            hook_value_as_reference_dict[key] = self.get_hook_value_as_reference(key)
        return hook_value_as_reference_dict

    @property
    @final
    def hook_dict(self) -> "dict[HK, HookLike[Any]]":
        return self.get_hook_dict()

    @property
    @final
    def hook_value_dict(self) -> dict[HK, Any]:
        return self.get_hook_value_dict()

    @property
    @final
    def hook_value_as_reference_dict(self) -> dict[HK, Any]:
        return self.get_hook_value_as_reference_dict()