from typing import Generic, TypeVar
from .hook_like import HookLike 
from .._utils.base_listening import BaseListeningLike

T = TypeVar("T")

class FloatingHookLike(HookLike[T], BaseListeningLike, Generic[T]):
    """
    A floating hook that can be used to store a value that is not owned by any observable.
    """