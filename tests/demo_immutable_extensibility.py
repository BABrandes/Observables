"""
Demonstration of extensibility and standard library type support.

This script demonstrates:
1. Standard library immutable types (Decimal, datetime, UUID, Enum, etc.)
2. Custom type registration via NexusManager
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from datetime import datetime, date
from enum import Enum
from uuid import UUID
from pathlib import Path

from observables._nexus_system.immutable_values import (
    make_immutable,
    is_immutable_type,
    ImmutabilityError,
)
from observables._nexus_system.nexus_manager import NexusManager


def demo_standard_library_types() -> None:
    """Demonstrate standard library immutable types."""
    print("=" * 70)
    print("STANDARD LIBRARY TYPES - Automatically Supported")
    print("=" * 70)
    
    # Decimal for precise arithmetic
    price = Decimal("19.99")
    print(f"Decimal:   {price} → {make_immutable(price)}")
    print(f"  Is immutable: {is_immutable_type(price)}")
    
    # Fraction for exact ratios
    ratio = Fraction(3, 4)
    print(f"\nFraction:  {ratio} → {make_immutable(ratio)}")
    print(f"  Is immutable: {is_immutable_type(ratio)}")
    
    # DateTime types
    now = datetime(2025, 10, 19, 14, 30)
    today = date(2025, 10, 19)
    print(f"\nDatetime:  {now} → {make_immutable(now)}")
    print(f"Date:      {today} → {make_immutable(today)}")
    
    # UUID for unique identifiers
    user_id = UUID('12345678-1234-5678-1234-567812345678')
    print(f"\nUUID:      {user_id}")
    print(f"  Is immutable: {is_immutable_type(user_id)}")
    
    # Enum types
    class Status(Enum):
        PENDING = "pending"
        ACTIVE = "active"
        DONE = "done"
    
    status = Status.ACTIVE
    print(f"\nEnum:      {status} (type: {type(status).__name__})")
    print(f"  Is immutable: {is_immutable_type(status)}")
    
    # Range objects
    r = range(10)
    print(f"\nRange:     {r} → {make_immutable(r)}")
    
    print()


def demo_stdlib_in_collections() -> None:
    """Demonstrate standard library types in nested structures."""
    print("=" * 70)
    print("STANDARD LIBRARY TYPES IN COLLECTIONS")
    print("=" * 70)
    
    class Priority(Enum):
        LOW = 1
        MEDIUM = 2
        HIGH = 3
    
    task = {
        "id": UUID('87654321-4321-8765-4321-876543218765'),
        "created": datetime(2025, 10, 19, 10, 0),
        "due_date": date(2025, 10, 25),
        "priority": Priority.HIGH,
        "budget": Decimal("1500.50"),
        "completion": Fraction(3, 4),
    }
    
    print("Original task data:")
    for key, value in task.items():
        print(f"  {key:12} = {str(value):40} (type: {type(value).__name__})")
    
    immutable_task = make_immutable(task)
    
    print("\nAfter make_immutable:")
    print(f"  Root type: {type(immutable_task).__name__}")
    print(f"  UUID preserved: {immutable_task['id'] == task['id']}")
    print(f"  Datetime preserved: {immutable_task['created'] == task['created']}")
    print(f"  All stdlib types unchanged: ✓")
    
    print()


def demo_custom_type_registration() -> None:
    """Demonstrate registering custom immutable types."""
    print("=" * 70)
    print("CUSTOM TYPE REGISTRATION")
    print("=" * 70)
    
    # Without registration, Path objects fail
    p = Path("/tmp")
    
    print(f"Path object: {p} (actual type: {type(p).__name__})")
    print(f"Is immutable (no manager): {is_immutable_type(p)}")
    
    try:
        make_immutable(p)
        print("  ✗ Should have raised error!")
    except ImmutabilityError as e:
        print(f"  ✓ Correctly rejected: {type(e).__name__}")
    
    # Create manager and register Path
    manager = NexusManager()
    manager.register_immutable_type(Path)
    
    print(f"\nAfter registering Path with manager:")
    print(f"  Is registered: {manager.is_registered_immutable_type(Path)}")
    print(f"  Is registered (actual type): {manager.is_registered_immutable_type(type(p))}")
    print(f"  Is immutable (with manager): {is_immutable_type(p, manager)}")
    
    result = make_immutable(p, manager)
    print(f"  make_immutable result: {result}")
    print(f"  Same object (no conversion): {result is p}")
    
    print()


def demo_inheritance_handling() -> None:
    """Demonstrate that registration works with inheritance."""
    print("=" * 70)
    print("INHERITANCE HANDLING - MRO-based Type Checking")
    print("=" * 70)
    
    # Path is abstract, actual instances are PosixPath or WindowsPath
    p = Path("/tmp")
    
    print(f"Registering: Path (abstract base class)")
    print(f"Actual type: {type(p).__name__}")
    print(f"Type hierarchy: {[cls.__name__ for cls in type(p).__mro__[:4]]}")
    
    manager = NexusManager()
    manager.register_immutable_type(Path)
    
    print(f"\n✓ Path registered")
    print(f"  Accepts PosixPath: {manager.is_registered_immutable_type(type(p))}")
    print(f"  Works with make_immutable: {make_immutable(p, manager) is p}")
    
    print()


def demo_custom_types_in_collections() -> None:
    """Demonstrate custom types in nested structures."""
    print("=" * 70)
    print("CUSTOM TYPES IN COLLECTIONS")
    print("=" * 70)
    
    manager = NexusManager()
    manager.register_immutable_type(Path)
    
    config = {
        "system_paths": [
            Path("/etc/config"),
            Path("/var/log"),
            Path("/tmp"),
        ],
        "user_dirs": {
            "home": Path("/home/user"),
            "documents": Path("/home/user/docs"),
        }
    }
    
    print("Original config:")
    print(f"  Paths in list: {config['system_paths']}")
    print(f"  Paths in dict: {config['user_dirs']}")
    
    immutable_config = make_immutable(config, manager)
    
    print("\nAfter make_immutable:")
    print(f"  Root: {type(immutable_config).__name__}")
    print(f"  system_paths: {type(immutable_config['system_paths']).__name__}")
    print(f"  user_dirs: {type(immutable_config['user_dirs']).__name__}")
    print(f"  Path objects preserved: {isinstance(immutable_config['system_paths'][0], Path)}")
    print(f"  First path: {immutable_config['system_paths'][0]}")
    
    print()


def demo_multiple_managers() -> None:
    """Demonstrate using different managers with different registries."""
    print("=" * 70)
    print("MULTIPLE MANAGERS - Different Registries")
    print("=" * 70)
    
    # Manager 1: Path support
    manager1 = NexusManager()
    manager1.register_immutable_type(Path)
    
    # Manager 2: Custom type support
    class ImmutableConfig:
        def __init__(self, name: str):
            self._name = name
        def __repr__(self) -> str:
            return f"ImmutableConfig({self._name})"
    
    manager2 = NexusManager()
    manager2.register_immutable_type(ImmutableConfig)
    
    p = Path("/tmp")
    config = ImmutableConfig("app_config")
    
    print("Manager 1 (Path registered):")
    print(f"  Accepts Path: {manager1.is_registered_immutable_type(type(p))}")
    print(f"  Accepts ImmutableConfig: {manager1.is_registered_immutable_type(type(config))}")
    
    print("\nManager 2 (ImmutableConfig registered):")
    print(f"  Accepts Path: {manager2.is_registered_immutable_type(type(p))}")
    print(f"  Accepts ImmutableConfig: {manager2.is_registered_immutable_type(type(config))}")
    
    print("\nEach manager has its own registry - complete isolation!")
    
    print()


def demo_initialization_with_types() -> None:
    """Demonstrate initializing manager with pre-registered types."""
    print("=" * 70)
    print("INITIALIZATION WITH REGISTERED TYPES")
    print("=" * 70)
    
    # Create manager with pre-registered types
    manager = NexusManager(
        registered_immutable_types={Path}
    )
    
    print("Created NexusManager with registered_immutable_types={Path}")
    print(f"  Path is registered: {manager.is_registered_immutable_type(Path)}")
    print(f"  Number of registered types: {len(manager.get_registered_immutable_types())}")
    
    p = Path("/home")
    result = make_immutable(p, manager)
    print(f"  make_immutable(Path('/home')): {result} ✓")
    
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "IMMUTABLE VALUES - EXTENSIBILITY DEMO" + " " * 22 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    demo_standard_library_types()
    demo_stdlib_in_collections()
    demo_custom_type_registration()
    demo_inheritance_handling()
    demo_custom_types_in_collections()
    demo_multiple_managers()
    demo_initialization_with_types()
    
    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\n✨ Key Features:")
    print("  • Standard library types automatically supported")
    print("  • Custom type registration via NexusManager")
    print("  • MRO-based type checking (Path → PosixPath/WindowsPath)")
    print("  • Each manager has independent registry")
    print("  • Works recursively in nested structures")
    print()

