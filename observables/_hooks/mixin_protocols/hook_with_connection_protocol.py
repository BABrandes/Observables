from typing import Protocol, Literal, TYPE_CHECKING, TypeVar, runtime_checkable

if TYPE_CHECKING:
    from ..._nexus_system.hook_nexus import HookNexus
    from ..._nexus_system.nexus_manager import NexusManager
    from ..._carries_hooks.carries_single_hook_protocol import CarriesSingleHookProtocol    

T = TypeVar("T")

@runtime_checkable
class HookWithConnectionProtocol(Protocol[T]):
    """
    Protocol for hook objects that can connect to other hooks.
    """

    @property
    def hook_nexus(self) -> "HookNexus[T]":
        """
        Get the hook nexus that this hook belongs to.
        """
        ...

    @property
    def nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this hook belongs to.
        """
        ...

    @property
    def value(self) -> T:
        """
        Get the value behind this hook.
        """
        ...

    def connect_hook(self, target_hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]", initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> tuple[bool, str]:
        """
        Connect this hook to another hook.

        Args:
            target_hook: The hook or CarriesSingleHookProtocol to connect to
            initial_sync_mode: The initial synchronization mode

        Returns:
            A tuple containing a boolean indicating if the connection was successful and a string message
        """
        ...

    def disconnect_hook(self) -> None:
        """
        Disconnect this hook from the hook nexus.

        The hook will be disconnected.
        """
        ...

    def is_connected_to(self, hook: "HookWithConnectionProtocol[T]|CarriesSingleHookProtocol[T]") -> bool:
        """
        Check if this hook is connected to another hook or CarriesSingleHookLike.

        Args:
            hook: The hook or CarriesSingleHookProtocol to check if it is connected to

        Returns:
            True if the hook is connected to the other hook or CarriesSingleHookProtocol, False otherwise
        """
        ...

    def _replace_hook_nexus(self, hook_nexus: "HookNexus[T]") -> None:
        """
        Replace the hook nexus that this hook belongs to.
        """
        ...