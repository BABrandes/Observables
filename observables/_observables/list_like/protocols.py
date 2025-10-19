from typing import TypeVar, Protocol, runtime_checkable, Iterable, Sequence

from ..._hooks.hook_aliases import Hook, ReadOnlyHook


T = TypeVar("T")

@runtime_checkable
class ObservableListProtocol(Protocol[T]):

    #-------------------------------- list value --------------------------------

    @property
    def value_hook(self) -> Hook[Sequence[T]]:
        """
        Get the hook for the list (contains Sequence).
        """
        ...

    @property
    def value(self) -> list[T]:
        """
        Get the list value as mutable list (copied from the hook).
        """
        ...
    
    @value.setter
    def value(self, value: Iterable[T]) -> None:
        """
        Set the list value (accepts any iterable, stores as tuple).
        """
        ...

    def change_value(self, new_value: Iterable[T]) -> None:
        """
        Change the list value (lambda-friendly method).
        """
        ...

    #-------------------------------- length --------------------------------

    @property
    def length(self) -> int:
        """
        Get the current length of the list.
        """
        ...

    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the list length.
        """
        ...