from typing import Literal, TypeVar, Generic, Optional, Mapping, Any
from .observable_transfer import ObservableTransfer, HookLike
from logging import Logger

K = TypeVar("K")
V = TypeVar("V")

class ObservableTransferDict(ObservableTransfer[Literal["dict", "key"], Literal["value"]], Generic[K, V]):

    def __init__(
        self,
        dict_hook: HookLike[dict[K, V]],
        key_hook: HookLike[K],
        value_hook: HookLike[V],
        logger: Optional[Logger] = None):

        def forward_callable() -> Mapping[Literal["value"], V]:
            dict_value: dict[K, V] = self._input_hooks["dict"].value
            key_value: K = self._input_hooks["key"].value
            value_value: V = dict_value[key_value]
            return {"value": value_value}

        def reverse_callable() -> Mapping[Literal["dict", "key"], Any]:
            dict_value: dict[K, V] = self._input_hooks["dict"].value
            key_value: K = self._input_hooks["key"].value
            value_value: V = self._output_hooks["value"].value
            dict_value[key_value] = value_value
            return {"dict": dict_value, "key": key_value}
        
        super().__init__(
            input_trigger_hooks={"dict": dict_hook, "key": key_hook},
            output_trigger_hooks={"value": value_hook},
            forward_callable=lambda _: forward_callable(),
            reverse_callable=lambda _: reverse_callable(),
            logger=logger
        )

class ObservableTransferOptionalDict(ObservableTransfer[Literal["dict", "key"], Literal["value"]], Generic[K, V]):

    def __init__(
        self,
        dict_hook: HookLike[dict[K, V]],
        key_hook: HookLike[Optional[K]],
        value_hook: HookLike[Optional[V]],
        logger: Optional[Logger] = None):

        def forward_callable() -> Mapping[Literal["value"], Optional[V]]:
            dict_value: dict[K, V] = self._input_hooks["dict"].value
            key_value: Optional[K] = self._input_hooks["key"].value
            if key_value is None:
                return {"value": None}
            else:
                value_value: V = dict_value[key_value]
                return {"value": value_value}

        def reverse_callable() -> Mapping[Literal["dict", "key"], Any]:
            dict_value: dict[K, V] = self._input_hooks["dict"].value
            key_value: Optional[K] = self._input_hooks["key"].value
            value_value: Optional[V] = self._output_hooks["value"].value
            if key_value is None:
                if value_value is None:
                    return {"dict": dict_value, "key": None}
                else:
                    raise ValueError(f"When the key is None, the value must be None as well, but it is '{value_value}'")
            else:
                return {"dict": {**dict_value, key_value: value_value}, "key": key_value}
        
        super().__init__(
            input_trigger_hooks={"dict": dict_hook, "key": key_hook},
            output_trigger_hooks={"value": value_hook},
            forward_callable=lambda _: forward_callable(),
            reverse_callable=lambda _: reverse_callable(),
            logger=logger
        )