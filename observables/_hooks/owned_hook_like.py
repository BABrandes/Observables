from typing import TypeVar, TYPE_CHECKING, Any, Generic
from .hook_like import HookLike
from .hook_with_validation_mixin import HookWithValidationMixin

if TYPE_CHECKING:
    from .._utils.carries_hooks_like import CarriesHooksLike

T = TypeVar("T")

class OwnedHookLike(HookWithValidationMixin[T], HookLike[T], Generic[T]):
    """
    Protocol for owned hook objects.
    """
    
    @property
    def owner(self) -> "CarriesHooksLike[Any, Any]":
        """
        Get the owner of this hook.
        """
        ...

    def invalidate_owner(self) -> None:
        """Invalidate the owner of this hook."""
        self.owner.invalidate()

    def is_valid(self, value: T) -> bool:
        """Check if the hook is valid."""

        hook_key = self.owner.get_hook_key(self)
        success, _ = self.owner.validate_value(hook_key, value)
        return success