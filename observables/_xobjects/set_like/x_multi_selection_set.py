from typing import Generic, TypeVar, Optional, Literal, Mapping
from collections.abc import Iterable
from logging import Logger

from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ..._carries_hooks.x_complex_base import ComplexObservableBase
from ..._nexus_system.submission_error import SubmissionError
from .protocols import ObservableMultiSelectionOptionsProtocol
from .utils import likely_settable

T = TypeVar("T")

class ObservableMultiSelectionSet(ComplexObservableBase[Literal["selected_options", "available_options"], Literal["number_of_selected_options", "number_of_available_options"], Iterable[T], int, "ObservableMultiSelectionSet"], ObservableMultiSelectionOptionsProtocol[T], Generic[T]):
    """
    An observable multi-selection option that manages both available options and selected values.
    
    This class combines the functionality of an observable set (for available options) and
    an observable set (for selected options). It ensures that all selected options are always
    valid according to the available options and supports bidirectional linking for both
    the available options set and the selected values set.
    
    Features:
    - Bidirectional linking for both available options and selected options
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
        
        >>> # Create bidirectional linking for available options
        >>> available_options_source = ObservableSet(["A", "B", "C"])
        >>> selector = ObservableMultiSelectionOption({"A"}, available_options_source)
        >>> available_options_source.add("D")  # Updates selector available options
        >>> print(selector.available_options)
        {'A', 'B', 'C', 'D'}
    
    Args:
        available_options: Set of available options or observable set to link to
        selected_options: Initially selected options or observable set to link to
    """

    def __init__(self, selected_options: Iterable[T] | Hook[Iterable[T]] | ReadOnlyHook[Iterable[T]] | ObservableMultiSelectionOptionsProtocol[T], available_options: Iterable[T] | Hook[Iterable[T]] | ReadOnlyHook[Iterable[T]] | None = None, logger: Optional[Logger] = None) -> None: # type: ignore
        """
        Initialize the ObservableMultiSelectionOption.
        
        Args:
            selected_options: Initially selected options (set), hook to link to, or ObservableMultiSelectionOptionProtocol object
            available_options: Set of available options (set) or hook to link to (optional if selected_options is ObservableMultiSelectionOptionProtocol)
            
        Note:
            Sets are automatically converted to immutable sets by the nexus system.
            
        Raises:
            ValueError: If any selected option is not in available options set
        """
        
        # Handle initialization from ObservableMultiSelectionOptionProtocol
        if isinstance(selected_options, ObservableMultiSelectionOptionsProtocol):            
            source_observable = selected_options # type: ignore
            initial_selected_options: Iterable[T] = source_observable.selected_options # type: ignore
            initial_available_options: Iterable[T] = source_observable.available_options # type: ignore
            selected_options_hook: Optional[ManagedHookProtocol[Iterable[T]]] = None
            available_options_hook: Optional[ManagedHookProtocol[Iterable[T]]] = None
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
                initial_available_options = set(available_options) # type: ignore
                available_options_hook = None

            if isinstance(selected_options, ManagedHookProtocol):
                initial_selected_options = selected_options.value # type: ignore
                selected_options_hook = selected_options # type: ignore
            else:
                initial_selected_options = set(selected_options) # type: ignore
                selected_options_hook = None

        def is_valid_value(x: Mapping[Literal["selected_options", "available_options"], Iterable[T]]) -> tuple[bool, str]:
            selected_options = set(x["selected_options"])
            available_options = x["available_options"]
            
            if not likely_settable(available_options):
                return False, f"Available options '{available_options}' cannot be used as a set!"
            
            if not selected_options.issubset(available_options):
                return False, f"Selected options '{selected_options}' not in available options '{available_options}'!"

            return True, "Verification method passed"

        super().__init__(
            initial_hook_values={"selected_options": initial_selected_options, "available_options": initial_available_options}, # type: ignore
            verification_method=is_valid_value,
            secondary_hook_callbacks={"number_of_selected_options": lambda x: len(x["selected_options"]), "number_of_available_options": lambda x: len(x["available_options"])}, # type: ignore
            logger=logger
        )

        # Establish linking if hooks were provided
        if observable is not None:
            self._join("selected_options", observable.selected_options_hook, "use_target_value") # type: ignore
            self._join("available_options", observable.available_options_hook, "use_target_value") # type: ignore
        if available_options_hook is not None:
            self._join("available_options", available_options_hook, "use_target_value") # type: ignore
        if selected_options_hook is not None and selected_options_hook is not available_options_hook:
            self._join("selected_options", selected_options_hook, "use_target_value") # type: ignore

    #############################################################
    # ObservableMultiSelectionOptionsProtocol implementation
    #############################################################

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> Hook[Iterable[T]]:
        return self._primary_hooks["available_options"] # type: ignore

    @property
    def available_options(self) -> Iterable[T]: # type: ignore
        """Get the available options as an immutable set."""
        return self._primary_hooks["available_options"].value # type: ignore
    
    @available_options.setter
    def available_options(self, available_options: Iterable[T]) -> None:
        self.change_available_options(available_options)
    
    def change_available_options(self, available_options: Iterable[T]) -> None:
        """Set the available options (automatically converted to set by nexus system)."""
        success, msg = self._submit_value("available_options", available_options) # type: ignore
        if not success:
            raise SubmissionError(msg, available_options, "available_options")

    #-------------------------------- selected options --------------------------------

    @property
    def selected_options_hook(self) -> Hook[Iterable[T]]:
        return self._primary_hooks["selected_options"] # type: ignore

    @property
    def selected_options(self) -> Iterable[T]: # type: ignore
        return self._primary_hooks["selected_options"].value # type: ignore
    
    @selected_options.setter
    def selected_options(self, selected_options: Iterable[T]) -> None:
        self.change_selected_options(selected_options)
    
    def change_selected_options(self, selected_options: Iterable[T]) -> None:
        """Set the selected options (automatically converted to set by nexus system)."""
        # Let nexus system handle immutability conversion
        success, msg = self._submit_value("selected_options", set(selected_options))
        if not success:
            raise SubmissionError(msg, selected_options)

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

    def change_selected_options_and_available_options(self, selected_options: Iterable[T], available_options: Iterable[T]) -> None:
        """
        Set both the selected options and available options atomically.
        
        Args:
            selected_options: The new selected options (set automatically converted)
            available_options: The new set of available options (set automatically converted)
        """
        # Let nexus system handle immutability conversion
        success, msg = self._submit_values({"selected_options": set(selected_options), "available_options": set(available_options)})
        if not success: 
            raise ValueError(msg)

    def add_available_option(self, option: T) -> None:
        """Add an option to the available options set."""
        success, msg = self._submit_value("available_options", set(self._primary_hooks["available_options"].value) | {option})
        if not success:
            raise ValueError(msg)

    def add_available_options(self, options: Iterable[T]) -> None:
        """Add an option to the available options set."""
        success, msg = self._submit_value("available_options", set(self._primary_hooks["available_options"].value) | set(options))
        if not success:
            raise ValueError(msg)

    def remove_available_option(self, option: T) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_value("available_options", set(self._primary_hooks["available_options"].value) - {option})
        if not success:
            raise ValueError(msg)

    def remove_available_options(self, option: Iterable[T]) -> None:
        """Remove an option from the available options set."""
        success, msg = self._submit_value("available_options", set(self._primary_hooks["available_options"].value) - set(option))
        if not success:
            raise ValueError(msg)

    def clear_available_options(self) -> None:
        """Remove all items from the available options set."""
        success, msg = self._submit_value("available_options", set()) # type: ignore
        if not success:
            raise ValueError(msg)

    def add_selected_option(self, option: T) -> None:
        """Add an option to the selected options set."""
        success, msg = self._submit_value("selected_options", set(self._primary_hooks["selected_options"].value) | {option})
        if not success:
            raise ValueError(msg)

    def add_selected_options(self, options: Iterable[T]) -> None:
        """Add an option to the selected options set."""
        success, msg = self._submit_value("selected_options", set(self._primary_hooks["selected_options"].value) | set(options))
        if not success:
            raise ValueError(msg)

    def remove_selected_option(self, option: T) -> None:
        """Remove an option from the selected options set."""
        success, msg = self._submit_value("selected_options", set(self._primary_hooks["selected_options"].value) - {option})
        if not success:
            raise ValueError(msg)

    def remove_selected_options(self, option: Iterable[T]) -> None:
        """Remove an option from the selected options set."""
        success, msg = self._submit_value("selected_options", set(self._primary_hooks["selected_options"].value) - set(option))
        if not success:
            raise ValueError(msg)

    def clear_selected_options(self) -> None:
        """Remove all items from the selected options set."""
        success, msg = self._submit_value("selected_options", set())
        if not success:
            raise ValueError(msg)

    def __str__(self) -> str:
        sorted_selected = sorted(self.selected_options) # type: ignore
        sorted_available = sorted(self.available_options) # type: ignore
        return f"OMSO(selected_options={sorted_selected}, available_options={sorted_available})"
    
    def __repr__(self) -> str:
        sorted_selected = sorted(self.selected_options) # type: ignore
        sorted_available = sorted(self.available_options) # type: ignore
        return f"OMSO(selected_options={sorted_selected}, available_options={sorted_available})"