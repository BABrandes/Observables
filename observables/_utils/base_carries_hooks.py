from typing import TYPE_CHECKING, Any, TypeVar, Optional, final, Mapping, Generic, Callable
from logging import Logger
from abc import ABC, abstractmethod
from .initial_sync_mode import InitialSyncMode
from .base_listening import BaseListeningLike
from threading import RLock
from .carries_hooks_like import CarriesHooksLike
from .nexus_manager import NexusManager
from .hook_nexus import HookNexus
from .._utils.default_nexus_manager import DEFAULT_NEXUS_MANAGER

if TYPE_CHECKING:
    from .._hooks.owned_hook_like import OwnedHookLike
    from .hook_nexus import HookNexus

HK = TypeVar("HK")
HV = TypeVar("HV")

class BaseCarriesHooks(CarriesHooksLike[HK, HV], Generic[HK, HV], ABC):
    """
    Base class for observables in the new hook-based architecture.
    
    This class provides the core functionality for observables that manage multiple
    hooks and participate in the sync system. It replaces the old binding system
    with a more flexible approach where observables define their own logic for:
    
    - Value completion (add_values_to_be_updated_callback)
    - Value validation (validation_of_complete_value_set_in_isolation_callback)  
    - Invalidation (invalidate_callback)
    
    The new architecture allows observables to define custom behavior for how
    values are synchronized and validated, making the system more extensible.

    Must implement:

        - def get_hook(self, key: HK) -> "OwnedHookLike[HV]":
        
            Get a hook by its key.

        - def get_hook_value_as_reference(self, key: HK) -> HV:
        
            Get a value as a reference by its key.
            The returned value is a reference, so modifying it will modify the observable.

        - def get_hook_keys(self) -> set[HK]:
        
            Get all keys of the hooks.

        - def get_hook_key(self, hook_or_nexus: "OwnedHookLike[HV]|HookNexus[HV]") -> HK:
        
            Get the key of a hook or nexus.
    """

    def __init__(
        self,
        invalidate_callback: Optional[Callable[[], tuple[bool, str]]] = None,
        validation_of_complete_value_set_in_isolation_callback: Optional[Callable[[Mapping[HK, HV]], tuple[bool, str]]] = None,
        add_values_to_be_updated_callback: Optional[Callable[[Mapping[HK, HV], Mapping[HK, HV]], Mapping[HK, HV]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER, 
        ) -> None:
        """
        Initialize the CarriesHooksBase.
        """
        self._invalidate_callback: Optional[Callable[[], tuple[bool, str]]] = invalidate_callback
        self._validation_of_complete_value_set_in_isolation_callback: Optional[Callable[[Mapping[HK, HV]], tuple[bool, str]]] = validation_of_complete_value_set_in_isolation_callback
        self._add_values_to_be_updated_callback: Optional[Callable[[Mapping[HK, HV], Mapping[HK, HV]], Mapping[HK, HV]]] = add_values_to_be_updated_callback
        self._logger: Optional[Logger] = logger
        self._nexus_manager: NexusManager = nexus_manager

        self._lock = RLock()

    def get_nexus_manager(self) -> NexusManager:
        """
        Get the nexus manager that this observable belongs to.
        """
        return self._nexus_manager

    @abstractmethod
    def _get_hook(self, key: HK) -> "OwnedHookLike[HV]":
        """
        Get a hook by its key.

        Args:
            key: The key of the hook to get

        Returns:
            The hook
        """
        ...

    @abstractmethod
    def _get_value_reference_of_hook(self, key: HK) -> HV:
        """
        Get a value as a reference by its key.

        ** The returned value is a reference, so modifying it will modify the observable.

        Args:
            key: The key of the hook to get

        Returns:
            The value
        """
        ...

    @abstractmethod
    def _get_hook_keys(self) -> set[HK]:
        """
        Get all keys of the hooks.
        """
        ...

    @abstractmethod
    def _get_hook_key(self, hook_or_nexus: "OwnedHookLike[HV]|HookNexus[HV]") -> HK:
        """
        Get the key for a hook or nexus.

        Args:
            hook_or_nexus: The hook or nexus to get the key for

        Returns:
            The key for the hook or nexus

        Raises:
            ValueError: If the hook or nexus is not found in component_hooks or secondary_hooks
        """
        ...

    #########################################################
    # Final methods
    #########################################################

    @final
    def get_hook(self, key: HK) -> "OwnedHookLike[HV]":
        """
        Get a hook by its key.
        """
        with self._lock:
            return self._get_hook(key)

    @final
    def get_value_reference_of_hook(self, key: HK) -> HV:
        """
        Get a value as a reference by its key.
        """
        with self._lock:
            return self._get_value_reference_of_hook(key)
    
    @final
    def get_hook_keys(self) -> set[HK]:
        """
        Get all keys of the hooks.
        """
        with self._lock:
            return self._get_hook_keys()

    @final
    def get_hook_key(self, hook_or_nexus: "OwnedHookLike[HV]|HookNexus[HV]") -> HK:
        """
        Get the key of a hook or nexus.
        """
        with self._lock:
            return self._get_hook_key(hook_or_nexus)

    @final
    def invalidate(self) -> tuple[bool, str]:
        """
        Invalidate all hooks.
        """
        with self._lock:
            if self._invalidate_callback is not None:
                success, msg = self._invalidate_callback()
                if success == False:
                    return False, msg
                else:
                    return True, msg
            else:
                return True, "No invalidate callback provided"

    @final
    def validate_values_in_isolation(self, values: dict[HK, HV]) -> tuple[bool, str]:
        """
        Check if the values are valid as part of the owner.
        """

        with self._lock:
            complete_values: dict[HK, HV] = {}
            if self._validation_of_complete_value_set_in_isolation_callback is not None:
                for key in self._get_hook_keys():
                    if key in values:
                        complete_values[key] = values[key]
                    else:
                        complete_values[key] = self._get_hook(key).value
                return self._validation_of_complete_value_set_in_isolation_callback(complete_values)
            else:
                return True, "No validation in isolation callback provided"

    @final
    def get_value_of_hook(self, key: HK) -> HV:
        """
        Get a value as a copy by its key.

        ** The returned value is a copy, so modifying it will not modify the observable.
        """

        with self._lock:
            value_as_reference = self._get_value_reference_of_hook(key)
            if hasattr(value_as_reference, "copy"):
                return value_as_reference.copy() # type: ignore
            else:
                return value_as_reference # type: ignore

    @final
    def _get_dict_of_hooks(self) ->  "dict[HK, OwnedHookLike[HV]]":
        """
        Get a dictionary of hooks.
        """
        hook_dict: dict[HK, "OwnedHookLike[Any]"] = {}
        for key in self._get_hook_keys():
            hook_dict[key] = self._get_hook(key)
        return hook_dict


    @final
    def get_dict_of_hooks(self) ->  "dict[HK, OwnedHookLike[HV]]":
        """
        Get a dictionary of hooks.
        """

        with self._lock:
            return self._get_dict_of_hooks()

    @final
    def get_dict_of_values(self) -> dict[HK, HV]:
        """
        Get a dictionary of values.

        ** The returned values are copies, so modifying them will not modify the observable.

        Returns:
            A dictionary of keys to values
        """

        with self._lock:
            hook_value_dict: dict[HK, Any] = {}
            for key in self._get_hook_keys():
                hook_value_dict[key] = self.get_value_of_hook(key)
            return hook_value_dict

    @final
    def get_dict_of_value_references(self) -> dict[HK, HV]:
        """
        Get a dictionary of values as references.

        ** The returned values are references, so modifying them will modify the owner.
        
        ** Items can be added and removed without affecting the owner.

        Returns:
            A dictionary of keys to values as references
        """

        with self._lock:
            hook_value_as_reference_dict: dict[HK, Any] = {}
            for key in self._get_hook_keys():
                hook_value_as_reference_dict[key] = self._get_value_reference_of_hook(key)
            return hook_value_as_reference_dict

    @final
    def _add_values_to_be_updated(self, current_values: Mapping[HK, HV], submitted_values: Mapping[HK, HV]) -> Mapping[HK, HV]:
        """
        Add values to be updated.
        """
        with self._lock:
            if self._add_values_to_be_updated_callback is not None:
                return self._add_values_to_be_updated_callback(current_values, submitted_values)
            else:
                return {}

    @final
    def connect_hook(self, hook: "OwnedHookLike[HV]", to_key: HK, initial_sync_mode: InitialSyncMode) -> None:
        """
        Connect a hook to the observable.

        Args:
            hook: The hook to connect
            to_key: The key to connect the hook to
            initial_sync_mode: The initial synchronization mode

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """

        with self._lock:
            if to_key in self._get_hook_keys():
                hook_of_observable: "OwnedHookLike[HV]" = self.get_hook(to_key)
                success, msg = hook_of_observable.connect_hook(hook, initial_sync_mode)
                if not success:
                    raise ValueError(msg)
            else:
                raise ValueError(f"Key {to_key} not found in component_hooks or secondary_hooks")

    @final
    def connect_hooks(self, hooks: Mapping[HK, "OwnedHookLike[HV]"], initial_sync_mode: InitialSyncMode) -> None:
        """
        Connect a list of hooks to the observable.

        Args:
            hooks: A mapping of keys to hooks
            initial_sync_mode: The initial synchronization mode

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """

        with self._lock:
            hook_pairs: list[tuple["OwnedHookLike[HV]", "OwnedHookLike[HV]"]] = []
            for key, hook in hooks.items():
                hook_of_observable = self._get_hook(key)
                match initial_sync_mode:
                    case InitialSyncMode.USE_CALLER_VALUE:
                        hook_pairs.append((hook_of_observable, hook))
                    case InitialSyncMode.USE_TARGET_VALUE:
                        hook_pairs.append((hook, hook_of_observable))
                    case _: # type: ignore
                        raise ValueError(f"Invalid initial sync mode: {initial_sync_mode}")
            HookNexus[HV].connect_hook_pairs(*hook_pairs)

    @final
    def disconnect(self, key: Optional[HK] = None) -> None:
        """
        Disconnect a hook by its key.

        Args:
            key: The key of the hook to disconnect. If None, all hooks will be disconnected.
        """
        
        with self._lock:
            if key is None:
                for hook in self._get_dict_of_hooks().values():
                    hook.disconnect()
            else:
                self._get_hook(key).disconnect()

    @final
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

        with self._lock:
            self.disconnect(None)
            if isinstance(self, BaseListeningLike):
                self.remove_all_listeners()

    @final
    def validate_value(self, hook_key: HK, value: HV) -> tuple[bool, str]:
        """
        Check if a value is valid.
        """

        with self._lock:
            hook: "OwnedHookLike[Any]" = self._get_hook(hook_key)

            success, msg = self._nexus_manager.submit_values({hook.hook_nexus: value}, only_check_values=True)
            if success == False:
                return False, msg
            else:
                return True, "Value is valid"

    @final
    def validate_values(self, values: Mapping[HK, HV]) -> tuple[bool, str]:
        """
        Check if the values can be accepted.
        """

        with self._lock:
            if len(values) == 0:
                return True, "No values provided"

            nexus_and_values: Mapping[HookNexus[Any], Any] = self.get_nexus_and_values(values)
            success, msg = self._nexus_manager.submit_values(nexus_and_values, only_check_values=True)
            if success == True:
                return True, msg
            else:
                return False, msg

    @final
    def submit_value(self, key: HK, value: HV, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Submit a value to the observable.
        """
        with self._lock:
            return self._nexus_manager.submit_values(
                {self._get_hook(key).hook_nexus: value},
                logger=logger
            )

    @final
    def submit_values(self, values: Mapping[HK, HV], not_notifying_listeners_after_submission: set[BaseListeningLike] = set(), logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Submit values to the observable using the new hook-based sync system.
        
        This method is the main entry point for value submissions in the new architecture.
        It converts the submitted values into nexus-and-values format and delegates to
        the NexusManager for processing.
        
        The NexusManager will:
        1. Complete missing values using add_values_to_be_updated_callback
        2. Validate all values using validation callbacks
        3. Update hook nexuses with new values
        4. Trigger invalidation and listener notifications
        
        Args:
            values: Mapping of hook keys to their new values
            not_notifying_listeners_after_submission: Set of listeners to skip notification
            logger: Optional logger for debugging
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        with self._lock:
            nexus_and_values: dict[HookNexus[Any], Any] = self.get_nexus_and_values(values)
            return self._nexus_manager.submit_values(
                nexus_and_values,
                not_notifying_listeners_after_submission=not_notifying_listeners_after_submission,
                logger=logger
            )

    def get_nexus_and_values(self, values: Mapping[HK, HV]) -> dict[HookNexus[Any], Any]:
        """
        Get a dictionary of nexuses and values.
        """
        nexus_and_values: dict[HookNexus[Any], Any] = {}
        for key, value in values.items():
            nexus_and_values[self._get_hook(key).hook_nexus] = value
        return nexus_and_values