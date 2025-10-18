from .nexus_manager import NexusManager
from .has_nexus_manager_protocol import HasNexusManagerProtocol

class HasNexusManager(HasNexusManagerProtocol):

    def __init__(self, nexus_manager: NexusManager):
        self._nexus_manager = nexus_manager

    @property
    def nexus_manager(self) -> NexusManager:
        return self._nexus_manager