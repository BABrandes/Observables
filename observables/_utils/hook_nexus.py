import logging
from typing import Generic, Mapping, Optional, TypeVar, TYPE_CHECKING, Any

from .initial_sync_mode import InitialSyncMode
from .general import log

if TYPE_CHECKING:
    from .hook import HookLike
    
T = TypeVar("T")

class HookNexus(Generic[T]):
    """
    A nexus of hooks that can be used to manage a group of hooks.

    A nexus is a group of hooks that are connected to each other.
    It is used to manage a group of hooks that are connected to each other.
    """

    def __init__(self, value: T, *hooks: "HookLike[T]", logger: Optional[logging.Logger] = None):
        self._hooks: set["HookLike[T]"] = set(hooks)
        self._value: T = value
        self._previous_value: T = value
        self._logger: Optional[logging.Logger] = logger

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
        """
        return self._value
    
    @property
    def previous_value(self) -> T:
        return self._previous_value

    
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
        owners: set[CarriesHooks[Any]] = set()
        for nexus in all_nexus_and_values:
            for hook in nexus.hooks:
                owners.add(hook.owner)

        # Step 3: Check for each owner if the values would be valid as a collective
        def nexus_intersection(carries_collective_hooks: CarriesCollectiveHooks[Any]) -> set["HookNexus[Any]"]:
            intersection: set["HookNexus[Any]"] = set()
            for nexus in all_nexus_and_values:
                for collective_hook in carries_collective_hooks._collective_hooks: # type: ignore
                    if collective_hook.hook_nexus is nexus or collective_hook is nexus:
                        intersection.add(nexus)
            return intersection
        remaining_owners: set[CarriesHooks[Any]] = owners.copy()
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
            nexus._previous_value = nexus._value
            nexus._value = value

        # Step 6: If all values are valid, invalidate the hooks
        for owner in owners:
            if isinstance(owner, CarriesCollectiveHooks):
                hooks_to_invalidate = owner._collective_hooks.intersection(nexus_and_values.keys()) # type: ignore
                owner._invalidate_hooks(hooks_to_invalidate) # type: ignore
                for hook in hooks_to_invalidate:
                    hook._notify_listeners() # type: ignore
                
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
                log(self, "submit_single_value", self._logger, False, msg)
                return False, msg
        
        # Step 2: Update the HookNexus value after successful invalidation
        self._previous_value = self._value
        self._value = value

        # Step 3: Invalidate the hooks
        for hook in hooks_to_invalidate:
            if hook.can_be_invalidated:
                hook.invalidation_callback(hook) # type: ignore
                hook._notify_listeners() # type: ignore
        
        log(self, "submit_single_value", self._logger, True, "Submission successful")
        return True, "Submission successful"

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
        
        hook_type: Optional[type["HookLike[T]"]] = None
        for hook_group in nexus:
            for hook in hook_group._hooks:
                if hook_type is None:
                    hook_type = type(hook)
                elif type(hook) != hook_type:
                    raise ValueError("The hooks in the hook groups must have the same type of T")

        # Check if any groups have overlapping hooks (not disjoint)
        for i, group1 in enumerate(nexus):
            for group2 in nexus[i+1:]:
                if group1._hooks & group2._hooks:  # Check for intersection
                    raise ValueError("The hook groups must be disjoint")
        
        # Create new merged group with the reference value
        merged_group: HookNexus[T] = HookNexus[T](reference_value)
        
        # Add all hooks to the merged group
        for hook_group in nexus:
            for hook in hook_group._hooks:
                merged_group.add_hook(hook)
        
        return merged_group
    
    @staticmethod
    def connect_hook_pairs(*hook_pairs: tuple["HookLike[T]", "HookLike[T]"], logger: Optional[logging.Logger] = None) -> tuple[bool, str]:
        """
        Connect a list of hook pairs together.
        """

        for hook_pair in hook_pairs:
            if not hook_pair[0].is_active:
                raise ValueError(f"Hook {hook_pair[0]} is deactivated")
            if not hook_pair[1].is_active:
                raise ValueError(f"Hook {hook_pair[1]} is deactivated")

        nexus_and_values: dict["HookNexus[Any]", Any] = {}
        for hook_pair in hook_pairs:
            nexus_and_values[hook_pair[1].hook_nexus] = hook_pair[0].value
        success, msg = HookNexus.submit_multiple_values(nexus_and_values)
        if not success:
            raise ValueError(msg)
        
        for hook_pair in hook_pairs:
            merged_nexus = HookNexus[T]._merge_nexus(hook_pair[0].hook_nexus, hook_pair[1].hook_nexus)
            for hook in merged_nexus._hooks:
                hook._replace_hook_nexus(merged_nexus) # type: ignore

        return True, "Successfully connected hook pairs"
    
    @staticmethod
    def connect_hooks(source_hook: "HookLike[T]", target_hook: "HookLike[T]", initial_sync_mode: InitialSyncMode = InitialSyncMode.PUSH_TO_TARGET) -> tuple[bool, str]:
        """
        Connect two hooks together.

        Args:
            source_hook: The hook to take the value from upon initialization
            target_hook: The hook to set the value to upon initialization
            initial_sync_mode: Determines which value becomes the source of truth

        Raises:
            ValueError: If the hooks are not of the same type
        """

        # Validate that both hooks are not None
        if source_hook is None or target_hook is None: # type: ignore
            raise ValueError("Cannot connect None hooks")
        
        # Ensure that the value in both hook groups is the same
        # The source_hook's value becomes the source of truth
        source_hook.in_submission = True
        success, msg = target_hook.hook_nexus.submit_single_value(source_hook.value, {source_hook}, {target_hook})
        source_hook.in_submission = False
        if not success:
            raise ValueError(msg)
            
        # Then merge the hook groups
        # Use the synchronized value for the merged group
        merged_nexus: HookNexus[T] = HookNexus[T]._merge_nexus(source_hook.hook_nexus, target_hook.hook_nexus)
        
        # Replace all hooks' hook groups with the merged one
        for hook in merged_nexus._hooks:
            hook._replace_hook_nexus(merged_nexus) # type: ignore

        return True, "Successfully connected hooks"