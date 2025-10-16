from .nexus_manager import NexusManager
from typing import Mapping, Any, Optional, Sequence
from .hook_nexus import HookNexus
from logging import Logger
from .._hooks.hook_like import HookLike
from typing import Protocol, final

class HasNexusManagerLike(Protocol):

    @property
    def nexus_manager(self) -> NexusManager:
        ...
    
    @final
    def batch_submit_values(self, hooks_and_values: Mapping[HookLike[Any], Any]|Sequence[tuple[HookLike[Any], Any]], logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Submit values to the nexus manager in a batch.

        Args:
            hooks_and_values: Mapping of hooks to their new values or sequence of tuples of (hook, value)
            logger: Logger to use for logging

        Returns:
            Tuple of (success, message)
        """

        if len(hooks_and_values) == 0:
            return True, "No values provided"

        nexus_and_values: dict[HookNexus[Any], Any] = {}
        if isinstance(hooks_and_values, Mapping):
            for hook, value in hooks_and_values.items():
                if hook.nexus_manager != self.nexus_manager:
                    raise ValueError("Submit between different nexus managers is not allowed")
                nexus_and_values[hook.hook_nexus] = value
        elif isinstance(hooks_and_values, Sequence): # type: ignore
            for hook, value in hooks_and_values:
                if hook.nexus_manager != self.nexus_manager:
                    raise ValueError("Submit between different nexus managers is not allowed")
                if hook.hook_nexus in nexus_and_values:
                    raise ValueError("All hook nexuses must be unique")
                nexus_and_values[hook.hook_nexus] = value
        else:
            raise ValueError("hooks_and_values must be a mapping or a sequence")

        return self.nexus_manager.submit_values(nexus_and_values, mode="Normal submission", logger=logger)