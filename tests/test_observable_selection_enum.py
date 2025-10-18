from enum import Enum
from observables import ObservableSelectionEnum, ObservableOptionalSelectionEnum

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3
    YELLOW = 4


class TestObservableSelectionEnum:
    """Test cases for ObservableSelectionEnum"""

    def test_serialization(self):
        """Test the complete serialization and deserialization cycle."""
        # Step 1: Create an ObservableSelectionEnum instance
        obs = ObservableSelectionEnum(Color.RED, {Color.RED, Color.GREEN, Color.BLUE})
        
        # Step 2: Fill it (modify the value)
        obs.selected_option = Color.GREEN
        obs.available_options = {Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW}
        
        # Store the expected state after step 2
        expected_selected = obs.selected_option
        expected_options = obs.available_options.copy()
        
        # Step 3: Serialize it and get a dict from "get_value_references_for_serialization"
        serialized_data = obs.get_value_references_for_serialization()
        
        # Verify serialized data contains expected keys
        assert "enum_value" in serialized_data
        assert "enum_options" in serialized_data
        assert serialized_data["enum_value"] == expected_selected
        assert serialized_data["enum_options"] == expected_options
        
        # Step 4: Delete the object
        del obs
        
        # Step 5: Create a fresh ObservableSelectionEnum instance
        obs_restored = ObservableSelectionEnum(Color.RED, {Color.RED})
        
        # Verify it starts with different values
        assert obs_restored.selected_option == Color.RED
        assert obs_restored.available_options == {Color.RED}
        
        # Step 6: Use "set_value_references_from_serialization"
        obs_restored.set_value_references_from_serialization(serialized_data)
        
        # Step 7: Check if the object is the same as after step 2
        assert obs_restored.selected_option == expected_selected
        assert obs_restored.available_options == expected_options


class TestObservableOptionalSelectionEnum:
    """Test cases for ObservableOptionalSelectionEnum"""

    def test_serialization(self):
        """Test the complete serialization and deserialization cycle."""
        # Step 1: Create an ObservableOptionalSelectionEnum instance
        obs = ObservableOptionalSelectionEnum(Color.RED, {Color.RED, Color.GREEN, Color.BLUE})
        
        # Step 2: Fill it (modify the value, including None)
        obs.selected_option = None
        obs.available_options = {Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW}
        
        # Store the expected state after step 2
        expected_selected = obs.selected_option
        expected_options = obs.available_options.copy()
        
        # Step 3: Serialize it and get a dict from "get_value_references_for_serialization"
        serialized_data = obs.get_value_references_for_serialization()
        
        # Verify serialized data contains expected keys
        assert "enum_value" in serialized_data
        assert "enum_options" in serialized_data
        assert serialized_data["enum_value"] == expected_selected
        assert serialized_data["enum_options"] == expected_options
        
        # Step 4: Delete the object
        del obs
        
        # Step 5: Create a fresh ObservableOptionalSelectionEnum instance
        obs_restored = ObservableOptionalSelectionEnum(Color.RED, {Color.RED})
        
        # Verify it starts with different values
        assert obs_restored.selected_option == Color.RED
        assert obs_restored.available_options == {Color.RED}
        
        # Step 6: Use "set_value_references_from_serialization"
        obs_restored.set_value_references_from_serialization(serialized_data)
        
        # Step 7: Check if the object is the same as after step 2
        assert obs_restored.selected_option == expected_selected
        assert obs_restored.available_options == expected_options

    def test_serialization_with_value(self):
        """Test serialization when value is not None."""
        # Step 1: Create an ObservableOptionalSelectionEnum instance
        obs = ObservableOptionalSelectionEnum(None, {Color.RED, Color.GREEN, Color.BLUE})
        
        # Step 2: Fill it (modify the value to non-None)
        obs.selected_option = Color.BLUE
        
        # Store the expected state after step 2
        expected_selected = obs.selected_option
        expected_options = obs.available_options.copy()
        
        # Step 3: Serialize it and get a dict from "get_value_references_for_serialization"
        serialized_data = obs.get_value_references_for_serialization()
        
        # Verify serialized data contains expected keys
        assert "enum_value" in serialized_data
        assert "enum_options" in serialized_data
        assert serialized_data["enum_value"] == expected_selected
        assert serialized_data["enum_options"] == expected_options
        
        # Step 4: Delete the object
        del obs
        
        # Step 5: Create a fresh ObservableOptionalSelectionEnum instance
        obs_restored = ObservableOptionalSelectionEnum(None, {Color.RED})
        
        # Verify it starts with different values
        assert obs_restored.selected_option is None
        
        # Step 6: Use "set_value_references_from_serialization"
        obs_restored.set_value_references_from_serialization(serialized_data)
        
        # Step 7: Check if the object is the same as after step 2
        assert obs_restored.selected_option == expected_selected
        assert obs_restored.available_options == expected_options

