from typing import Protocol, TypeVar, runtime_checkable, Any

from .._hooks.hook_protocols.owned_hook_protocol import OwnedHookProtocol

from .carries_hooks_protocol import CarriesHooksProtocol

T = TypeVar("T")

@runtime_checkable
class CarriesSingleHookProtocol(CarriesHooksProtocol[Any, T], Protocol[T]):
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