from typing import Mapping, Any, Optional

from logging import Logger

from .base_listening import BaseListeningLike
from .base_carries_hooks import BaseCarriesHooks
from .._hooks.hook_like import HookLike
from .._hooks.owned_hook_like import OwnedHookLike
from .._utils.hook_nexus import HookNexus
from .._hooks.floating_hook_like import FloatingHookLike

class NexusManager:
    """
    Manager for nexuses.
    """

    def __init__(self):
        pass

    def reset(self) -> None:
        """Reset the nexus manager state for testing purposes."""
        pass

    @staticmethod
    def _filter_nexus_and_values_for_owner(nexus_and_values: dict["HookNexus[Any]", Any], owner: BaseCarriesHooks[Any, Any]) -> tuple[dict[Any, Any], dict[Any, HookLike[Any]]]:
        """
        This method extracts the value and hook dict from the nexus and values dictionary for a specific owner.
        It essentially filters the nexus and values dictionary to only include values which the owner has a hook for. It then finds the hook keys for the owner and returns the value and hook dict for these keys.

        Args:
            nexus_and_values: The nexus and values dictionary
            owner: The owner to filter for

        Returns:
            A tuple containing the value and hook dict corresponding to the owner
        """
        key_and_value_dict: dict[Any, Any] = {}
        key_and_hook_dict: dict[Any, HookLike[Any]] = {}
        for nexus, value in nexus_and_values.items():
            for hook in nexus.hooks:
                if isinstance(hook, OwnedHookLike):
                    if hook.owner == owner:
                        hook_key: Any = owner.get_hook_key(hook)
                        key_and_value_dict[hook_key] = value
                        key_and_hook_dict[hook_key] = hook
        return key_and_value_dict, key_and_hook_dict

    def _complete_nexus_and_values_dict(self, nexus_and_values: dict["HookNexus[Any]", Any]) -> tuple[bool, str]:
        """
        This method updates the nexus and values dictionary with the additional nexus and values, if requested by the owners.

        e.g. if a value of a dict is updated, the dict must be updated as well. It will therefore add another entry for the dict nexus with the new dict.

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

        def update_nexus_and_value_dict(owner: BaseCarriesHooks[Any, Any], nexus_and_values: dict["HookNexus[Any]", Any]) -> tuple[Optional[int], str]:
            """
            This method updates the nexus and values dictionary with the additional nexus and values, if requested by the owner.
            """

            # Step 1: Prepare the value and hook dict to provide to the owner method
            value_dict, hook_dict = NexusManager._filter_nexus_and_values_for_owner(nexus_and_values, owner)

            # Step 2: Get the additional values from the owner method
            current_values_of_owner: Mapping[Any, Any] = owner.get_hook_value_as_reference_dict()
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
            
        while True:

            # Step 1: Collect the all the owners that need to be checked for additional nexus and values
            owners_to_check_for_additional_nexus_and_values: set[BaseCarriesHooks[Any, Any]] = set()
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
        Submit values to the nexuses.
        """

        # Step 1: Update the nexus and values
        complete_nexus_and_values: dict["HookNexus[Any]", Any] = {}
        complete_nexus_and_values.update(nexus_and_values)
        success, msg = self._complete_nexus_and_values_dict(complete_nexus_and_values)
        if success == False:
            return False, msg

        # Step 2: Collect the owners and floating hooks to validate
        owners_to_validate: set[BaseCarriesHooks[Any, Any]] = set()
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

DEFAULT_NEXUS_MANAGER: "NexusManager" = NexusManager()