from typing import TypeVar, TYPE_CHECKING, runtime_checkable, Protocol, Any, Mapping
from .hook_like import HookLike

if TYPE_CHECKING:
    from .._utils.carries_hooks import CarriesHooks

T = TypeVar("T")

@runtime_checkable
class OwnedHookLike(HookLike[T], Protocol[T]):
    """
    Protocol for owned hook objects.
    """
    
    @property
    def owner(self) -> "CarriesHooks[Any, Any]":
        """
        Get the owner of this hook.
        """
        ...

    @staticmethod
    def submit_multiple_values(
        *hooks_and_values: tuple["OwnedHookLike[Any]", Any]) -> None:
        """
        Set the values of multiple hooks.
        """
        from .._utils.hook_nexus import HookNexus

        if len(hooks_and_values) == 0:
            return

        nexus_and_values: Mapping[HookNexus[Any], Any] = {}
        for hook, value in hooks_and_values:
            nexus_and_values[hook.hook_nexus] = value

        # Submit the values to the hook nexus
        HookNexus.submit_multiple_values(nexus_and_values)

        # Notify listeners of the hooks
        for hook, _ in hooks_and_values:
            hook._notify_listeners()