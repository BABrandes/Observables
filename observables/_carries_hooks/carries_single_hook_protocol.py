from typing import Protocol, TypeVar, runtime_checkable, Any, Literal

from .._hooks.hook_aliases import Hook, ReadOnlyHook
from .._hooks.hook_protocols.owned_hook_protocol import OwnedHookProtocol
from .._nexus_system.has_nexus_protocol import HasNexusProtocol
from .carries_hooks_protocol import CarriesHooksProtocol

T = TypeVar("T")

@runtime_checkable
class CarriesSingleHookProtocol(CarriesHooksProtocol[Any, T], HasNexusProtocol[T], Protocol[T]):
    """
    Protocol for objects that carry a single hook.
    """

    def _get_single_hook(self) -> OwnedHookProtocol[T]:
        """
        Get the hook for the single value.

        ** This method is not thread-safe and should only be called by the get_single_value_hook method.

        Returns:
            The hook for the single value
        """
        ...

    def _get_single_value(self) -> T:
        """
        Get the value of the single hook.

        ** This method is not thread-safe and should only be called by the get_single_value method.

        Returns:
            The value of the single hook
        """
        ...

    def _change_single_value(self, value: T) -> None:
        """
        Change the value of the single hook.

        ** This method is not thread-safe and should only be called by the change_single_value method.

        Args:
            value: The new value to set
        """
        ...

    def link(self, hook: "Hook[T] | ReadOnlyHook[T] | CarriesSingleHookProtocol[T]", sync_mode: Literal["use_caller_value", "use_target_value"] = "use_caller_value") -> None:
        """
        Link the single hook to the target hook.

        Args:
            hook: The hook to link to
            sync_mode: The sync mode to use
        """
        ...