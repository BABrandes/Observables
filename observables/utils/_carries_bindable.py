from abc import ABC, abstractmethod

class CarriesBindable(ABC):

    @abstractmethod
    def check_binding_system_consistency(self) -> tuple[bool, str]:
        ...