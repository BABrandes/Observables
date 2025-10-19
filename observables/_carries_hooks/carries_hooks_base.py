from typing import Any, TypeVar, Optional, final, Mapping, Generic, Callable, Literal
from logging import Logger
from abc import ABC, abstractmethod
from threading import RLock


from .._auxiliary.listening_protocol import ListeningProtocol
from .._nexus_system.nexus_manager import NexusManager
from .._nexus_system.nexus import Nexus
from .._nexus_system.update_function_values import UpdateFunctionValues
from .._hooks.hook_protocols.owned_hook_protocol import OwnedHookProtocol
from .._nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER
from .._nexus_system.has_nexus_manager import HasNexusManager
from .._nexus_system.submission_error import SubmissionError
from .._hooks.hook_aliases import Hook, ReadOnlyHook

from .carries_hooks_protocol import CarriesHooksProtocol
from .carries_single_hook_protocol import CarriesSingleHookProtocol
from .._hooks.mixin_protocols.hook_with_connection_protocol import HookWithConnectionProtocol

import weakref

HK = TypeVar("HK")
HV = TypeVar("HV")
O = TypeVar("O", bound="CarriesHooksBase[Any, Any, Any]")

class CarriesHooksBase(HasNexusManager, CarriesHooksProtocol[HK, HV], Generic[HK, HV, O], ABC):
    """
    Base class for observables in the new hook-based architecture.
    
    This class provides the core functionality for observables that manage multiple
    hooks and participate in the sync system. It replaces the old binding system
    with a more flexible approach where observables define their own logic for:
    
    - Value completion (add_values_to_be_updated_callback)
    - Value validation (validate_complete_values_in_isolation_callback)  
    - Invalidation (invalidate_callback)
    
    The new architecture allows observables to define custom behavior for how
    values are synchronized and validated, making the system more extensible.

    Inheritance Structure:
    - Inherits from: CarriesHooksProtocol[HK, HV] (Protocol), Generic[HK, HV], ABC
    - Implements: Most CarriesHooksProtocol methods as @final methods with thread safety
    - Provides: Core sync system functionality, validation, and hook management

    Abstract Methods (Must Implement):
    Subclasses must implement these 4 abstract methods to define their specific behavior:
    
    1. _get_hook(key: HK) -> HookWithOwnerProtocol[HV]
       - Get a hook by its key
       - Must return the hook associated with the given key
       
    2. _get_value_reference_of_hook(key: HK) -> HV  
       - Get a value as a reference by its key
       - Must return a reference to the actual value (not a copy)
       - Modifying the returned value should modify the observable
       
    3. _get_hook_keys() -> set[HK]
       - Get all keys of the hooks managed by this observable
       - Must return the complete set of hook keys
       
    4. _get_hook_key(hook_or_nexus: HookWithOwnerProtocol[HV]|Nexus[HV]) -> HK
       - Get the key for a given hook or nexus
       - Must return the key that identifies the hook/nexus
       - Should raise ValueError if hook/nexus not found

    Provided Functionality:
    - Thread-safe access to all methods via RLock
    - Complete implementation of CarriesHooksProtocol protocol
    - Hook connection/disconnection management
    - Value submission and validation via NexusManager
    - Memory management and cleanup via destroy()
    - Callback-based customization for validation and value completion
    
    Example Implementation:
        class MyObservable(BaseCarriesHooks[str, Any]):
            def __init__(self):
                super().__init__()
                self._hooks = {"value": OwnedHook(self, "initial")}
                
            def _get_hook(self, key: str) -> HookWithOwnerProtocol[Any]:
                return self._hooks[key]
                
            def _get_value_reference_of_hook(self, key: str) -> Any:
                return self._hooks[key].value
                
            def _get_hook_keys(self) -> set[str]:
                return set(self._hooks.keys())
                
            def _get_hook_key(self, hook_or_nexus: HookWithOwnerProtocol[Any]|Nexus[Any]) -> str:
                for key, hook in self._hooks.items():
                    if hook is hook_or_nexus or hook.hook_nexus is hook_or_nexus:
                        return key
                raise ValueError("Hook not found")
    """

    def __init__(
        self,
        invalidate_callback: Optional[Callable[[O], tuple[bool, str]]] = None,
        validate_complete_values_in_isolation_callback: Optional[Callable[[O, Mapping[HK, HV]], tuple[bool, str]]] = None,
        add_values_to_be_updated_callback: Optional[Callable[[O, UpdateFunctionValues[HK, HV]], Mapping[HK, HV]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER, 
        ) -> None:
        """
        Initialize the CarriesHooksBase.
        """

        HasNexusManager.__init__(self, nexus_manager)

        # Store weak references to callbacks to avoid circular references
        self._self_ref = weakref.ref(self)
        self._invalidate_callback = invalidate_callback
        self._validate_complete_values_in_isolation_callback = validate_complete_values_in_isolation_callback
        self._add_values_to_be_updated_callback = add_values_to_be_updated_callback
        self._logger: Optional[Logger] = logger
        self._nexus_manager: NexusManager = nexus_manager

        self._lock = RLock()

    #########################################################
    # Public properties and methods
    #########################################################

    def link(self, hook: Hook[HV]|ReadOnlyHook[HV]|CarriesSingleHookProtocol[HV], to_key: HK, initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Connect a hook to the observable.

        ** Thread-safe **

        This method implements the hook connection process by delegating to the observable's
        hook's connect_hook method, which follows the standard connection flow:
        
        1. Get the two nexuses from the hooks to connect
        2. Submit one of the hooks' value to the other nexus
        3. If successful, both nexus must now have the same value
        4. Merge the nexuses to one -> Connection established!

        Args:
            hook: The external hook to connect to this observable
            to_key: The key identifying which hook in this observable to connect to
            initial_sync_mode: Determines which hook's value is used initially:
                - "use_caller_value": Use the external hook's value
                - "use_target_value": Use the observable hook's value

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """

        with self._lock:
            self._link(hook, to_key, initial_sync_mode)

    def link_many(self, hooks: Mapping[HK, Hook[HV]|ReadOnlyHook[HV]], initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Connect multiple hooks to the observable simultaneously.

        ** Thread-safe **

        This method efficiently connects multiple hooks by batching the connection process.
        Each connection follows the standard hook connection flow:
        
        1. Get the two nexuses from the hooks to connect
        2. Submit one of the hooks' value to the other nexus
        3. If successful, both nexus must now have the same value
        4. Merge the nexuses to one -> Connection established!

        Args:
            hooks: A mapping of keys to external hooks to connect
            initial_sync_mode: Determines which hook's value is used initially for each connection:
                - "use_caller_value": Use the external hook's value
                - "use_target_value": Use the observable hook's value

        Raises:
            ValueError: If any key is not found in component_hooks or secondary_hooks
        """

        with self._lock:
            self._link_many(hooks, initial_sync_mode)

    def unlink(self, key: Optional[HK] = None) -> None:
        """
        Disconnect a hook by its key.

        Args:
            key: The key of the hook to disconnect. If None, all hooks will be disconnected.
        """
        
        with self._lock:
            self._unlink(key)


    #########################################################
    # Private methods
    #########################################################

    @final
    def _invalidate(self) -> tuple[bool, str]:
        """
        Invalidate all hooks.

        ** Thread-safe **

        Returns:
            A tuple of (success: bool, message: str)

        Raises:
            ValueError: If the owner has been garbage collected
            ValueError: If the invalidate callback is not provided
        """

        if self._invalidate_callback is not None:
            if self._self_ref() is None:
                raise ValueError("Owner has been garbage collected")
            self_ref: O = self._self_ref() # type: ignore
            success, msg = self._invalidate_callback(self_ref)
            if success == False:
                return False, msg
            else:
                return True, msg
        else:
            return True, "No invalidate callback provided"

    @final
    def _validate_complete_values_in_isolation(self, values: dict[HK, HV]) -> tuple[bool, str]:
        """
        Check if the values are valid as part of the owner.
        
        Values are provided for all hooks according to get_hook_keys().

        ** Thread-safe **

        Returns:
            A tuple of (success: bool, message: str)

        Raises:
            ValueError: If the owner has been garbage collected
            ValueError: If the validate complete values in isolation callback is not provided
        """


        if self._validate_complete_values_in_isolation_callback is not None:
            if self._self_ref() is None:
                raise ValueError("Owner has been garbage collected")
            self_ref: O = self._self_ref() # type: ignore
            return self._validate_complete_values_in_isolation_callback(self_ref, values)
        else:
            return True, "No validation in isolation callback provided"

    @final
    def _get_value_of_hook(self, key: HK) -> HV:
        """
        Get a value as a copy by its key.

        ** This method is not thread-safe and should only be called by the get_value_of_hook method.

        Args:
            key: The key of the hook to get the value of

        Returns:
            The value of the hook
        """

        value = self._get_value_of_hook_impl(key)
        return value

    @final
    def _get_dict_of_hooks(self) ->  dict[HK, OwnedHookProtocol[HV]]:
        """
        Get a dictionary of hooks.

        ** This method is not thread-safe and should only be called by the get_dict_of_hooks method.

        Returns:
            A dictionary of keys to hooks
        """
        hook_dict: dict[HK, OwnedHookProtocol[HV]] = {}
        for key in self._get_hook_keys_impl():
            hook_dict[key] = self._get_hook_impl(key)
        return hook_dict

    @final
    def _get_dict_of_values(self) -> dict[HK, HV]:
        """
        Get a dictionary of values.

        ** This method is not thread-safe and should only be called by the get_dict_of_values method.

        Returns:
            A dictionary of keys to values
        """

        hook_value_dict: dict[HK, Any] = {}
        for key in self._get_hook_keys_impl():
            hook_value_dict[key] = self._get_value_of_hook(key)
        return hook_value_dict

    @final
    def _add_values_to_be_updated(self, values: UpdateFunctionValues[HK, HV]) -> Mapping[HK, HV]:
        """
        Add values to be updated.

        ** This method is not thread-safe and should only be called by the add_values_to_be_updated method.
        
        Args:
            values: UpdateFunctionValues containing current (complete state) and submitted (being updated) values
            
        Returns:
            Mapping of additional hook keys to values that should be updated
        """
        with self._lock:
            if self._add_values_to_be_updated_callback is not None:
                if self._self_ref() is None:
                    raise ValueError("Owner has been garbage collected")
                self_ref: O = self._self_ref() # type: ignore
                return self._add_values_to_be_updated_callback(self_ref, values)
            else:
                return {}

    def _link(self, hook: Hook[HV]|ReadOnlyHook[HV]|CarriesSingleHookProtocol[HV], to_key: HK, initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Connect a hook to the observable.

        ** This method is not thread-safe and should only be called by the link method.
        """

        if to_key in self._get_hook_keys_impl():
            hook_of_observable: OwnedHookProtocol[HV] = self._get_hook_impl(to_key)
            if isinstance(hook, CarriesSingleHookProtocol):
                hook = hook.hook # type: ignore
            success, msg = hook_of_observable._link(hook, initial_sync_mode) # type: ignore
            if not success:
                raise ValueError(msg)
        else:
            raise ValueError(f"Key {to_key} not found in component_hooks or secondary_hooks")

    def _link_many(self, hooks: Mapping[HK, Hook[HV]|ReadOnlyHook[HV]], initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Connect multiple hooks to the observable simultaneously.

        ** This method is not thread-safe and should only be called by the link_many method.

        Args:
            hooks: A mapping of keys to external hooks to connect
            initial_sync_mode: Determines which hook's value is used initially for each connection:
                - "use_caller_value": Use the external hook's value
                - "use_target_value": Use the observable hook's value

        Raises:
            ValueError: If any key is not found in component_hooks or secondary_hooks
        """

        hook_pairs: list[tuple[HookWithConnectionProtocol[HV], HookWithConnectionProtocol[HV]]] = []
        for key, hook in hooks.items():
            hook_of_observable = self._get_hook_impl(key)
            match initial_sync_mode:
                case "use_caller_value":
                    hook_pairs.append((hook_of_observable, hook))
                case "use_target_value":
                    hook_pairs.append((hook, hook_of_observable))
                case _: # type: ignore
                    raise ValueError(f"Invalid initial sync mode: {initial_sync_mode}")
        Nexus[HV].connect_hook_pairs(*hook_pairs) # type: ignore

    def _unlink(self, key: Optional[HK] = None) -> None:
        """
        Unlink a hook by its key.

        ** This method is not thread-safe and should only be called by the unlink method.

        Args:
            key: The key of the hook to disconnect. If None, all hooks will be disconnected.
        """

        if key is None:
            for hook in self._get_dict_of_hooks().values():
                hook._unlink() # type: ignore
        else:
            self._get_hook_impl(key)._unlink() # type: ignore

    def _destroy(self) -> None:
        """
        Destroy the observable by disconnecting all hooks, removing listeners, and invalidating.

        ** This method is not thread-safe and should only be called by the destroy method.
        
        This method should be called before the observable is deleted to ensure proper
        memory cleanup and prevent memory leaks. After calling this method, the observable
        should not be used anymore as it will be in an invalid state.
        
        Example:
            >>> obs = ObservableSingleValue("test")
            >>> obs.cleanup()  # Properly clean up before deletion
            >>> del obs
        """

        with self._lock:
            self.unlink(None)
            if isinstance(self, ListeningProtocol): # type: ignore
                self.remove_all_listeners() # type: ignore

    def _validate_value(self, hook_key: HK, value: HV) -> tuple[bool, str]:
        """
        Check if a value is valid.

        ** This method is not thread-safe and should only be called by the validate_value method.

        Args:
            hook_key: The key of the hook to validate
            value: The value to validate

        Returns:
            A tuple of (success: bool, message: str)
        """

        hook: OwnedHookProtocol[HV] = self._get_hook_impl(hook_key)

        success, msg = self._nexus_manager.submit_values({hook._get_hook_nexus(): value}, mode="Check values") # type: ignore
        if success == False:
            return False, msg
        else:
            return True, "Value is valid"

    def _validate_values(self, values: Mapping[HK, HV]) -> tuple[bool, str]:
        """
        Check if the values can be accepted.

        ** This method is not thread-safe and should only be called by the validate_values method.

        Args:
            values: The values to validate

        Returns:
            A tuple of (success: bool, message: str)
        """

        if len(values) == 0:
            return True, "No values provided"

        nexus_and_values: Mapping[Nexus[Any], Any] = self._get_nexus_and_values(values)
        success, msg = self._nexus_manager.submit_values(nexus_and_values, mode="Check values")
        if success == True:
            return True, msg
        else:
            return False, msg

    def _submit_value(self, key: HK, value: HV, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Submit a value to the observable.
        
        Args:
            key: The key of the hook to submit the value to
            value: The value to submit
            logger: Optional logger for debugging
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        with self._lock:
            success, msg = self._nexus_manager.submit_values(
                {self._get_hook_impl(key)._get_hook_nexus(): value}, # type: ignore
                mode="Normal submission",
                logger=logger
            )
            if not success and raise_submission_error_flag:
                raise SubmissionError(msg, value)
            return success, msg

    def _submit_values(self, values: Mapping[HK, HV], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
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
            logger: Optional logger for debugging
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        with self._lock:
            nexus_and_values: dict[Nexus[Any], Any] = self._get_nexus_and_values(values)
            success, msg = self._nexus_manager.submit_values(
                nexus_and_values,
                logger=logger
            )
            if not success and raise_submission_error_flag:
                raise SubmissionError(msg, values)
            return success, msg

    def _get_nexus_and_values(self, values: Mapping[HK, HV]) -> dict[Nexus[Any], Any]:
        """
        Get a dictionary of nexuses and values.
        """
        nexus_and_values: dict[Nexus[Any], Any] = {}
        for key, value in values.items():
            nexus_and_values[self._get_hook_impl(key)._get_nexus()] = value # type: ignore
        return nexus_and_values

    def _get_nexus_manager(self) -> "NexusManager":
        return self._nexus_manager

    # ------------------ To be implemented by subclasses ------------------

    @abstractmethod
    def _get_hook_impl(self, key: HK) -> OwnedHookProtocol[HV]:
        """
        Get a hook by its key.

        ** This method is not thread-safe and should only be called by the get_hook method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Args:
            key: The key of the hook to get

        Returns:
            The hook associated with the key
        """
        ...

    @abstractmethod
    def _get_value_of_hook_impl(self, key: HK) -> HV:
        """
        Get a value as a copy by its key.

        ** This method is not thread-safe and should only be called by the get_value_of_hook method.

        ** Must be implemented by subclasses to provide efficient lookup for values.

        Args:
            key: The key of the hook to get the value of
        """
        ...

    @abstractmethod
    def _get_hook_keys_impl(self) -> set[HK]:
        """
        Get all keys of the hooks.

        ** This method is not thread-safe and should only be called by the get_hook_keys method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Returns:
            The set of keys for the hooks
        """
        ...

    @abstractmethod
    def _get_hook_key_impl(self, hook_or_nexus: OwnedHookProtocol[HV]|Nexus[HV]) -> HK:
        """
        Get the key for a hook or nexus.

        ** This method is not thread-safe and should only be called by the get_hook_key method.

        ** Must be implemented by subclasses to provide efficient lookup for hooks.

        Args:
            hook_or_nexus: The hook or nexus to get the key for

        Returns:
            The key for the hook or nexus
        """
        ...