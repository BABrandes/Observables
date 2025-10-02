from typing import TypeVar, Generic, Optional
from enum import Enum
from logging import Logger

from .._other_observables.observable_selection_option import ObservableSelectionOption, ObservableOptionalSelectionOption
from .._hooks.hook_like import HookLike


E = TypeVar("E", bound=Enum)

class ObservableSelectionEnum(ObservableSelectionOption[E], Generic[E]):
    """
    An observable that manages a selection from a set of enum options.
    """

    def __init__(self, enum_value: E, enum_options: Optional[set[E]] | HookLike[set[E]] = None, logger: Optional[Logger] = None) -> None:
        """
        Initialize the ObservableSelectionEnum.

        Args:
            enum_value: The initial enum value
            enum_options: The initial enum options or hook for the enum options. If None, all enum options are used (inferred from the enum value)
            logger: The logger to use
        """

        if enum_options is None:
            enum_options = set(enum_value.__class__)

        super().__init__(enum_value, enum_options, logger=logger)

class ObservableOptionalSelectionEnum(ObservableOptionalSelectionOption[E], Generic[E]):
    """
    An observable that manages a selection from a set of enum options.
    """

    def __init__(self, enum_value: Optional[E], enum_options: Optional[set[E]] | HookLike[set[E]] = None, logger: Optional[Logger] = None) -> None:
        """
        Initialize the ObservableOptionalSelectionEnum.
        """

        if enum_options is None:
            if enum_value is None:
                raise ValueError("enum_options is required when enum_value is None")
            enum_options = set(enum_value.__class__)

        super().__init__(enum_value, enum_options, logger=logger)