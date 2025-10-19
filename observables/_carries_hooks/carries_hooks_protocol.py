from typing import TYPE_CHECKING, TypeVar, Optional, Mapping, Protocol, final, Literal
from logging import Logger

from .._nexus_system.has_nexus_manager_protocol import HasNexusManagerProtocol
from .._nexus_system.update_function_values import UpdateFunctionValues
from .._hooks.hook_protocols.owned_hook_protocol import OwnedHookProtocol
from .._nexus_system.hook_nexus import HookNexus
from .._hooks.hook_aliases import Hook, ReadOnlyHook

if TYPE_CHECKING:
    from .carries_single_hook_protocol import CarriesSingleHookProtocol
    from .._nexus_system.nexus_manager import NexusManager

HK = TypeVar("HK")
HV = TypeVar("HV")

class CarriesHooksProtocol(HasNexusManagerProtocol, Protocol[HK, HV]):
    """
    Protocol for objects that carry a set of hooks.
    """

    #########################################################################
    # Methods to get hooks and values
    #########################################################################

    def get_hook(self, key: HK) -> OwnedHookProtocol[HV]:
        """
        Get a hook by its key.
        """
        ...

    def get_value_reference_of_hook(self, key: HK) -> HV:
        """
        Get a value as a reference by its key.
        """
        ...
    
    def get_hook_keys(self) -> set[HK]:
        """
        Get all keys of the hooks.
        """
        ...

    def get_hook_key(self, hook_or_nexus: OwnedHookProtocol[HV]|HookNexus[HV]) -> HK:
        """
        Get the key of a hook or nexus.
        """
        ...

    def get_value_of_hook(self, key: HK) -> HV:
        """
        Get a value as a copy by its key.

        ** The returned value is a copy, so modifying it will not modify the observable.
        """
        ...

    def get_dict_of_hooks(self) ->  dict[HK, OwnedHookProtocol[HV]]:
        """
        Get a dictionary of hooks.
        """
        ...

    def get_dict_of_values(self) -> dict[HK, HV]:
        """
        Get a dictionary of values.

        ** The returned values are copies, so modifying them will not modify the observable.

        Returns:
            A dictionary of keys to values
        """
        ...

    def get_dict_of_value_references(self) -> dict[HK, HV]:
        """
        Get a dictionary of values as references.

        ** The returned values are references, so modifying them will modify the owner.
        
        ** Items can be added and removed without affecting the owner.

        Returns:
            A dictionary of keys to values as references
        """
        ...

    #########################################################################
    # Methods to invalidate and validate
    #########################################################################

    def get_nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this observable belongs to.
        """
        ...

    def invalidate(self) -> tuple[bool, str]:
        """
        Invalidate all hooks.
        """
        ...

    def validate_complete_values_in_isolation(self, values: dict[HK, HV]) -> tuple[bool, str]:
        """
        Check if the values are valid as part of the owner.
        
        Values are provided for all hooks according to get_hook_keys().
        """
        ...

    def validate_value(self, hook_key: HK, value: HV) -> tuple[bool, str]:
        """
        Check if a value is valid.
        """
        ...

    def validate_values(self, values: Mapping[HK, HV]) -> tuple[bool, str]:
        """
        Check if the values can be accepted.
        """
        ...

    def submit_value(self, key: HK, value: HV, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Submit a value to the observable.
        """
        ...

    def submit_values(self, values: Mapping[HK, HV], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Submit values to the observable.
        """
        ...

    #########################################################################
    # Methods to connect and disconnect hooks
    #########################################################################

    def connect_hook(self, hook: Hook[HV]|ReadOnlyHook[HV]|"CarriesSingleHookProtocol[HV]", to_key: HK, initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Connect a hook to the observable.

        Args:
            hook: The hook to connect
            to_key: The key to connect the hook to
            initial_sync_mode: The initial synchronization mode

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """
        ...

    def connect_hooks(self, hooks: Mapping[HK, Hook[HV]|ReadOnlyHook[HV]], initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Connect a list of hooks to the observable.

        Args:
            hooks: A mapping of keys to hooks
            initial_sync_mode: The initial synchronization mode

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """
        ...

    def disconnect_hook(self, key: Optional[HK]) -> None:
        """
        Disconnect a hook by its key.

        Args:
            key: The key of the hook to disconnect. If None, all hooks will be disconnected.
        """
        ...

    def destroy(self) -> None:
        """
        Destroy the observable by disconnecting all hooks, removing listeners, and invalidating.
        
        This method should be called before the observable is deleted to ensure proper
        memory cleanup and prevent memory leaks. After calling this method, the observable
        should not be used anymore as it will be in an invalid state.
        
        Example:
            >>> obs = ObservableSingleValue("test")
            >>> obs.cleanup()  # Properly clean up before deletion
            >>> del obs
        """
        ...

    #########################################################################
    # Main sync system methods
    #########################################################################

    def _add_values_to_be_updated(self, values: UpdateFunctionValues[HK, HV]) -> Mapping[HK, HV]:
        """
        Add values to be updated.
        
        Args:
            values: UpdateFunctionValues containing current (complete state) and submitted (being updated) values
            
        Returns:
            Mapping of additional hook keys to values that should be updated
        """
        ...

    #########################################################################
    # Final Properties
    #########################################################################

    @property
    @final
    def nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this observable belongs to.
        """
        return self.get_nexus_manager()

    @property
    @final
    def dict_of_hooks(self) -> dict[HK, OwnedHookProtocol[HV]]:
        """
        Get a dictionary of hooks.
        """
        return self.get_dict_of_hooks()

    @property
    @final
    def dict_of_values(self) -> dict[HK, HV]:
        """
        Get a dictionary of values.

        ** The returned values are copies, so modifying them will not modify the observable.
        """
        return self.get_dict_of_values()

    @property
    @final
    def dict_of_value_references(self) -> dict[HK, HV]:
        """
        Get a dictionary of values as references.

        ** The returned values are references, so modifying them will modify the observable.
        """
        return self.get_dict_of_value_references()