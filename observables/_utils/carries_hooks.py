from typing import Protocol, TYPE_CHECKING, Any, runtime_checkable, TypeVar, Optional, final, Literal
from .initial_sync_mode import InitialSyncMode

if TYPE_CHECKING:
    from .._hooks.owned_hook_like import OwnedHookLike
    from .hook_nexus import HookNexus

HK = TypeVar("HK")
HV = TypeVar("HV")

@runtime_checkable
class CarriesHooks(Protocol[HK, HV]):
    """
    Protocol for observables that carry a set of hooks.

    Must implement:

        - def get_hook(self, key: HK) -> "OwnedHookLike[HV]":
        
            Get a hook by its key.

        - def get_hook_value_as_reference(self, key: HK) -> HV:
        
            Get a value as a reference by its key.
            The returned value is a reference, so modifying it will modify the observable.

        - def get_hook_keys(self) -> set[HK]:
        
            Get all keys of the hooks.

        - def get_hook_key(self, hook_or_nexus: "OwnedHookLike[HV]|HookNexus[HV]") -> HK:
        
            Get the key of a hook or nexus.

        - def connect(self, hook: "OwnedHookLike[HV]", to_key: HK, initial_sync_mode: InitialSyncMode) -> None:
        
            Connect a hook to another hook.

        - def disconnect(self, key: Optional[HK]) -> None:
        
            Disconnect a hook by its key.

        - def _internal_invalidate_hooks(self, submitted_values: dict[HK, HV]) -> None:
        
            Internal invalidate for the nexus to use before the hooks are invalidated.
        
        - def invalidate_hooks(self) -> tuple[bool, str]:
        
            Invalidate all hooks.

        - destroy(self) -> None:
        
            Destroy the observable by disconnecting all hooks, removing listeners, and invalidating.
    """

    def get_hook(self, key: HK) -> "OwnedHookLike[HV]":
        """
        Get a hook by its key.

        Args:
            key: The key of the hook to get

        Returns:
            The hook
        """
        ...

    def get_hook_value_as_reference(self, key: HK) -> HV:
        """
        Get a value as a reference by its key.

        ** The returned value is a reference, so modifying it will modify the observable.

        Args:
            key: The key of the hook to get

        Returns:
            The value
        """
        ...

    def get_hook_keys(self) -> set[HK]:
        """
        Get all keys of the hooks.
        """
        ...

    def get_hook_key(self, hook_or_nexus: "OwnedHookLike[HV]|HookNexus[HV]") -> HK:
        """
        Get the key of a hook or nexus.
        """
        ...

    def connect(self, hook: "OwnedHookLike[HV]", to_key: HK, initial_sync_mode: InitialSyncMode) -> None:
        """
        Connect a hook to another hook.
        """
        ...

    def disconnect(self, key: Optional[HK]) -> None:
        """
        Disconnect a hook by its key.

        Args:
            key: The key of the hook to disconnect. If None, all hooks will be disconnected.
        """
        ...

    def destroy(self) -> None:
        """
        Destroy the observable by disconnecting all hooks, removing listeners, and invalidating.
        """
        ...

    def invalidate_hooks(self) -> tuple[bool, str]:
        """
        Invalidate all hooks.
        """
        ...

    def _internal_invalidate_hooks(self, submitted_values: dict[HK, HV]) -> None:
        """
        Internal invalidate for the nexus to use before the hooks are invalidated.
        """
        ...

    #########################################################

    @final
    def _is_valid_value_as_part_of_owner(self, hook_key: HK, value: HV) -> tuple[Literal[True, False, "InternalInvalidationNeeded"], str]:
        """
        Check if a value is valid as part of the owner.
        """

        hook = self.get_hook(hook_key)
        success, msg = hook._is_valid_value_as_part_of_owner(value) # type: ignore
        return success, msg

    @final
    def is_valid_value(self, hook_key: HK, value: HV) -> tuple[bool, str]:
        """
        Check if a value is valid.
        """

        hook = self.get_hook(hook_key)

        success, msg = hook.hook_nexus.validate_single_value(value)
        if success == False:
            return False, msg
        else:
            return True, "Value is valid"

    @final
    def get_hook_value(self, key: HK) -> HV:
        """
        Get a value as a copy by its key.

        ** The returned value is a copy, so modifying it will not modify the observable.
        """
        value_as_reference = self.get_hook_value_as_reference(key)
        if hasattr(value_as_reference, "copy"):
            return value_as_reference.copy() # type: ignore
        else:
            return value_as_reference # type: ignore

    @final
    def get_hook_dict(self) ->  "dict[HK, OwnedHookLike[HV]]":
        """
        Get a dictionary of hooks.
        """
        hook_dict: dict[HK, "OwnedHookLike[Any]"] = {}
        for key in self.get_hook_keys():
            hook_dict[key] = self.get_hook(key)
        return hook_dict

    @final
    def get_hook_value_dict(self) -> dict[HK, HV]:
        """
        Get a dictionary of values.

        ** The returned values are copies, so modifying them will not modify the observable.
        """
        hook_value_dict: dict[HK, Any] = {}
        for key in self.get_hook_keys():
            hook_value_dict[key] = self.get_hook_value(key)
        return hook_value_dict

    @final
    def get_hook_value_as_reference_dict(self) -> dict[HK, HV]:
        """
        Get a dictionary of values as references.

        ** The returned values are references, so modifying them will modify the owner.
        
        ** Items can be added and removed without affecting the owner.
        """
        hook_value_as_reference_dict: dict[HK, Any] = {}
        for key in self.get_hook_keys():
            hook_value_as_reference_dict[key] = self.get_hook_value_as_reference(key)
        return hook_value_as_reference_dict

    @property
    @final
    def hook_dict(self) -> "dict[HK, OwnedHookLike[HV]]":
        """
        Get a dictionary of hooks.
        """
        return self.get_hook_dict()

    @property
    @final
    def hook_value_dict(self) -> dict[HK, HV]:
        """
        Get a dictionary of values.

        ** The returned values are copies, so modifying them will not modify the observable.
        """
        return self.get_hook_value_dict()

    @property
    @final
    def hook_value_as_reference_dict(self) -> dict[HK, HV]:
        """
        Get a dictionary of values as references.

        ** The returned values are references, so modifying them will modify the observable.
        """
        return self.get_hook_value_as_reference_dict()