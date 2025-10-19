from typing import Literal, TypeVar, Generic, Mapping, Any, Callable

from .observable_dict_base import ObservableDictBase
from .protocols import ObservableSelectionDictProtocol

K = TypeVar("K")
V = TypeVar("V")

class ObservableSelectionDict(
    ObservableDictBase[K, V, K, V], 
    ObservableSelectionDictProtocol[K, V], 
    Generic[K, V]
):
    """
    An observable that manages a selection from a dictionary.
    
    This observable maintains three components:
    - dict: The dictionary to select from
    - key: The selected key in the dictionary (must be in dict)
    - value: The value at the selected key
    
    Plus three read-only secondary hooks:
    - keys: Tuple of dictionary keys
    - values: Tuple of dictionary values
    - length: Dictionary length
    
    The observable ensures that these three components stay synchronized:
    - When dict or key changes, value is automatically updated
    - When value changes, the dictionary is updated at the current key
    - When key changes, value is updated to match the new key
    
    **Architecture:**
    - Inherits from ObservableDictBase for common dict observable functionality
    - Uses ComplexObservableBase (via ObservableDictBase) for hook management
    - Integrates with NexusManager for value submission
    """

    def _create_add_values_callback(self) -> Callable[
        ["ObservableSelectionDict[K, V]", Mapping[Literal["dict", "key", "value"], Any], Mapping[Literal["dict", "key", "value"], Any]], 
        Mapping[Literal["dict", "key", "value"], Any]
    ]:
        """
        Create the add_values_to_be_updated_callback for selection logic.
        
        This callback ensures that key must always exist in dict.
        """
        def add_values_to_be_updated_callback(
            self_ref: "ObservableSelectionDict[K, V]",
            current_values: Mapping[Literal["dict", "key", "value"], Any],
            submitted_values: Mapping[Literal["dict", "key", "value"], Any]
        ) -> Mapping[Literal["dict", "key", "value"], Any]:
            
            match ("dict" in submitted_values, "key" in submitted_values, "value" in submitted_values):
                case (True, True, True):
                    # All three values provided - validate consistency
                    if submitted_values["key"] not in submitted_values["dict"]:
                        raise KeyError(f"Key {submitted_values['key']} not in dictionary")
                    expected_value = submitted_values["dict"][submitted_values["key"]]
                    if submitted_values["value"] != expected_value:
                        return {"value": expected_value}
                    return {}
                    
                case (True, True, False):
                    # Dict and key provided - get value from dict
                    if submitted_values["key"] not in submitted_values["dict"]:
                        raise KeyError(f"Key {submitted_values['key']} not in dictionary")
                    return {"value": submitted_values["dict"][submitted_values["key"]]}
                
                case (True, False, True):
                    # Dict and value provided - validate value matches current key
                    if submitted_values["value"] != submitted_values["dict"][current_values["key"]]:
                        raise ValueError(f"Value {submitted_values['value']} is not the same as the value in the dictionary {submitted_values['dict'][current_values['key']]}")
                    return {}
                
                case (True, False, False):
                    # Dict provided - get value for current key
                    if current_values["key"] not in submitted_values["dict"]:
                        raise KeyError(f"Current key {current_values['key']} not in submitted dictionary")
                    return {"value": submitted_values["dict"][current_values["key"]]}
                
                case (False, True, True):
                    # Key and value provided - update dict with new value
                    if submitted_values["key"] not in current_values["dict"]:
                        raise KeyError(f"Key {submitted_values['key']} not in current dictionary")
                    _dict = current_values["dict"].copy()
                    _dict[submitted_values["key"]] = submitted_values["value"]
                    return {"dict": _dict}
                
                case (False, True, False):
                    # Key provided - get value from current dict
                    if submitted_values["key"] not in current_values["dict"]:
                        raise KeyError(f"Key {submitted_values['key']} not in dictionary")
                    return {"value": current_values["dict"][submitted_values["key"]]}
                
                case (False, False, True):
                    # Value provided - update dict at current key
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
        Create the validate_complete_values_in_isolation_callback for selection.
        
        Validates that dict/key/value are consistent and key is in dict.
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

            # Check that the key is in the dictionary
            if values["key"] not in values["dict"]:
                raise KeyError(f"Key {values['key']} not in dictionary")

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
        
        Returns dict[key].
        """
        return initial_dict[initial_key]

    def set_dict_and_key(self, dict_value: dict[K, V], key_value: K) -> None:
        """
        Set the dictionary and key behind this hook atomically.
        
        Args:
            dict_value: The new dictionary
            key_value: The new key (must be in dict_value)
        """
        _inferred_value = dict_value[key_value]
        self.submit_values({
            "dict": dict_value, 
            "key": key_value, 
            "value": _inferred_value
        })
