from .nexus_manager import NexusManager
from .has_nexus_manager_like import HasNexusManagerLike

class HasNexusManager(HasNexusManagerLike):

    def __init__(self, nexus_manager: NexusManager):
        self._nexus_manager = nexus_manager

    @property
    def nexus_manager(self) -> NexusManager:
        return self._nexus_manager