from typing import Literal, TypeVar, Generic, Optional, Mapping, Any, Callable
from logging import Logger
from types import MappingProxyType

from ..._hooks.hook_aliases import Hook
from .observable_dict_base import ObservableDictBase
from .protocols import ObservableOptionalSelectionDictProtocol

K = TypeVar("K")
V = TypeVar("V")

class ObservableOptionalDefaultSelectionDict(
    ObservableDictBase[K, V, Optional[K], Optional[V]], 
    ObservableOptionalSelectionDictProtocol[K, V], 
    Generic[K, V]
):
    """
    An observable that manages an optional selection from a dictionary with automatic default entry creation.
    
    This observable combines features of both Optional and Default variants:
    - dict: The dictionary to select from
    - key: The selected key in the dictionary (can be None)
    - value: The value at the selected key (can be None)
    
    Plus three read-only secondary hooks:
    - keys: Tuple of dictionary keys
    - values: Tuple of dictionary values
    - length: Dictionary length
    
    Valid Key Combinations:
    ┌─────────────────┬──────────────────────────┬──────────────────────────┐
    │                 │    if key in dict        │  if key not in dict      │
    ├─────────────────┼──────────────────────────┼──────────────────────────┤
    │ if key is       │                          │                          │
    │ not None        │           ✓              │   default (auto-create)  │
    ├─────────────────┼──────────────────────────┼──────────────────────────┤
    │ if key is       │                          │                          │
    │ None            │      None (value)        │      None (value)        │
    └─────────────────┴──────────────────────────┴──────────────────────────┘
    
    **Optional + Default Behavior:**
    - If key is None, then value must be None
    - If key is not None and not in dict, a default entry is automatically created
    - The default value can be a constant or a callable: Callable[[K], V]
    - Allows setting value to None even when key is not None (for flexibility)
    
    **Architecture:**
    - Inherits from ObservableDictBase for common dict observable functionality
    - Uses ComplexObservableBase (via ObservableDictBase) for hook management
    - Integrates with NexusManager for value submission
    """

    def __init__(
        self,
        dict_hook: Mapping[K, V] | Hook[Mapping[K, V]],
        key_hook: Optional[K] | Hook[Optional[K]] = None,
        value_hook: Optional[Hook[Optional[V]]] = None,
        default_value: V | Callable[[K], V] = None,  # type: ignore
        logger: Optional[Logger] = None
    ):
        """
        Initialize an ObservableOptionalDefaultSelectionDict.
        
        Args:
            dict_hook: The mapping or hook containing the mapping
            key_hook: The initial key or hook (can be None)
            value_hook: Optional hook for the value (if None, will be derived)
            default_value: Default value or callable to use when key is not in dict
            logger: Optional logger for debugging
        """
        # Store default_value for use in callbacks
        self._default_value: V | Callable[[K], V] = default_value
        
        # Pre-process dict to add default entry if needed (before wrapping in MappingProxyType)
        if not isinstance(dict_hook, Hook):
            # Extract initial key
            initial_key = key_hook.value if isinstance(key_hook, Hook) else key_hook
            # Add default entry if key is not None and not in dict
            if initial_key is not None and initial_key not in dict_hook:
                _dict = dict(dict_hook)
                _dict[initial_key] = self._get_default_value(initial_key)
                dict_hook = _dict
        
        # Call parent constructor
        super().__init__(dict_hook, key_hook, value_hook, invalidate_callback=None, logger=logger)

    def _get_default_value(self, key: K) -> V:
        """Helper to get default value (call if callable, return if constant)."""
        if callable(self._default_value):
            return self._default_value(key)  # type: ignore
        return self._default_value  # type: ignore

    def _create_add_values_callback(self) -> Callable[
        ["ObservableOptionalDefaultSelectionDict[K, V]", Mapping[Literal["dict", "key", "value"], Any], Mapping[Literal["dict", "key", "value"], Any]], 
        Mapping[Literal["dict", "key", "value"], Any]
    ]:
        """
        Create the add_values_to_be_updated_callback for optional + default logic.
        
        Handles None keys AND auto-creates missing keys with default values.
        """
        def add_values_to_be_updated_callback(
            self_ref: "ObservableOptionalDefaultSelectionDict[K, V]",
            current_values: Mapping[Literal["dict", "key", "value"], Any],
            submitted_values: Mapping[Literal["dict", "key", "value"], Any]
        ) -> Mapping[Literal["dict", "key", "value"], Any]:
            
            match ("dict" in submitted_values, "key" in submitted_values, "value" in submitted_values):
                case (True, True, True):
                    # All three values provided - pass through for validation
                    return {}
                    
                case (True, True, False):
                    # Dict and key provided - get value from dict (or None if key is None)
                    if submitted_values["key"] is None:
                        return {"value": None}
                    else:
                        # Auto-create default if key not in dict
                        if submitted_values["key"] not in submitted_values["dict"]:
                            _dict = dict(submitted_values["dict"])
                            _default_val = self_ref._get_default_value(submitted_values["key"])
                            _dict[submitted_values["key"]] = _default_val
                            return {"dict": MappingProxyType(_dict), "value": _default_val}
                        return {"value": submitted_values["dict"][submitted_values["key"]]}
                
                case (True, False, True):
                    # Dict and value provided - validate value matches current key
                    if current_values["key"] is None:
                        if submitted_values["value"] is not None:
                            raise ValueError(f"Value {submitted_values['value']} is not None when key is None")
                        return {}
                    else:
                        # Allow None dict to pass through
                        if submitted_values["dict"] is not None:
                            if submitted_values["value"] != submitted_values["dict"][current_values["key"]]:
                                raise ValueError(f"Value {submitted_values['value']} is not the same as the value in the dictionary {submitted_values['dict'][current_values['key']]}")
                        return {}
                
                case (True, False, False):
                    # Dict provided - get value for current key (or None if key is None)
                    if current_values["key"] is None:
                        return {"value": None}
                    else:
                        # Auto-create default if key not in dict
                        if current_values["key"] not in submitted_values["dict"]:
                            _dict = dict(submitted_values["dict"])
                            _default_val = self_ref._get_default_value(current_values["key"])
                            _dict[current_values["key"]] = _default_val
                            return {"dict": MappingProxyType(_dict), "value": _default_val}
                        return {"value": submitted_values["dict"][current_values["key"]]}
                
                case (False, True, True):
                    # Key and value provided - update dict with new value
                    if submitted_values["key"] is None:
                        return {}
                    else:
                        _dict = dict(current_values["dict"])
                        _dict[submitted_values["key"]] = submitted_values["value"]
                        return {"dict": MappingProxyType(_dict)}
                
                case (False, True, False):
                    # Key provided - get value from current dict (or create default)
                    if submitted_values["key"] is None:
                        return {"value": None}
                    else:
                        # Auto-create default if key not in dict
                        if submitted_values["key"] not in current_values["dict"]:
                            _dict = dict(current_values["dict"])
                            _default_val = self_ref._get_default_value(submitted_values["key"])
                            _dict[submitted_values["key"]] = _default_val
                            return {"dict": MappingProxyType(_dict), "value": _default_val}
                        return {"value": current_values["dict"][submitted_values["key"]]}
                
                case (False, False, True):
                    # Value provided - if current key is None, value must be None, otherwise update dict
                    if current_values["key"] is None:
                        if submitted_values["value"] is not None:
                            raise ValueError(f"Value {submitted_values['value']} is not None when key is None")
                        return {}
                    else:
                        _dict = dict(current_values["dict"])
                        _dict[current_values["key"]] = submitted_values["value"]
                        return {"dict": MappingProxyType(_dict)}
                
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
        Create the validate_complete_values_in_isolation_callback for optional + default selection.
        
        Validates that dict/key/value are consistent with optional and auto-create handling.
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

            if values["key"] is None:
                # Check that the value is None when the key is None
                if values["value"] is not None:
                    return False, "Value is not None when key is None"
            else:
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
        initial_dict: Mapping[K, V], 
        initial_key: Optional[K]
    ) -> Optional[V]:
        """
        Compute the initial value from dict and key.
        
        Returns None if key is None, returns default if key not in dict.
        """
        if initial_key is None:
            return None
        elif initial_key not in initial_dict:
            # Return default value
            return self._get_default_value(initial_key)
        else:
            return initial_dict[initial_key]

    def set_dict_and_key(self, dict_value: Mapping[K, V], key_value: Optional[K]) -> None:
        """
        Set the dictionary and key behind this hook atomically.
        
        If key is not None and not in dict, auto-creates a default entry.
        
        Args:
            dict_value: The new mapping
            key_value: The new key (can be None, will be auto-created if not present)
        """
        if key_value is None:
            _inferred_value = None
            # Wrap in MappingProxyType for immutability
            if not isinstance(dict_value, MappingProxyType):
                dict_value = MappingProxyType(dict(dict_value))
        elif key_value not in dict_value:
            # Auto-create default entry
            _inferred_value = self._get_default_value(key_value)
            _dict = dict(dict_value)
            _dict[key_value] = _inferred_value
            dict_value = MappingProxyType(_dict)
        else:
            _inferred_value = dict_value[key_value]
            # Wrap in MappingProxyType for immutability
            if not isinstance(dict_value, MappingProxyType):
                dict_value = MappingProxyType(dict(dict_value))

        self.submit_values({
            "dict": dict_value, 
            "key": key_value, 
            "value": _inferred_value
        })
