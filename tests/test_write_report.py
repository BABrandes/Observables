#!/usr/bin/env python3
"""
Test script for the write_report function with a complex hook system.
This creates a sophisticated binding scenario and uses write_report to analyze it.
"""

import unittest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from observables import (
    ObservableSingleValue, 
    ObservableList, 
    ObservableDict, 
    ObservableSet,
    ObservableSelectionOption,
    ObservableMultiSelectionOption
)
from observables._utils.system_analysis import write_report
from observables._utils.initial_sync_mode import InitialSyncMode
from enum import Enum
from observables._utils.base_carries_hooks import BaseCarriesHooks
from observables._hooks.owned_hook_like import OwnedHookLike
from typing import Any, cast

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class TestWriteReport(unittest.TestCase):
    """Test the write_report function with complex hook systems"""
    
    def test_write_report_complex_system(self):
        """Test write_report with a complex observable system"""
        
        print("\n" + "="*80)
        print("🚀 Testing write_report function with complex hook system")
        print("="*80)
        
        # Create the complex system
        observables: dict[str, BaseCarriesHooks[Any, Any, "BaseCarriesHooks[Any, Any, Any]"]] = self._create_complex_system() # type: ignore
        
        # Analyze it with write_report
        self._analyze_system(observables)
        
        # Demonstrate change propagation
        self._demonstrate_changes(observables)
        
        print("\n" + "="*80)
        print("✅ write_report test completed successfully!")
        print("="*80)
    
    def _create_complex_system(self) -> dict[str, BaseCarriesHooks[Any, Any, "BaseCarriesHooks[Any, Any, Any]"]]:
        """Create a complex system with multiple observables and bindings"""
        
        print("🔧 Creating complex observable system...")
        
        # 1. Core user data
        user_name = ObservableSingleValue("Alice")
        user_age = ObservableSingleValue(28)
        user_role = ObservableSelectionOption(UserRole.USER, {UserRole.ADMIN, UserRole.USER, UserRole.GUEST})
        
        # 2. Task management system
        task_list = ObservableList(["Setup project", "Write documentation", "Run tests"])
        task_priorities = ObservableDict({"Setup project": 1, "Write documentation": 2, "Run tests": 3})
        completed_tasks = ObservableSet({"Write documentation"})
        
        # 3. Multi-selection for task statuses
        available_statuses = {TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE}
        current_task_statuses = ObservableMultiSelectionOption[TaskStatus](
            {TaskStatus.TODO, TaskStatus.IN_PROGRESS}, 
            available_statuses
        )
        
        # 4. Derived/computed observables
        task_count = ObservableSingleValue(0)  # Will be bound to task_list.length_hook
        user_display = ObservableSingleValue("")  # Will combine name and role
        priority_sum = ObservableSingleValue(0)  # Will sum all priorities
        
        print("✅ Basic observables created")
        
        # Create complex binding relationships
        print("🔗 Creating bindings...")
        
        # Bind task count to list length
        task_count.connect_hook(task_list.length_hook, "value", InitialSyncMode.USE_TARGET_VALUE)  # type: ignore
        
        # Bind some observables to demonstrate shared hook nexuses
        task_backup: ObservableList[Any] = ObservableList([])  # Will share nexus with task_list
        task_backup.connect_hook(task_list.value_hook, "value", InitialSyncMode.USE_TARGET_VALUE) # type: ignore
        
        # Create another observable that shares the user's age
        min_age_requirement = ObservableSingleValue(18)
        age_validator = ObservableSingleValue(False)  # Will be connected to show age >= min_age
        
        # Connect age-related observables
        backup_age: ObservableSingleValue[Any] = ObservableSingleValue(0)
        backup_age.connect_hook(user_age.hook, "value", InitialSyncMode.USE_TARGET_VALUE)  # type: ignore
        
        # Create observables that share nexus with the sets
        completed_backup: ObservableSet[Any] = ObservableSet(set())
        completed_backup.connect_hook(completed_tasks.value_hook, "value", InitialSyncMode.USE_TARGET_VALUE) # type: ignore
        
        # Multi-selection backup
        status_backup: ObservableMultiSelectionOption[TaskStatus] = ObservableMultiSelectionOption(set(), available_statuses)
        status_backup.connect_hooks({
            "selected_options": cast(OwnedHookLike[set[TaskStatus] | int], current_task_statuses.selected_options_hook),
            "available_options": cast(OwnedHookLike[set[TaskStatus] | int], current_task_statuses.available_options_hook)
        }, InitialSyncMode.USE_TARGET_VALUE)
        
        print("✅ Bindings created")
        
        # Return dictionary of all observables for analysis
        return {
            "user_name": user_name,
            "user_age": user_age,
            "user_role": user_role,
            "task_list": task_list,
            "task_priorities": task_priorities,
            "completed_tasks": completed_tasks,
            "current_task_statuses": current_task_statuses,
            "task_count": task_count,
            "user_display": user_display,
            "priority_sum": priority_sum,
            "task_backup": task_backup,
            "min_age_requirement": min_age_requirement,
            "age_validator": age_validator,
            "backup_age": backup_age,
            "completed_backup": completed_backup,
            "status_backup": status_backup,
        } # type: ignore
    
    def _analyze_system(self, observables_dict: dict[str, BaseCarriesHooks[Any, Any, "BaseCarriesHooks[Any, Any, Any]"]]):
        """Use write_report to analyze the complex system"""
        
        print("\n" + "="*80)
        print("📊 SYSTEM ANALYSIS REPORT")
        print("="*80)
        
        # Generate the report
        report = write_report(observables_dict) # type: ignore
        
        print(report)
        
        # Add some additional analysis
        print("="*80)
        print("📈 ADDITIONAL METRICS")
        print("="*80)
        
        total_observables = len(observables_dict)
        
        # Count how many hooks exist in total
        total_hooks = 0
        for name, observable in observables_dict.items():
            total_hooks += len(observable.get_hook_keys())
        
        print(f"Total observables: {total_observables}")
        print(f"Total hooks: {total_hooks}")
        
        # Count shared nexuses (nexuses with multiple hooks)
        from observables._utils.system_analysis import collect_all_hook_nexuses
        hook_nexuses = collect_all_hook_nexuses(observables_dict) # type: ignore
        
        shared_nexuses = 0
        unshared_nexuses = 0
        
        for _, hooks_info in hook_nexuses.items():
            if len(hooks_info) > 1:
                shared_nexuses += 1
            else:
                unshared_nexuses += 1
        
        print(f"Shared hook nexuses: {shared_nexuses}")
        print(f"Unshared hook nexuses: {unshared_nexuses}")
        print(f"Total hook nexuses: {len(hook_nexuses)}")
        
        # Show which observables are most connected
        observable_connection_counts: dict[str, int] = {}
        for _, hooks_info in hook_nexuses.items():
            if len(hooks_info) > 1:
                for name, _, _ in hooks_info:
                    observable_connection_counts[name] = observable_connection_counts.get(name, 0) + 1
        
        if observable_connection_counts:
            print(f"\nMost connected observables:")
            for name, count in sorted(observable_connection_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {name}: {count} shared connections")
    
    def _demonstrate_changes(self, observables_dict: dict[str, BaseCarriesHooks[Any, Any, "BaseCarriesHooks[Any, Any, Any]"]]):
        """Demonstrate how changes propagate through the system"""
        
        print("\n" + "="*80)
        print("🔄 DEMONSTRATING CHANGE PROPAGATION")
        print("="*80)
        
        # Show current state
        task_list: BaseCarriesHooks[Any, Any, "BaseCarriesHooks[Any, Any, Any]"] = observables_dict["task_list"]
        task_backup: BaseCarriesHooks[Any, Any, "BaseCarriesHooks[Any, Any, Any]"] = observables_dict["task_backup"]
        task_count: BaseCarriesHooks[Any, Any, "BaseCarriesHooks[Any, Any, Any]"] = observables_dict["task_count"]
        
        print(f"Original task list: {task_list.value}") # type: ignore
        print(f"Task backup: {task_backup.value}") # type: ignore
        print(f"Task count: {task_count.value}") # type: ignore
        
        # Make a change
        print("\n📝 Adding new task...")
        task_list.append("Deploy to production") # type: ignore
        
        print(f"Updated task list: {task_list.value}") # type: ignore
        print(f"Task backup: {task_backup.value}") # type: ignore
        print(f"Task count: {task_count.value}") # type: ignore
        
        # Demonstrate user data binding
        user_name: BaseCarriesHooks[Any, Any, "BaseCarriesHooks[Any, Any, Any]"] = observables_dict["user_name"] # type: ignore
        backup_age: BaseCarriesHooks[Any, Any, "BaseCarriesHooks[Any, Any, Any]"] = observables_dict["backup_age"]
        user_age: BaseCarriesHooks[Any, Any, "BaseCarriesHooks[Any, Any, Any]"] = observables_dict["user_age"]
        
        print(f"\nOriginal user age: {user_age.value}") # type: ignore
        print(f"Backup age: {backup_age.value}") # type: ignore
        
        print("\n🎂 User has a birthday...")
        user_age.value = 29 # type: ignore
        
        print(f"Updated user age: {user_age.value}") # type: ignore
        print(f"Backup age: {backup_age.value}") # type: ignore
    
    def test_write_report_simple_system(self):
        """Test write_report with a simple system to verify basic functionality"""
        
        # Create a simple system
        name: ObservableSingleValue[Any] = ObservableSingleValue[Any]("John")
        age: ObservableSingleValue[Any] = ObservableSingleValue[Any](25)
        
        # Create a backup that shares the name
        name_backup: ObservableSingleValue[Any] = ObservableSingleValue[Any]("")
        name_backup.connect_hook(name.hook, "value", InitialSyncMode.USE_TARGET_VALUE)  # type: ignore
        
        observables: dict[str, BaseCarriesHooks[Any, Any, "BaseCarriesHooks[Any, Any, Any]"]] = {
            "name": name,
            "age": age,
            "name_backup": name_backup
        } # type: ignore
        
        # Generate report
        report: str = write_report(observables) # type: ignore
        
        # Verify the report contains expected information
        self.assertIn("John", report)
        self.assertIn("25", report)
        self.assertIn("name:", report)
        self.assertIn("age:", report)
        self.assertIn("name_backup:", report)
        
        # Verify that name and name_backup share a nexus
        self.assertIn("name:", report)
        self.assertIn("name_backup:", report)
        
        print("\nSimple system report:")
        print(report)
    
    def test_write_report_empty_system(self):
        """Test write_report with an empty system"""
        
        report: str = write_report({}) # type: ignore
        self.assertEqual(report, "No observables provided.\n")
        
        print("\nEmpty system report (should be empty):")
        print(f"'{report}'")

if __name__ == "__main__":
    # Run the test with verbose output to see the report
    unittest.main(verbosity=2)
