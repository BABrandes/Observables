from typing import Generic, TypeVar

from .hook_with_validation_mixin import HookWithValidationMixin
from .hook_like import HookLike 
from .._utils.base_listening import BaseListeningLike

T = TypeVar("T")

class FloatingHookLike(HookWithValidationMixin[T], HookLike[T], BaseListeningLike, Generic[T]):
    """
    A floating hook that can be used to store a value that is not owned by any observable.
    """