from typing import Generic, TypeVar, Callable, Optional

from .hook_like import HookLike

T = TypeVar("T")

class HookWithReactionMixin(HookLike[T], Generic[T]):
    """
    A mixin that adds reactive capabilities to a hook.
    """

    def __init__(
        self,
        react_to_value_changed_callback: Optional[Callable[[T], None]] = None,
    ) -> None:
        
        self._react_to_value_changed_callback = react_to_value_changed_callback

    def react_to_value_changed(self) -> None:
        """
        React to the value changed.

        It reacts to the current value of the hook.
        """

        value: T = self.value

        if self._react_to_value_changed_callback is not None:
            self._react_to_value_changed_callback(value)