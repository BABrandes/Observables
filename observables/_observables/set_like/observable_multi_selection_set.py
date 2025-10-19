from typing import Generic, TypeVar, Optional, overload, Literal, Mapping, AbstractSet
from collections.abc import Iterable
from logging import Logger

from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._hooks.hook_protocols.managed_hook import ManagedHookProtocol
from ..._carries_hooks.complex_observable_base import ComplexObservableBase
from .protocols import ObservableMultiSelectionOptionsProtocol

T = TypeVar("T")

class ObservableMultiSelectionSet(ComplexObservableBase[Literal["selected_options", "available_options"], Literal["number_of_selected_options", "number_of_available_options"], frozenset[T], int, "ObservableMultiSelectionSet"], ObservableMultiSelectionOptionsProtocol[T], Generic[T]):
    """
    An observable multi-selection option that manages both available options and selected values.
    
    This class combines the functionality of an observable set (for available options) and
    an observable set (for selected options). It ensures that all selected options are always
    valid according to the available options and supports bidirectional bindings for both
    the available options set and the selected values set.
    
    Features:
    - Bidirectional bindings for both available options and selected options
    - Automatic validation ensuring all selected options are in available options set
    - Listener notification system for change events
    - Full set interface for both available options and selections management
    - Type-safe generic implementation
    - Natural support for empty selections (sets can be empty)

    Handling of no selection:
    - The selected options can be empty (sets naturally support empty state)
    - If there are no available options, the selected options will be empty
    
    Example:
        >>> # Create a multi-selection with available options
        >>> country_selector = ObservableMultiSelectionOption(
        ...     selected_options={"USA", "Canada"},
        ...     options={"USA", "Canada", "UK", "Germany"}
        ... )
        >>> country_selector.add_listeners(lambda: print("Selection changed!"))
        >>> country_selector.add_selected_option("UK")  # Triggers listener
        Selection changed!
        
        >>> # Create bidirectional binding for available options
        >>> available_options_source = ObservableSet(["A", "B", "C"])
        >>> selector = ObservableMultiSelectionOption({"A"}, available_options_source)
        >>> available_options_source.add("D")  # Updates selector available options
        >>> print(selector.available_options)
        {'A', 'B', 'C', 'D'}
    
    Args:
        available_options: Set of available options or observable set to bind to
        selected_options: Initially selected options or observable set to bind to
    """

    @overload
    def __init__(self, selected_options: Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]], available_options: Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]], logger: Optional[Logger] = None) -> None:
        """Initialize with observable available options and observable selected options."""
        ...

    @overload
    def __init__(self, selected_options: AbstractSet[T], available_options: Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]], logger: Optional[Logger] = None) -> None:
        """Initialize with observable available options and direct selected options."""
        ...

    @overload
    def __init__(self, selected_options: Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]], available_options: AbstractSet[T], logger: Optional[Logger] = None) -> None:
        """Initialize with direct available options and observable selected options."""
        ...
    
    @overload
    def __init__(self, selected_options: AbstractSet[T], available_options: AbstractSet[T], logger: Optional[Logger] = None) -> None:
        """Initialize with direct available options and direct selected options."""
        ...

    @overload
    def __init__(self, observable: ObservableMultiSelectionOptionsProtocol[T], logger: Optional[Logger] = None) -> None:
        """Initialize from another ObservableMultiSelectionOptionProtocol object."""
        ...

    def __init__(self, selected_options: AbstractSet[T] | Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]] | ObservableMultiSelectionOptionsProtocol[T], available_options: AbstractSet[T] | Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]] | None = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize the ObservableMultiSelectionOption.
        
        Args:
            selected_options: Initially selected options (set/frozenset), hook to bind to, or ObservableMultiSelectionOptionProtocol object
            available_options: Set of available options (set/frozenset) or hook to bind to (optional if selected_options is ObservableMultiSelectionOptionProtocol)
            
        Note:
            Sets are automatically converted to immutable frozensets by the nexus system.
            
        Raises:
            ValueError: If any selected option is not in available options set
        """
        
        # Handle initialization from ObservableMultiSelectionOptionProtocol
        if isinstance(selected_options, ObservableMultiSelectionOptionsProtocol):            
            source_observable = selected_options # type: ignore
            initial_selected_options: AbstractSet[T] | frozenset[T] = source_observable.selected_options # type: ignore
            initial_available_options: AbstractSet[T] | frozenset[T] = source_observable.available_options # type: ignore
            selected_options_hook: Optional[ManagedHookProtocol[frozenset[T]]] = None
            available_options_hook: Optional[ManagedHookProtocol[frozenset[T]]] = None
            observable: Optional[ObservableMultiSelectionOptionsProtocol[T]] = selected_options
        else:
            observable = None
            # Handle initialization from separate selected_options and available_options
            if available_options is None:
                raise ValueError("available_options must be provided when not initializing from ObservableMultiSelectionOptionProtocol")
            
            if isinstance(available_options, ManagedHookProtocol):
                initial_available_options = available_options.value # type: ignore
                available_options_hook = available_options # type: ignore
            else:
                # Convert to frozenset for validation
                initial_available_options = frozenset(available_options) # type: ignore
                available_options_hook = None

            if isinstance(selected_options, ManagedHookProtocol):
                initial_selected_options = selected_options.value # type: ignore
                selected_options_hook = selected_options # type: ignore
            else:
                # Convert to frozenset for validation
                initial_selected_options = frozenset(selected_options) # type: ignore
                selected_options_hook = None

        # Validate that selected options are subset of available options
        # Convert to frozensets for comparison if needed
        selected_frozen = frozenset(initial_selected_options) if not isinstance(initial_selected_options, frozenset) else initial_selected_options
        available_frozen = frozenset(initial_available_options) if not isinstance(initial_available_options, frozenset) else initial_available_options
        
        if selected_frozen and not selected_frozen.issubset(available_frozen):
            invalid_options = selected_frozen - available_frozen
            raise ValueError(f"Selected options {invalid_options} not in available options {available_frozen}")
        
        def is_valid_value(x: Mapping[Literal["selected_options", "available_options"], frozenset[T]|int]) -> tuple[bool, str]:
            
            if "selected_options" in x:
                selected_options: frozenset[T] = x["selected_options"] # type: ignore
            else:
                selected_options = self._primary_hooks["selected_options"].value # type: ignore
            
            if "available_options" in x:
                available_options: frozenset[T] = x["available_options"] # type: ignore
            else:
                available_options = self._primary_hooks["available_options"].value # type: ignore
            
            if selected_options and not selected_options.issubset(available_options):
                return False, f"Selected options {selected_options} not in available options {available_options}"

            return True, "Verification method passed"

        super().__init__(
            initial_hook_values={"selected_options": initial_selected_options, "available_options": initial_available_options}, # type: ignore
            verification_method=is_valid_value,
            secondary_hook_callbacks={"number_of_selected_options": lambda x: len(x["selected_options"]), "number_of_available_options": lambda x: len(x["available_options"])}, # type: ignore
            logger=logger
        )

        # Establish bindings if hooks were provided
        if observable is not None:
            self.connect_hook(observable.selected_options_hook, "selected_options", "use_target_value") # type: ignore
            self.connect_hook(observable.available_options_hook, "available_options", "use_target_value") # type: ignore
        if available_options_hook is not None:
            self.connect_hook(available_options_hook, "available_options", "use_target_value") # type: ignore
        if selected_options_hook is not None and selected_options_hook is not available_options_hook:
            self.connect_hook(selected_options_hook, "selected_options", "use_target_value") # type: ignore

    #############################################################
    # ObservableMultiSelectionOptionsProtocol implementation
    #############################################################

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> Hook[AbstractSet[T]]:
        return self._primary_hooks["available_options"] # type: ignore

    @property
    def available_options(self) -> AbstractSet[T]:
        """Get the available options as an immutable frozenset."""
        return self._primary_hooks["available_options"].value # type: ignore
    
    @available_options.setter
    def available_options(self, available_options: Iterable[T]) -> None:
        """Set the available options (automatically converted to frozenset by nexus system)."""
        self.change_available_options(available_options)

    def change_available_options(self, available_options: Iterable[T]) -> None:
        """Set the available options set (automatically converted to frozenset)."""
        # Let nexus system handle immutability conversion
        success, msg = self._submit_values({"available_options": frozenset(available_options)})
        if not success:
            raise ValueError(msg)

    #-------------------------------- selected options --------------------------------

    @property
    def selected_options_hook(self) -> Hook[AbstractSet[T]]:
        return self._primary_hooks["selected_options"] # type: ignore

    @property
    def selected_options(self) -> AbstractSet[T]:
        """Get the currently selected options as an immutable frozenset."""
        return self._primary_hooks["selected_options"].value # type: ignore
    
    @selected_options.setter
    def selected_options(self, selected_options: AbstractSet[T]) -> None:
        """Set the selected options (automatically converted to frozenset by nexus system)."""
        # Let nexus system handle immutability conversion
        success, msg = self._submit_values({"selected_options": frozenset(selected_options)})
        if not success:
            raise ValueError(msg)

    def change_selected_options(self, selected_options: AbstractSet[T]) -> None:
        """Set the selected options (automatically converted to frozenset)."""
        # Let nexus system handle immutability conversion
        success, msg = self._submit_values({"selected_options": frozenset(selected_options)})
        if not success:
            raise ValueError(msg)

    #-------------------------------- length --------------------------------

    @property
    def number_of_available_options_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the number of available options.
        """
        return self._secondary_hooks["number_of_available_options"] # type: ignore

    @property
    def number_of_available_options(self) -> int:
        """
        Get the current number of available options.
        """
        return self._secondary_hooks["number_of_available_options"].value # type: ignore
    
    @property
    def number_of_selected_options_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the number of selected options.
        """
        return self._secondary_hooks["number_of_selected_options"] # type: ignore

    @property
    def number_of_selected_options(self) -> int:
        """
        Get the current number of selected options.
        """
        return self._secondary_hooks["number_of_selected_options"].value # type: ignore

    #-------------------------------- Convenience methods --------------------------------

    def change_selected_options_and_available_options(self, selected_options: AbstractSet[T], available_options: Iterable[T]) -> None:
        """
        Set both the selected options and available options atomically.
        
        Args:
            selected_options: The new selected options (set/frozenset automatically converted)
            available_options: The new set of available options (set/frozenset automatically converted)
        """
        # Let nexus system handle immutability conversion
        success, msg = self._submit_values({"selected_options": frozenset(selected_options), "available_options": frozenset(available_options)})
        if not success:
            raise ValueError(msg)

    def clear_selected_options(self) -> None:
        """Remove all items from the selected options set."""
        success, msg = self._submit_values({"selected_options": frozenset()}) # type: ignore
        if not success:
            raise ValueError(msg)
