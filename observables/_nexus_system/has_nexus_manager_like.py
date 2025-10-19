from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .nexus_manager import NexusManager

class HasNexusManagerProtocol(Protocol):

    @property
    def nexus_manager(self) -> "NexusManager":
        ...