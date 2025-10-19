from typing import TypeVar, Generic, Optional, Literal, Mapping
from enum import Enum
from logging import Logger

from .observable_selection_option import ObservableSelectionOption, ObservableOptionalSelectionOption
from ..._hooks.hook_aliases import Hook, ReadOnlyHook
from ..._carries_hooks.observable_serializable import ObservableSerializable

E = TypeVar("E", bound=Enum)

class ObservableSelectionEnum(ObservableSelectionOption[E], ObservableSerializable[Literal["enum_value", "enum_options"], E|frozenset[E]], Generic[E]):
    """
    An observable that manages a selection from a set of enum options.
    """

    def __init__(self, enum_value: E, enum_options: Optional[frozenset[E]] | Hook[frozenset[E]]|ReadOnlyHook[frozenset[E]] = None, logger: Optional[Logger] = None) -> None:
        """
        Initialize the ObservableSelectionEnum.

        Args:
            enum_value: The initial enum value
            enum_options: The initial enum options or hook for the enum options. If None, all enum options are used (inferred from the enum value)
            logger: The logger to use
        """

        if enum_options is None:
            enum_options = frozenset(enum_value.__class__)

        super().__init__(enum_value, enum_options, logger=logger)

    #### ObservableSerializable implementation ####

    def get_value_references_for_serialization(self) -> Mapping[Literal["enum_value", "enum_options"], E|frozenset[E]]:
        return {"enum_value": self.selected_option, "enum_options": self.available_options}

    def set_value_references_from_serialization(self, values: Mapping[Literal["enum_value", "enum_options"], E|frozenset[E]]) -> None:
        enum_value: E = values["enum_value"] # type: ignore
        enum_options: frozenset[E] = values["enum_options"] # type: ignore
        self.submit_values({"selected_option": enum_value, "available_options": enum_options})

class ObservableOptionalSelectionEnum(ObservableOptionalSelectionOption[E], ObservableSerializable[Literal["enum_value", "enum_options"], Optional[E]|frozenset[E]], Generic[E]):
    """
    An observable that manages a selection from a set of enum options.
    """

    def __init__(self, enum_value: Optional[E], enum_options: Optional[frozenset[E]] | Hook[frozenset[E]] | ReadOnlyHook[frozenset[E]] = None, logger: Optional[Logger] = None) -> None:
        """
        Initialize the ObservableOptionalSelectionEnum.
        """

        if enum_options is None:
            if enum_value is None:
                raise ValueError("enum_options is required when enum_value is None")
            enum_options = frozenset(enum_value.__class__)

        super().__init__(enum_value, enum_options, logger=logger)

    #### ObservableSerializable implementation ####

    def get_value_references_for_serialization(self) -> Mapping[Literal["enum_value", "enum_options"], Optional[E]|frozenset[E]]:
        return {"enum_value": self.selected_option, "enum_options": self.available_options}

    def set_value_references_from_serialization(self, values: Mapping[Literal["enum_value", "enum_options"], Optional[E]|frozenset[E]]) -> None:
        enum_value: Optional[E] = values["enum_value"] # type: ignore
        enum_options: frozenset[E] = values["enum_options"] # type: ignore
        self.submit_values({"selected_option": enum_value, "available_options": enum_options})