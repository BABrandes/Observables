from threading import RLock
from typing import TypeVar, runtime_checkable, Protocol, TYPE_CHECKING, Mapping, Any, final, Optional, Literal
from .._utils.base_listening import BaseListeningLike
from logging import Logger

if TYPE_CHECKING:
    from .._utils.hook_nexus import HookNexus
    from .._utils.nexus_manager import NexusManager
    from .._utils.has_nexus_manager_like import HasNexusManagerLike
    
T = TypeVar("T")

@runtime_checkable
class HookLike(BaseListeningLike, HasNexusManagerLike, Protocol[T]):
    """
    Protocol for hook objects.
    """    
    @property
    def value(self) -> T:
        """
        Get the value behind this hook.

        ** The returned value is a copy, so modifying is allowed.
        """
        ...

    @property
    def value_reference(self) -> T:
        """
        Get the value reference behind this hook.

        *This is a reference to the value behind this hook, not a copy. Do not modify it!*

        Returns:
            The value reference behind this hook.
        """
        ...

    @property
    def previous_value(self) -> T:
        """
        Get the previous value behind this hook.

        ** The returned value is a copy, so modifying is allowed.
        """
        ...
    
    @property
    def hook_nexus(self) -> "HookNexus[T]":
        """
        Get the hook nexus that this hook belongs to.
        """
        ...

    @property
    def lock(self) -> RLock:
        """
        Get the lock for thread safety.
        """
        ...

    def connect_hook(self, target_hook: "HookLike[T]", initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> tuple[bool, str]:
        """
        Connect this hook to another hook.

        Args:
            target_hook: The hook to connect to
            initial_sync_mode: The initial synchronization mode
        """
        ...

    def disconnect_hook(self) -> None:
        """
        Disconnect this hook from the hook nexus.

        The hook will be disconnected.
        """
        ...

    def is_connected_to(self, hook: "HookLike[T]") -> bool:
        """
        Check if this hook is connected to another hook.
        """
        ...

    def _replace_hook_nexus(self, hook_nexus: "HookNexus[T]") -> None:
        """
        Replace the hook nexus that this hook belongs to.
        """
        ...

    #########################################################
    # Final methods
    #########################################################

    @final
    def submit_value(self, value: T, not_notifying_listeners_after_submission: set[BaseListeningLike] = set(), logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Submit a value to this hook. This will not invalidate the hook!

        Args:
            value: The value to submit
            not_notifying_listeners_after_submission: Whether to not notify listeners on certain objects after submission
            logger: The logger to use
        """

        return self.nexus_manager.submit_values({self.hook_nexus: value}, mode="Normal submission", not_notifying_listeners_after_submission=not_notifying_listeners_after_submission, logger=logger)


    @final
    @staticmethod
    def submit_values(values: Mapping["HookLike[Any]", Any], not_notifying_listeners_after_submission: set[BaseListeningLike] = set(), logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Submit values to this hook. This will not invalidate the hook!

        Args:
            values: The values to submit
            not_notifying_listeners_after_submission: Whether to not notify listeners on certain objects after submission
            logger: The logger to use
        """

        if len(values) == 0:
            return True, "No values provided"
        hook_manager: "NexusManager" = next(iter(values.keys())).nexus_manager
        hook_nexus_and_values: Mapping[HookNexus[Any], Any] = {}
        for hook, value in values.items():
            if hook.nexus_manager != hook_manager:
                raise ValueError("The nexus managers must be the same")
            hook_nexus_and_values[hook.hook_nexus] = value
        return hook_manager.submit_values(hook_nexus_and_values, mode="Normal submission", not_notifying_listeners_after_submission=not_notifying_listeners_after_submission, logger=logger)

    @final
    def validate_value(self, value: T, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Check if the value is valid for submission.
        """

        return self.nexus_manager.submit_values({self.hook_nexus: value}, mode="Check values", logger=logger)

    @staticmethod
    @final
    def validate_values(values: Mapping["HookLike[Any]", Any], logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Check if the values are valid for submission.
        """

        if len(values) == 0:
            return True, "No values provided"
        hook_manager: "NexusManager" = next(iter(values.keys())).nexus_manager
        hook_nexus_and_values: Mapping[HookNexus[Any], Any] = {}
        for hook, value in values.items():
            if hook.nexus_manager != hook_manager:
                raise ValueError("The nexus managers must be the same")
            hook_nexus_and_values[hook.hook_nexus] = value
        return hook_manager.submit_values(hook_nexus_and_values, mode="Check values", logger=logger)