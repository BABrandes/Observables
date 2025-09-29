
import logging
from typing import Generic, Optional, TypeVar, TYPE_CHECKING, Any
from .._utils.base_listening import BaseListening
from .owned_hook_like import OwnedHookLike
from .hook import Hook
from .._utils.nexus_manager import NexusManager
from .._utils.default_nexus_manager import DEFAULT_NEXUS_MANAGER

if TYPE_CHECKING:
    from .._utils.carries_hooks_like import CarriesHooksLike

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
            owner: "CarriesHooksLike[Any, Any]",
            initial_value: T,
            logger: Optional[logging.Logger] = None,
            nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER
            ) -> None:

        def validate_value_in_isolation_callback(value: T) -> tuple[bool, str]:
            """Validate the value in isolation."""
            key_of_this_hook = owner.get_hook_key(self)
            values: dict[Any, Any] = {}
            for key, value_for_key in owner.hook_value_as_reference_dict.items():
                if key == key_of_this_hook:
                    values[key] = value
                else:
                    values[key] = value_for_key

            return owner.validate_values_in_isolation(values)

        super().__init__(
            value=initial_value,
            validate_value_in_isolation_callback=validate_value_in_isolation_callback,
            nexus_manager=nexus_manager,
            logger=logger
        )

        self._owner: "CarriesHooksLike[Any, T]" = owner

    @property
    def owner(self) -> "CarriesHooksLike[Any, T]":
        """Get the owner of this hook."""
        return self._owner

    def _get_owner(self) -> "CarriesHooksLike[Any, T]":
        """Get the owner of this hook."""

        with self._lock:
            return self._owner