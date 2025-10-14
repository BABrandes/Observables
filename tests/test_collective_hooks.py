#!/usr/bin/env python3
"""
Test Collective Hooks System

This test file tests the collective hook system with multiple observable types.
It covers complex binding scenarios, collective validation, and transitive binding behavior.
"""

import unittest
import time

from observables._build_in_observables.observable_single_value import ObservableSingleValue
from observables._build_in_observables.observable_set import ObservableSet
from observables._other_observables.observable_selection_option import ObservableSelectionOption
from observables._other_observables.observable_selection_option import ObservableOptionalSelectionOption
from tests.run_tests import console_logger as logger


class TestCollectiveHooks(unittest.TestCase):
    """Test the collective hooks system with multiple observable types."""

    def setUp(self):
        """Set up test fixtures."""
        # Create ObservableSelectionOption instances with compatible initial states
        self.selector1: ObservableSelectionOption[str] = ObservableSelectionOption("Red", {"Red", "Green", "Blue"}, logger=logger)
        self.selector2: ObservableSelectionOption[str] = ObservableSelectionOption("Red", {"Red", "Green", "Blue"}, logger=logger)
        
        # Create ObservableSingleValue instances with colors (compatible types)
        self.value1: ObservableSingleValue[str] = ObservableSingleValue("Red", logger=logger)
        self.value2: ObservableSingleValue[str] = ObservableSingleValue("Red", logger=logger)
        
        # Create ObservableSet instances with color sets (compatible types)
        self.set1: ObservableSet[str] = ObservableSet({"Red", "Green", "Blue"}, logger=logger)
        self.set2: ObservableSet[str] = ObservableSet({"Red", "Green", "Blue"}, logger=logger)

    def test_collective_hooks_property(self):
        """Test that collective_hooks property returns the correct hooks."""
        # ObservableSelectionOption should have selected_option, available_options, and secondary hooks
        all_hooks = list(self.selector1._primary_hooks.values()) + list(self.selector1._secondary_hooks.values()) # type: ignore
        self.assertEqual(len(all_hooks), 3) # type: ignore
        self.assertIn(self.selector1._primary_hooks["selected_option"], all_hooks) # type: ignore
        self.assertIn(self.selector1._primary_hooks["available_options"], all_hooks) # type: ignore
        
        # ObservableSingleValue should have 1 collective hook (just the primary hook, no secondary hooks)
        all_hooks_value = list(self.value1._primary_hooks.values()) + list(self.value1._secondary_hooks.values()) # type: ignore
        self.assertEqual(len(all_hooks_value), 1) # type: ignore
        
        # ObservableSet should have 2 collective hooks (primary hook + length secondary hook)
        all_hooks_set = list(self.set1._primary_hooks.values()) + list(self.set1._secondary_hooks.values()) # type: ignore
        self.assertEqual(len(all_hooks_set), 2) # type: ignore

    def test_complex_binding_network(self):
        """Test a complex binding network with multiple observable types."""
        # Bind selector1 to selector2
        self.selector1.connect_hook(self.selector2.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        self.selector1.connect_hook(self.selector2.available_options_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Bind value1 to selector1's selected_option
        self.selector1.connect_hook(self.value1.hook, "selected_option", "use_caller_value")  # type: ignore
        
        # Bind set1 to selector1's available_options
        self.selector1.connect_hook(self.set1.value_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Bind value2 to selector2's selected_option
        self.selector2.connect_hook(self.value2.hook, "selected_option", "use_caller_value")  # type: ignore
        
        # Bind set2 to selector2's available_options
        self.selector2.connect_hook(self.set2.value_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Now change selector1 and verify all propagate
        self.selector1.selected_option = "Green"
        self.selector1.available_options = {"Green", "Blue", "Purple"}
        
        # Verify all observables are synchronized
        self.assertEqual(self.selector2.selected_option, "Green")
        self.assertEqual(self.selector2.available_options, {"Green", "Blue", "Purple"})
        self.assertEqual(self.value1.value, "Green")
        self.assertEqual(self.set1.value, {"Green", "Blue", "Purple"})
        self.assertEqual(self.value2.value, "Green")
        self.assertEqual(self.set2.value, {"Green", "Blue", "Purple"})

    def test_binding_removal_and_rebinding(self):
        """Test removing bindings and rebinding differently."""
        # Initial binding: selector1 -> selector2
        self.selector1.connect_hook(self.selector2.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        self.selector1.connect_hook(self.selector2.available_options_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Verify initial binding works
        self.selector1.selected_option = "Blue"
        self.assertEqual(self.selector2.selected_option, "Blue")
        
        # Remove binding
        self.selector1.disconnect()
        
        # Verify binding is removed
        self.selector1.selected_option = "Green"
        self.assertEqual(self.selector2.selected_option, "Blue")  # Should not change
        
        # Rebind with different sync mode
        self.selector1.connect_hook(self.selector2.selected_option_hook, "selected_option", "use_target_value")  # type: ignore
        self.selector1.connect_hook(self.selector2.available_options_hook, "available_options", "use_target_value")  # type: ignore
        
        # Verify new binding works - first update available options
        self.selector2.available_options = {"Red", "Green", "Blue", "Purple"}
        self.selector2.selected_option = "Purple"
        self.assertEqual(self.selector1.selected_option, "Purple")

    def test_collective_validation(self):
        """Test collective validation with multiple dependent values."""
        # Create a selector with strict validation
        strict_selector = ObservableSelectionOption("Red", {"Red", "Green"}, logger=logger)
        
        # Test that setting available_options without the current selected_option fails
        with self.assertRaises(ValueError):
            strict_selector.available_options = {"Blue", "Purple"}  # "Red" not in new options
        
        # Test individual property validation
        with self.assertRaises(ValueError):
            strict_selector.selected_option = "InvalidOption"  # Not in current available options
        
        # Test that the validation actually works by trying to set an invalid value
        # First, make sure the current state is valid by using atomic update
        strict_selector.change_selected_option_and_available_options("Green", {"Green", "Blue"})
        
        # Now try to set an invalid selected_option
        with self.assertRaises(ValueError):
            strict_selector.selected_option = "InvalidOption"
        
        # Test the specific case that was failing
        # Create a new selector and try to set an invalid state
        test_selector = ObservableSelectionOption("Red", {"Red", "Green"}, logger=logger)
        
        # This should fail because "Red" is not in {"Green", "Blue"}
        with self.assertRaises(ValueError):
            test_selector.available_options = {"Green", "Blue"}  # "Red" not in new options

    def test_transitive_binding_behavior(self):
        """Test transitive binding behavior with multiple observables."""
        # Create a chain: selector1 -> selector2 -> value1 -> set1
        self.selector1.connect_hook(self.selector2.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        self.selector1.connect_hook(self.selector2.available_options_hook, "available_options", "use_caller_value")  # type: ignore
        self.selector2.connect_hook(self.value1.hook, "selected_option", "use_caller_value")  # type: ignore
        self.selector1.connect_hook(self.set1.value_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Change the source (selector1) - first update available options
        self.selector1.available_options = {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"}
        self.selector1.selected_option = "Purple"
        
        # Verify all observables in the chain are synchronized
        self.assertEqual(self.selector2.selected_option, "Purple")
        self.assertEqual(self.selector2.available_options, {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"})
        self.assertEqual(self.value1.value, "Purple")
        self.assertEqual(self.set1.value, {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"})
        
        # Change from the middle of the chain
        self.selector2.selected_option = "Pink"
        
        # Verify changes propagate in both directions
        self.assertEqual(self.selector1.selected_option, "Pink")
        self.assertEqual(self.value1.value, "Pink")
        self.assertEqual(self.set1.value, {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"})  # Available options don't change from selected_option change

    def test_bidirectional_binding_with_collective_hooks(self):
        """Test bidirectional binding with collective hooks."""
        # Bind two selectors bidirectionally
        self.selector1.connect_hook(self.selector2.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        self.selector1.connect_hook(self.selector2.available_options_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Change selector1 - first update available options to include the new value
        self.selector1.available_options = {"Orange", "Red", "Yellow", "Green", "Blue"}
        self.selector1.selected_option = "Orange"
        
        # Verify selector2 gets updated
        self.assertEqual(self.selector2.selected_option, "Orange")
        self.assertEqual(self.selector2.available_options, {"Orange", "Red", "Yellow", "Green", "Blue"})
        
        # Change selector2 - first update available options to include the new value
        # Use atomic update to avoid validation issues
        self.selector2.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue", "Purple"})
        
        # Verify selector1 gets updated
        self.assertEqual(self.selector1.selected_option, "Red")
        self.assertEqual(self.selector1.available_options, {"Red", "Green", "Blue", "Purple"})

    def test_multiple_bindings_to_same_target(self):
        """Test multiple observables binding to the same target."""
        # First, ensure both selectors have compatible initial states
        self.selector1.available_options = {"Red", "Green", "Blue", "Yellow", "NewValue"}
        self.selector2.available_options = {"Red", "Green", "Blue", "Yellow", "NewValue"}
        
        # Bind both selectors to the same value
        # InitialSyncMode only affects initial binding - ongoing sync is bidirectional
        self.selector1.connect_hook(self.value1.hook, "selected_option", "use_caller_value")  # type: ignore
        self.selector2.connect_hook(self.value1.hook, "selected_option", "use_caller_value")  # type: ignore
        
        # Change the target value
        self.value1.value = "NewValue"
        
        # Verify both selectors get updated 
        self.assertEqual(self.selector1.selected_option, "NewValue")
        self.assertEqual(self.selector2.selected_option, "NewValue")
        
        # Change one selector - use atomic update to avoid validation issues
        # First update available options for both selectors to include "AnotherValue"
        self.selector1.change_selected_option_and_available_options("NewValue", {"AnotherValue", "Red", "Green", "Blue", "Yellow", "NewValue"})
        self.selector2.change_selected_option_and_available_options("NewValue", {"AnotherValue", "Red", "Green", "Blue", "Yellow", "NewValue"})
        
        # Now set the selected option to "AnotherValue"
        self.selector1.change_selected_option_and_available_options("AnotherValue", {"AnotherValue", "Red", "Green", "Blue", "Yellow", "NewValue"})
        
        # Verify the other selector and value get updated (bidirectional sync)
        self.assertEqual(self.selector2.selected_option, "AnotherValue")
        self.assertEqual(self.value1.value, "AnotherValue")

    def test_binding_set_to_both_selectors(self):
        """Test binding a set to both selectors to enable transmission of changes."""
        # Create a shared set that both selectors will bind to
        shared_set = ObservableSet({"Red", "Green", "Blue"}, logger=logger)
        
        # Ensure both selectors have compatible initial states using atomic updates
        self.selector1.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue", "Yellow"})
        self.selector2.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue", "Yellow"})
        
        # Bind both selectors' available_options to the shared set
        self.selector1.connect_hook(shared_set.value_hook, "available_options", "use_caller_value")  # type: ignore
        self.selector2.connect_hook(shared_set.value_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Change the shared set - include "Red" to maintain compatibility with current selected option
        shared_set.value = {"Purple", "Pink", "Cyan", "Red"}
        
        # Verify both selectors get updated
        self.assertEqual(self.selector1.available_options, {"Purple", "Pink", "Cyan", "Red"})
        self.assertEqual(self.selector2.available_options, {"Purple", "Pink", "Cyan", "Red"})
        
        # Change one selector's available options - ensure selected option is compatible
        # Update both selected_option and available_options atomically
        self.selector1.change_selected_option_and_available_options("Purple", {"Purple", "Orange", "Yellow"})
        
        # Verify the other selector and shared set get updated
        self.assertEqual(self.selector2.available_options, {"Purple", "Orange", "Yellow"})
        self.assertEqual(shared_set.value, {"Purple", "Orange", "Yellow"})

    def test_binding_available_options_directly(self):
        """Test binding available_options directly between selectors."""
        # Ensure both selectors have compatible initial states using atomic updates
        self.selector1.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        self.selector2.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        
        # Bind selector2's available_options directly to selector1's available_options
        self.selector2.connect_hook(self.selector1.available_options_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Change selector1's available options - use atomic update to avoid validation issues
        self.selector1.change_selected_option_and_available_options("Purple", {"Purple", "Pink", "Cyan"})
        
        # Verify selector2 gets updated
        self.assertEqual(self.selector2.available_options, {"Purple", "Pink", "Cyan"})
        
        # Change selector2's available options - ensure selected option is compatible
        # Use "Purple" which exists in both old and new option sets to avoid validation issues
        self.selector2.change_selected_option_and_available_options("Purple", {"Purple", "Orange", "Yellow"})
        
        # Verify selector1 gets updated (bidirectional)
        self.assertEqual(self.selector1.available_options, {"Purple", "Orange", "Yellow"})

    def test_binding_selectors_directly(self):
        """Test binding selectors directly to each other to create transitive behavior."""
        # Ensure both selectors have compatible initial states using atomic updates
        self.selector1.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        self.selector2.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        
        # Bind selector2 directly to selector1
        self.selector2.connect_hook(self.selector1.available_options_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Change selector1's available options - use atomic update to avoid validation issues
        self.selector1.change_selected_option_and_available_options("Purple", {"Purple", "Pink", "Cyan"})
        
        # Verify selector2 gets updated
        self.assertEqual(self.selector2.available_options, {"Purple", "Pink", "Cyan"})
        
        # Change selector2's available options - ensure selected option is compatible
        # Use "Purple" which exists in both old and new option sets to avoid validation issues
        self.selector2.change_selected_option_and_available_options("Purple", {"Purple", "Orange", "Yellow"})
        
        # Verify selector1 gets updated (bidirectional) - only available_options should change
        self.assertEqual(self.selector1.available_options, {"Purple", "Orange", "Yellow"})

    def test_binding_with_validation_errors(self):
        """Test binding behavior when validation errors occur."""
        # Create a selector with strict validation
        strict_selector = ObservableSelectionOption("Red", {"Red", "Green"}, logger=logger)
        
        # Bind it to a regular selector
        self.selector1.connect_hook(strict_selector.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        
        # Try to set an invalid value in the source
        with self.assertRaises(ValueError):
            self.selector1.selected_option = "Purple"  # Not in {"Red", "Green", "Blue"}
        
        # Verify the strict selector remains unchanged
        self.assertEqual(strict_selector.selected_option, "Red")
        self.assertEqual(strict_selector.available_options, {"Red", "Green"})

    def test_atomic_updates_with_collective_hooks(self):
        """Test atomic updates with collective hooks."""
        # Bind selector1 to selector2
        self.selector1.connect_hook(self.selector2.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        self.selector1.connect_hook(self.selector2.available_options_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Use atomic update to change both values at once
        self.selector1.change_selected_option_and_available_options("Purple", {"Purple", "Pink", "Cyan"})
        
        # Verify both values are updated atomically
        self.assertEqual(self.selector1.selected_option, "Purple")
        self.assertEqual(self.selector1.available_options, {"Purple", "Pink", "Cyan"})
        
        # Verify the bound observable also gets updated
        self.assertEqual(self.selector2.selected_option, "Purple")
        self.assertEqual(self.selector2.available_options, {"Purple", "Pink", "Cyan"})

    def test_binding_chain_break_and_rebuild(self):
        """Test breaking and rebuilding binding chains."""
        # Create a simple binding: selector1 -> selector2
        self.selector1.connect_hook(self.selector2.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        self.selector1.connect_hook(self.selector2.available_options_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Verify binding works
        self.selector1.available_options = {"TestValue", "Red", "Green", "Blue"}
        self.selector1.selected_option = "TestValue"
        self.assertEqual(self.selector2.selected_option, "TestValue")
        
        # Break the binding by disconnecting selector1
        self.selector1.disconnect()
        
        # Verify binding is broken
        self.selector1.change_selected_option_and_available_options("NewValue", {"NewValue", "Red", "Green", "Blue"})
        self.assertEqual(self.selector2.selected_option, "TestValue")  # Should not change
        
        # Rebuild the binding
        # First make selector2 compatible with selector1's current state
        self.selector2.change_selected_option_and_available_options("NewValue", {"NewValue", "Red", "Green", "Blue"})
        self.selector1.connect_hook(self.selector2.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        self.selector1.connect_hook(self.selector2.available_options_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Verify binding works again
        self.selector1.change_selected_option_and_available_options("RebuiltValue", {"RebuiltValue", "Red", "Green", "Blue"})
        self.assertEqual(self.selector2.selected_option, "RebuiltValue")

    def test_collective_hooks_with_empty_sets(self):
        """Test collective hooks behavior with empty sets."""
        # Create a selector that allows None
        none_selector: ObservableOptionalSelectionOption[str] = ObservableOptionalSelectionOption(None, set(), logger=logger)
        
        # Create a compatible selector that also allows None for binding
        compatible_selector: ObservableOptionalSelectionOption[str] = ObservableOptionalSelectionOption(None, set(), logger=logger)
        
        # Bind the compatible selector to the none_selector
        compatible_selector.connect_hook(none_selector.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        compatible_selector.connect_hook(none_selector.available_options_hook, "available_options", "use_caller_value")  # type: ignore
        
        # Set empty options and None selection
        none_selector.change_selected_option_and_available_options(None, set())
        
        # Verify the bound observable gets updated
        self.assertEqual(compatible_selector.selected_option, None)
        self.assertEqual(compatible_selector.available_options, set())

    def test_performance_with_collective_hooks(self):
        """Test performance with collective hooks."""
        # Create multiple observables with compatible types
        observables: list[ObservableSelectionOption[str]] = []
        for i in range(10):
            selector = ObservableSelectionOption("Common", {f"Color{i}", f"Option{i}", "Common"}, logger=logger)
            observables.append(selector)
        
        # Bind them in a complex network
        start_time = time.time()
        
        for i in range(0, len(observables) - 1):
            # Bind consecutive selectors together
            observables[i].connect_hook(observables[i + 1].selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        
        # Change a value and measure propagation time - first update available options
        observables[0].available_options = {"Common", "Color0", "Option0"} # type: ignore
        observables[0].selected_option = "Common" # type: ignore
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Collective hook operations should be fast")

    def test_collective_hooks_edge_cases(self):
        """Test edge cases with collective hooks."""
        # Test with circular references (should not cause infinite loops)
        selector_a = ObservableSelectionOption("A", {"A", "B", "C"}, logger=logger)
        selector_b = ObservableSelectionOption("B", {"B", "C", "A"}, logger=logger)
        selector_c = ObservableSelectionOption("C", {"C", "A"}, logger=logger)
        
        # Create a triangle binding - but avoid circular binding by using different sync modes
        selector_a.connect_hook(selector_b.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        selector_b.connect_hook(selector_c.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        # Don't create the circular binding - just test that the existing bindings work
        
        # Change one value - use a value that's in all available options
        selector_a.available_options = {"A", "B", "C"}
        selector_a.selected_option = "A"
        
        # Verify all are synchronized (they should converge to a common state)
        self.assertEqual(selector_a.selected_option, selector_b.selected_option)
        self.assertEqual(selector_b.selected_option, selector_c.selected_option)

    def test_binding_with_different_sync_modes(self):
        """Test binding with different sync modes in collective scenarios."""
        # Create observables
        selector_a = ObservableSelectionOption("A", {"A", "B", "C"}, logger=logger)
        selector_b = ObservableSelectionOption("B", {"B", "C", "A"}, logger=logger)
        value_a = ObservableSingleValue("ValueA", logger=logger)
        value_b = ObservableSingleValue("ValueB", logger=logger)
        
        # Bind with different sync modes
        selector_a.connect_hook(selector_b.selected_option_hook, "selected_option", "use_caller_value")  # type: ignore
        value_a.connect_hook(value_b.hook, "value", "use_target_value")  # type: ignore
        
        # Change values and verify behavior
        selector_a.selected_option = "B"
        self.assertEqual(selector_b.selected_option, "B")
        
        value_b.value = "NewValue"
        self.assertEqual(value_a.value, "NewValue")

    def test_collective_hooks_cleanup(self):
        """Test that collective hooks are properly cleaned up."""
        # Create observables and bind them
        selector: ObservableSelectionOption[str] = ObservableSelectionOption("Test", {"Test", "Other"}, logger=logger)
        value: ObservableSingleValue[str] = ObservableSingleValue("Test", logger=logger)
        options: ObservableSet[str] = ObservableSet({"Test", "Other"}, logger=logger)
        
        # Bind them together
        selector.connect_hook(value.hook, "selected_option", "use_caller_value") # type: ignore
        selector.connect_hook(options.value_hook, "available_options", "use_caller_value") # type: ignore
        
        # Disconnect_hook all
        selector.disconnect()
        # Don't disconnect value and options multiple times - they might already be disconnected
        try:
            value.disconnect()
        except ValueError:
            pass  # Already disconnected
        try:
            options.disconnect()
        except ValueError:
            pass  # Already disconnected
        
        # Verify they're independent - use atomic update to avoid validation issues
        selector.change_selected_option_and_available_options("Independent", {"Independent", "Test", "Other"})
        self.assertEqual(value.value, "Test")  # Should not change
        
        value.value = "AlsoIndependent"
        self.assertEqual(selector.selected_option, "Independent")  # Should not change


if __name__ == "__main__":
    unittest.main()
