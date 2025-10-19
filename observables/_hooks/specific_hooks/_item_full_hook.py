from typing import Any, TypeVar, Generic

from observables._hooks.hook_bases.full_hook_base import FullHookBase
from observables._nexus_system.immutable_values import convert_to_immutable_or_raise
from observables._nexus_system.immutable_values import convert_from_immutable_to_item


T = TypeVar("T")

class ItemFullHook(FullHookBase[T], Generic[T]):
    """
    A full hook that can be used to store an item.
    """

    def __init__(self, item: Any):

        super().__init__(convert_to_immutable_or_raise(item))


    def get_value(self) -> T:
        return convert_from_immutable_to_item(self.hook_nexus.value)