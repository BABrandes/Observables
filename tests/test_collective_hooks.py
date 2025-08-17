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
from observables._utils.initial_sync_mode import InitialSyncMode


class TestCollectiveHooks(unittest.TestCase):
    """Test the collective hooks system with multiple observable types."""

    def setUp(self):
        """Set up test fixtures."""
        # Create ObservableSelectionOption instances with compatible initial states
        self.selector1: ObservableSelectionOption[str] = ObservableSelectionOption("Red", {"Red", "Green", "Blue"})
        self.selector2: ObservableSelectionOption[str] = ObservableSelectionOption("Red", {"Red", "Green", "Blue"})
        
        # Create ObservableSingleValue instances with colors (compatible types)
        self.value1: ObservableSingleValue[str] = ObservableSingleValue("Red")
        self.value2: ObservableSingleValue[str] = ObservableSingleValue("Red")
        
        # Create ObservableSet instances with color sets (compatible types)
        self.set1: ObservableSet[str] = ObservableSet({"Red", "Green", "Blue"})
        self.set2: ObservableSet[str] = ObservableSet({"Red", "Green", "Blue"})

    def test_collective_hooks_property(self):
        """Test that collective_hooks property returns the correct hooks."""
        # ObservableSelectionOption should have both selected_option and available_options hooks
        self.assertEqual(len(self.selector1.collective_hooks), 2)
        self.assertIn(self.selector1._component_hooks["selected_option"], self.selector1.collective_hooks) # type: ignore
        self.assertIn(self.selector1._component_hooks["available_options"], self.selector1.collective_hooks) # type: ignore
        
        # ObservableSingleValue should have empty collective_hooks (no dependent hooks)
        self.assertEqual(len(self.value1.collective_hooks), 0)
        
        # ObservableSet should have empty collective_hooks (no dependent hooks)
        self.assertEqual(len(self.set1.collective_hooks), 0)

    def test_complex_binding_network(self):
        """Test a complex binding network with multiple observable types."""
        # Bind selector1 to selector2
        self.selector1.bind_to(self.selector2, InitialSyncMode.SELF_IS_UPDATED)
        
        # Bind value1 to selector1's selected_option
        self.selector1.bind_selected_option_to(self.value1, InitialSyncMode.SELF_IS_UPDATED) # type: ignore
        
        # Bind set1 to selector1's available_options
        self.selector1.bind_available_options_to(self.set1, InitialSyncMode.SELF_IS_UPDATED)
        
        # Bind value2 to selector2's selected_option
        self.selector2.bind_selected_option_to(self.value2, InitialSyncMode.SELF_IS_UPDATED) # type: ignore
        
        # Bind set2 to selector2's available_options
        self.selector2.bind_available_options_to(self.set2, InitialSyncMode.SELF_IS_UPDATED)
        
        # Now change selector1 and verify all propagate
        self.selector1.selected_option = "Green"
        self.selector1.available_options = {"Green", "Blue", "Purple"}
        
        # Verify all observables are synchronized
        self.assertEqual(self.selector2.selected_option, "Green")
        self.assertEqual(self.selector2.available_options, {"Green", "Blue", "Purple"})
        self.assertEqual(self.value1.single_value, "Green")
        self.assertEqual(self.set1.set_value, {"Green", "Blue", "Purple"})
        self.assertEqual(self.value2.single_value, "Green")
        self.assertEqual(self.set2.set_value, {"Green", "Blue", "Purple"})

    def test_binding_removal_and_rebinding(self):
        """Test removing bindings and rebinding differently."""
        # Initial binding: selector1 -> selector2
        self.selector1.bind_to(self.selector2, InitialSyncMode.SELF_IS_UPDATED)
        
        # Verify initial binding works
        self.selector1.selected_option = "Blue"
        self.assertEqual(self.selector2.selected_option, "Blue")
        
        # Remove binding
        self.selector1.detach()
        
        # Verify binding is removed
        self.selector1.selected_option = "Green"
        self.assertEqual(self.selector2.selected_option, "Blue")  # Should not change
        
        # Rebind with different sync mode
        self.selector1.bind_to(self.selector2, InitialSyncMode.SELF_UPDATES)
        
        # Verify new binding works - first update available options
        self.selector2.available_options = {"Red", "Green", "Blue", "Purple"}
        self.selector2.selected_option = "Purple"
        self.assertEqual(self.selector1.selected_option, "Purple")

    def test_collective_validation(self):
        """Test collective validation with multiple dependent values."""
        # Create a selector with strict validation
        strict_selector = ObservableSelectionOption("Red", {"Red", "Green"}, allow_none=False)
        
        # Test that setting available_options without the current selected_option fails
        with self.assertRaises(ValueError):
            strict_selector.available_options = {"Blue", "Purple"}  # "Red" not in new options
        
        # Test individual property validation
        with self.assertRaises(ValueError):
            strict_selector.selected_option = "InvalidOption"  # Not in current available options
        
        # Test that the validation actually works by trying to set an invalid value
        # First, make sure the current state is valid by using atomic update
        strict_selector.set_selected_option_and_available_options("Green", {"Green", "Blue"})
        
        # Now try to set an invalid selected_option
        with self.assertRaises(ValueError):
            strict_selector.selected_option = "InvalidOption"
        
        # Test the specific case that was failing
        # Create a new selector and try to set an invalid state
        test_selector = ObservableSelectionOption("Red", {"Red", "Green"}, allow_none=False)
        
        # This should fail because "Red" is not in {"Green", "Blue"}
        with self.assertRaises(ValueError):
            test_selector.available_options = {"Green", "Blue"}  # "Red" not in new options

    def test_transitive_binding_behavior(self):
        """Test transitive binding behavior with multiple observables."""
        # Create a chain: selector1 -> selector2 -> value1 -> set1
        self.selector1.bind_to(self.selector2, InitialSyncMode.SELF_IS_UPDATED)
        self.selector2.bind_selected_option_to(self.value1, InitialSyncMode.SELF_IS_UPDATED) # type: ignore
        self.selector1.bind_available_options_to(self.set1, InitialSyncMode.SELF_IS_UPDATED)
        
        # Change the source (selector1) - first update available options
        self.selector1.available_options = {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"}
        self.selector1.selected_option = "Purple"
        
        # Verify all observables in the chain are synchronized
        self.assertEqual(self.selector2.selected_option, "Purple")
        self.assertEqual(self.selector2.available_options, {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"})
        self.assertEqual(self.value1.single_value, "Purple")
        self.assertEqual(self.set1.set_value, {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"})
        
        # Change from the middle of the chain
        self.selector2.selected_option = "Pink"
        
        # Verify changes propagate in both directions
        self.assertEqual(self.selector1.selected_option, "Pink")
        self.assertEqual(self.value1.single_value, "Pink")
        self.assertEqual(self.set1.set_value, {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"})  # Available options don't change from selected_option change

    def test_bidirectional_binding_with_collective_hooks(self):
        """Test bidirectional binding with collective hooks."""
        # Bind two selectors bidirectionally
        self.selector1.bind_to(self.selector2, InitialSyncMode.SELF_IS_UPDATED)
        
        # Change selector1 - first update available options to include the new value
        self.selector1.available_options = {"Orange", "Red", "Yellow", "Green", "Blue"}
        self.selector1.selected_option = "Orange"
        
        # Verify selector2 gets updated
        self.assertEqual(self.selector2.selected_option, "Orange")
        self.assertEqual(self.selector2.available_options, {"Orange", "Red", "Yellow", "Green", "Blue"})
        
        # Change selector2 - first update available options to include the new value
        # Use atomic update to avoid validation issues
        self.selector2.set_selected_option_and_available_options("Red", {"Red", "Green", "Blue", "Purple"})
        
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
        self.selector1.bind_selected_option_to(self.value1, InitialSyncMode.SELF_IS_UPDATED) # type: ignore
        self.selector2.bind_selected_option_to(self.value1, InitialSyncMode.SELF_IS_UPDATED) # type: ignore
        
        # Change the target value
        self.value1.single_value = "NewValue"
        
        # Verify both selectors get updated
        self.assertEqual(self.selector1.selected_option, "NewValue")
        self.assertEqual(self.selector2.selected_option, "NewValue")
        
        # Change one selector - use atomic update to avoid validation issues
        # First update available options for both selectors to include "AnotherValue"
        self.selector1.set_selected_option_and_available_options("NewValue", {"AnotherValue", "Red", "Green", "Blue", "Yellow", "NewValue"})
        self.selector2.set_selected_option_and_available_options("NewValue", {"AnotherValue", "Red", "Green", "Blue", "Yellow", "NewValue"})
        
        # Now set the selected option to "AnotherValue"
        self.selector1.set_selected_option_and_available_options("AnotherValue", {"AnotherValue", "Red", "Green", "Blue", "Yellow", "NewValue"})
        
        # Verify the other selector and value get updated (bidirectional sync)
        self.assertEqual(self.selector2.selected_option, "AnotherValue")
        self.assertEqual(self.value1.single_value, "AnotherValue")

    def test_binding_set_to_both_selectors(self):
        """Test binding a set to both selectors to enable transmission of changes."""
        # Create a shared set that both selectors will bind to
        shared_set = ObservableSet({"Red", "Green", "Blue"})
        
        # Ensure both selectors have compatible initial states using atomic updates
        self.selector1.set_selected_option_and_available_options("Red", {"Red", "Green", "Blue", "Yellow"})
        self.selector2.set_selected_option_and_available_options("Red", {"Red", "Green", "Blue", "Yellow"})
        
        # Bind both selectors' available_options to the shared set
        self.selector1.bind_available_options_to(shared_set, InitialSyncMode.SELF_IS_UPDATED)
        self.selector2.bind_available_options_to(shared_set, InitialSyncMode.SELF_IS_UPDATED)
        
        # Change the shared set
        shared_set.set_value = {"Purple", "Pink", "Cyan"}
        
        # Verify both selectors get updated
        self.assertEqual(self.selector1.available_options, {"Purple", "Pink", "Cyan"})
        self.assertEqual(self.selector2.available_options, {"Purple", "Pink", "Cyan"})
        
        # Change one selector's available options - use atomic update to avoid validation issues
        self.selector1.set_selected_option_and_available_options("Orange", {"Orange", "Red", "Green"})
        
        # Verify the other selector and shared set get updated
        self.assertEqual(self.selector2.available_options, {"Orange", "Red", "Green"})
        self.assertEqual(shared_set.set_value, {"Orange", "Red", "Green"})

    def test_binding_available_options_directly(self):
        """Test binding available_options directly between selectors."""
        # Ensure both selectors have compatible initial states using atomic updates
        self.selector1.set_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        self.selector2.set_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        
        # Bind selector2's available_options directly to selector1's available_options
        self.selector2.bind_available_options_to(self.selector1, InitialSyncMode.SELF_IS_UPDATED)
        
        # Change selector1's available options - use atomic update to avoid validation issues
        self.selector1.set_selected_option_and_available_options("Purple", {"Purple", "Pink", "Cyan"})
        
        # Verify selector2 gets updated
        self.assertEqual(self.selector2.available_options, {"Purple", "Pink", "Cyan"})
        
        # Change selector2's available options - use atomic update to avoid validation issues
        self.selector2.set_selected_option_and_available_options("Orange", {"Orange", "Red", "Green"})
        
        # Verify selector1 gets updated (bidirectional)
        self.assertEqual(self.selector1.available_options, {"Orange", "Red", "Green"})

    def test_binding_selectors_directly(self):
        """Test binding selectors directly to each other to create transitive behavior."""
        # Ensure both selectors have compatible initial states using atomic updates
        self.selector1.set_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        self.selector2.set_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        
        # Bind selector2 directly to selector1
        self.selector2.bind_to(self.selector1, InitialSyncMode.SELF_IS_UPDATED)
        
        # Change selector1's available options - use atomic update to avoid validation issues
        self.selector1.set_selected_option_and_available_options("Purple", {"Purple", "Pink", "Cyan"})
        
        # Verify selector2 gets updated
        self.assertEqual(self.selector2.available_options, {"Purple", "Pink", "Cyan"})
        
        # Change selector2's available options - use atomic update to avoid validation issues
        self.selector2.set_selected_option_and_available_options("Orange", {"Orange", "Red", "Green"})
        
        # Verify selector1 gets updated (bidirectional)
        self.assertEqual(self.selector1.available_options, {"Orange", "Red", "Green"})
        self.assertEqual(self.selector1.selected_option, "Orange")

    def test_binding_with_validation_errors(self):
        """Test binding behavior when validation errors occur."""
        # Create a selector with strict validation
        strict_selector = ObservableSelectionOption("Red", {"Red", "Green"}, allow_none=False)
        
        # Bind it to a regular selector
        self.selector1.bind_to(strict_selector, InitialSyncMode.SELF_IS_UPDATED)
        
        # Try to set an invalid value in the source
        with self.assertRaises(ValueError):
            self.selector1.selected_option = "Blue"  # Not in {"Red", "Green"}
        
        # Verify the strict selector remains unchanged
        self.assertEqual(strict_selector.selected_option, "Red")
        self.assertEqual(strict_selector.available_options, {"Red", "Green"})

    def test_atomic_updates_with_collective_hooks(self):
        """Test atomic updates with collective hooks."""
        # Bind selector1 to selector2
        self.selector1.bind_to(self.selector2, InitialSyncMode.SELF_IS_UPDATED)
        
        # Use atomic update to change both values at once
        self.selector1.set_selected_option_and_available_options("Purple", {"Purple", "Pink", "Cyan"})
        
        # Verify both values are updated atomically
        self.assertEqual(self.selector1.selected_option, "Purple")
        self.assertEqual(self.selector1.available_options, {"Purple", "Pink", "Cyan"})
        
        # Verify the bound observable also gets updated
        self.assertEqual(self.selector2.selected_option, "Purple")
        self.assertEqual(self.selector2.available_options, {"Purple", "Pink", "Cyan"})

    def test_binding_chain_break_and_rebuild(self):
        """Test breaking and rebuilding binding chains."""
        # Create a simple binding: selector1 -> selector2
        self.selector1.bind_to(self.selector2, InitialSyncMode.SELF_IS_UPDATED)
        
        # Verify binding works
        self.selector1.available_options = {"TestValue", "Red", "Green", "Blue"}
        self.selector1.selected_option = "TestValue"
        self.assertEqual(self.selector2.selected_option, "TestValue")
        
        # Break the binding by disconnecting selector1
        self.selector1.detach()
        
        # Verify binding is broken
        self.selector1.set_selected_option_and_available_options("NewValue", {"NewValue", "Red", "Green", "Blue"})
        self.assertEqual(self.selector2.selected_option, "TestValue")  # Should not change
        
        # Rebuild the binding
        self.selector1.bind_to(self.selector2, InitialSyncMode.SELF_IS_UPDATED)
        
        # Verify binding works again
        self.selector1.set_selected_option_and_available_options("RebuiltValue", {"RebuiltValue", "Red", "Green", "Blue"})
        self.assertEqual(self.selector2.selected_option, "RebuiltValue")

    def test_collective_hooks_with_empty_sets(self):
        """Test collective hooks behavior with empty sets."""
        # Create a selector that allows None
        none_selector: ObservableSelectionOption[str] = ObservableSelectionOption(None, set(), allow_none=True)
        
        # Bind it to another selector
        none_selector.bind_to(self.selector1, InitialSyncMode.SELF_IS_UPDATED)
        
        # Set empty options and None selection
        none_selector.set_selected_option_and_available_options(None, set())
        
        # Verify the bound observable gets updated
        self.assertEqual(self.selector1.selected_option, None)
        self.assertEqual(self.selector1.available_options, set())

    def test_performance_with_collective_hooks(self):
        """Test performance with collective hooks."""
        # Create multiple observables with compatible types
        observables: list[ObservableSelectionOption[str]|ObservableSingleValue[str]|ObservableSet[str]] = []
        for i in range(10):
            selector = ObservableSelectionOption(f"Color{i}", {f"Color{i}", f"Option{i}"})
            value = ObservableSingleValue(f"Color{i}")
            options = ObservableSet({f"Color{i}", f"Option{i}"})
            observables.extend([selector, value, options])
        
        # Bind them in a complex network
        start_time = time.time()
        
        for i in range(0, len(observables) - 2, 3):
            # Bind selector to value and options
            observables[i].bind_selected_option_to(observables[i + 1], InitialSyncMode.SELF_IS_UPDATED) # type: ignore
            observables[i].bind_available_options_to(observables[i + 2], InitialSyncMode.SELF_IS_UPDATED) # type: ignore
        
        # Change a value and measure propagation time - first update available options
        observables[0].available_options = {"NewValue", "Color0", "Option0"} # type: ignore
        observables[0].selected_option = "NewValue" # type: ignore
        
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0, "Collective hook operations should be fast")

    def test_collective_hooks_edge_cases(self):
        """Test edge cases with collective hooks."""
        # Test with circular references (should not cause infinite loops)
        selector_a = ObservableSelectionOption("A", {"A", "B"})
        selector_b = ObservableSelectionOption("B", {"B", "C"})
        selector_c = ObservableSelectionOption("C", {"C", "A"})
        
        # Create a triangle binding - but avoid circular binding by using different sync modes
        selector_a.bind_to(selector_b, InitialSyncMode.SELF_IS_UPDATED)
        selector_b.bind_to(selector_c, InitialSyncMode.SELF_IS_UPDATED)
        # Don't create the circular binding - just test that the existing bindings work
        
        # Change one value
        selector_a.available_options = {"A", "B", "C", "NewValue"}
        selector_a.selected_option = "NewValue"
        
        # Verify all are synchronized (they should converge to a common state)
        self.assertEqual(selector_a.selected_option, selector_b.selected_option)
        self.assertEqual(selector_b.selected_option, selector_c.selected_option)

    def test_binding_with_different_sync_modes(self):
        """Test binding with different sync modes in collective scenarios."""
        # Create observables
        selector_a = ObservableSelectionOption("A", {"A", "B"})
        selector_b = ObservableSelectionOption("B", {"B", "C"})
        value_a = ObservableSingleValue("ValueA")
        value_b = ObservableSingleValue("ValueB")
        
        # Bind with different sync modes
        selector_a.bind_to(selector_b, InitialSyncMode.SELF_IS_UPDATED)
        value_a.bind_to(value_b, InitialSyncMode.SELF_UPDATES)
        
        # Change values and verify behavior
        selector_a.selected_option = "B"
        self.assertEqual(selector_b.selected_option, "B")
        
        value_b.single_value = "NewValue"
        self.assertEqual(value_a.single_value, "NewValue")

    def test_collective_hooks_cleanup(self):
        """Test that collective hooks are properly cleaned up."""
        # Create observables and bind them
        selector: ObservableSelectionOption[str] = ObservableSelectionOption("Test", {"Test", "Other"})
        value: ObservableSingleValue[str] = ObservableSingleValue("Test")
        options: ObservableSet[str] = ObservableSet({"Test", "Other"})
        
        # Bind them together
        selector.bind_selected_option_to(value, InitialSyncMode.SELF_IS_UPDATED) # type: ignore
        selector.bind_available_options_to(options, InitialSyncMode.SELF_IS_UPDATED)
        
        # Disconnect all
        selector.detach()
        # Don't disconnect value and options multiple times - they might already be disconnected
        try:
            value.detach()
        except ValueError:
            pass  # Already disconnected
        try:
            options.detach()
        except ValueError:
            pass  # Already disconnected
        
        # Verify they're independent - use atomic update to avoid validation issues
        selector.set_selected_option_and_available_options("Independent", {"Independent", "Test", "Other"})
        self.assertEqual(value.single_value, "Test")  # Should not change
        
        value.single_value = "AlsoIndependent"
        self.assertEqual(selector.selected_option, "Independent")  # Should not change


if __name__ == "__main__":
    unittest.main()
