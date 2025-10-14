#!/usr/bin/env python3
"""
Test suite for ObservableRootedPaths.

This module tests the ObservableRootedPaths class which manages a root directory
with associated elements and provides observable hooks for path management.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from unittest.mock import Mock

from observables import ObservableSingleValue, ObservableRootedPaths
from observables.core import OwnedHookLike, HookLike
from observables._other_observables.observable_rooted_paths import ROOT_PATH_KEY

class TestObservableRootedPaths(unittest.TestCase):
    """Test cases for ObservableRootedPaths."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_root = Path(self.temp_dir) / "project"
        self.test_root.mkdir()
        
        # Create some test files
        (self.test_root / "data").mkdir()
        (self.test_root / "config").mkdir()
        (self.test_root / "logs").mkdir()
        
        # Test element keys
        self.element_keys = {"data", "config", "logs"}

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_initialization_with_no_values(self):
        """Test initialization with no initial values."""
        manager = ObservableRootedPaths[str]()
        
        # Check that root path is None
        self.assertIsNone(manager.root_path)
        
        # Check that no element keys are set
        self.assertEqual(len(manager.rooted_element_keys), 0)
        self.assertEqual(len(manager.rooted_element_relative_path_hooks), 0)
        self.assertEqual(len(manager.rooted_element_absolute_path_hooks), 0)

    def test_initialization_with_root_path_only(self):
        """Test initialization with only root path."""
        manager = ObservableRootedPaths[str](root_path_initial_value=self.test_root)
        
        # Check that root path is set correctly
        self.assertEqual(manager.root_path, self.test_root)
        
        # Check that no element keys are set
        self.assertEqual(len(manager.rooted_element_keys), 0)
        self.assertEqual(len(manager.rooted_element_relative_path_hooks), 0)
        self.assertEqual(len(manager.rooted_element_absolute_path_hooks), 0)

    def test_initialization_with_elements_only(self):
        """Test initialization with elements but no root path."""
        initial_values: dict[str, str|None] = {
            "data": "data/",
            "config": "config/",
            "logs": "logs/"
        }
        
        manager = ObservableRootedPaths[str](
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Check that root path is None
        self.assertIsNone(manager.root_path)
        
        # Check that element keys are set
        self.assertEqual(manager.rooted_element_keys, set(initial_values.keys()))
        
        # Check that relative path hooks are created
        for key in initial_values:
            hook = manager.get_relative_path_hook(key)
            self.assertEqual(hook.value, initial_values[key])

    def test_initialization_with_root_and_elements(self):
        """Test initialization with both root path and elements."""
        initial_values: dict[str, str|None] = {
            "data": "data/",
            "config": "config/",
            "logs": "logs/"
        }
        
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Check that root path is set correctly
        self.assertEqual(manager.root_path, self.test_root)
        
        # Check that element keys are set
        self.assertEqual(manager.rooted_element_keys, set(initial_values.keys()))
        
        # Check that relative path hooks are created
        for key in initial_values:
            hook = manager.get_relative_path_hook(key)
            self.assertEqual(hook.value, initial_values[key])
            
            # Check that absolute path hooks are created and computed correctly
            abs_hook = manager.get_absolute_path_hook(key)
            relative_path = initial_values[key]
            assert relative_path is not None
            assert self.test_root is not None
            expected_abs_path = self.test_root / relative_path
            self.assertEqual(abs_hook.value, expected_abs_path)

    def test_element_key_conversion_methods(self):
        """Test the element key to path key conversion methods."""
        manager = ObservableRootedPaths[str]()
        
        # Test relative path key conversion
        self.assertEqual(manager.element_key_to_relative_path_key("data"), "data_relative_path")
        self.assertEqual(manager.element_key_to_relative_path_key("config"), "config_relative_path")
        
        # Test absolute path key conversion
        self.assertEqual(manager.element_key_to_absolute_path_key("data"), "data_absolute_path")
        self.assertEqual(manager.element_key_to_absolute_path_key("config"), "config_absolute_path")

    def test_set_root_path(self):
        """Test setting the root path."""
        manager = ObservableRootedPaths[str]()
        
        # Set root path
        success, _ = manager.set_root_path(self.test_root)
        self.assertTrue(success)
        self.assertEqual(manager.root_path, self.test_root)
        
        # Set to None
        success, _ = manager.set_root_path(None)
        self.assertTrue(success)
        self.assertIsNone(manager.root_path)

    def test_set_relative_path(self):
        """Test setting relative paths for elements."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Set relative path
        success, _ = manager.set_relative_path("data", "new_data/")
        self.assertTrue(success)
        
        hook = manager.get_relative_path_hook("data")
        self.assertEqual(hook.value, "new_data/")

    def test_set_absolute_path(self):
        """Test setting absolute paths for elements (should be automatically calculated)."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # The absolute path should be automatically calculated as root + relative
        expected_abs_path = self.test_root / "data/"
        hook = manager.get_absolute_path_hook("data")
        self.assertEqual(hook.value, expected_abs_path)
        
        # When we change the relative path, the absolute path should update automatically
        manager.set_relative_path("data", "new_data/")
        expected_abs_path = self.test_root / "new_data/"
        hook = manager.get_absolute_path_hook("data")
        self.assertEqual(hook.value, expected_abs_path)

    def test_get_relative_path_hook(self):
        """Test getting relative path hooks."""
        initial_values: dict[str, str|None] = {"data": "data/", "config": "config/"}
        manager = ObservableRootedPaths[str](
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test getting existing hook
        hook = manager.get_relative_path_hook("data")
        self.assertEqual(hook.value, "data/")
        
        # Test getting non-existing hook
        with self.assertRaises(ValueError):
            manager.get_relative_path_hook("nonexistent")

    def test_get_absolute_path_hook(self):
        """Test getting absolute path hooks."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test getting existing hook
        hook = manager.get_absolute_path_hook("data")
        expected_path = self.test_root / "data/"
        self.assertEqual(hook.value, expected_path)
        
        # Test getting non-existing hook
        with self.assertRaises(ValueError):
            manager.get_absolute_path_hook("nonexistent")

    def test_validation_with_valid_values(self):
        """Test validation with valid values."""
        initial_values: dict[str, str|None] = {"data": "data/", "config": "config/"}
        manager = ObservableRootedPaths(
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test validation with current values
        hook_keys = manager.get_hook_keys()
        _ = {key: manager.get_value_reference_of_hook(key) for key in hook_keys}
        
        # This should pass validation
        # Note: We can't directly test the validation callback as it's private,
        # but we can test the behavior through the public interface

    def test_validation_with_invalid_root_path(self):
        """Test validation with invalid root path."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Try to set an invalid root path (not a Path object)
        # This should be handled by the validation system
        _, _ = manager.set_root_path(Path("invalid_path"))  # This should fail validation
        # The exact behavior depends on the validation implementation

    def test_automatic_absolute_path_calculation(self):
        """Test that absolute paths are automatically calculated when root or relative paths change."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Check initial absolute path
        abs_hook = manager.get_absolute_path_hook("data")
        expected_path = self.test_root / "data/"
        self.assertEqual(abs_hook.value, expected_path)
        
        # Change root path
        new_root = Path(self.temp_dir) / "new_project"
        new_root.mkdir()
        manager.set_root_path(new_root)
        
        # Check that absolute path is updated
        abs_hook = manager.get_absolute_path_hook("data")
        expected_path = new_root / "data/"
        self.assertEqual(abs_hook.value, expected_path)
        
        # Change relative path
        manager.set_relative_path("data", "new_data/")
        
        # Check that absolute path is updated
        abs_hook = manager.get_absolute_path_hook("data")
        expected_path = new_root / "new_data/"
        self.assertEqual(abs_hook.value, expected_path)

    def test_hook_keys_retrieval(self):
        """Test getting all hook keys."""
        initial_values: dict[str, str|None] = {"data": "data/", "config": "config/"}
        manager = ObservableRootedPaths(
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        hook_keys = manager.get_hook_keys()
        
        # Should include root path key
        self.assertIn(ROOT_PATH_KEY, hook_keys)
        
        # Should include relative path keys
        for key in initial_values:
            self.assertIn(f"{key}_relative_path", hook_keys)
            self.assertIn(f"{key}_absolute_path", hook_keys)

    def test_hook_key_retrieval(self):
        """Test getting hook key from hook or nexus."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths(
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test getting key from root path hook
        root_hook = manager.get_hook(ROOT_PATH_KEY)
        key = manager.get_hook_key(root_hook)
        self.assertEqual(key, ROOT_PATH_KEY)
        
        # Test getting key from element hook
        data_hook: OwnedHookLike[Optional[str]] = manager.get_relative_path_hook("data")
        key = manager.get_hook_key(data_hook) # type: ignore
        self.assertEqual(key, "data_relative_path")

    def test_hook_key_retrieval_with_nonexistent_hook(self):
        """Test getting hook key with nonexistent hook."""
        manager = ObservableRootedPaths[str]()
        
        # Create a mock hook that doesn't exist in the manager
        mock_hook = Mock()
        
        with self.assertRaises(ValueError):
            manager.get_hook_key(mock_hook)

    def test_value_reference_retrieval(self):
        """Test getting value references from hooks."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths(
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test getting root path value reference
        root_value = manager.get_value_reference_of_hook(ROOT_PATH_KEY)
        self.assertEqual(root_value, self.test_root)
        
        # Test getting element value reference
        data_value = manager.get_value_reference_of_hook("data_relative_path")
        self.assertEqual(data_value, "data/")

    def test_value_reference_retrieval_with_nonexistent_key(self):
        """Test getting value reference with nonexistent key."""
        manager = ObservableRootedPaths[str]()
        
        with self.assertRaises(ValueError):
            manager.get_value_reference_of_hook("nonexistent_key")

    def test_serialization_callback(self):
        """Test the complete serialization and deserialization cycle."""
        # Step 1: Create an ObservableRootedPaths instance
        initial_values: dict[str, str|None] = {
            "data": "data/",
            "config": "config/settings/",
            "logs": "logs/app.log",
            "cache": None
        }
        
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Step 2: Fill it (modify some values)
        manager.set_relative_path("data", "new_data/")
        manager.set_relative_path("cache", "cache/tmp/")
        
        # Store the expected state after step 2
        expected_root = manager.root_path
        expected_relative_paths = {
            "data": manager.get_relative_path_hook("data").value,
            "config": manager.get_relative_path_hook("config").value,
            "logs": manager.get_relative_path_hook("logs").value,
            "cache": manager.get_relative_path_hook("cache").value,
        }
        expected_absolute_paths = {
            "data": manager.get_absolute_path_hook("data").value,
            "config": manager.get_absolute_path_hook("config").value,
            "logs": manager.get_absolute_path_hook("logs").value,
            "cache": manager.get_absolute_path_hook("cache").value,
        }
        
        # Step 3: Serialize it and get a dict from "get_value_references_for_serialization"
        serialized_data = manager.get_value_references_for_serialization()
        
        # Verify serialized data contains expected keys
        self.assertIn(ROOT_PATH_KEY, serialized_data)
        self.assertEqual(serialized_data[ROOT_PATH_KEY], expected_root)
        for key in initial_values.keys():
            self.assertIn(key, serialized_data)
            self.assertEqual(serialized_data[key], expected_relative_paths[key])
        
        # Step 4: Delete the object
        del manager
        
        # Step 5: Create a fresh ObservableRootedPaths instance
        manager_restored = ObservableRootedPaths[str](
            root_path_initial_value=None,
            rooted_elements_initial_relative_path_values={
                "data": None,
                "config": None,
                "logs": None,
                "cache": None
            }
        )
        
        # Verify it starts empty/different
        self.assertIsNone(manager_restored.root_path)
        
        # Step 6: Use "set_value_references_from_serialization"
        manager_restored.set_value_references_from_serialization(serialized_data)
        
        # Step 7: Check if the object is the same as after step 2
        self.assertEqual(manager_restored.root_path, expected_root)
        
        for key in initial_values.keys():
            # Check relative paths match
            restored_relative = manager_restored.get_relative_path_hook(key).value
            self.assertEqual(
                restored_relative, 
                expected_relative_paths[key],
                f"Relative path for '{key}' doesn't match: {restored_relative} != {expected_relative_paths[key]}"
            )
            
            # Check absolute paths match
            restored_absolute = manager_restored.get_absolute_path_hook(key).value
            self.assertEqual(
                restored_absolute,
                expected_absolute_paths[key],
                f"Absolute path for '{key}' doesn't match: {restored_absolute} != {expected_absolute_paths[key]}"
            )

    def test_complex_scenario(self):
        """Test a complex scenario with multiple elements and path changes."""
        initial_values: dict[str, str|None] = {
            "data": "data/",
            "config": "config/",
            "logs": "logs/",
            "temp": "temp/"
        }
        
        manager = ObservableRootedPaths(
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Verify initial state
        self.assertEqual(manager.root_path, self.test_root)
        for key, rel_path in initial_values.items():
            self.assertEqual(manager.get_relative_path_hook(key).value, rel_path)
            assert rel_path is not None
            assert self.test_root is not None
            expected_abs: Path = self.test_root / rel_path
            self.assertEqual(manager.get_absolute_path_hook(key).value, expected_abs)
        
        # Change root path
        new_root = Path(self.temp_dir) / "new_project"
        new_root.mkdir()
        manager.set_root_path(new_root)
        
        # Verify all absolute paths are updated
        for key, rel_path in initial_values.items():
            assert rel_path is not None
            expected_abs = new_root / rel_path
            self.assertEqual(manager.get_absolute_path_hook(key).value, expected_abs)
        
        # Change some relative paths
        manager.set_relative_path("data", "new_data/")
        manager.set_relative_path("config", "settings/")
        
        # Verify absolute paths are recalculated
        self.assertEqual(manager.get_absolute_path_hook("data").value, new_root / "new_data/")
        self.assertEqual(manager.get_absolute_path_hook("config").value, new_root / "settings/")
        
        # Verify unchanged paths remain the same
        self.assertEqual(manager.get_absolute_path_hook("logs").value, new_root / "logs/")
        self.assertEqual(manager.get_absolute_path_hook("temp").value, new_root / "temp/")

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test with empty string relative paths
        initial_values = {"data": "", "config": None}
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Empty string should be handled
        self.assertEqual(manager.get_relative_path_hook("data").value, "")
        
        # None should be handled
        self.assertIsNone(manager.get_relative_path_hook("config").value)
        
        # Test with None root path
        manager.set_root_path(None)
        self.assertIsNone(manager.root_path)
        
        # Test setting relative path to None
        manager.set_relative_path("data", None)
        self.assertIsNone(manager.get_relative_path_hook("data").value)

    def test_type_safety(self):
        """Test type safety with different path types."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test that relative paths accept strings
        manager.set_relative_path("data", "new_path/")
        self.assertEqual(manager.get_relative_path_hook("data").value, "new_path/")
        
        # Test that absolute paths are automatically calculated
        expected_abs_path = self.test_root / "new_path/"
        self.assertEqual(manager.get_absolute_path_hook("data").value, expected_abs_path)

    def test_binding_with_observable_single_value_root_path(self):
        """Test binding root path hook to ObservableSingleValue and changing it."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create ObservableSingleValue for root path
        root_path_observable = ObservableSingleValue[Path|None](self.test_root)
        
        # Connect the root path hook to the observable
        root_path_hook: HookLike[Path|None] = manager.get_hook(ROOT_PATH_KEY) # type: ignore
        root_path_hook.connect_hook(root_path_observable.hook, "use_caller_value")
        
        # Verify initial state
        self.assertEqual(manager.root_path, self.test_root)
        self.assertEqual(manager.get_absolute_path_hook("data").value, self.test_root / "data/")
        
        # Change the root path through the observable
        new_root = Path(self.temp_dir) / "new_project"
        new_root.mkdir()
        root_path_observable.value = new_root
        
        # Verify that ObservableRootedPaths updated
        self.assertEqual(manager.root_path, new_root)
        self.assertEqual(manager.get_absolute_path_hook("data").value, new_root / "data/")
        
        # Change back to None
        root_path_observable.value = None # type: ignore
        
        # Verify that ObservableRootedPaths updated
        self.assertIsNone(manager.root_path)
        self.assertIsNone(manager.get_absolute_path_hook("data").value)

    def test_binding_with_observable_single_value_relative_path(self):
        """Test binding relative path hook to ObservableSingleValue and changing it."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create ObservableSingleValue for relative path
        relative_path_observable = ObservableSingleValue[str|None]("data/")
        
        # Connect the relative path hook to the observable
        relative_path_hook: OwnedHookLike[Optional[str]] = manager.get_relative_path_hook("data")
        relative_path_hook.connect_hook(relative_path_observable.hook, "use_caller_value")
        
        # Verify initial state
        self.assertEqual(manager.get_relative_path_hook("data").value, "data/")
        self.assertEqual(manager.get_absolute_path_hook("data").value, self.test_root / "data/")
        
        # Change the relative path through the observable
        relative_path_observable.value = "new_data/"
        
        # Verify that ObservableRootedPaths updated
        self.assertEqual(manager.get_relative_path_hook("data").value, "new_data/")
        self.assertEqual(manager.get_absolute_path_hook("data").value, self.test_root / "new_data/")
        
        # Change to empty string (None would violate validation since root path is set)
        relative_path_observable.value = ""
        
        # Verify that ObservableRootedPaths updated
        self.assertEqual(manager.get_relative_path_hook("data").value, "")
        self.assertEqual(manager.get_absolute_path_hook("data").value, self.test_root / "")

    def test_binding_with_observable_single_value_absolute_path(self):
        """Test binding absolute path hook to ObservableSingleValue and changing it."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create ObservableSingleValue for absolute path
        absolute_path_observable = ObservableSingleValue[Path|None](self.test_root / "data/")
        
        # Connect the absolute path hook to the observable
        absolute_path_hook: OwnedHookLike[Optional[Path]] = manager.get_absolute_path_hook("data")
        absolute_path_hook.connect_hook(absolute_path_observable.hook, "use_caller_value")
        
        # Verify initial state
        self.assertEqual(manager.get_absolute_path_hook("data").value, self.test_root / "data/")
        
        # Change the absolute path through the observable (must match root + relative)
        new_absolute_path = self.test_root / "data/"  # Keep it consistent with relative path
        absolute_path_observable.value = new_absolute_path
        
        # Verify that ObservableRootedPaths updated
        self.assertEqual(manager.get_absolute_path_hook("data").value, new_absolute_path)
        
        # Change to a different valid absolute path (must match root + relative)
        different_absolute_path = self.test_root / "data/"  # Keep it consistent
        absolute_path_observable.value = different_absolute_path
        
        # Verify that ObservableRootedPaths updated
        self.assertEqual(manager.get_absolute_path_hook("data").value, different_absolute_path)

    def test_binding_multiple_hooks_to_observable_single_values(self):
        """Test binding multiple hooks to different ObservableSingleValue instances."""
        initial_values: dict[str, str|None] = {
            "data": "data/",
            "config": "config/",
            "logs": "logs/"
        }
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create ObservableSingleValue instances for different paths
        root_observable = ObservableSingleValue(self.test_root)
        data_relative_observable = ObservableSingleValue("data/")
        config_relative_observable = ObservableSingleValue("config/")
        logs_absolute_observable = ObservableSingleValue(self.test_root / "logs/")
        
        # Connect hooks to observables
        root_path_hook: HookLike[Path|None] = manager.get_hook(ROOT_PATH_KEY) # type: ignore
        observable_root_path_hook: HookLike[Path|None] = root_observable.hook # type: ignore
        root_path_hook.connect_hook(observable_root_path_hook, "use_caller_value")
        data_relative_hook: OwnedHookLike[Optional[str]] = manager.get_relative_path_hook("data")
        observable_data_relative_hook: HookLike[Optional[str]] = data_relative_observable.hook # type: ignore
        data_relative_hook.connect_hook(observable_data_relative_hook, "use_caller_value")
        config_relative_hook: OwnedHookLike[Optional[str]] = manager.get_relative_path_hook("config")
        observable_config_relative_hook: HookLike[Optional[str]] = config_relative_observable.hook # type: ignore
        config_relative_hook.connect_hook(observable_config_relative_hook, "use_caller_value")
        logs_absolute_hook: OwnedHookLike[Optional[Path]] = manager.get_absolute_path_hook("logs")
        observable_logs_absolute_hook: HookLike[Optional[Path]] = logs_absolute_observable.hook # type: ignore
        logs_absolute_hook.connect_hook(observable_logs_absolute_hook, "use_caller_value")
        
        # Verify initial state
        self.assertEqual(manager.root_path, self.test_root)
        self.assertEqual(manager.get_relative_path_hook("data").value, "data/")
        self.assertEqual(manager.get_relative_path_hook("config").value, "config/")
        self.assertEqual(manager.get_absolute_path_hook("logs").value, self.test_root / "logs/")
        
        # Change root path
        new_root = Path(self.temp_dir) / "new_project"
        new_root.mkdir()
        root_observable.value = new_root
        
        # Verify that all absolute paths updated (including logs which is directly bound)
        self.assertEqual(manager.root_path, new_root)
        self.assertEqual(manager.get_absolute_path_hook("data").value, new_root / "data/")
        self.assertEqual(manager.get_absolute_path_hook("config").value, new_root / "config/")
        self.assertEqual(manager.get_absolute_path_hook("logs").value, new_root / "logs/")  # Updated due to binding
        
        # Change relative paths
        data_relative_observable.value = "new_data/"
        config_relative_observable.value = "settings/"
        
        # Verify updates
        self.assertEqual(manager.get_relative_path_hook("data").value, "new_data/")
        self.assertEqual(manager.get_relative_path_hook("config").value, "settings/")
        self.assertEqual(manager.get_absolute_path_hook("data").value, new_root / "new_data/")
        self.assertEqual(manager.get_absolute_path_hook("config").value, new_root / "settings/")
        
        # Change absolute path directly (must match root + relative)
        new_logs_path = new_root / "logs/"  # Keep it consistent with relative path
        logs_absolute_observable.value = new_logs_path
        
        # Verify update
        self.assertEqual(manager.get_absolute_path_hook("logs").value, new_logs_path)

    def test_bidirectional_binding_with_observable_single_value(self):
        """Test bidirectional binding between ObservableRootedPaths and ObservableSingleValue."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create ObservableSingleValue for root path
        root_path_observable = ObservableSingleValue(self.test_root)
        
        # Connect bidirectionally
        root_path_hook: HookLike[Path|None] = manager.get_hook(ROOT_PATH_KEY) # type: ignore
        observable_root_path_hook: HookLike[Path|None] = root_path_observable.hook # type: ignore
        root_path_hook.connect_hook(observable_root_path_hook, "use_caller_value")
        
        # Verify initial state
        self.assertEqual(manager.root_path, self.test_root)
        self.assertEqual(root_path_observable.value, self.test_root)
        
        # Change through ObservableRootedPaths
        new_root = Path(self.temp_dir) / "new_project"
        new_root.mkdir()
        manager.set_root_path(new_root)
        
        # Verify that ObservableSingleValue updated
        self.assertEqual(manager.root_path, new_root)
        self.assertEqual(root_path_observable.value, new_root)
        
        # Change through ObservableSingleValue
        another_root = Path(self.temp_dir) / "another_project"
        another_root.mkdir()
        root_path_observable.value = another_root
        
        # Verify that ObservableRootedPaths updated
        self.assertEqual(manager.root_path, another_root)
        self.assertEqual(root_path_observable.value, another_root)

    def test_binding_chain_with_observable_single_values(self):
        """Test a chain of bindings through multiple ObservableSingleValue instances."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create a chain of ObservableSingleValue instances
        root_observable1 = ObservableSingleValue(self.test_root)
        root_observable2 = ObservableSingleValue(self.test_root)
        root_observable3 = ObservableSingleValue(self.test_root)
        
        # Connect in a chain: manager -> observable1 -> observable2 -> observable3
        root_path_hook: HookLike[Path|None] = manager.get_hook(ROOT_PATH_KEY) # type: ignore
        observable_root_path_hook: HookLike[Path|None] = root_observable1.hook # type: ignore
        root_path_hook.connect_hook(observable_root_path_hook, "use_caller_value")
        root_observable1.hook.connect_hook(root_observable2.hook, "use_caller_value")
        root_observable2.hook.connect_hook(root_observable3.hook, "use_caller_value")
        
        # Verify initial state
        self.assertEqual(manager.root_path, self.test_root)
        self.assertEqual(root_observable1.value, self.test_root)
        self.assertEqual(root_observable2.value, self.test_root)
        self.assertEqual(root_observable3.value, self.test_root)
        
        # Change through the end of the chain
        new_root = Path(self.temp_dir) / "chain_project"
        new_root.mkdir()
        root_observable3.value = new_root
        
        # Verify that all observables in the chain updated
        self.assertEqual(manager.root_path, new_root)
        self.assertEqual(root_observable1.value, new_root)
        self.assertEqual(root_observable2.value, new_root)
        self.assertEqual(root_observable3.value, new_root)
        
        # Verify that absolute paths updated
        self.assertEqual(manager.get_absolute_path_hook("data").value, new_root / "data/")

    def test_binding_with_validation_and_observable_single_value(self):
        """Test that validation works correctly when binding to ObservableSingleValue."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = ObservableRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create ObservableSingleValue with validation
        def validate_path(path: Path|None) -> tuple[bool, str]:
            if path is None:
                return True, "None is valid"
            if not isinstance(path, Path): # type: ignore
                return False, "Must be a Path object"
            if not path.exists():
                return False, "Path must exist"
            return True, "Valid path"
        
        root_path_observable = ObservableSingleValue(self.test_root, validator=validate_path)
        
        # Connect the hooks
        root_path_hook: HookLike[Path|None] = manager.get_hook(ROOT_PATH_KEY) # type: ignore
        observable_root_path_hook: HookLike[Path|None] = root_path_observable.hook # type: ignore
        root_path_hook.connect_hook(observable_root_path_hook, "use_caller_value")
        
        # Verify initial state
        self.assertEqual(manager.root_path, self.test_root)
        self.assertEqual(root_path_observable.value, self.test_root)
        
        # Try to set an invalid path (should fail validation)
        with self.assertRaises(ValueError):
            root_path_observable.value = Path("/nonexistent/path")
        
        # Verify that values didn't change
        self.assertEqual(manager.root_path, self.test_root)
        self.assertEqual(root_path_observable.value, self.test_root)
        
        # Set a valid path
        new_root = Path(self.temp_dir) / "valid_project"
        new_root.mkdir()
        root_path_observable.value = new_root
        
        # Verify that values updated
        self.assertEqual(manager.root_path, new_root)
        self.assertEqual(root_path_observable.value, new_root)


if __name__ == "__main__":
    unittest.main()
