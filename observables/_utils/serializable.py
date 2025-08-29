from typing import Any, Mapping, Optional, Generic
from typing_extensions import final
from logging import Logger
from typing_extensions import TypeVar
from abc import ABC, abstractmethod


HK = TypeVar("HK")
Obs = TypeVar("Obs", bound="Serializable[Any, Any]", covariant=True)

class Serializable(ABC, Generic[HK, Obs]):
    """
    A protocol for serializable observables.
    """

    @abstractmethod
    def _internal_construct_from_values(
        self,
        initial_values: Mapping[HK, Any],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """
        Construct an Observable instance.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    @final  
    def create_from_values(
        cls,
        initial_values: Mapping[HK, Any],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> "Obs":
        """
        Create an BaseObservable instance from a mapping of initial values.

        This is a factory method for creating an instance of the class, useful for serializing and deserializing.
        """
        instance: Obs = cls.__new__(cls) # type: ignore
        instance._internal_construct_from_values(initial_values, logger, **kwargs)
        return instance
    
    @abstractmethod
    def get_values_as_references(self) -> Mapping[HK, Any]:
        """
        Get the values of the observable as references, usefull for serializing the observable.

        This method is used for serializing the observable.

        ** The returned values are references, so modifying them will modify the observable.
        Use with caution.
        """
        raise NotImplementedError("Subclasses must implement this method")