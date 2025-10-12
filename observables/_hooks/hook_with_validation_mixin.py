from typing import Callable, Generic, Optional, TypeVar

from .hook_like import HookLike

T = TypeVar("T")

class HookWithValidationMixin(HookLike[T], Generic[T]):
    """
    A mixin that adds validation capabilities to a hook.
    """

    def __init__(
        self,
        validate_value_in_isolation_callback: Optional[Callable[[T], tuple[bool, str]]] = None
    ) -> None:

        self._validate_value_in_isolation_callback = validate_value_in_isolation_callback

    def validate_value_in_isolation(self, value: T) -> tuple[bool, str]:
        """
        Validate the value in isolation. This is used to validate the value of a hook
        in isolation, without considering the value of other hooks in the same nexus.

        Args:
            value: The value to validate

        Returns:
            Tuple of (success: bool, message: str)
        """

        if self._validate_value_in_isolation_callback is not None:
            return self._validate_value_in_isolation_callback(value)
        else:
            return True, "No validate value in isolation callback provided"