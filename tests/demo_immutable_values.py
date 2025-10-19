"""
Demonstration of immutable values functionality.

This script demonstrates how to use the make_immutable function
to ensure data integrity in the nexus system.
"""

from dataclasses import dataclass
import immutables

from observables._nexus_system.immutable_values import (
    make_immutable,
    is_immutable_type,
    validate_immutable,
    ImmutabilityError,
)


def demo_primitives() -> None:
    """Demonstrate that primitives are already immutable."""
    print("=" * 60)
    print("PRIMITIVES - Already Immutable")
    print("=" * 60)
    
    # Primitives pass through unchanged
    values = [42, 3.14, "hello", True, None, b"bytes", 1+2j]
    
    for value in values:
        result = make_immutable(value)
        print(f"{type(value).__name__:12} {str(value):20} → {result}")
        assert value is result  # Same object, no conversion needed
    print()


def demo_frozen_dataclass() -> None:
    """Demonstrate frozen dataclasses."""
    print("=" * 60)
    print("FROZEN DATACLASSES - Immutable by Design")
    print("=" * 60)
    
    @dataclass(frozen=True)
    class Point:
        x: int
        y: int
    
    @dataclass(frozen=True)
    class Circle:
        center: Point
        radius: float
    
    # Frozen dataclasses are recognized as immutable
    p = Point(10, 20)
    print(f"Point: {p}")
    print(f"Is immutable: {is_immutable_type(p)}")
    print(f"After make_immutable: {make_immutable(p)}")
    
    c = Circle(p, 5.0)
    print(f"\nCircle: {c}")
    print(f"Is immutable: {is_immutable_type(c)}")
    
    # Attempt to modify (will fail as expected)
    try:
        p.x = 30  # type: ignore
    except Exception as e:
        print(f"\nAttempted modification prevented: {type(e).__name__}")
    
    print()


def demo_dict_conversion() -> None:
    """Demonstrate dict to immutables.Map conversion."""
    print("=" * 60)
    print("DICTIONARY CONVERSION - dict → immutables.Map")
    print("=" * 60)
    
    # Simple dict
    config = {
        "host": "localhost",
        "port": 8080,
        "debug": True
    }
    
    print("Original dict:")
    print(f"  Type: {type(config).__name__}")
    print(f"  Content: {config}")
    
    immutable_config = make_immutable(config)
    print("\nAfter make_immutable:")
    print(f"  Type: {type(immutable_config).__name__}")
    print(f"  Content: {dict(immutable_config)}")
    print(f"  Access: immutable_config['host'] = {immutable_config['host']}")
    
    # Nested dict
    nested = {
        "database": {
            "host": "db.example.com",
            "credentials": {
                "user": "admin",
                "pass": "secret"
            }
        }
    }
    
    print("\n\nNested dict:")
    immutable_nested = make_immutable(nested)
    print(f"  Type of root: {type(immutable_nested).__name__}")
    print(f"  Type of nested: {type(immutable_nested['database']).__name__}")
    print(f"  Type of deeply nested: {type(immutable_nested['database']['credentials']).__name__}")
    print(f"  All levels are immutables.Map: {isinstance(immutable_nested['database']['credentials'], immutables.Map)}")
    
    # Attempt to modify (will fail)
    try:
        immutable_config["new_key"] = "value"  # type: ignore
    except Exception as e:
        print(f"\n\nAttempted modification prevented: {type(e).__name__}")
    
    print()


def demo_list_conversion() -> None:
    """Demonstrate list to tuple conversion."""
    print("=" * 60)
    print("LIST CONVERSION - list → tuple")
    print("=" * 60)
    
    # Simple list
    numbers = [1, 2, 3, 4, 5]
    print(f"Original list: {numbers} (type: {type(numbers).__name__})")
    
    immutable_numbers = make_immutable(numbers)
    print(f"After make_immutable: {immutable_numbers} (type: {type(immutable_numbers).__name__})")
    
    # Nested list
    matrix = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    
    print(f"\nOriginal nested list:")
    for row in matrix:
        print(f"  {row}")
    
    immutable_matrix = make_immutable(matrix)
    print(f"\nAfter make_immutable:")
    for row in immutable_matrix:
        print(f"  {row} (type: {type(row).__name__})")
    
    print()


