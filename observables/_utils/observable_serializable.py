from typing import Any, Mapping, Optional, Generic, Callable
import weakref
from typing_extensions import final
from logging import Logger
from typing_extensions import TypeVar
from .carries_hooks_like import CarriesHooksLike


HK = TypeVar("HK")
O = TypeVar("O", bound="CarriesHooksLike[Any, Any]", covariant=True)

class ObservableSerializable(Generic[HK, O]):
    """
    A protocol for serializable observables.
    """

    def __init__(
        self,
        get_primary_value_references_callback: Callable[[O], Mapping[HK, Any]],
        ) -> None:
        """
        Initialize the ObservableSerializable.
        """
        self._get_primary_value_references_callback = get_primary_value_references_callback

    def get_primary_value_references_for_serialization(self) -> Mapping[HK, Any]:
        """
        Get the values of the primary component hooks as references, usefull for serializing the observable.
        """

        self_ref: O = weakref.ref(self)() # type: ignore

        return self._get_primary_value_references_callback(self_ref)
    
    @classmethod
    @final  
    def create_from_values(
        cls,
        values: Mapping[HK, Any],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> "O":
        """
        Create an BaseObservable instance from a mapping of initial values.

        This is a factory method for creating an instance of the class, useful for serializing and deserializing.
        """
        instance: O = cls.__new__(cls) # type: ignore
        instance.submit_values(values, logger=logger, **kwargs)
        return instance