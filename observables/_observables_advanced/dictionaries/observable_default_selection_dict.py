from typing import Literal, TypeVar, Generic, Optional, Mapping, Any, Callable
from logging import Logger

from ..._hooks.hook_aliases import Hook
from .observable_dict_base import ObservableDictBase
from .protocols import ObservableSelectionDictProtocol

K = TypeVar("K")
V = TypeVar("V")

class ObservableDefaultSelectionDict(
    ObservableDictBase[K, V, K, V], 
    ObservableSelectionDictProtocol[K, V], 
    Generic[K, V]
):
    """
    An observable that manages a selection from a dictionary with automatic default entry creation.
    
    This observable manages three components:
    - dict: The dictionary to select from
    - key: The selected key in the dictionary (must not be None)
    - value: The value at the selected key
    
    Plus three read-only secondary hooks:
    - keys: Tuple of dictionary keys
    - values: Tuple of dictionary values
    - length: Dictionary length
    
    **Default Value Behavior:**
    - The key must not be None
    - If the key is not in the dictionary, a default entry is automatically added to the dictionary for this key
    - The default value can be a constant or a callable that takes the key and returns the value: Callable[[K], V]
    - This allows creating different default values based on which key is being accessed
    - The value will always match the dictionary value at the key (after default entry creation if needed)
    
    **Architecture:**
    - Inherits from ObservableDictBase for common dict observable functionality
    - Uses ComplexObservableBase (via ObservableDictBase) for hook management
    - Integrates with NexusManager for value submission
    """

    def __init__(
        self,
        dict_hook: dict[K, V] | Hook[dict[K, V]],
        key_hook: K | Hook[K],
        value_hook: Optional[Hook[V]],
        default_value: V | Callable[[K], V],
        logger: Optional[Logger] = None
    ):
        """
        Initialize an ObservableDefaultSelectionDict.
        
        Args:
            dict_hook: The dictionary or hook containing the dictionary
            key_hook: The initial key or hook (must not be None)
            value_hook: Optional hook for the value (if None, will be derived from dict[key])
            default_value: Default value or callable to use when key is not in dict
            logger: Optional logger for debugging
        """
        # Store default_value for use in callbacks
        self._default_value: V | Callable[[K], V] = default_value
        
        # Call parent constructor
        super().__init__(dict_hook, key_hook, value_hook, logger)

    def _get_default_value(self, key: K) -> V:
        """Helper to get default value (call if callable, return if constant)."""
        if callable(self._default_value):
            return self._default_value(key)  # type: ignore
        return self._default_value  # type: ignore

    def _create_add_values_callback(self) -> Callable[
        ["ObservableDefaultSelectionDict[K, V]", Mapping[Literal["dict", "key", "value"], Any], Mapping[Literal["dict", "key", "value"], Any]], 
        Mapping[Literal["dict", "key", "value"], Any]
    ]:
        """
        Create the add_values_to_be_updated_callback for default selection logic.
        
        This callback auto-creates missing keys with default values.
        """
        def add_values_to_be_updated_callback(
            self_ref: "ObservableDefaultSelectionDict[K, V]",
            current_values: Mapping[Literal["dict", "key", "value"], Any],
            submitted_values: Mapping[Literal["dict", "key", "value"], Any]
        ) -> Mapping[Literal["dict", "key", "value"], Any]:
            
            match ("dict" in submitted_values, "key" in submitted_values, "value" in submitted_values):
                case (True, True, True):
                    # All three values provided - pass through for validation
                    # Validation callback will check if key is in dict
                    return {}
                    
                case (True, True, False):
                    # Dict and key provided - derive value from dict
                    # If key not in dict, validation will catch it
                    if submitted_values["key"] is not None and submitted_values["key"] in submitted_values["dict"]:
                        return {"value": submitted_values["dict"][submitted_values["key"]]}
                    return {}
                
                case (True, False, True):
                    # Dict and value provided - validate value matches current key
                    if current_values["key"] not in submitted_values["dict"]:
                        raise KeyError(f"Current key {current_values['key']} not in submitted dictionary")
                    if submitted_values["value"] != submitted_values["dict"][current_values["key"]]:
                        raise ValueError(f"Value {submitted_values['value']} is not the same as the value in the dictionary {submitted_values['dict'][current_values['key']]}")
                    return {}
                
                case (True, False, False):
                    # Dict provided alone - current key must be in dict
                    if current_values["key"] not in submitted_values["dict"]:
                        raise KeyError(f"Current key {current_values['key']} not in submitted dictionary")
                    return {"value": submitted_values["dict"][current_values["key"]]}
                
                case (False, True, True):
                    # Key and value provided - update dict with new value
                    _dict = current_values["dict"].copy()
                    _dict[submitted_values["key"]] = submitted_values["value"]
                    return {"dict": _dict}
                
                case (False, True, False):
                    # Key provided alone - add key to dict with default if not present
                    if submitted_values["key"] not in current_values["dict"]:
                        _dict = current_values["dict"].copy()
                        _default_val = self_ref._get_default_value(submitted_values["key"])
                        _dict[submitted_values["key"]] = _default_val
                        return {"dict": _dict, "value": _default_val}
                    return {"value": current_values["dict"][submitted_values["key"]]}
                
                case (False, False, True):
                    # Value provided alone - update dict at current key
                    _dict = current_values["dict"].copy()
                    _dict[current_values["key"]] = submitted_values["value"]
                    return {"dict": _dict}
                
                case (False, False, False):
                    # Nothing provided - no updates needed
                    return {}

            raise ValueError("Invalid keys")
        
        return add_values_to_be_updated_callback

    def _create_validation_callback(self) -> Callable[
        [Mapping[Literal["dict", "key", "value"], Any]], 
        tuple[bool, str]
    ]:
        """
        Create the validate_complete_values_in_isolation_callback for default selection.
        
        Validates that dict/key/value are consistent. Key must not be None.
        """
        def validate_complete_values_in_isolation_callback(
            values: Mapping[Literal["dict", "key", "value"], Any]
        ) -> tuple[bool, str]:
            
            # Check that all three values are present
            if "dict" not in values:
                return False, "Dict not in values"
            if "key" not in values:
                return False, "Key not in values"
            if "value" not in values:
                return False, "Value not in values"

            # Check that the dictionary is not None
            if values["dict"] is None:
                return False, "Dictionary is None"
            
            # Check that the key is not None
            if values["key"] is None:
                return False, "Key must not be None"

            # Check that the key is in the dictionary
            if values["key"] not in values["dict"]:
                return False, "Key not in dictionary"

            # Check that the value is equal to the value in the dictionary
            if values["value"] != values["dict"][values["key"]]:
                return False, "Value not equal to value in dictionary"

            return True, "Validation of complete value set in isolation passed"
        
        return validate_complete_values_in_isolation_callback

    def _compute_initial_value(
        self, 
        initial_dict: dict[K, V], 
        initial_key: K
    ) -> V:
        """
        Compute the initial value from dict and key.
        
        If key is not in dict, creates a default entry and returns the default value.
        """
        if initial_key not in initial_dict:
            # Auto-create default entry
            default_val = self._get_default_value(initial_key)
            initial_dict[initial_key] = default_val
            return default_val
        else:
            return initial_dict[initial_key]

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: K) -> None:
        """
        Set the dictionary and key behind this hook atomically.
        
        If key is not in dict, auto-creates a default entry.
        
        Args:
            dict_value: The new dictionary
            key_value: The new key (will be auto-created if not present)
        """
        if key_value not in dict_value:
            # Auto-create default entry
            _inferred_value = self._get_default_value(key_value)
            dict_value = dict_value.copy()
            dict_value[key_value] = _inferred_value
        else:
            _inferred_value = dict_value[key_value]
        
        self.submit_values({
            "dict": dict_value, 
            "key": key_value, 
            "value": _inferred_value
        })
