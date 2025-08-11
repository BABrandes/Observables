from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Generic, Literal, Optional, TypeVar
from .._utils._internal_binding_handler import InternalBindingHandler, SyncMode
from .._utils._listening_base import ListeningBase
from .._utils._carries_bindable_single_value import CarriesBindableSingleValue
from .._utils._carries_bindable_set import CarriesBindableSet

T = TypeVar("T")

class ObservableSelectionOption(ListeningBase, CarriesBindableSingleValue[T], CarriesBindableSet[T], Generic[T]):

    def __init__(self, options: set[T], selected_option: T):
        super().__init__()  # Initialize ListeningBase
        
        self._options: set[T] = options
        self._selected_option: T = selected_option

        self._options_binding_handler: InternalBindingHandler[set[T]] = InternalBindingHandler(self, self._get_set, self._set_set, self._check_set)
        self._selected_option_binding_handler: InternalBindingHandler[T] = InternalBindingHandler(self, self._get_single_value, self._set_single_value, self._check_single_value)

    @property
    def options(self) -> set[T]:
        return self._options
    
    @property
    def selected_option(self) -> T:
        return self._selected_option
    
    def _get_set(self) -> set[T]:
        return self._options
    
    def _get_single_value(self) -> T:
        return self._selected_option
    
    def _set_set(self, value: set[T]) -> None:
        self.change_options(value)
    
    def _set_single_value(self, value: T) -> None:
        self.change_selected_option(value)
    
    def _get_single_value_binding_handler(self) -> InternalBindingHandler[T]:
        return self._selected_option_binding_handler
    
    def _get_set_binding_handler(self) -> InternalBindingHandler[set[T]]:
        return self._options_binding_handler
    
    def _check_set(self, set_to_check: set[T]) -> bool:
        return self._selected_option in set_to_check
    
    def _check_single_value(self, single_value_to_check: T) -> bool:
        return single_value_to_check in self._options
    
    def set_options_and_selected_option(self, options: set[T], selected_option: T) -> None:

        if selected_option not in options:
            raise ValueError(f"Selected option {selected_option} not in options {options}")
        
        if options == self._options and selected_option == self._selected_option:
            return
        
        self._options = options
        self._selected_option = selected_option
        self._options_binding_handler.notify_bindings(options)
        self._selected_option_binding_handler.notify_bindings(selected_option)

        self._notify_listeners()
    
    def change_options(self, options: set[T]) -> None:
        if options == self._options:
            return
        
        self.raise_if_selected_option_not_in_options(self._selected_option, options)

        self._options = options
        self._options_binding_handler.notify_bindings(options)
        self._notify_listeners()

    def change_selected_option(self, selected_option: T) -> None:
        if selected_option == self._selected_option:
            return

        self.raise_if_selected_option_not_in_options(selected_option, self._options)

        self._selected_option = selected_option
        self._selected_option_binding_handler.notify_bindings(selected_option)
        self._notify_listeners()

    def raise_if_selected_option_not_in_options(self, selected_option: T, options: set[T]) -> None:
        if selected_option not in options:
            raise ValueError(f"Selected option {selected_option} not in options {options}")

    def bind_selected_option_to_observable(self, observable: CarriesBindableSingleValue[T], initial_sync_mode: SyncMode = SyncMode.UPDATE_VALUE_FROM_OBSERVABLE) -> None:
        if observable is None:
            raise ValueError("Observable is None")
        self._selected_option_binding_handler.establish_binding(observable._get_single_value_binding_handler(), initial_sync_mode)

    def bind_options_to_observable(self, observable: CarriesBindableSet[T], initial_sync_mode: SyncMode = SyncMode.UPDATE_VALUE_FROM_OBSERVABLE) -> None:        
        if observable is None:
            raise ValueError("Observable is None")
        self._options_binding_handler.establish_binding(observable._get_set_binding_handler(), initial_sync_mode)

    def unbind_selected_option_from_observable(self, observable: CarriesBindableSingleValue[T]) -> None:
        self._selected_option_binding_handler.remove_binding(observable._get_single_value_binding_handler())

    def unbind_options_from_observable(self, observable: CarriesBindableSet[T]) -> None:
        self._options_binding_handler.remove_binding(observable._get_set_binding_handler())

    def check_binding_system_consistency(self) -> tuple[bool, str]:
        binding_state_consistent, binding_state_consistent_message = self._selected_option_binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        binding_state_consistent, binding_state_consistent_message = self._options_binding_handler.check_binding_state_consistency()
        if not binding_state_consistent:
            return False, binding_state_consistent_message
        values_synced, values_synced_message = self._selected_option_binding_handler.check_values_synced()
        if not values_synced:
            return False, values_synced_message
        values_synced, values_synced_message = self._options_binding_handler.check_values_synced()
        if not values_synced:
            return False, values_synced_message
        return True, "Binding system is consistent"
    
    def __str__(self) -> str:
        return f"OSO(options={self._options}, selected={self._selected_option})"
    
    def __repr__(self) -> str:
        return f"ObservableSelectionOption({self._options}, {self._selected_option})"
    
    def __len__(self) -> int:
        return len(self._options)
    
    def __contains__(self, item: T) -> bool:
        return item in self._options
    
    def __iter__(self):
        """Iterate over the options"""
        return iter(self._options)
    
    def __eq__(self, other) -> bool:
        """Compare with another selection option or observable"""
        if isinstance(other, ObservableSelectionOption):
            return (self._options == other._options and 
                   self._selected_option == other._selected_option)
        return False
    
    def __ne__(self, other) -> bool:
        """Compare with another selection option or observable"""
        return not (self == other)
    
    def __hash__(self) -> int:
        """Hash based on the current options and selected option"""
        return hash((frozenset(self._options), self._selected_option))
    
    def __bool__(self) -> bool:
        """Boolean conversion based on selected option"""
        return bool(self._selected_option)