"""
Test cases for emitter hooks functionality across all observable types.

This test file validates the emitter hook architecture and ensures that
emitter hooks are properly recomputed when component values change.
"""

import pytest
from observables import ObservableList, ObservableDict, ObservableSet, ObservableTuple
from observables import ObservableSelectionOption, ObservableOptionalSelectionOption, ObservableMultiSelectionOption


class TestEmitterHooksBasicFunctionality:
    """Test basic emitter hook functionality."""
    
    def test_observable_list_length_emitter_hook(self):
        """Test that ObservableList has a length emitter hook."""
        obs_list = ObservableList([1, 2, 3])
        
        # Check that length hook exists
        assert "length" in [key for key in obs_list._emitter_hooks.keys()] # type: ignore
        
        # Check initial length value
        length_hook = obs_list.get_hook("length")
        assert length_hook.value == 3
        
        # Check get_value works for emitter hooks
        assert obs_list.get_value("length") == 3
    
    def test_observable_dict_length_emitter_hook(self):
        """Test that ObservableDict has a length emitter hook.""" 
        obs_dict = ObservableDict({"a": 1, "b": 2})
        
        # Check that length hook exists
        assert "length" in [key for key in obs_dict._emitter_hooks.keys()] # type: ignore
        
        # Check initial length value
        length_hook = obs_dict.get_hook("length")
        assert length_hook.value == 2
        
        # Check get_value works for emitter hooks
        assert obs_dict.get_value("length") == 2
    
    def test_observable_set_length_emitter_hook(self):
        """Test that ObservableSet has a length emitter hook."""
        obs_set = ObservableSet({1, 2, 3, 4})
        
        # Check that length hook exists
        assert "length" in [key for key in obs_set._emitter_hooks.keys()] # type: ignore
        
        # Check initial length value
        length_hook = obs_set.get_hook("length")
        assert length_hook.value == 4
        
        # Check get_value works for emitter hooks
        assert obs_set.get_value("length") == 4
    
    def test_observable_tuple_length_emitter_hook(self):
        """Test that ObservableTuple has a length emitter hook."""
        obs_tuple = ObservableTuple((1, 2, 3, 4, 5))
        
        # Check that length hook exists
        assert "length" in [key for key in obs_tuple._emitter_hooks.keys()] # type: ignore
        
        # Check initial length value
        length_hook = obs_tuple.get_hook("length")
        assert length_hook.value == 5
        
        # Check get_value works for emitter hooks
        assert obs_tuple.get_value("length") == 5


