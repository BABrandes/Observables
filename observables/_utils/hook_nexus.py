import logging
from typing import Generic, Optional, TypeVar, TYPE_CHECKING, Any, cast
from .general import log

if TYPE_CHECKING:
    from .._hooks.hook_like import HookLike
    from .nexus_manager import NexusManager
    
T = TypeVar("T")

class HookNexus(Generic[T]):
    """
    A nexus of hooks that can be used to manage a group of hooks.

    A nexus is a group of hooks that are connected to each other.
    It is used to manage a group of hooks that are connected to each other.
    """

    def __init__(
        self,
        nexus_manager: "NexusManager",
        value: T,
        *hooks: "HookLike[T]",
        logger: Optional[logging.Logger] = None):

        self._nexus_manager: "NexusManager" = nexus_manager
        self._hooks: set["HookLike[T]"] = set(hooks)
        self._value: T = value
        self._previous_value: T = value
        self._logger: Optional[logging.Logger] = logger
        self._submit_depth_counter: int = 0
        self._submit_touched_hooks: set["HookLike[T]"] = set()

        log(self, "HookNexus.__init__", self._logger, True, "Successfully initialized hook nexus")

    def add_hook(self, hook: "HookLike[T]") -> tuple[bool, str]:
        self._hooks.add(hook)
        log(self, "add_hook", self._logger, True, "Successfully added hook")
        return True, "Successfully added hook"

    def remove_hook(self, hook: "HookLike[T]") -> tuple[bool, str]:
        try:
            self._hooks.remove(hook)
            log(self, "remove_hook", self._logger, True, "Successfully removed hook")
            return True, "Successfully removed hook"
        except KeyError:
            return False, "Hook not found in nexus"

    @property
    def hooks(self) -> tuple["HookLike[T]", ...]:
        return tuple(self._hooks)
    
    @property
    def value(self) -> T:
        """
        Get the value of the hook group.

        ** The returned value is a copy, so modifying is allowed.
        """
        value: T = self._value
        if hasattr(value, "copy"):
            value = cast(T, value.copy()) # type: ignore
        return value

    @property
    def value_reference(self) -> T:
        """
        Get the value reference of the hook group.

        ** The returned value is a reference, so modifying is not allowed.
        """
        return self._value
    
    @property
    def previous_value(self) -> T:
        return self._previous_value

    @staticmethod
    def _merge_nexus(*nexus: "HookNexus[T]") -> "HookNexus[T]":
        """
        Merge multiple hook groups into a single hook group.

        - There must not be any overlapping hooks in the input groups
        - The hooks in both groups must have the same type of T and be synced to the same value
        - The hooks in both groups must be disjoint, if not something went wrong in the binding system

        Args:
            *hook_groups: The hook groups to merge

        Returns:
            A new hook group that contains all the hooks from the input groups

        Raises:
            ValueError: If the hook groups are not disjoint
        """
        
        if len(nexus) == 0:
            raise ValueError("No hook groups provided")
        
        # Get the first hook group's value as the reference
        reference_value = nexus[0]._value

        # Check that all nexus managers are the same
        for nexus_group in nexus:
            if nexus_group._nexus_manager != nexus[0]._nexus_manager:
                raise ValueError("The nexus managers must be the same")
        nexus_manager: "NexusManager" = nexus[0]._nexus_manager
        
        value_type: Optional[type[T]] = None
        for hook_group in nexus:
            for hook in hook_group._hooks:
                if value_type is None:
                    value_type = type(hook.value)
                elif type(hook.value) != value_type:
                    raise ValueError("The hooks in the hook groups must have the same value type")

        # Check if any groups have overlapping hooks (not disjoint)
        for i, group1 in enumerate(nexus):
            for group2 in nexus[i+1:]:
                if group1._hooks & group2._hooks:  # Check for intersection
                    raise ValueError("The hook groups must be disjoint")
        
        # Create new merged group with the reference value
        merged_group: HookNexus[T] = HookNexus[T](nexus_manager, reference_value)
        
        # Add all hooks to the merged group
        for hook_group in nexus:
            for hook in hook_group._hooks:
                merged_group.add_hook(hook)
        
        return merged_group
    
    @staticmethod
    def connect_hook_pairs(*hook_pairs: tuple["HookLike[T]", "HookLike[T]"]) -> tuple[bool, str]:
        """
        Connect a list of hook pairs together.

        The value of the first hook will be used to set the value of the second hook.

        Args:
            *hook_pairs: The pairs of hooks to connect

        Returns:
            A tuple containing a boolean indicating if the connection was successful and a string message
        """

        # Check that all nexus managers are the same
        for hook_pair in hook_pairs:
            if hook_pair[0].hook_nexus._nexus_manager != hook_pair[1].hook_nexus._nexus_manager:
                raise ValueError("The nexus managers must be the same")
        nexus_manager: "NexusManager" = hook_pairs[0][0].hook_nexus._nexus_manager

        nexus_and_values: dict["HookNexus[Any]", Any] = {}
        for hook_pair in hook_pairs:
            nexus_and_values[hook_pair[1].hook_nexus] = hook_pair[0].value
        success, msg = nexus_manager.submit_values(nexus_and_values)
        if not success:
            raise ValueError(msg)
        
        for hook_pair in hook_pairs:
            merged_nexus = HookNexus[T]._merge_nexus(hook_pair[0].hook_nexus, hook_pair[1].hook_nexus)
            for hook in merged_nexus._hooks:
                hook._replace_hook_nexus(merged_nexus) # type: ignore

        return True, "Successfully connected hook pairs"
    
    @staticmethod
    def connect_hooks(source_hook: "HookLike[T]", target_hook: "HookLike[T]") -> tuple[bool, str]:
        """
        Connect two hooks together.

        Args:
            source_hook: The hook to take the value from upon initialization
            target_hook: The hook to set the value to upon initialization

        Raises:
            ValueError: If the hooks are not of the same type
        """
        
        # Check that all nexus managers are the same
        if source_hook.hook_nexus._nexus_manager != target_hook.hook_nexus._nexus_manager:
            raise ValueError("The nexus managers must be the same")
        nexus_manager: "NexusManager" = source_hook.hook_nexus._nexus_manager

        # Validate that both hooks are not None
        if source_hook is None or target_hook is None: # type: ignore
            raise ValueError("Cannot connect None hooks")
        
        # Ensure that the value in both hook groups is the same
        # The source_hook's value becomes the source of truth
        success, msg = nexus_manager.submit_values({target_hook.hook_nexus: source_hook.value})
        if not success:
            raise ValueError(msg)
            
        # Then merge the hook groups
        # Use the synchronized value for the merged group
        merged_nexus: HookNexus[T] = HookNexus[T]._merge_nexus(source_hook.hook_nexus, target_hook.hook_nexus)
        
        # Replace all hooks' hook groups with the merged one
        for hook in merged_nexus._hooks:
            hook._replace_hook_nexus(merged_nexus) # type: ignore

        return True, "Successfully connected hooks"