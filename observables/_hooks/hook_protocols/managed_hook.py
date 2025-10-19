from typing import Protocol, TypeVar, runtime_checkable

from ..mixin_protocols.hook_with_connection_protocol import HookWithConnectionProtocol
from ..mixin_protocols.hook_with_getter_protocol import HookWithGetterProtocol

T = TypeVar("T")

@runtime_checkable
class ManagedHookProtocol(HookWithConnectionProtocol[T], HookWithGetterProtocol[T], Protocol[T]):
    """
    Protocol for managed hook objects.
    """