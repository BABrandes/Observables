from typing import TypeVar, Protocol, runtime_checkable, Iterable

from ..._hooks.hook_aliases import Hook, ReadOnlyHook


T = TypeVar("T")

@runtime_checkable
class ObservableListProtocol(Protocol[T]):

    #-------------------------------- list value --------------------------------

    @property
    def list_hook(self) -> Hook[tuple[T, ...]]:
        """
        Get the hook for the list (contains tuple).
        """
        ...

    @property
    def list_value(self) -> tuple[T, ...]:
        """
        Get the list value as immutable tuple.
        """
        ...
    
    @list_value.setter
    def list_value(self, new_list: Iterable[T]) -> None:
        """
        Set the list value (accepts any iterable, stores as tuple).
        """
        ...

    def change_list(self, new_list: Iterable[T]) -> None:
        """
        Change the list value (lambda-friendly method).
        """
        ...

    #-------------------------------- length --------------------------------

    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the list length.
        """
        ...

    @property
    def length(self) -> int:
        """
        Get the current length of the list.
        """
        ...