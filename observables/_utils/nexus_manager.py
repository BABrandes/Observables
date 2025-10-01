from typing import Mapping, Any, Optional, TYPE_CHECKING

from logging import Logger


if TYPE_CHECKING:
    from .carries_hooks_like import CarriesHooksLike

from .._hooks.hook_like import HookLike
from .base_listening import BaseListeningLike
from .hook_nexus import HookNexus


class NexusManager:
    """
    Central coordinator for the observable sync system.
    
    The NexusManager handles the complete value submission flow in the new architecture:
    1. Receives value submissions from observables
    2. Completes missing values using add_values_to_be_updated_callback
    3. Validates all values using validation callbacks
    4. Updates hook nexuses with new values
    5. Triggers invalidation and listener notifications
    
    This replaces the old binding system with a more flexible hook-based approach
    where observables can define custom logic for value completion and validation.
    """

    def __init__(self):
        pass

    def reset(self) -> None:
        """Reset the nexus manager state for testing purposes."""
        pass

    @staticmethod
    def _filter_nexus_and_values_for_owner(nexus_and_values: dict["HookNexus[Any]", Any], owner: "CarriesHooksLike[Any, Any]") -> tuple[dict[Any, Any], dict[Any, HookLike[Any]]]:
        """
        This method extracts the value and hook dict from the nexus and values dictionary for a specific owner.
        It essentially filters the nexus and values dictionary to only include values which the owner has a hook for. It then finds the hook keys for the owner and returns the value and hook dict for these keys.

        Args:
            nexus_and_values: The nexus and values dictionary
            owner: The owner to filter for

        Returns:
            A tuple containing the value and hook dict corresponding to the owner
        """

        from .._hooks.owned_hook_like import OwnedHookLike
        from .._hooks.hook_like import HookLike

        key_and_value_dict: dict[Any, Any] = {}
        key_and_hook_dict: dict[Any, HookLike[Any]] = {}
        for nexus, value in nexus_and_values.items():
            for hook in nexus.hooks:
                if isinstance(hook, OwnedHookLike):
                    if hook.owner is owner:
                        hook_key: Any = owner.get_hook_key(hook)
                        key_and_value_dict[hook_key] = value
                        key_and_hook_dict[hook_key] = hook
        return key_and_value_dict, key_and_hook_dict

    @staticmethod
    def _complete_nexus_and_values_for_owner(value_dict: dict[Any, Any], owner: "CarriesHooksLike[Any, Any]", as_reference_values: bool = False) -> None:
        """
        Complete the value dict for an owner.

        Args:
            value_dict: The value dict to complete
            owner: The owner to complete the value dict for
            as_reference_values: If True, the values will be returned as reference values
        """

        for hook_key in owner.get_hook_keys():
            if hook_key not in value_dict:
                if as_reference_values:
                    value_dict[hook_key] = owner.get_value_reference_of_hook(hook_key)
                else:
                    value_dict[hook_key] = owner.get_value_of_hook(hook_key)

    def _complete_nexus_and_values_dict(self, nexus_and_values: dict["HookNexus[Any]", Any]) -> tuple[bool, str]:
        """
        Complete the nexus and values dictionary using add_values_to_be_updated_callback.
        
        This method iteratively calls the add_values_to_be_updated_callback on all
        affected observables to complete missing values. For example, if a dictionary
        value is updated, the dictionary itself must be updated as well.
        
        The process continues until no more values need to be added, ensuring all
        related values are synchronized.
        """

        def insert_value_and_hook_dict_into_nexus_and_values(nexus_and_values: dict["HookNexus[Any]", Any], value_dict: dict[Any, Any], hook_dict: dict[Any, HookLike[Any]]) -> tuple[bool, str]:
            """
            This method inserts the value and hook dict into the nexus and values dictionary.
            It inserts the values from the value dict into the nexus and values dictionary. The hook dict helps to find the hook nexus for each value.
            """
            if value_dict.keys() != hook_dict.keys():
                return False, "Value and hook dict keys do not match"
            for hook_key, value in value_dict.items():
                hook_nexus: HookNexus[Any] = hook_dict[hook_key].hook_nexus
                if hook_nexus in nexus_and_values:
                    # The nexus is already in the nexus and values, this is not good. But maybe the associated value is the same?
                    if nexus_and_values[hook_nexus] != value:
                        return False, f"Hook nexus already in nexus and values and the associated value is not the same! ({nexus_and_values[hook_nexus]} != {value})"
                nexus_and_values[hook_nexus] = value
            return True, "Successfully inserted value and hook dict into nexus and values"

        def update_nexus_and_value_dict(owner: "CarriesHooksLike[Any, Any]", nexus_and_values: dict["HookNexus[Any]", Any]) -> tuple[Optional[int], str]:
            """
            This method updates the nexus and values dictionary with the additional nexus and values, if requested by the owner.
            """

            # Step 1: Prepare the value and hook dict to provide to the owner method
            value_dict, hook_dict = NexusManager._filter_nexus_and_values_for_owner(nexus_and_values, owner)

            # Step 2: Get the additional values from the owner method
            current_values_of_owner: Mapping[Any, Any] = owner.get_dict_of_value_references()
            additional_value_dict: Mapping[Any, Any] = owner._add_values_to_be_updated(current_values_of_owner, value_dict) # type: ignore

            # Step 3: Add the additional values and hooks to the value and hook dict
            for hook_key, value in additional_value_dict.items():
                value_dict[hook_key] = value
                hook_dict[hook_key] = owner.get_hook(hook_key)

            # Step 4: Insert the value and hook dict into the nexus and values
            number_of_items_before: int = len(nexus_and_values)
            success, msg = insert_value_and_hook_dict_into_nexus_and_values(nexus_and_values, value_dict, hook_dict)
            if success == False:
                return None, msg
            number_of_inserted_items: int = len(nexus_and_values) - number_of_items_before

            # Step 5: Return the nexus and values
            return number_of_inserted_items, "Successfully updated nexus and values"

        from .._hooks.owned_hook_like import OwnedHookLike
        from .._hooks.floating_hook_like import FloatingHookLike
            
        while True:

            # Step 1: Collect the all the owners that need to be checked for additional nexus and values
            owners_to_check_for_additional_nexus_and_values: set["CarriesHooksLike[Any, Any]"] = set()
            for nexus in nexus_and_values:
                for hook in nexus.hooks:
                    match hook:
                        case OwnedHookLike():
                            owners_to_check_for_additional_nexus_and_values.add(hook.owner)
                        case FloatingHookLike():
                            pass
                        case _:
                            pass

            # Step 2: Check for each owner if there are additional nexus and values
            number_of_inserted_items: Optional[int] = 0
            for owner in owners_to_check_for_additional_nexus_and_values:
                number_of_inserted_items, msg = update_nexus_and_value_dict(owner, nexus_and_values)
                if number_of_inserted_items is None:
                    return False, msg
                if number_of_inserted_items > 0:
                    break

            # Step 3: If no additional nexus and values were found, break the loop
            if number_of_inserted_items == 0:
                break

        return True, "Successfully updated nexus and values"

    def submit_values(
        self,
        nexus_and_values: Mapping["HookNexus[Any]", Any],
        only_check_values: bool = False,
        not_notifying_listeners_after_submission: set[BaseListeningLike] = set(),
        logger: Optional[Logger] = None
        ) -> tuple[bool, str]:
        """
        Submit values to the hook nexuses in the new architecture.
        
        This is the main entry point for value submissions. It orchestrates the complete
        submission flow:
        
        1. **Value Completion**: Uses add_values_to_be_updated_callback to complete
           missing values based on submitted values
        2. **Validation**: Validates all values using validation callbacks
        3. **Value Update**: Updates hook nexuses with new values
        4. **Invalidation**: Triggers invalidation of affected observables
        5. **Notification**: Notifies listeners of changes
        
        Args:
            nexus_and_values: Mapping of hook nexuses to their new values
            only_check_values: If True, only validates without updating values
            not_notifying_listeners_after_submission: Set of listeners to skip notification
            logger: Optional logger for debugging
            
        Returns:
            Tuple of (success: bool, message: str)
        """

        from .._hooks.owned_hook_like import OwnedHookLike
        from .._hooks.floating_hook_like import FloatingHookLike

        # Step 1: Update the nexus and values
        complete_nexus_and_values: dict["HookNexus[Any]", Any] = {}
        complete_nexus_and_values.update(nexus_and_values)
        success, msg = self._complete_nexus_and_values_dict(complete_nexus_and_values)
        if success == False:
            return False, msg

        # Step 2: Collect the owners and floating hooks to validate
        owners_to_validate: set["CarriesHooksLike[Any, Any]"] = set()
        floating_hooks_to_validate: set[FloatingHookLike[Any]] = set()
        for nexus, value in complete_nexus_and_values.items():
            for hook in nexus.hooks:
                match hook:
                    case OwnedHookLike():
                        owners_to_validate.add(hook.owner)
                    case FloatingHookLike():
                        floating_hooks_to_validate.add(hook)
                    case _:
                        pass

        # Step 3: Validate the values
        for owner in owners_to_validate:
            value_dict, _ = NexusManager._filter_nexus_and_values_for_owner(complete_nexus_and_values, owner)
            NexusManager._complete_nexus_and_values_for_owner(value_dict, owner, as_reference_values=True)
            success, msg = owner.validate_values_in_isolation(value_dict)
            if success == False:
                return False, msg
        for floating_hook in floating_hooks_to_validate:
            success, msg = floating_hook.validate_value_in_isolation(complete_nexus_and_values[floating_hook.hook_nexus])
            if success == False:
                return False, msg

        if only_check_values:
            return True, "Values are valid"

        # Step 4: Update each nexus with the new value
        for nexus, value in complete_nexus_and_values.items():
            nexus._previous_value = nexus._value # type: ignore
            nexus._value = value # type: ignore

        # Step 5: Invalidate the affected owners and hooks
        for owner in owners_to_validate:
            owner.invalidate()
        for floating_hook in floating_hooks_to_validate:
            pass

        # Step 6: Notify the listeners
        if not not_notifying_listeners_after_submission:
            for owner in owners_to_validate:
                if isinstance(owner, BaseListeningLike):
                    if owner not in not_notifying_listeners_after_submission:
                        owner._notify_listeners() # type: ignore
                for hook in owner.get_dict_of_hooks().values():
                    if hook is None: # type: ignore
                        raise RuntimeError("Hook is None. This should not happen.")
                    if hook not in not_notifying_listeners_after_submission:
                        hook._notify_listeners() # type: ignore
            for floating_hook in floating_hooks_to_validate:
                if floating_hook not in not_notifying_listeners_after_submission:
                    floating_hook._notify_listeners() # type: ignore

        return True, "Values are submitted"

    @staticmethod
    def get_nexus_and_values(hooks: set["HookLike[Any]"]) -> dict[HookNexus[Any], Any]:
        """
        Get the nexus and values dictionary for a set of hooks.
        """
        nexus_and_values: dict[HookNexus[Any], Any] = {}
        for hook in hooks:
            nexus_and_values[hook.hook_nexus] = hook.value
        return nexus_and_values
