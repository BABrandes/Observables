from typing import Generic, Optional, TypeVar, Any
from logging import Logger
from .._utils.base_listening import BaseListening
from .hook import Hook
from .._utils.nexus_manager import NexusManager
from .._utils.default_nexus_manager import DEFAULT_NEXUS_MANAGER
from .hook_with_owner_like import HookWithOwnerLike
from .._utils.carries_hooks_like import CarriesHooksLike

T = TypeVar("T")

class OwnedHook(Hook[T], HookWithOwnerLike[T], BaseListening, Generic[T]):
    """
    A owned hook that provides value access and basic capabilities.
    
    This class focuses on:
    - Value access via callbacks
    - Basic capabilities (sending/receiving)
    - Owner reference and auxiliary information
    
    Complex binding logic is delegated to the BindingSystem class.
    """

    def __init__(
            self,
            owner: CarriesHooksLike[Any, Any],
            initial_value: T,
            logger: Optional[Logger] = None,
            nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
            ) -> None:

        BaseListening.__init__(self, logger)
        Hook.__init__( # type: ignore
            self,
            value=initial_value,
            nexus_manager=nexus_manager,
            logger=logger
        )

        self._owner = owner

    @property
    def owner(self) -> CarriesHooksLike[Any, T]:
        """Get the owner of this hook."""
        return self._owner

    def _get_owner(self) -> CarriesHooksLike[Any, T]:
        """Get the owner of this hook."""

        with self._lock:
            owner = self._owner
            return owner

    def invalidate_owner(self) -> None:
        """Invalidate the owner of this hook."""
        self.owner.invalidate()

    def is_valid(self, value: T) -> bool:
        """Check if the hook is valid."""

        hook_key = self.owner.get_hook_key(self)
        success, _ = self.owner.validate_value(hook_key, value)
        return success

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook."""
        return f"OwnedHook(v={self.value}, id={id(self)})"

    def __str__(self) -> str:
        """Get the string representation of this hook."""
        return f"OwnedHook(v={self.value}, id={id(self)})"