from typing import Literal, TypeVar, Generic, Optional, Mapping, Any, Callable

from .observable_dict_base import ObservableDictBase
from .protocols import ObservableOptionalSelectionDictProtocol

K = TypeVar("K")
V = TypeVar("V")

class ObservableOptionalSelectionDict(
    ObservableDictBase[K, V, Optional[K], Optional[V]], 
    ObservableOptionalSelectionDictProtocol[K, V], 
    Generic[K, V]
):
    """
    An observable that manages an optional selection from a dictionary.
    
    This observable manages three components:
    - dict: The dictionary to select from
    - key: The selected key in the dictionary (can be None)
    - value: The value at the selected key (can be None)
    
    Plus three read-only secondary hooks:
    - keys: Tuple of dictionary keys
    - values: Tuple of dictionary values
    - length: Dictionary length
    
    **Optional Behavior:**
    - If key is None, then value must be None
    - If key is not None, then value must match the dictionary value at that key
    - Allows setting value to None even when key is not None (for flexibility)
    
    **Architecture:**
    - Inherits from ObservableDictBase for common dict observable functionality
    - Uses ComplexObservableBase (via ObservableDictBase) for hook management
    - Integrates with NexusManager for value submission
    """

    def _create_add_values_callback(self) -> Callable[
        ["ObservableOptionalSelectionDict[K, V]", Mapping[Literal["dict", "key", "value"], Any], Mapping[Literal["dict", "key", "value"], Any]], 
        Mapping[Literal["dict", "key", "value"], Any]
    ]:
        """
        Create the add_values_to_be_updated_callback for optional selection logic.
        
        This callback handles None keys and ensures value consistency.
        """
        def add_values_to_be_updated_callback(
            self_ref: "ObservableOptionalSelectionDict[K, V]",
            current_values: Mapping[Literal["dict", "key", "value"], Any],
            submitted_values: Mapping[Literal["dict", "key", "value"], Any]
        ) -> Mapping[Literal["dict", "key", "value"], Any]:
            
            match ("dict" in submitted_values, "key" in submitted_values, "value" in submitted_values):
                case (True, True, True):
                    # All three values provided - validate consistency
                    # Note: None dict will be caught by validation callback
                    if submitted_values["key"] is None:
                        if submitted_values["value"] is not None:
                            raise ValueError(f"Value must be None when key is None")
                        return {}
                    else:
                        # Allow None dict to pass through - validation will catch it
                        if submitted_values["dict"] is not None:
                            if submitted_values["key"] not in submitted_values["dict"]:
                                raise KeyError(f"Key {submitted_values['key']} not in dictionary")
                            expected_value = submitted_values["dict"][submitted_values["key"]]
                            if submitted_values["value"] != expected_value:
                                return {"value": expected_value}
                        return {}
                        
                case (True, True, False):
                    # Dict and key provided - get value from dict
                    if submitted_values["key"] is None:
                        return {"value": None}
                    else:
                        # Allow None dict to pass through - validation will catch it
                        if submitted_values["dict"] is not None:
                            if submitted_values["key"] not in submitted_values["dict"]:
                                raise KeyError(f"Key {submitted_values['key']} not in dictionary")
                            return {"value": submitted_values["dict"][submitted_values["key"]]}
                        return {}
                
                case (True, False, True):
                    # Dict and value provided - validate value matches current key
                    if current_values["key"] is None:
                        if submitted_values["value"] is not None:
                            raise ValueError(f"Value {submitted_values['value']} is not None when key is None")
                        return {}
                    else:
                        # Allow None dict to pass through - validation will catch it
                        if submitted_values["dict"] is not None:
                            if submitted_values["value"] != submitted_values["dict"][current_values["key"]]:
                                raise ValueError(f"Value {submitted_values['value']} is not the same as the value in the dictionary {submitted_values['dict'][current_values['key']]}")
                        return {}
                
                case (True, False, False):
                    # Dict provided - get value for current key
                    if current_values["key"] is None:
                        return {"value": None}
                    else:
                        # Allow None dict to pass through - validation will catch it
                        if submitted_values["dict"] is not None:
                            return {"value": submitted_values["dict"][current_values["key"]]}
                        return {}
                
                case (False, True, True):
                    # Key and value provided - update dict with new value
                    if submitted_values["key"] is None:
                        return {}
                    else:
                        _dict = current_values["dict"].copy()
                        _dict[submitted_values["key"]] = submitted_values["value"]
                        return {"dict": _dict}
                
                case (False, True, False):
                    # Key provided - get value from current dict
                    if submitted_values["key"] is None:
                        return {"value": None}
                    else:
                        if submitted_values["key"] not in current_values["dict"]:
                            raise KeyError(f"Key {submitted_values['key']} not in dictionary")
                        return {"value": current_values["dict"][submitted_values["key"]]}
                
                case (False, False, True):
                    # Value provided - if current key is None, value must be None, otherwise update dict
                    if current_values["key"] is None:
                        if submitted_values["value"] is not None:
                            raise ValueError(f"Value {submitted_values['value']} is not None when key is None")
                        else:
                            return {}
                    else:
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
        Create the validate_complete_values_in_isolation_callback for optional selection.
        
        Validates that dict/key/value are consistent with optional None handling.
        """
        def validate_complete_values_in_isolation_callback(
            values: Mapping[Literal["dict", "key", "value"], Any]
        ) -> tuple[bool, str]:
            
            # Check that all three values are in the values
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
        initial_dict: dict[K, V], 
        initial_key: Optional[K]
    ) -> Optional[V]:
        """
        Compute the initial value from dict and key.
        
        Returns None if key is None, otherwise returns dict[key].
        """
        if initial_key is None:
            return None
        else:
            return initial_dict[initial_key]

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: Optional[K]) -> None:
        """
        Set the dictionary and key behind this hook atomically.
        
        Args:
            dict_value: The new dictionary
            key_value: The new key (can be None)
        """
        if key_value is None:
            _inferred_value = None
        else:
            _inferred_value = dict_value[key_value]

        self.submit_values({
            "dict": dict_value, 
            "key": key_value, 
            "value": _inferred_value
        })
