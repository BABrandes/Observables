from typing import TypeVar, Protocol, runtime_checkable
from .hook_protocol import HookProtocol

T = TypeVar("T")

@runtime_checkable
class HookWithIsolatedValidationProtocol(HookProtocol[T], Protocol[T]):
    """
    Protocol for hook objects that can validate values in isolation (independent of other hooks in the same nexus).
    """

    def validate_value_in_isolation(self, value: T) -> tuple[bool, str]:
        """
        Validate the value in isolation. This is used to validate the value of a hook
        in isolation, without considering the value of other hooks in the same nexus.

        Args:
            value: The value to validate

        Returns:
            Tuple of (success: bool, message: str)
        """
        ...