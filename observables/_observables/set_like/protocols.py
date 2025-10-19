from typing import Any, TypeVar, Protocol, runtime_checkable, Optional, AbstractSet
from collections.abc import Iterable
from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._carries_hooks.carries_hooks_protocol import CarriesHooksProtocol

T = TypeVar("T")

@runtime_checkable
class ObservableSetProtocol(CarriesHooksProtocol[Any, Any], Protocol[T]):
    """
    Protocol for observable set objects.
    
    Note:
        Internally stores values as frozenset for immutability.
    """

    #-------------------------------- set value --------------------------------
    
    @property
    def value_hook(self) -> Hook[AbstractSet[T]]:
        """
        Get the hook for the set (contains AbstractSet).
        """
        ...

    @property
    def value(self) -> AbstractSet[T]:
        """
        Get the set as immutable AbstractSet.
        """
        ...
    
    @value.setter
    def value(self, value: Iterable[T]) -> None:
        """
        Set the set value (accepts any iterable, stores as frozenset).
        """
        ...

    def change_value(self, value: Iterable[T]) -> None:
        """
        Change the set value (lambda-friendly method).
        """
        ...

    #-------------------------------- length --------------------------------
    
    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the set length.
        """
        ...

    @property
    def length(self) -> int:
        """
        Get the current length of the set.
        """
        ...

@runtime_checkable
class ObservableSelectionOptionsProtocol(Protocol[T]):

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> Hook[AbstractSet[T]]:
        ...

    @property
    def available_options(self) -> AbstractSet[T]:
        ...
    
    @available_options.setter
    def available_options(self, available_options: Iterable[T]) -> None:
        ...

    def change_available_options(self, available_options: Iterable[T]) -> None:
        ...

    #-------------------------------- selected options --------------------------------

    @property
    def selected_option_hook(self) -> Hook[T]:
        ...

    @property
    def selected_option(self) -> T:
        ...
    
    @selected_option.setter
    def selected_option(self, selected_option: T) -> None:
        ...

    def change_selected_option(self, selected_option: T) -> None:
        ...

    #-------------------------------- length --------------------------------
    
    @property
    def number_of_available_options_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the set length.
        """
        ...

    @property
    def number_of_available_options(self) -> int:
        """
        Get the current length of the set.
        """
        ...

    #-------------------------------- convenience methods --------------------------------

    def change_selected_option_and_available_options(self, selected_option: T, available_options: Iterable[T]) -> None:
        ...

@runtime_checkable
class ObservableOptionalSelectionOptionProtocol(Protocol[T]):

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> Hook[AbstractSet[T]]:
        ...

    @property
    def available_options(self) -> AbstractSet[T]:
        ...
    
    @available_options.setter
    def available_options(self, available_options: Iterable[T]) -> None:
        ...

    def change_available_options(self, available_options: Iterable[T]) -> None:
        ...

    #-------------------------------- selected options --------------------------------

    @property
    def selected_option_hook(self) -> Hook[Optional[T]]:
        ...

    @property
    def selected_option(self) -> Optional[T]:
        ...
    
    @selected_option.setter
    def selected_option(self, selected_option: Optional[T]) -> None:
        ...

    def change_selected_option(self, selected_option: Optional[T]) -> None:
        ...

    #-------------------------------- length --------------------------------
    
    @property
    def number_of_available_options_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the set length.
        """
        ...

    @property
    def number_of_available_options(self) -> int:
        """
        Get the current length of the set.
        """
        ...

    #-------------------------------- convenience methods --------------------------------

    def change_selected_option_and_available_options(self, selected_option: Optional[T], available_options: Iterable[T]) -> None:
        ...

@runtime_checkable
class ObservableMultiSelectionOptionsProtocol(Protocol[T]):

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> Hook[AbstractSet[T]]:
        ...

    @property
    def available_options(self) -> AbstractSet[T]:
        ...
    
    @available_options.setter
    def available_options(self, available_options: Iterable[T]) -> None:
        ...

    def change_available_options(self, available_options: Iterable[T]) -> None:
        ...

    #-------------------------------- selected options --------------------------------

    @property
    def selected_options_hook(self) -> Hook[AbstractSet[T]]:
        ...

    @property
    def selected_options(self) -> AbstractSet[T]:
        ...
    
    @selected_options.setter
    def selected_options(self, selected_options: AbstractSet[T]) -> None:
        ...

    def change_selected_options(self, selected_options: AbstractSet[T]) -> None:
        ...

    #-------------------------------- length --------------------------------

    @property
    def number_of_available_options_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the number of available options.
        """
        ...

    @property
    def number_of_available_options(self) -> int:
        """
        Get the current number of available options.
        """
        ...
    
    @property
    def number_of_selected_options_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the number of selected options.
        """
        ...

    @property
    def number_of_selected_options(self) -> int:
        """
        Get the current number of selected options.
        """
        ...

    #-------------------------------- Convenience methods --------------------------------

    def change_selected_options_and_available_options(self, selected_options: AbstractSet[T], available_options: Iterable[T]) -> None:
        ...

    def clear_selected_options(self) -> None:
        ...