class TestEmitterHooksRecomputation:
    """Test that emitter hooks are properly recomputed when component values change."""
    
    def test_observable_list_length_updates_on_append(self):
        """Test that length emitter hook updates when list is modified."""
        obs_list = ObservableList([1, 2])
        
        # Initial length should be 2
        assert obs_list.get_value("length") == 2
        assert obs_list.get_hook("length").value == 2
        
        # Append an item
        obs_list.append(3)
        
        # Length should now be 3 - THIS WILL FAIL due to the bug
        # The emitter hook is not being recomputed
        assert obs_list.get_value("length") == 3, "Length emitter hook should update when list changes"
        assert obs_list.get_hook("length").value == 3, "Length hook value should update when list changes"
    
    def test_observable_list_length_updates_on_clear(self):
        """Test that length emitter hook updates when list is cleared."""
        obs_list = ObservableList([1, 2, 3, 4])
        
        # Initial length should be 4
        assert obs_list.get_value("length") == 4
        
        # Clear the list
        obs_list.clear()
        
        # Length should now be 0
        assert obs_list.get_value("length") == 0, "Length emitter hook should update when list is cleared"
        assert obs_list.get_hook("length").value == 0, "Length hook value should update when list is cleared"
    
    def test_observable_list_length_updates_on_direct_assignment(self):
        """Test that length emitter hook updates when list_value is directly assigned."""
        obs_list = ObservableList([1, 2])
        
        # Initial length should be 2
        assert obs_list.get_value("length") == 2
        
        # Directly assign new list
        obs_list.list_value = [1, 2, 3, 4, 5]
        
        # Length should now be 5
        assert obs_list.get_value("length") == 5, "Length emitter hook should update when list_value is assigned"
        assert obs_list.get_hook("length").value == 5, "Length hook value should update when list_value is assigned"
    
    def test_observable_dict_length_updates_on_modification(self):
        """Test that length emitter hook updates when dict is modified."""
        obs_dict = ObservableDict({"a": 1, "b": 2})
        
        # Initial length should be 2
        assert obs_dict.get_value("length") == 2
        
        # Add a new key-value pair
        obs_dict["c"] = 3
        
        # Length should now be 3
        assert obs_dict.get_value("length") == 3, "Length emitter hook should update when dict changes"
        assert obs_dict.get_hook("length").value == 3, "Length hook value should update when dict changes"
    
    def test_observable_set_length_updates_on_modification(self):
        """Test that length emitter hook updates when set is modified."""
        obs_set = ObservableSet({1, 2, 3})
        
        # Initial length should be 3
        assert obs_set.get_value("length") == 3
        
        # Add a new element
        obs_set.add(4)
        
        # Length should now be 4
        assert obs_set.get_value("length") == 4, "Length emitter hook should update when set changes"
        assert obs_set.get_hook("length").value == 4, "Length hook value should update when set changes"
    
    def test_observable_tuple_length_updates_on_modification(self):
        """Test that length emitter hook updates when tuple is modified."""
        obs_tuple = ObservableTuple((1, 2, 3))
        
        # Initial length should be 3
        assert obs_tuple.get_value("length") == 3
        
        # Replace the tuple
        obs_tuple.tuple_value = (1, 2, 3, 4, 5)
        
        # Length should now be 5
        assert obs_tuple.get_value("length") == 5, "Length emitter hook should update when tuple changes"
        assert obs_tuple.get_hook("length").value == 5, "Length hook value should update when tuple changes"


class TestEmitterHooksSelection:
    """Test emitter hooks for selection observables."""
    
    def test_selection_option_number_of_available_options(self):
        """Test that ObservableSelectionOption has number_of_available_options emitter hook."""
        obs = ObservableSelectionOption("a", {"a", "b", "c"})
        
        # Check that hook exists
        assert "number_of_available_options" in [key for key in obs._emitter_hooks.keys()] # type: ignore
        
        # Check initial value
        assert obs.get_value("number_of_available_options") == 3
        
        # Modify available options
        obs.available_options = {"a", "b", "c", "d", "e"}
        
        # Should update to 5
        assert obs.get_value("number_of_available_options") == 5, "Emitter hook should update when available options change"
    
    def test_optional_selection_option_number_of_available_options(self):
        """Test that ObservableOptionalSelectionOption has number_of_available_options emitter hook."""
        obs = ObservableOptionalSelectionOption(None, {"a", "b", "c"})
        
        # Check that hook exists  
        assert "number_of_available_options" in [key for key in obs._emitter_hooks.keys()] # type: ignore
        
        # Check initial value
        assert obs.get_value("number_of_available_options") == 3
        
        # Modify available options
        obs.available_options = {"a", "b"}
        
        # Should update to 2
        assert obs.get_value("number_of_available_options") == 2, "Emitter hook should update when available options change"
    
    def test_multi_selection_option_emitter_hooks(self):
        """Test that ObservableMultiSelectionOption has multiple emitter hooks."""
        obs = ObservableMultiSelectionOption({"a", "b"}, {"a", "b", "c", "d"})
        
        # Check that hooks exist
        assert "number_of_selected_options" in [key for key in obs._emitter_hooks.keys()] # type: ignore
        assert "number_of_available_options" in [key for key in obs._emitter_hooks.keys()] # type: ignore
        
        # Check initial values
        assert obs.get_value("number_of_selected_options") == 2
        assert obs.get_value("number_of_available_options") == 4
        
        # Modify selected options
        obs.selected_options = {"a", "b", "c"}
        
        # Should update
        assert obs.get_value("number_of_selected_options") == 3, "Selected options emitter hook should update"
        
        # Modify available options
        obs.available_options = {"a", "b", "c", "d", "e", "f"}
        
        # Should update
        assert obs.get_value("number_of_available_options") == 6, "Available options emitter hook should update"


