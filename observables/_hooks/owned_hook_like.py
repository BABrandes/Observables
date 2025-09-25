from typing import TypeVar, TYPE_CHECKING, runtime_checkable, Protocol, Any, Mapping, final, Literal
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

    def _is_valid_value_as_part_of_owner(self, value: T) -> tuple[Literal[True, False, "InternalInvalidationNeeded"], str]:
        """
        Check if the value is valid for submission.

        This method checks if the new value would be valid to be set in all connected hooks.

        Args:
            value: The value to check
            value_check_mode: The mode of value check

        Returns:
            A tuple containing a boolean indicating if the value is valid and a string explaining why
        """
        ...

    #########################################################
    # Final methods
    #########################################################

    @final
    def is_valid_value_in_isolation(self, value: T) -> tuple[Literal[True, False, "InternalInvalidationNeeded"], str]:
        """
        Check if the value is valid for submission in isolation.
        """
        return self._is_valid_value_as_part_of_owner(value)

    @final
    def is_valid_value(self, value: T) -> tuple[bool, str]:
        """
        Check if the value is valid for submission.
        """

        success, msg = self.hook_nexus.validate_single_value(value)

        if success == False:
            return False, msg
        else:
            return True, "Value can be submitted and should result in a valid state"

    def submit_single_value(self, value: T) -> tuple[bool, str]:
        """
        Submit a value to this hook. This will not invalidate the hook!

        Args:
            value: The value to submit
        """

        success, msg = self.hook_nexus.submit_single_value(value=value)
        return success, msg

    @staticmethod
    @final
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
    @final
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

        success, msg = HookNexus.validate_multiple_values(nexus_and_values)
        if success == False:
            return False, msg
        else:
            return True, "Values can be submitted and should result in a valid state"