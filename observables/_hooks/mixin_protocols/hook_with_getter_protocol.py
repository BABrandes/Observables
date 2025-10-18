from typing import TypeVar, runtime_checkable, Protocol, TYPE_CHECKING, Mapping, Any, final, Optional
from threading import RLock
from logging import Logger

from ..._auxiliary.listening_protocol import ListeningProtocol
from ..._nexus_system.has_nexus_manager_protocol import HasNexusManagerProtocol
from ..._publisher_subscriber.publisher_protocol import PublisherProtocol

if TYPE_CHECKING:
    from ..._nexus_system.hook_nexus import HookNexus
    from ..._nexus_system.nexus_manager import NexusManager

T = TypeVar("T")

@runtime_checkable
class HookWithGetterProtocol(ListeningProtocol, PublisherProtocol, HasNexusManagerProtocol, Protocol[T]):
    """
    Protocol for getter hook objects that can get values.
    
    This protocol extends the base hook functionality with the ability to get values,
    making it suitable for getter hooks in observables that can get values.
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

    #########################################################
    # Final methods - Only validation, no submission
    #########################################################

    @final
    def validate_value(self, value: T, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Check if the value is valid for submission.
        
        Note: This method only validates, it does not submit values.
        """
        return self.nexus_manager.submit_values({self.hook_nexus: value}, mode="Check values", logger=logger)

    @staticmethod
    @final
    def validate_values(values: Mapping["HookWithGetterProtocol[Any]", Any], *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Check if the values are valid for submission.
        
        Note: This method only validates, it does not submit values.
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
