
import logging
from typing import Generic, Optional, TypeVar, TYPE_CHECKING, Any
from .._utils.base_listening import BaseListening
from .owned_hook_like import OwnedHookLike
from .hook import Hook
from .._utils.nexus_manager import NexusManager
from .._utils.default_nexus_manager import DEFAULT_NEXUS_MANAGER

if TYPE_CHECKING:
    from .._utils.base_carries_hooks import BaseCarriesHooks

T = TypeVar("T")

class OwnedHook(Hook[T], OwnedHookLike[T], BaseListening, Generic[T]):
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
            owner: "BaseCarriesHooks[Any, Any]",
            initial_value: T,
            logger: Optional[logging.Logger] = None,
            nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER
            ) -> None:

        def validate_value_in_isolation_callback(value: T) -> tuple[bool, str]:
            """Validate the value in isolation."""
            hook_key = owner.get_hook_key(self)
            return self._owner.validate_values_in_isolation({hook_key: value})

        super().__init__(
            value=initial_value,
            validate_value_in_isolation_callback=validate_value_in_isolation_callback,
            nexus_manager=nexus_manager,
            logger=logger
        )

        self._owner: "BaseCarriesHooks[Any, T]" = owner

    @property
    def owner(self) -> "BaseCarriesHooks[Any, T]":
        """Get the owner of this hook."""
        return self._owner

    def _get_owner(self) -> "BaseCarriesHooks[Any, T]":
        """Get the owner of this hook."""

        with self._lock:
            return self._owner