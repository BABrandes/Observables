from typing import Protocol, Literal, TYPE_CHECKING, TypeVar, runtime_checkable, Hashable

if TYPE_CHECKING:
    from ..._nexus_system.nexus import Nexus
    from ..._nexus_system.nexus_manager import NexusManager
    from ..._carries_hooks.carries_single_hook_protocol import CarriesSingleHookProtocol    

T = TypeVar("T")

@runtime_checkable
class HookWithConnectionProtocol(Hashable, Protocol[T]):
    """
    Protocol for hook objects that can connect to other hooks.
    """

    #########################################################
    # Public Properties and methods
    #########################################################

    @property
    def nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this hook belongs to.

        ** Thread-safe **
        """
        ...

    @property
    def value(self) -> T:
        """
        Get the value behind this hook.

        ** Thread-safe **
        """
        ...

    @value.setter
    def value(self, value: T) -> None:
        raise ValueError("Value cannot be set for connection hooks without implementation of HookWithSetterProtocol")

    def link(self, target_hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]", initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> tuple[bool, str]:
        """
        Connect this hook to another hook.

        ** Thread-safe **

        Args:
            target_hook: The hook or CarriesSingleHookProtocol to connect to
            initial_sync_mode: The initial synchronization mode

        Returns:
            A tuple containing a boolean indicating if the connection was successful and a string message
        """
        ...

    def unlink(self) -> None:
        """
        Disconnect this hook from the hook nexus.

        ** Thread-safe **

        The hook will be disconnected.

        Args:
            key: The key of the hook to disconnect. If None, all hooks will be disconnected.
        """
        ...

    def is_linked_to(self, hook_or_carries_single_hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]") -> bool:
        """
        Check if this hook is connected to another hook or CarriesSingleHookLike.

        ** Thread-safe **

        Args:
            hook: The hook or CarriesSingleHookProtocol to check if it is connected to

        Returns:
            True if the hook is connected to the other hook or CarriesSingleHookProtocol, False otherwise
        """
        ...

    #########################################################
    # Private methods
    #########################################################

    def _get_nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this hook belongs to.

        ** This method is not thread-safe and should only be called by the get_nexus_manager method.
        """
        ...

    def _get_nexus(self) -> "Nexus[T]":
        """
        Get the nexus that this hook belongs to.

        ** This method is not thread-safe and should only be called by the get_nexus method.
        """
        ...

    def _replace_nexus(self, nexus: "Nexus[T]") -> None:
        """
        Replace the nexus that this hook belongs to.

        ** This method is not thread-safe and should only be called by the replace_nexus method.
        """
        ...

    def _link(self, target_hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]", initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> tuple[bool, str]:
        """
        Link this hook to another hook.

        ** This method is not thread-safe and should only be called by the link method.
        """
        ...

    def _unlink(self) -> None:
        """
        Unlink this hook from the nexus.

        ** This method is not thread-safe and should only be called by the unlink method.
        """
        ...

    def _is_linked_to(self, hook_or_carries_single_hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]") -> bool:
        """
        Check if this hook is connected to another hook or CarriesSingleHookProtocol[T].

        ** This method is not thread-safe and should only be called by the is_linked_to method.

        Args:
            hook_or_carries_single_hook: The hook or CarriesSingleHookProtocol[T] to check if it is connected to

        Returns:
            True if the hook is connected to the other hook or CarriesSingleHookProtocol[T], False otherwise
        """
        ...