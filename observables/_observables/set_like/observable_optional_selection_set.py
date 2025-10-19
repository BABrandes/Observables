from typing import Generic, TypeVar, Optional, overload, Literal, AbstractSet, Mapping, Any
from collections.abc import Iterable
from logging import Logger

from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._hooks.hook_protocols.managed_hook import ManagedHookProtocol
from ..._carries_hooks.complex_observable_base import ComplexObservableBase
from .protocols import ObservableOptionalSelectionOptionProtocol

T = TypeVar("T")

class ObservableOptionalSelectionSet(ComplexObservableBase[Literal["selected_option", "available_options"], Literal["number_of_available_options"], Optional[T] | frozenset[T], int, "ObservableOptionalSelectionSet"], ObservableOptionalSelectionOptionProtocol[T], Generic[T]):

    @overload
    def __init__(self, selected_option: Hook[Optional[T]] | ReadOnlyHook[Optional[T]], available_options: Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]], *, logger: Optional[Logger] = None) -> None:
        ...

    @overload
    def __init__(self, selected_option: Optional[T], available_options: Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]], *, logger: Optional[Logger] = None) -> None:
        ...

    @overload
    def __init__(self, selected_option: Hook[Optional[T]] | ReadOnlyHook[Optional[T]], available_options: Iterable[T], *, logger: Optional[Logger] = None) -> None:
        ...

    @overload
    def __init__(self, observable: ObservableOptionalSelectionOptionProtocol[T], available_options: None=None, *, logger: Optional[Logger] = None) -> None:
        ...
    
    @overload
    def __init__(self, selected_option: Optional[T], available_options: Iterable[T], *, logger: Optional[Logger] = None) -> None:
        ...

    def __init__(self, selected_option: Optional[T] | Hook[Optional[T]] | ReadOnlyHook[Optional[T]] | ObservableOptionalSelectionOptionProtocol[T], available_options: Iterable[T] | Hook[frozenset[T]] | ReadOnlyHook[frozenset[T]] | None = None, *, logger: Optional[Logger] = None) -> None: # type: ignore
        
        if isinstance(selected_option, ObservableOptionalSelectionOptionProtocol):
            initial_selected_option: Optional[T] = selected_option.selected_option # type: ignore
            initial_available_options: frozenset[T] = selected_option.available_options # type: ignore
            hook_selected_option: Optional[Hook[Optional[T]]] = selected_option.selected_option_hook # type: ignore
            hook_available_options: Optional[Hook[frozenset[T]]] = selected_option.available_options_hook # type: ignore

        else:
            if selected_option is None:
                initial_selected_option: Optional[T] = None
                hook_selected_option: Optional[ManagedHookProtocol[Optional[T]]] = None
            
            elif isinstance(selected_option, ManagedHookProtocol):
                initial_selected_option = selected_option.value # type: ignore
                hook_selected_option = selected_option # type: ignore

            else:
                # selected_option is a T (or None)
                initial_selected_option = selected_option # type: ignore
                hook_selected_option = None

            if available_options is None:
                initial_available_options = frozenset()
                hook_available_options = None

            elif isinstance(available_options, ManagedHookProtocol):
                initial_available_options = available_options.value # type: ignore
                hook_available_options = available_options # type: ignore

            else:
                # available_options is an Iterable[T]
                initial_available_options = frozenset(available_options) # type: ignore
                hook_available_options = None
                
        def is_valid_value(x: Mapping[Literal["selected_option", "available_options"], Any]) -> tuple[bool, str]:
            if "selected_option" in x:
                selected_option: Optional[T] = x["selected_option"]
            else:
                selected_option = self._primary_hooks["selected_option"].value # type: ignore
                
            if "available_options" in x:
                available_options: frozenset[T] = x["available_options"] # type: ignore
            else:
                _available_options = self._primary_hooks["available_options"].value
                if isinstance(_available_options, frozenset):
                    available_options: frozenset[T] = _available_options # type: ignore
                else:
                    raise ValueError("Available options is not a frozenset")

            if selected_option is None:
                return True, "Verification method passed"
            elif selected_option in available_options:
                return True, "Verification method passed"
            else:
                return False, f"Selected option {selected_option} not in options {available_options}"

        super().__init__(
            initial_hook_values={"selected_option": initial_selected_option, "available_options": initial_available_options}, # type: ignore
            verification_method=is_valid_value,
            secondary_hook_callbacks={"number_of_available_options": lambda x: len(x["available_options"])}, # type: ignore
            logger=logger
        )

        if hook_selected_option is not None:
            self._link(hook_selected_option, "selected_option", "use_target_value") # type: ignore
        if hook_available_options is not None:
            self._link(hook_available_options, "available_options", "use_target_value") # type: ignore

    #########################################################
    # ObservableSelectionOptionsProtocol implementation
    #########################################################

    #-------------------------------- available options --------------------------------

    @property
    def available_options_hook(self) -> Hook[AbstractSet[T]]:
        return self._primary_hooks["available_options"] # type: ignore
    
    @property
    def available_options(self) -> AbstractSet[T]:
        return self._primary_hooks["available_options"].value # type: ignore

    @available_options.setter
    def available_options(self, available_options: Iterable[T]) -> None:
        success, msg = self._submit_values({"available_options": frozenset(available_options)})
        if not success:
            raise ValueError(msg)

    def change_available_options(self, available_options: Iterable[T]) -> None:
        if available_options == self._primary_hooks["available_options"].value:
            return
        
        success, msg = self._submit_values({"available_options": frozenset(available_options)})
        if not success:
            raise ValueError(msg)

    #-------------------------------- selected option --------------------------------
    
    @property
    def selected_option_hook(self) -> Hook[Optional[T]]:
        return self._primary_hooks["selected_option"] # type: ignore
    
    @property
    def selected_option(self) -> Optional[T]:
        return self._primary_hooks["selected_option"].value # type: ignore
    
    @selected_option.setter
    def selected_option(self, selected_option: Optional[T]) -> None:
        if selected_option == self._primary_hooks["selected_option"].value:
            return
        
        success, msg = self._submit_values({"selected_option": selected_option})
        if not success:
            raise ValueError(msg)   
    
    def change_selected_option(self, selected_option: Optional[T]) -> None:
        if selected_option == self._primary_hooks["selected_option"].value:
            return
        
        success, msg = self._submit_values({"selected_option": selected_option})
        if not success:
            raise ValueError(msg)

    #-------------------------------- change selected option and available options --------------------------------
    
    def change_selected_option_and_available_options(self, selected_option: Optional[T], available_options: Iterable[T]) -> None:
        if selected_option == self._primary_hooks["selected_option"].value and available_options == self._primary_hooks["available_options"].value:
            return
        
        success, msg = self._submit_values({"selected_option": selected_option, "available_options": frozenset(available_options)})
        if not success:
            raise ValueError(msg)

    #-------------------------------- length --------------------------------
    
    @property
    def number_of_available_options_hook(self) -> ReadOnlyHook[int]:
        return self._secondary_hooks["number_of_available_options"] # type: ignore

    @property
    def number_of_available_options(self) -> int:
        return len(self._primary_hooks["available_options"].value) # type: ignore