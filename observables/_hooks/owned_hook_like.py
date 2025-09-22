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
        *hooks_and_values: tuple["OwnedHookLike[Any]", Any]) -> tuple[bool, str]:
        """
        Set the values of multiple hooks.

        Args:
            *hooks_and_values: The hooks and values to set

        Returns:
            A tuple containing a boolean indicating if the submission was successful and a string message

        Raises:
            ValueError: If the submission fails
        """
        from .._utils.hook_nexus import HookNexus

        if len(hooks_and_values) == 0:
            return True, "No hooks and values provided"

        nexus_and_values: Mapping[HookNexus[Any], Any] = {}
        for hook, value in hooks_and_values:
            nexus_and_values[hook.hook_nexus] = value

        # Submit the values to the hook nexus
        success, msg = HookNexus.submit_multiple_values(nexus_and_values)

        # Notify listeners of the hooks
        for hook, _ in hooks_and_values:
            hook._notify_listeners()

        return success, msg

    @staticmethod
    def validate_multiple_values_for_submit(
        *hooks_and_values: tuple["OwnedHookLike[Any]", Any]) -> tuple[bool, str]:
        """
        Validate multiple values for a hook nexus.

        This method checks if the new values would be valid to be set in all connected hooks.
        """
        from .._utils.hook_nexus import HookNexus

        nexus_and_values: Mapping[HookNexus[Any], Any] = {}
        for hook, value in hooks_and_values:
            nexus_and_values[hook.hook_nexus] = value

        return HookNexus.validate_multiple_values(nexus_and_values)