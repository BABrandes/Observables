from typing import Generic, Mapping, Optional, TypeVar, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .hook import HookLike
    
T = TypeVar("T")

class HookNexus(Generic[T]):
    """
    A nexus of hooks that can be used to manage a group of hooks.

    A nexus is a group of hooks that are connected to each other.
    It is used to manage a group of hooks that are connected to each other.
    """

    def __init__(self, value: T, *hooks: "HookLike[T]"):
        self._hooks: set["HookLike[T]"] = set(hooks)
        self._value: T = value

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
        return self._value
    
    @staticmethod
    def submit_multiple_values(nexus_and_values: Mapping["HookNexus[Any]", Any]) -> tuple[bool, str]:
        """
        This function submits multiple values to one or more hooks.

        If multiple hook groups are provided, the values are submitted at once, so that complex states can be synchronized.

        Args:
            hooks_and_values: A mapping of hooks to their values

        Returns:
            A tuple containing a boolean indicating if the submission was successful and a string message
        """
        from .carries_collective_hooks import CarriesCollectiveHooks
        from .carries_hooks import CarriesHooks

        # Step 1: Collect the source nexus and value for each hook group
        all_nexus_and_values: dict["HookNexus[Any]", Any] = {}
        for nexus, value in nexus_and_values.items():
            all_nexus_and_values[nexus] = value

        # Step 2: Collect all owners
        owners: set[CarriesHooks] = set()
        for nexus in all_nexus_and_values:
            for hook in nexus.hooks:
                owners.add(hook.owner)

        # Step 3: Check for each owner if the values would be valid as a collective
        def nexus_intersection(carries_collective_hooks: CarriesCollectiveHooks) -> set["HookNexus[Any]"]:
            intersection: set["HookNexus[Any]"] = set()
            for nexus in all_nexus_and_values:
                for collective_hook in carries_collective_hooks.collective_hooks:
                    if collective_hook.hook_nexus is nexus or collective_hook is nexus:
                        intersection.add(nexus)
            return intersection
        remaining_owners: set[CarriesHooks] = owners.copy()
        for owner in owners:
            # Check if the hook is affected by the submission (if there is an overlap of at least 2 hooks)
            if isinstance(owner, CarriesCollectiveHooks):
                if len(nexus_intersection(owner)) >= 2:
                    # Overlap found - verify that the values would be valid
                    are_valid, msg = owner._are_valid_values(nexus_and_values) # type: ignore
                    if are_valid:
                        remaining_owners.remove(owner)
                    else:
                        return False, msg
                    
        # Step 4: Check for each remaining owner if the values would be valid as a single value
        for owner in remaining_owners:
            for hook in owner.hooks:
                # Check if this hook's hook_nexus is in the nexus_and_values
                if hook.hook_nexus in nexus_and_values:
                    success, msg = hook.is_valid_value(nexus_and_values[hook.hook_nexus])
                    if not success:
                        return False, msg
                # Also check if the hook itself is in nexus_and_values
                elif hook in nexus_and_values:
                    success, msg = hook.is_valid_value(nexus_and_values[hook.hook_nexus])
                    if not success:
                        return False, msg
                
        # Step 5: Update the HookNexus value after successful invalidation
        for nexus, value in nexus_and_values.items():
            nexus._value = value

        # Step 6: If all values are valid, invalidate the hooks
        for owner in owners:
            if isinstance(owner, CarriesCollectiveHooks):
                hooks_to_invalidate = owner.collective_hooks.intersection(nexus_and_values.keys())
                owner._invalidate_hooks(hooks_to_invalidate) # type: ignore
                
        return True, "Invalidation successful"
    
    def submit_single_value(self, value: T, hooks_to_ignore: Optional[set["HookLike[T]"]] = None, hooks_to_consider: Optional[set["HookLike[T]"]] = None) -> tuple[bool, str]:
        """"
        Submit a value to the hook group.
        If the submission fails, the former values for the hooks are reset.

        Args:
            value: The value to set for the hooks
            hooks_to_ignore: The hooks to ignore for submission. If None, all hooks in the group are considered.
            hooks_to_consider: The hooks to consider for submission. If None, all hooks in the group are considered.

        Returns:
            A tuple containing a boolean indicating if the submission was successful and a string message
        """
        
        # Step 1: Check if the value is valid for each hook
        hooks_to_invalidate: set["HookLike[T]"] = set()
        for hook in self._hooks:
            if hooks_to_ignore is not None and hook in hooks_to_ignore:
                continue
            if hooks_to_consider is not None and hook not in hooks_to_consider:
                continue
            success, msg = hook.is_valid_value(value)
            if success:
                hooks_to_invalidate.add(hook)
            else:
                return False, msg
        
        # Step 2: Update the HookNexus value after successful invalidation
        self._value = value

        # Step 3: Invalidate the hooks
        for hook in hooks_to_invalidate:
            hook.invalidate()
        
        return True, "Submission successful"

    @staticmethod
    def merge_hook_groups(*hook_groups: "HookNexus[T]") -> "HookNexus[T]":
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
        
        if len(hook_groups) == 0:
            raise ValueError("No hook groups provided")
        
        # Get the first hook group's value as the reference
        reference_value = hook_groups[0]._value
        
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
        
        # Create new merged group with the reference value
        merged_group = HookNexus(reference_value)
        
        # Add all hooks to the merged group
        for hook_group in hook_groups:
            for hook in hook_group._hooks:
                merged_group.add_hook(hook)
        
        return merged_group
    
    @staticmethod
    def connect_hook_pairs(*hook_pairs: tuple["HookLike[Any]", "HookLike[Any]"]):
        """
        Connect a list of hook pairs together.
        """

        nexus_and_values: dict["HookNexus[Any]", Any] = {}
        for hook_pair in hook_pairs:
            nexus_and_values[hook_pair[1].hook_nexus] = hook_pair[0].value
        success, msg = HookNexus.submit_multiple_values(nexus_and_values)
        if not success:
            raise ValueError(msg)
        
        for hook_pair in hook_pairs:
            merged_hook_group = HookNexus[T].merge_hook_groups(hook_pair[0].hook_nexus, hook_pair[1].hook_nexus)
            for hook in merged_hook_group._hooks:
                hook._replace_hook_group(merged_hook_group) # type: ignore
    
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
        from_hook.in_submission = True
        success, msg = to_hook.hook_nexus.submit_single_value(from_hook.value, {from_hook}, {to_hook})
        from_hook.in_submission = False
        if not success:
            raise ValueError(msg)
            
        # Then merge the hook groups
        merged_hook_group: HookNexus[T] = HookNexus[T].merge_hook_groups(from_hook.hook_nexus, to_hook.hook_nexus)
        
        # Replace all hooks' hook groups with the merged one
        for hook in merged_hook_group._hooks:
            hook._replace_hook_group(merged_hook_group) # type: ignore