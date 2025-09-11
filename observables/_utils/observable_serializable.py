from typing import Any, Mapping, Optional, Generic
from typing_extensions import final
from logging import Logger
from typing_extensions import TypeVar
from abc import ABC, abstractmethod


HK = TypeVar("HK")
Obs = TypeVar("Obs", bound="ObservableSerializable[Any, Any]", covariant=True)

class ObservableSerializable(ABC, Generic[HK, Obs]):
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
        values: Mapping[HK, Any],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> "Obs":
        """
        Create an BaseObservable instance from a mapping of initial values.

        This is a factory method for creating an instance of the class, useful for serializing and deserializing.
        """
        instance: Obs = cls.__new__(cls) # type: ignore
        instance._internal_construct_from_values(values, logger, **kwargs)
        return instance
    
    @abstractmethod
    def _get_primary_values_as_references(self) -> Mapping[HK, Any]:
        """
        Get the values of the primary component hooks as references, usefull for serializing the observable.

        This method is used for serializing the observable.

        ** The returned values are references, so modifying them will modify the observable.
        Use with caution.
        """
        raise NotImplementedError("Subclasses must implement this method")