def demo_set_conversion() -> None:
    """Demonstrate set to frozenset conversion."""
    print("=" * 60)
    print("SET CONVERSION - set → frozenset")
    print("=" * 60)
    
    tags = {"python", "immutable", "observable", "nexus"}
    print(f"Original set: {tags} (type: {type(tags).__name__})")
    
    immutable_tags = make_immutable(tags)
    print(f"After make_immutable: {immutable_tags} (type: {type(immutable_tags).__name__})")
    
    # Attempt to modify (will fail)
    try:
        immutable_tags.add("new_tag")  # type: ignore
    except Exception as e:
        print(f"\nAttempted modification prevented: {type(e).__name__}")
    
    print()


def demo_complex_structure() -> None:
    """Demonstrate conversion of complex nested structures."""
    print("=" * 60)
    print("COMPLEX NESTED STRUCTURES")
    print("=" * 60)
    
    # A realistic data structure with mixed types
    user_data = {
        "users": [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@example.com",
                "roles": {"admin", "user"},
                "metadata": {
                    "last_login": "2025-10-19",
                    "preferences": {
                        "theme": "dark",
                        "notifications": True
                    }
                }
            },
            {
                "id": 2,
                "name": "Bob",
                "email": "bob@example.com",
                "roles": {"user"},
                "metadata": {
                    "last_login": "2025-10-18",
                    "preferences": {
                        "theme": "light",
                        "notifications": False
                    }
                }
            }
        ],
        "total_count": 2
    }
    
    print("Original structure:")
    print(f"  Type: {type(user_data).__name__}")
    print(f"  User list type: {type(user_data['users']).__name__}")
    print(f"  First user type: {type(user_data['users'][0]).__name__}")
    print(f"  Roles type: {type(user_data['users'][0]['roles']).__name__}")
    
    immutable_data = make_immutable(user_data)
    
    print("\nAfter make_immutable:")
    print(f"  Type: {type(immutable_data).__name__}")
    print(f"  User list type: {type(immutable_data['users']).__name__}")
    print(f"  First user type: {type(immutable_data['users'][0]).__name__}")
    print(f"  Roles type: {type(immutable_data['users'][0]['roles']).__name__}")
    
    # Verify we can still access all data
    first_user = immutable_data['users'][0]
    print(f"\nAccessing data:")
    print(f"  First user name: {first_user['name']}")
    print(f"  First user roles: {first_user['roles']}")
    print(f"  Theme preference: {first_user['metadata']['preferences']['theme']}")
    
    print()


def demo_validation() -> None:
    """Demonstrate validation of immutability."""
    print("=" * 60)
    print("VALIDATION")
    print("=" * 60)
    
    test_cases = [
        (42, "int"),
        ("hello", "str"),
        ([1, 2, 3], "list"),
        ({"a": 1}, "dict"),
        ({1, 2, 3}, "set"),
        ((1, 2, 3), "tuple (all immutable)"),
        ((1, [2, 3]), "tuple (contains mutable)"),
    ]
    
    for value, description in test_cases:
        is_valid, msg = validate_immutable(value)
        status = "✓" if is_valid else "✗"
        print(f"{status} {description:30} → {msg}")
    
    print()


def demo_error_handling() -> None:
    """Demonstrate error handling for unsupported types."""
    print("=" * 60)
    print("ERROR HANDLING")
    print("=" * 60)
    
    # Custom mutable object
    class CustomObject:
        def __init__(self, value: int):
            self.value = value
    
    obj = CustomObject(42)
    
    try:
        make_immutable(obj)
    except ImmutabilityError as e:
        print(f"Expected error for custom object:")
        print(f"  {e}")
    
    # Non-frozen dataclass
    @dataclass
    class MutablePoint:
        x: int
        y: int
    
    p = MutablePoint(10, 20)
    
    try:
        make_immutable(p)
    except ImmutabilityError as e:
        print(f"\nExpected error for non-frozen dataclass:")
        print(f"  {e}")
    
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "IMMUTABLE VALUES DEMONSTRATION" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    demo_primitives()
    demo_frozen_dataclass()
    demo_dict_conversion()
    demo_list_conversion()
    demo_set_conversion()
    demo_complex_structure()
    demo_validation()
    demo_error_handling()
    
    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("  • Primitives (int, float, str, etc.) are already immutable")
    print("  • Frozen dataclasses are recognized as immutable")
    print("  • dict → immutables.Map (recursively)")
    print("  • list → tuple (recursively)")
    print("  • set → frozenset")
    print("  • Custom mutable objects raise ImmutabilityError")
    print()

