from typing import Protocol, runtime_checkable, Mapping, TypeVar, final, Literal, Any
from .initial_sync_mode import InitialSyncMode
from .carries_hooks import CarriesHooks
from .._hooks.owned_hook_like import OwnedHookLike
from .._utils.hook_nexus import HookNexus

HK = TypeVar("HK")
HV = TypeVar("HV")

@runtime_checkable
class CarriesCollectiveHooks(CarriesHooks[HK, HV], Protocol[HK, HV]):
    """
    Protocol for observables that carry a set of hooks that can be used to synchronize their values.
    """ 

    def get_collective_hook_keys(self) -> set[HK]:
        ...

    def connect_multiple_hooks(self, hooks: Mapping[HK, OwnedHookLike[HV]], initial_sync_mode: InitialSyncMode) -> None:
        ...

    def _is_valid_values_as_part_of_owner_impl(self, values: Mapping[HK, HV]) -> tuple[Literal[True, False, "InternalInvalidationNeeded"], str]:
        """
        Check if the values can be accepted.
        """
        ...

    #########################################################

    @final
    def is_valid_values(self, values: Mapping[HK, HV]) -> tuple[bool, str]:
        """
        Check if the values can be accepted.
        """

        nexus_and_values: Mapping[HookNexus[Any], Any] = {}
        for key, value in values.items():
            nexus_and_values[self.get_hook(key).hook_nexus] = value

        success, msg = HookNexus.validate_multiple_values(nexus_and_values)
        if success == True:
            return True, msg
        else:
            return False, msg

    @property
    @final
    def _collective_hook_keys(self) -> set[HK]:
        return self.get_collective_hook_keys()

    @property
    @final
    def _collective_hooks(self) -> set[OwnedHookLike[HV]]:
        return {self.get_hook(key) for key in self._collective_hook_keys}