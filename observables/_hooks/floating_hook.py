from typing import Generic, TypeVar, Optional, Callable
from logging import Logger


from .floating_hook_like import FloatingHookLike
from .hook import Hook
from .hook_with_validation_mixin import HookWithValidationMixin
from .._utils.base_listening import BaseListening
from .._utils.nexus_manager import NexusManager
from .._utils.default_nexus_manager import DEFAULT_NEXUS_MANAGER

T = TypeVar("T")

class FloatingHook(Hook[T], FloatingHookLike[T], BaseListening, Generic[T]):
    """
    A floating hook that can be used to store a value that is not owned by any observable.
    """

    def __init__(
        self,
        value: T,
        invalidate_callback: Optional[Callable[[], tuple[bool, str]]] = None,
        validate_value_in_isolation_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER
        ) -> None:

        BaseListening.__init__(self, logger)
        Hook.__init__( # type: ignore
            self,
            value=value,
            nexus_manager=nexus_manager,
            logger=logger
        )
        HookWithValidationMixin.__init__( # type: ignore
            self,
            validate_value_in_isolation_callback=validate_value_in_isolation_callback
        )

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook."""
        return f"FloatingHook(v={self.value}, id={id(self)})"
    
    def __str__(self) -> str:
        """Get the string representation of this hook."""
        return f"FloatingHook(v={self.value}, id={id(self)})"
