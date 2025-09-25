import logging
from typing import Generic, Mapping, Optional, TypeVar, TYPE_CHECKING, Any, cast, Literal
from _utils.base_listening import BaseListeningLike


from .general import log
from .._hooks.owned_hook_like import OwnedHookLike
from .carries_hooks import CarriesHooks

if TYPE_CHECKING:
    from .._hooks.hook_like import HookLike
    
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


    #############################################################
    # Value Submission ##########################################
    #############################################################

    @staticmethod
    def _validate_multiple_values_helper(
        nexus_and_values: Mapping["HookNexus[Any]", Any]) -> tuple[
            Literal[True, False, "InternalInvalidationNeeded"],
            str,
            set[CarriesHooks[Any, Any]],
            set["HookLike[Any]"]]:
        """
        Validate multiple values for a hook nexus.

        Args:
            nexus_and_values: A mapping of nexus to their values

        Returns:
            A tuple containing a boolean indicating if the values are valid,
            
            a string explaining why,
            
            and a set of owners that were checked as being affected by the submission.
        """

        from .carries_collective_hooks import CarriesCollectiveHooks

        overall_status: Literal[True, False, "InternalInvalidationNeeded"] = True

        # Step 1: Collect the source nexus and value for each hook group
        all_nexus_and_values: dict["HookNexus[Any]", Any] = {}
        for nexus, value in nexus_and_values.items():
            all_nexus_and_values[nexus] = value

        # Step 2: Collect all owners
        all_affected_owners: set[CarriesHooks[Any, Any]] = set()
        all_affected_hooks: set["HookLike[Any]"] = set()
        for nexus in all_nexus_and_values:
            for hook in nexus.hooks:
                all_affected_hooks.add(hook)
                if isinstance(hook, OwnedHookLike):
                    all_affected_owners.add(hook.owner)

        # Step 3: Check for each owner if the values would be valid as a collective
        def nexus_intersection(carries_collective_hooks: CarriesCollectiveHooks[Any, Any]) -> set["HookNexus[Any]"]:
            intersection: set["HookNexus[Any]"] = set()
            for nexus in all_nexus_and_values:
                for collective_hook in carries_collective_hooks._collective_hooks: # type: ignore
                    if collective_hook.hook_nexus is nexus:
                        intersection.add(nexus)
            return intersection
        remaining_owners: set[CarriesHooks[Any, Any]] = all_affected_owners.copy()
        remaining_hooks: set["HookLike[Any]"] = all_affected_hooks.copy()
        for owner in all_affected_owners:
            # Check if the hook is affected by the submission (if there is an overlap of at least 2 hooks)
            if isinstance(owner, CarriesCollectiveHooks):
                if len(nexus_intersection(owner)) >= 2:
                    # Overlap found - verify that the values would be valid
                    dict_of_values: dict[Any, Any] = {}
                    for nexus in nexus_intersection(owner):
                        # Get the key in the owner's collective hooks of the hook with the nexus
                        key_for_nexus: Any = owner.get_hook_key(nexus) # type: ignore
                        dict_of_values[key_for_nexus] = nexus_and_values[nexus]
                    success, msg = owner._is_valid_values_as_part_of_owner_impl(dict_of_values) # type: ignore
                    if success == True or success == "InternalInvalidationNeeded":
                        remaining_owners.remove(owner)
                        hook_key = owner.get_hook_key(nexus) # type: ignore
                        hook_key = owner.get_hook(hook_key)
                        if not hook_key in remaining_hooks:
                            raise ValueError(f"Hook {hook_key} not found in all affected hooks")
                        remaining_hooks.remove(hook_key)
                        if success == "InternalInvalidationNeeded":
                            overall_status = "InternalInvalidationNeeded"
                    else:
                        return False, msg, set(), set()
                    
        # Step 4: Check for each remaining owner if the values would be valid as a single value
        for owner in remaining_owners:
            for _, hook in owner.get_hook_dict().items():
                # Check if this hook's hook_nexus is in the nexus_and_values
                if hook.hook_nexus in nexus_and_values:
                    value = nexus_and_values[hook.hook_nexus]
                    success, msg = hook.is_valid_value_in_isolation(value)
                    remaining_hooks.remove(hook)
                    if success == False:
                        return False, msg, set(), set()
                    elif success == "InternalInvalidationNeeded":
                        overall_status = "InternalInvalidationNeeded"

        # Step 5: Check all remaining hooks if the values would be valid as a single value
        for hook in remaining_hooks:
            success, msg = hook.is_valid_value_in_isolation(nexus_and_values[hook.hook_nexus])
            if success == False:
                return False, msg, set(), set()
            elif success == "InternalInvalidationNeeded":
                overall_status = "InternalInvalidationNeeded"

        return overall_status, "Values are valid", all_affected_owners, all_affected_hooks

    @staticmethod
    def validate_multiple_values(
        nexus_and_values: Mapping["HookNexus[Any]", Any]) -> tuple[Literal[True, False, "InternalInvalidationNeeded"], str]:
        """
        Validate multiple values for a hook nexus.
        """

        success, msg, _, _ = HookNexus._validate_multiple_values_helper(nexus_and_values)
        return success, msg

    @staticmethod
    def submit_multiple_values(
        nexus_and_values: Mapping["HookNexus[Any]", Any]) -> tuple[bool, str]:
        """
        This function submits multiple values to one or more hooks.

        If multiple hook groups are provided, the values are submitted at once, so that complex states can be synchronized.

        Args:
            hooks_and_values: A mapping of hooks to their values

        Returns:
            A tuple containing a boolean indicating if the submission was successful and a string message
        """

        # Step 1: Validate the values and perform internal invalidation if needed
        while True:
            success, msg, all_affected_owners, all_affected_hooks = HookNexus._validate_multiple_values_helper(nexus_and_values)
            
            # Remove all the hooks which belong to an owner that is alreay affected by the submission
            hooks_to_internally_invalidate: set["HookLike[Any]"] = all_affected_hooks.copy()
            for owner in all_affected_owners:
                for nexus in nexus_and_values:
                    hook_key = owner.get_hook_key(nexus)
                    hook: "HookLike[Any]" = owner.get_hook(hook_key)
                    hooks_to_internally_invalidate.remove(hook)

            if success == False:
                return False, msg
            elif success == "InternalInvalidationNeeded":
                for owner in all_affected_owners:
                    values: dict[Any, Any] = {}
                    for nexus in nexus_and_values:
                        hook_key = owner.get_hook_key(nexus)
                        value = nexus_and_values[nexus]
                        values[hook_key] = value
                    owner._internal_invalidate_hooks(values) # type: ignore
                for hook in hooks_to_internally_invalidate:
                    hook._internal_invalidate(nexus_and_values[hook.hook_nexus]) # type: ignore
            else:
                break

        # Step 2: Update the HookNexus value after successful invalidation
        for nexus, value in nexus_and_values.items():
            nexus._previous_value = nexus._value
            nexus._value = value

        # Step 3: If all values are valid, invalidate the hooks
        for owner in all_affected_owners:
            owner.invalidate_hooks()
        for hook in hooks_to_internally_invalidate:
            hook.invalidate()

        # Step 4: Notify listeners
        for owner in all_affected_owners:
            if isinstance(owner, BaseListeningLike):
                owner._notify_listeners() # type: ignore
        for hook in all_affected_hooks:
            hook._notify_listeners() # type: ignore

        return True, "Invalidation successful"

    def validate_single_value(
        self,
        value: T,
    ) -> tuple[Literal[True, False, "InternalInvalidationNeeded"], str]:
        """
        Checks for each hook if the value is valid.
        """

        overall_status: Literal[True, False, "InternalInvalidationNeeded"] = True

        for hook in self._hooks:
            if isinstance(hook, OwnedHookLike):
                success, msg = hook._is_valid_value_as_part_of_owner(value) #type: ignore
            else:
                success, msg = True, "Value is valid"
            if success == "InternalInvalidationNeeded":
                overall_status = "InternalInvalidationNeeded"
            if success == False:
                return False, msg

        return overall_status, "Value is valid"

    def submit_single_value(
        self,
        value: T,
    ) -> tuple[bool, str]:
        """"
        Submit a value to the hook group.
        If the submission fails, the former values for the hooks are reset.

        Args:
            value: The value to set for the hooks
            special_cases: The special cases for submission. If empty, all hooks in the group are considered.

        Returns:
            A tuple containing a boolean indicating if the submission was successful and a string message
        """

        # Step 1: Perform the value check and collect the hooks that should be invalidated
        while True:
            success, msg = self.validate_single_value(value)
            if success == False:
                return False, msg
            elif success == "InternalInvalidationNeeded":
                for hook in self._hooks:
                    hook._internal_invalidate(value) #type: ignore
            else:
                break

        # Step 2: Update the HookNexus value after successful invalidation
        self._previous_value = self._value
        self._value = value

        # Step 3: Invalidate the hooks
        if success == True:
            for hook in self._hooks:
                if hook.can_be_invalidated:
                    hook.invalidate()

        # Step 4: Notify listeners
        for hook in self._hooks:
            if isinstance(hook, OwnedHookLike):
                owner = hook.owner
                if isinstance(owner, BaseListeningLike):
                    owner._notify_listeners() # type: ignore

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
        merged_group: HookNexus[T] = HookNexus[T](reference_value)
        
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
    def connect_hooks(source_hook: "HookLike[T]", target_hook: "HookLike[T]") -> tuple[bool, str]:
        """
        Connect two hooks together.

        Args:
            source_hook: The hook to take the value from upon initialization
            target_hook: The hook to set the value to upon initialization

        Raises:
            ValueError: If the hooks are not of the same type
        """

        # Validate that both hooks are not None
        if source_hook is None or target_hook is None: # type: ignore
            raise ValueError("Cannot connect None hooks")
        
        # Ensure that the value in both hook groups is the same
        # The source_hook's value becomes the source of truth
        source_hook.in_submission = True
        success, msg = target_hook.hook_nexus.submit_single_value(value=source_hook.value)
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