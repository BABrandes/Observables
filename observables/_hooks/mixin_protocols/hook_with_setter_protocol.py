from typing import TypeVar, runtime_checkable, Protocol, TYPE_CHECKING, Mapping, Any, final, Optional
from threading import RLock
from logging import Logger

from ..._auxiliary.listening_protocol import ListeningProtocol
from ..._nexus_system.has_nexus_manager_protocol import HasNexusManagerProtocol
from ..._publisher_subscriber.publisher_protocol import PublisherProtocol
from ..._nexus_system.submission_error import SubmissionError

if TYPE_CHECKING:
    from ..._nexus_system.hook_nexus import HookNexus
    from ..._nexus_system.nexus_manager import NexusManager

T = TypeVar("T")

@runtime_checkable
class HookWithSetterProtocol(ListeningProtocol, PublisherProtocol, HasNexusManagerProtocol, Protocol[T]):
    """
    Protocol for hook objects that can submit values (have setter functionality).
    
    This protocol extends the base hook functionality with the ability to submit values,
    making it suitable for primary hooks in observables that can be modified directly.
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

    def _replace_hook_nexus(self, hook_nexus: "HookNexus[T]") -> None:
        """
        Replace the hook nexus that this hook belongs to.
        """
        ...

    #########################################################
    # Final methods - With submission capability
    #########################################################

    @final
    def submit_value(self, value: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Submit a value to this hook. This will not invalidate the hook!

        Args:
            value: The value to submit
            logger: The logger to use
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails
        """

        success, msg = self.nexus_manager.submit_values({self.hook_nexus: value}, mode="Normal submission", logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, value)
        return success, msg


    @final
    @staticmethod
    def submit_values(values: Mapping["HookWithSetterProtocol[Any]", Any], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Submit values to this hook. This will not invalidate the hook!

        Args:
            values: The values to submit
            logger: The logger to use
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails
        """

        if len(values) == 0:
            return True, "No values provided"
        hook_manager: "NexusManager" = next(iter(values.keys())).nexus_manager
        hook_nexus_and_values: Mapping[HookNexus[Any], Any] = {}
        for hook, value in values.items():
            if hook.nexus_manager != hook_manager:
                raise ValueError("The nexus managers must be the same")
            hook_nexus_and_values[hook.hook_nexus] = value
        success, msg = hook_manager.submit_values(hook_nexus_and_values, mode="Normal submission", logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, values)
        return success, msg