class TestEmitterHooksListeners:
    """Test that emitter hooks properly notify listeners when they change."""
    
    def test_emitter_hook_listener_notification(self):
        """Test that listeners are notified when emitter hooks change."""
        obs_list = ObservableList([1, 2])
        
        # Track listener calls
        listener_calls: list[int] = []
        
        def length_listener():
            listener_calls.append(obs_list.get_value("length"))
        
        # Add listener to length hook
        length_hook = obs_list.get_hook("length")
        length_hook.add_listeners(length_listener)
        
        # Modify the list
        obs_list.append(3)
        obs_list.append(4)
        
        # Listeners should have been called with updated values
        # This test will fail due to the emitter hook bug
        assert len(listener_calls) == 2, "Length hook listener should be called when list changes"
        assert listener_calls == [3, 4], "Listener should receive updated length values"
    
    def test_emitter_hook_binding(self):
        """Test that emitter hooks can be bound to other observables."""
        obs_list = ObservableList([1, 2, 3])
        
        # Create another observable to bind to the length
        from observables import ObservableSingleValue
        length_tracker = ObservableSingleValue(0)
        
        # Bind the length hook to the single value (reverse direction)
        from observables._utils.initial_sync_mode import InitialSyncMode
        length_hook = obs_list.get_hook("length")
        length_hook.connect_to(length_tracker.get_hook("value"), InitialSyncMode.PUSH_TO_TARGET)
        
        # Initial binding should work
        assert length_tracker.single_value == 3
        
        # Modify the list
        obs_list.extend([4, 5])
        
        # The bound observable should reflect the new length
        assert length_tracker.single_value == 5, "Bound observable should receive updated length from emitter hook"


class TestEmitterHooksEdgeCases:
    """Test edge cases for emitter hooks."""
    
    def test_empty_emitter_hooks(self):
        """Test observables with no emitter hooks."""
        from observables import ObservableSingleValue
        obs = ObservableSingleValue(42)
        
        # Should have no emitter hooks
        assert len(obs._emitter_hooks) == 0 # type: ignore
        assert len(obs._emitter_hook_callbacks) == 0 # type: ignore
    
    def test_get_value_with_invalid_key(self):
        """Test get_value with invalid emitter hook key."""
        obs_list = ObservableList([1, 2, 3])
        
        with pytest.raises(ValueError, match="Key nonexistent not found"):
            obs_list.get_value("nonexistent") # type: ignore
    
    def test_get_hook_with_invalid_key(self):
        """Test get_hook with invalid emitter hook key."""
        obs_list = ObservableList([1, 2, 3])
        
        with pytest.raises(ValueError, match="Key nonexistent not found"):
            obs_list.get_hook("nonexistent") # type: ignore
    
    def test_attach_to_emitter_hook(self):
        """Test attaching to emitter hooks."""
        obs_list = ObservableList([1, 2, 3])
        
        from observables import ObservableSingleValue
        target = ObservableSingleValue(0)
        
        # Should be able to attach to emitter hook
        obs_list.attach(target.get_hook("value"), "length")
        
        # Should sync immediately
        assert target.single_value == 3
    
    def test_detach_emitter_hook(self):
        """Test that emitter hooks cannot be detached since they are computed values."""
        obs_list = ObservableList([1, 2, 3])
        
        # Emitter hooks should not be detachable since they're computed from component values
        # They remain active as long as the observable exists
        length_hook = obs_list.get_hook("length")
        assert length_hook.is_active
        
        # Calling detach on an emitter hook should not change its active state
        obs_list.detach("length")
        assert length_hook.is_active, "Emitter hooks should remain active even after detach attempt"
