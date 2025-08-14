from typing import Generic, Optional, TypeVar
from typing import Callable
from .hook import Hook
from .observable import Observable
from .hook import SyncMode

T = TypeVar("T")

class IndexableHookManager(Generic[T]):
    """
    Manager for indexable hooks.
    """

    def __init__(
            self,
            owner: Observable,
            identifier_string: str,
            initial_number_of_hooks: int,
            get_by_index: Callable[[int], T],
            set_by_index: Callable[[int, T], None]):

        self._owner: Observable = owner
        self._identifier_string: str = identifier_string

        self._get_by_index: Callable[[int], T] = get_by_index
        self._set_by_index: Callable[[int, T], None] = set_by_index

        for index in range(initial_number_of_hooks):
            self.create_and_place_managed_hook(index)

    def get_hook(self, index: int) -> Hook[T]:
        if f"{self._identifier_string}_{index}" not in self._owner._component_hooks:
            raise ValueError(f"Hook at index {index} does not exist")
        return self._owner._component_hooks[f"{self._identifier_string}_{index}"]

    def create_and_place_managed_hook(self, index: Optional[int]) -> None:
        """
        Create a hook and place it in the component hooks of the owner.

        Args:
            index: The index of the hook to create. If None, the hook will be created at the next available index.

        Returns:
            The created hook.
        """

        new_hook: Hook[T] = Hook(
            self._owner,
            lambda idx=index: self._get_by_index(idx),
            lambda value, idx=index: self._set_by_index(idx, value)
        )

        hook_key = f"{self._identifier_string}_{index}"
        if hook_key in self._owner._component_hooks:
            raise ValueError(f"Hook at index {index} already exists")
        self._owner._component_hooks[hook_key] = new_hook
    
    @property
    def managed_hooks(self) -> list[Hook[T]]:
        """
        Get the list of managed hooks.
        """
        managed = []
        for key in self._owner._component_hooks.keys():
            if key.startswith(f"{self._identifier_string}_"):
                managed.append(self._owner._component_hooks[key])
        return managed
    
    def check_hook_removable(self, index: int) -> bool:
        """
        Check if the hook at the given index is removable, meaning it is not bound to any other observable.
        """
        return not any(hook.is_bound_to(self.get_hook(index)) for hook in self.managed_hooks)

    def remove_hook(self, index: int) -> None:
        """
        Remove the hook at the given index.
        """
        if self.check_hook_removable(index):
            self._owner._component_hooks.pop(f"{self._identifier_string}_{index}")
        else:
            raise ValueError(f"Hook at index {index} is not removable")
        
    def remove_hook_from_hook(self, index_of_managed_hook: int, hook_to_remove: Hook[T]) -> None:
        """
        Remove the hook from the managed hook at the given index.
        """
        self.get_hook(index_of_managed_hook).remove_binding(hook_to_remove)

    def add_hook_to_hook(self, index_of_managed_hook: int, hook_to_connect: Hook[T], initial_sync_mode: SyncMode) -> None:
        """
        Connect the hook to the managed hook at the given index.
        """
        self.get_hook(index_of_managed_hook).establish_binding(hook_to_connect, initial_sync_mode)