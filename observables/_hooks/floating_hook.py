from typing import Generic, TypeVar, Optional, TYPE_CHECKING, Callable
from logging import Logger
from .floating_hook_like import FloatingHookLike
from .hook import Hook
from .._utils.base_listening import BaseListening

if TYPE_CHECKING:
    from .._utils.nexus_manager import NexusManager

T = TypeVar("T")

class FloatingHook(Hook[T], FloatingHookLike[T], BaseListening, Generic[T]):
    """
    A floating hook that can be used to store a value that is not owned by any observable.
    """

    from .._utils.nexus_manager import DEFAULT_NEXUS_MANAGER

    def __init__(
        self,
        value: T,
        invalidate_callback: Optional[Callable[[], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER
        ) -> None:

        BaseListening.__init__(self, logger)
        Hook[T].__init__(
            self,
            value=value,
            validate_value_in_isolation_callback=None,
            nexus_manager=nexus_manager,
            logger=logger
        )

