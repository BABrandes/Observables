from typing import Generic, Optional, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from .hook import HookLike

T = TypeVar("T")

class HookGroup(Generic[T]):
    """
    A group of hooks that can be used to manage a group of hooks.
    """

    def __init__(self, *hooks: "HookLike[T]"):
        self._hooks: set["HookLike[T]"] = set(hooks)

    def add_hook(self, hook: "HookLike[T]"):
        self._hooks.add(hook)

    def remove_hook(self, hook: "HookLike[T]"):
        self._hooks.remove(hook)

    @property
    def hooks(self) -> tuple["HookLike[T]", ...]:
        return tuple(self._hooks)
    
    @property
    def value(self) -> T:
        """
        Get the value of the hook group.
        """
        for hook in self._hooks:
            if hook.can_send:
                return hook._binding_system_callback_get() # type: ignore
        raise ValueError("No hook in hook group can send values")
    
    def invalidate(self, source_hook_or_value: "HookLike[T]"|T) -> tuple[bool, str]:
        """"
        Invalidate the hook group.
        If the invalidation fails, the former values for the hooks are reset.

        Args:
            source_hook: The hook to invalidate the group from

        Returns:
            A tuple containing a boolean indicating if the invalidation was successful and a string message
        """

        from .hook import HookLike

        if isinstance(source_hook_or_value, HookLike):
            if source_hook_or_value.is_being_invalidated:
                raise ValueError("Source hook is already being invalidated. There is a cycle in the hook group.")
            
            if not source_hook_or_value.can_send:
                raise ValueError("Source hook cannot send values. It is not a valid source for invalidation.")

            if source_hook_or_value not in self._hooks:
                raise ValueError("Source hook not in group")
            value: T = source_hook_or_value._binding_system_callback_get() # type: ignore
        else:
            value: T = source_hook_or_value

        former_values_for_reset: dict["HookLike[T]", T] = {}
        try:
            for hook in self._hooks:
                if isinstance(source_hook_or_value, HookLike) and hook is source_hook_or_value:
                    continue
                if hook.can_receive:
                    former_values_for_reset[hook] = hook._binding_system_callback_get() # type: ignore
                    hook._binding_system_callback_set(value) # type: ignore
            if isinstance(source_hook_or_value, HookLike):
                source_hook_or_value.is_being_invalidated = False
            return True, "Invalidation successful"
        except Exception as e:
            for hook, value in former_values_for_reset.items():
                hook._binding_system_callback_set(value) # type: ignore
            if isinstance(source_hook_or_value, HookLike):
                source_hook_or_value.is_being_invalidated = False
            return False, f"Invalidation failed: {e}"

    @staticmethod
    def merge_hook_groups(*hook_groups: "HookGroup[T]") -> "HookGroup[T]":
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
        
        hook_type: Optional[type["HookLike[T]"]] = None
        for hook_group in hook_groups:
            for hook in hook_group._hooks:
                if hook_type is None:
                    hook_type = type(hook)
                elif type(hook) != hook_type:
                    raise ValueError("The hooks in the hook groups must have the same type of T")

        # Check if any groups have overlapping hooks (not disjoint)
        for i, group1 in enumerate(hook_groups):
            for group2 in hook_groups[i+1:]:
                if group1._hooks & group2._hooks:  # Check for intersection
                    raise ValueError("The hook groups must be disjoint")
        
        return HookGroup[T](*set.union(*[group._hooks for group in hook_groups])) # type: ignore
    
    @staticmethod
    def connect_hooks(from_hook: "HookLike[T]", to_hook: "HookLike[T]"):
        """
        Connect two hooks together.

        Args:
            from_hook: The hook to take the value from upon initialization
            to_hook: The hook to set the value to upon initialization

        Raises:
            ValueError: If the hooks are not of the same type
        """

        # Validate that both hooks are not None
        if from_hook is None or to_hook is None: # type: ignore
            raise ValueError("Cannot connect None hooks")

        # Ensure that the value in both hook groups is the same
        success, msg = to_hook.hook_group.invalidate(from_hook.value)
        if not success:
            raise ValueError(msg)
            
        # Then merge the hook groups
        merged_hook_group: HookGroup[T] = HookGroup[T].merge_hook_groups(from_hook.hook_group, to_hook.hook_group)

        # Check if all hooks are synced
        success, msg = HookGroup[T].check_all_hooks_synced(merged_hook_group)
        if not success:
            raise ValueError(msg)
        
        # Replace all hooks' hook groups with the merged one
        for hook in merged_hook_group._hooks:
            hook._binding_system_replace_hook_group(merged_hook_group) # type: ignore


    @staticmethod
    def check_all_hooks_synced(hook_group: "HookGroup[T]") -> tuple[bool, str]:
        """
        Check if all hooks in the group are synced by calling __eq__ for the value on each hook

        Returns:
            A tuple containing a boolean indicating if all hooks are synced and a string message
        
        """

        if len(hook_group._hooks) == 0:
            raise ValueError("Hook group is empty")
        elif len(hook_group._hooks) == 1:
            return True, "All hooks are synced"
        else:
            value: T = hook_group.value
            for hook in hook_group._hooks:
                if hook._binding_system_callback_get() != value: # type: ignore
                    return False, "Hooks are not synced"

        return True, "All hooks are synced"