from typing import TypeVar, Protocol, runtime_checkable
from .hook_like import HookLike

T = TypeVar("T")

@runtime_checkable
class HookWithReactionLike(HookLike[T], Protocol[T]):
    """
    Protocol for hook objects that can react to value changes.
    """

    def react_to_value_changed(self) -> None:
        """
        React to the value changed.

        It reacts to the current value of the hook.
        """
        ...