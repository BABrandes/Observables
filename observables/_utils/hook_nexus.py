import logging
import weakref
from typing import Generic, Optional, TypeVar, TYPE_CHECKING, Any, cast
from .general import log
if TYPE_CHECKING:
    from .._hooks.hook_like import HookLike
    from .nexus_manager import NexusManager
    
T = TypeVar("T")

class HookNexus(Generic[T]):
    """
    A nexus of hooks in the new hook-based architecture.

    A HookNexus represents a group of hooks that share the same value and are
    synchronized together. This is the core concept of the new architecture,
    replacing the old binding system.
    
    Key features:
    - Groups hooks that should have the same value
    - Manages value synchronization between connected hooks
    - Handles hook connection and disconnection
    - Provides thread-safe operations
    
    When hooks are connected, their nexuses are merged, allowing them to
    share values and stay synchronized. When disconnected, hooks get their
    own isolated nexus.
    """

    def __init__(
        self,
        value: T,
        hooks: set["HookLike[T]"] = set(),
        logger: Optional[logging.Logger] = None,
        nexus_manager: Optional["NexusManager"] = None
        ) -> None:
        """
        Initialize the HookNexus.
        """
        
        from .default_nexus_manager import DEFAULT_NEXUS_MANAGER
        
        if nexus_manager is None:
            nexus_manager = DEFAULT_NEXUS_MANAGER

        self._nexus_manager: "NexusManager" = nexus_manager
        self._hooks: set[weakref.ref["HookLike[T]"]] = {weakref.ref(hook) for hook in hooks}
        self._value: T = value
        self._previous_value: T = value
        self._logger: Optional[logging.Logger] = logger
        self._submit_depth_counter: int = 0
        self._submit_touched_hooks: set["HookLike[T]"] = set()

        log(self, "HookNexus.__init__", self._logger, True, "Successfully initialized hook nexus")

    def _get_hooks(self) -> set["HookLike[T]"]:
        """Get the actual hooks from weak references, filtering out dead references."""
        alive_hooks: set["HookLike[T]"] = set()
        dead_refs: set[weakref.ref["HookLike[T]"]] = set()
        
        for hook_ref in self._hooks:
            hook = hook_ref()
            if hook is not None:
                alive_hooks.add(hook)
            else:
                dead_refs.add(hook_ref)
        
        # Remove dead references
        self._hooks -= dead_refs
        
        return alive_hooks

    def add_hook(self, hook: "HookLike[T]") -> tuple[bool, str]:
        self._hooks.add(weakref.ref(hook))
        log(self, "add_hook", self._logger, True, "Successfully added hook")
        return True, "Successfully added hook"

    def remove_hook(self, hook: "HookLike[T]") -> tuple[bool, str]:
        try:
            # Find and remove the weak reference to this hook
            hook_ref_to_remove = None
            for hook_ref in self._hooks:
                if hook_ref() is hook:
                    hook_ref_to_remove = hook_ref
                    break
            
            if hook_ref_to_remove is not None:
                self._hooks.remove(hook_ref_to_remove)
                log(self, "remove_hook", self._logger, True, "Successfully removed hook")
                return True, "Successfully removed hook"
            else:
                log(self, "remove_hook", self._logger, False, "Hook not found")
                return False, "Hook not found"
        except KeyError:
            return False, "Hook not found in nexus"

    @property
    def hooks(self) -> tuple["HookLike[T]", ...]:
        return tuple(self._get_hooks())
    
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
    def _merge_nexus(*nexuses: "HookNexus[T]") -> "HookNexus[T]":
        """
        Merge multiple hook nexuses into a single hook nexus.

        - There must not be any overlapping hooks in the input nexuses
        - The hooks in both nexuses must have the same type of T and be synced to the same value
        - The hooks in both nexuses must be disjoint, if not something went wrong in the binding system

        Args:
            *hook_nexuses: The hook nexuses to merge

        Returns:
            A new hook nexus that contains all the hooks from the input nexuses

        Raises:
            ValueError: If the hook nexuses are not disjoint
        """
        
        if len(nexuses) == 0:
            raise ValueError("No hook nexuses provided")
        
        # Get the first hook nexus's value as the reference
        reference_value = nexuses[0]._value

        # Check that all nexus managers are the same
        for nexus in nexuses:
            if nexus._nexus_manager != nexuses[0]._nexus_manager:
                raise ValueError("The nexus managers must be the same")
        nexus_manager: "NexusManager" = nexuses[0]._nexus_manager
        
        value_type: Optional[type[T]] = None
        for hook_nexus in nexuses:
            for hook in hook_nexus._get_hooks():
                if value_type is None:
                    value_type = type(hook.value)
                elif type(hook.value) != value_type:
                    raise ValueError("The hooks in the hook nexuses must have the same value type")

        # Check if any groups have overlapping hooks (not disjoint) and collect all hooks
        # Optimize: Use a single set to track all hooks instead of O(n²) pairwise intersection
        all_hooks: set["HookLike[T]"] = set()
        list_of_hook_nexus: list[set["HookLike[T]"]] = []
        
        for hook_nexus in nexuses:
            hook_nexus = hook_nexus._get_hooks()
            if all_hooks & hook_nexus:  # Check for intersection with existing hooks
                raise ValueError("The hook nexuses must be disjoint")
            all_hooks.update(hook_nexus)
            list_of_hook_nexus.append(hook_nexus)  # Store for later use
        
        # Create new merged nexus with the reference value
        merged_nexus: HookNexus[T] = HookNexus[T](reference_value, nexus_manager=nexus_manager)
        
        # Add all hooks to the merged nexus (reuse the already computed hook sets)
        for hook_nexus in list_of_hook_nexus:
            for hook in hook_nexus:
                merged_nexus.add_hook(hook)
        
        return merged_nexus
    
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
        nexus_manager = hook_pairs[0][0].hook_nexus._nexus_manager

        nexus_and_values: dict["HookNexus[Any]", Any] = {}
        for hook_pair in hook_pairs:
            nexus_and_values[hook_pair[1].hook_nexus] = hook_pair[0].value
        success, msg = nexus_manager.submit_values(nexus_and_values)
        if not success:
            raise ValueError(msg)
        
        for hook_pair in hook_pairs:
            merged_nexus = HookNexus[T]._merge_nexus(hook_pair[0].hook_nexus, hook_pair[1].hook_nexus)
            for hook in merged_nexus._get_hooks():
                hook._replace_hook_nexus(merged_nexus) # type: ignore

        return True, "Successfully connected hook pairs"
    
    @staticmethod
    def connect_hooks(source_hook: "HookLike[T]", target_hook: "HookLike[T]") -> tuple[bool, str]:
        """
        Connect two hooks together in the new architecture.

        This method merges the hook nexuses of both hooks, allowing them to share
        the same value and be synchronized together. This replaces the old binding
        system with a more flexible hook-based approach.

        Args:
            source_hook: The hook to take the value from upon initialization
            target_hook: The hook to set the value to upon initialization

        Raises:
            ValueError: If the hooks are not of the same type
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        
        # Check that all nexus managers are the same
        if source_hook.hook_nexus._nexus_manager != target_hook.hook_nexus._nexus_manager:
            raise ValueError("The nexus managers must be the same")
        nexus_manager: "NexusManager" = source_hook.hook_nexus._nexus_manager

        # Validate that both hooks are not None
        if source_hook is None or target_hook is None: # type: ignore
            raise ValueError("Cannot connect None hooks")
        
        # Check if the hooks are already connected
        if source_hook.hook_nexus == target_hook.hook_nexus:
            return True, "Hooks are already connected"
        
        # Ensure that the value in both hook nexuses is the same
        # The source_hook's value becomes the source of truth
        success, msg = nexus_manager.submit_values({target_hook.hook_nexus: source_hook.value})
        if not success:
            raise ValueError(msg)
            
        # Then merge the hook nexuses
        # Use the synchronized value for the merged group
        merged_nexus: HookNexus[T] = HookNexus[T]._merge_nexus(source_hook.hook_nexus, target_hook.hook_nexus)
        
        # Replace all hooks' hook nexuses with the merged one
        for hook in merged_nexus._get_hooks():
            hook._replace_hook_nexus(merged_nexus) # type: ignore

        return True, "Successfully connected hooks"

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook nexus."""
        return f"HookNexus(v={self.value}, id={id(self)}, {len(self._get_hooks())} hooks)"
    
    def __str__(self) -> str:
        """Get the string representation of this hook nexus."""
        return f"HookNexus(v={self.value}, id={id(self)})"