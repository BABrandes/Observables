"""
Tests for immutable value utilities in the nexus system.
"""

import pytest
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from datetime import datetime, date, time, timedelta
from enum import Enum
from uuid import UUID
import immutables

from observables._nexus_system.immutable_values import (
    check_and_convert_to_immutable,
)
from observables._nexus_system.nexus_manager import NexusManager


class TestPrimitiveTypes:
    """Test handling of primitive immutable types."""
    
    def test_int_is_immutable(self) -> None:
        """Test that integers are recognized as immutable."""
        error, result = check_and_convert_to_immutable(42)
        assert error is None
        assert result == 42
    
    def test_float_is_immutable(self) -> None:
        """Test that floats are recognized as immutable."""
        error, result = check_and_convert_to_immutable(3.14)
        assert error is None
        assert result == 3.14
    
    def test_str_is_immutable(self) -> None:
        """Test that strings are recognized as immutable."""
        error, result = check_and_convert_to_immutable("hello")
        assert error is None
        assert result == "hello"
    
    def test_bool_is_immutable(self) -> None:
        """Test that booleans are recognized as immutable."""
        error, result = check_and_convert_to_immutable(True)
        assert error is None
        assert result is True
    
    def test_none_is_immutable(self) -> None:
        """Test that None is recognized as immutable."""
        error, result = check_and_convert_to_immutable(None)
        assert error is None
        assert result is None
    
    def test_bytes_is_immutable(self) -> None:
        """Test that bytes are recognized as immutable."""
        error, result = check_and_convert_to_immutable(b"hello")
        assert error is None
        assert result == b"hello"
    
    def test_complex_is_immutable(self) -> None:
        """Test that complex numbers are recognized as immutable."""
        error, result = check_and_convert_to_immutable(1 + 2j)
        assert error is None
        assert result == 1 + 2j


class TestFrozenDataclass:
    """Test handling of frozen dataclasses."""
    
    def test_frozen_dataclass_is_immutable(self) -> None:
        """Test that frozen dataclasses are recognized as immutable."""
        
        @dataclass(frozen=True)
        class Point:
            x: int
            y: int
        
        p = Point(1, 2)
        error, result = check_and_convert_to_immutable(p)
        assert error is None
        assert result is p
    
    def test_mutable_dataclass_raises_error(self) -> None:
        """Test that non-frozen dataclasses raise an error."""
        
        @dataclass
        class Point:
            x: int
            y: int
        
        p = Point(1, 2)
        error, result = check_and_convert_to_immutable(p)
        assert error is not None
        assert "not frozen" in error
        assert result is None
    
    def test_frozen_dataclass_with_nested_mutable(self) -> None:
        """Test frozen dataclass with nested mutable data."""
        
        @dataclass(frozen=True)
        class Container:
            data: list[int]
        
        # The frozen dataclass is accepted, even though it contains mutable data
        # The responsibility of ensuring internal immutability is on the user
        c = Container([1, 2, 3])
        error, result = check_and_convert_to_immutable(c)
        assert error is None
        assert result is c


class TestDictConversion:
    """Test conversion of dicts to immutables.Map."""
    
    def test_dict_to_immutable_map(self) -> None:
        """Test that dicts are converted to immutables.Map."""
        d = {"a": 1, "b": 2}
        error, result = check_and_convert_to_immutable(d)
        assert error is None
        assert isinstance(result, immutables.Map)
        assert result["a"] == 1
        assert result["b"] == 2
    
    def test_nested_dict_conversion(self) -> None:
        """Test that nested dicts are converted recursively."""
        d = {"outer": {"inner": 42}}
        error, result = check_and_convert_to_immutable(d)
        assert error is None
        assert isinstance(result, immutables.Map)
        assert isinstance(result["outer"], immutables.Map)
        assert result["outer"]["inner"] == 42
    
    def test_dict_with_list_values(self) -> None:
        """Test dict with list values gets converted."""
        d = {"items": [1, 2, 3]}
        error, result = check_and_convert_to_immutable(d)
        assert error is None
        assert isinstance(result, immutables.Map)
        assert isinstance(result["items"], tuple)
        assert result["items"] == (1, 2, 3)
    
    def test_dict_with_unconvertible_value(self) -> None:
        """Test that dict with unconvertible values returns error."""
        class CustomObject:
            pass
        
        d = {"item": CustomObject()}
        error, _ = check_and_convert_to_immutable(d)
        assert error is not None
        assert "value cannot be made immutable" in error.lower()
    
    def test_empty_dict(self) -> None:
        """Test that empty dict is converted correctly."""
        d = {}
        error, result = check_and_convert_to_immutable(d)
        assert error is None
        assert isinstance(result, immutables.Map)
        assert len(result) == 0 # type: ignore


class TestListConversion:
    """Test conversion of lists to tuples."""
    
    def test_list_to_tuple(self) -> None:
        """Test that lists are converted to tuples."""
        lst = [1, 2, 3]
        error, result = check_and_convert_to_immutable(lst)
        assert error is None
        assert isinstance(result, tuple)
        assert result == (1, 2, 3)
    
    def test_nested_list_conversion(self) -> None:
        """Test that nested lists are converted recursively."""
        lst = [1, [2, 3], 4]
        error, result = check_and_convert_to_immutable(lst)
        assert error is None
        assert isinstance(result, tuple)
        assert isinstance(result[1], tuple)
        assert result == (1, (2, 3), 4)
    
    def test_empty_list(self) -> None:
        """Test that empty list is converted correctly."""
        lst = []
        error, result = check_and_convert_to_immutable(lst)
        assert error is None
        assert isinstance(result, tuple)
        assert len(result) == 0 # type: ignore
    
    def test_list_with_dict(self) -> None:
        """Test list containing dicts."""
        lst = [{"a": 1}, {"b": 2}]
        error, result = check_and_convert_to_immutable(lst)
        assert error is None
        assert isinstance(result, tuple)
        assert isinstance(result[0], immutables.Map)
        assert result[0]["a"] == 1


class TestSetConversion:
    """Test conversion of sets to frozensets."""
    
    def test_set_to_frozenset(self) -> None:
        """Test that sets are converted to frozensets."""
        s = {1, 2, 3}
        error, result = check_and_convert_to_immutable(s)
        assert error is None
        assert isinstance(result, frozenset)
        assert result == frozenset({1, 2, 3})
    
    def test_empty_set(self) -> None:
        """Test that empty set is converted correctly."""
        s = set() # type: ignore
        error, result = check_and_convert_to_immutable(s)
        assert error is None
        assert isinstance(result, frozenset)
        assert len(result) == 0 # type: ignore
    
    def test_frozenset_is_immutable(self) -> None:
        """Test that frozensets are recognized as immutable."""
        fs = frozenset({1, 2, 3})
        error, result = check_and_convert_to_immutable(fs)
        assert error is None
        assert result == fs


class TestTupleHandling:
    """Test handling of tuples."""
    
    def test_tuple_with_immutable_contents(self) -> None:
        """Test tuple with immutable contents."""
        t = (1, 2, "hello")
        error, result = check_and_convert_to_immutable(t)
        assert error is None
        assert isinstance(result, tuple)
        assert result == (1, 2, "hello")
    
    def test_tuple_with_mutable_contents(self) -> None:
        """Test tuple with mutable contents gets converted."""
        t = (1, [2, 3], 4)
        error, result = check_and_convert_to_immutable(t)
        assert error is None
        assert isinstance(result, tuple)
        assert isinstance(result[1], tuple)
        assert result == (1, (2, 3), 4)
    
    def test_nested_tuple(self) -> None:
        """Test nested tuples."""
        t = (1, (2, [3, 4]), 5)
        error, result = check_and_convert_to_immutable(t)
        assert error is None
        assert result == (1, (2, (3, 4)), 5)
    
    def test_empty_tuple(self) -> None:
        """Test empty tuple."""
        t = ()
        error, result = check_and_convert_to_immutable(t)
        assert error is None
        assert result == ()


class TestImmutablesLibraryTypes:
    """Test handling of types from the immutables library."""
    
    def test_immutable_map_is_recognized(self) -> None:
        """Test that immutables.Map is recognized as immutable."""
        m = immutables.Map({"a": 1, "b": 2})
        error, result = check_and_convert_to_immutable(m)
        assert error is None
        assert result is m
    
    def test_empty_immutable_map(self) -> None:
        """Test empty immutables.Map."""
        m = immutables.Map() # type: ignore
        error, result = check_and_convert_to_immutable(m)
        assert error is None
        assert result is m


class TestComplexNestedStructures:
    """Test complex nested data structures."""
    
    def test_complex_nested_structure(self) -> None:
        """Test a complex nested structure with mixed types."""
        data = {
            "users": [
                {"name": "Alice", "scores": [95, 87, 92]},
                {"name": "Bob", "scores": [88, 91, 85]},
            ],
            "metadata": {
                "version": 1,
                "tags": {"python", "test"},
            }
        }
        
        error, result = check_and_convert_to_immutable(data)
        assert error is None
        
        # Check top level
        assert isinstance(result, immutables.Map)
        
        # Check users list → tuple
        assert isinstance(result["users"], tuple)
        
        # Check user dicts → immutables.Map
        assert isinstance(result["users"][0], immutables.Map)
        
        # Check scores list → tuple
        assert isinstance(result["users"][0]["scores"], tuple)
        assert result["users"][0]["scores"] == (95, 87, 92)
        
        # Check metadata dict → immutables.Map
        assert isinstance(result["metadata"], immutables.Map)
        
        # Check tags set → frozenset
        assert isinstance(result["metadata"]["tags"], frozenset)
    
    def test_deeply_nested_lists(self) -> None:
        """Test deeply nested list structures."""
        data = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
        error, result = check_and_convert_to_immutable(data)
        assert error is None
        assert result == (((1, 2), (3, 4)), ((5, 6), (7, 8)))


class TestCustomObjects:
    """Test handling of custom objects."""
    
    def test_custom_object_returns_error(self) -> None:
        """Test that custom mutable objects return an error."""
        
        class CustomObject:
            def __init__(self, value: int):
                self.value = value
        
        obj = CustomObject(42)
        error, result = check_and_convert_to_immutable(obj)
        assert error is not None
        assert "cannot be made immutable" in error
        assert result is None


class TestStandardLibraryTypes:
    """Test handling of standard library immutable types."""
    
    def test_decimal_is_immutable(self) -> None:
        """Test that Decimal is recognized as immutable."""
        d = Decimal("3.14")
        error, result = check_and_convert_to_immutable(d)
        assert error is None
        assert result is d
    
    def test_fraction_is_immutable(self) -> None:
        """Test that Fraction is recognized as immutable."""
        f = Fraction(3, 4)
        error, result = check_and_convert_to_immutable(f)
        assert error is None
        assert result is f
    
    def test_datetime_types_are_immutable(self) -> None:
        """Test that datetime types are recognized as immutable."""
        dt = datetime(2025, 10, 19, 12, 30)
        d = date(2025, 10, 19)
        t = time(12, 30, 45)
        td = timedelta(days=7)
        
        for value in [dt, d, t, td]:
            error, result = check_and_convert_to_immutable(value)
            assert error is None
            assert result is value
    
    def test_uuid_is_immutable(self) -> None:
        """Test that UUID is recognized as immutable."""
        u = UUID('12345678-1234-5678-1234-567812345678')
        error, result = check_and_convert_to_immutable(u)
        assert error is None
        assert result is u
    
    def test_range_is_immutable(self) -> None:
        """Test that range is recognized as immutable."""
        r = range(10)
        error, result = check_and_convert_to_immutable(r)
        assert error is None
        assert result is r
    
    def test_enum_is_immutable(self) -> None:
        """Test that Enum values are recognized as immutable."""
        class Color(Enum):
            RED = 1
            BLUE = 2
        
        error, result = check_and_convert_to_immutable(Color.RED)
        assert error is None
        assert result is Color.RED
    
    def test_stdlib_types_in_collections(self) -> None:
        """Test standard library types inside collections."""
        data = {
            "decimal": Decimal("3.14"),
            "fraction": Fraction(1, 2),
            "datetime": datetime(2025, 10, 19),
            "uuid": UUID('12345678-1234-5678-1234-567812345678'),
        }
        
        error, result = check_and_convert_to_immutable(data)
        assert error is None
        assert isinstance(result, immutables.Map)
        assert result["decimal"] == Decimal("3.14")
        assert result["fraction"] == Fraction(1, 2)
        assert isinstance(result["datetime"], datetime)


class TestExtensibleRegistry:
    """Test the extensible registry system via NexusManager."""
    
    def test_register_custom_type(self) -> None:
        """Test registering a custom immutable type."""
        from pathlib import Path
        
        manager = NexusManager()
        manager.register_immutable_type(Path)
        
        p = Path("/tmp")
        
        # Without manager, Path would return error
        error, result = check_and_convert_to_immutable(p)
        assert error is not None
        assert result is None
        
        # With manager, Path is accepted
        error, result = check_and_convert_to_immutable(p, manager)
        assert error is None
        assert result is p
    
    def test_register_duplicate_type_raises_error(self) -> None:
        """Test that registering the same type twice raises an error."""
        from pathlib import Path
        
        manager = NexusManager()
        manager.register_immutable_type(Path)
        
        with pytest.raises(ValueError, match="already registered"):
            manager.register_immutable_type(Path)
    
    def test_unregister_custom_type(self) -> None:
        """Test unregistering a custom type."""
        from pathlib import Path
        
        manager = NexusManager()
        manager.register_immutable_type(Path)
        assert manager.is_registered_immutable_type(Path)
        
        manager.unregister_immutable_type(Path)
        assert not manager.is_registered_immutable_type(Path)
    
    def test_unregister_nonexistent_type_raises_error(self) -> None:
        """Test unregistering a type that isn't registered."""
        from pathlib import Path
        
        manager = NexusManager()
        
        with pytest.raises(ValueError, match="not registered"):
            manager.unregister_immutable_type(Path)
    
    def test_get_registered_types(self) -> None:
        """Test getting all registered types."""
        from pathlib import Path
        
        manager = NexusManager()
        assert len(manager.get_registered_immutable_types()) == 0
        
        manager.register_immutable_type(Path)
        types = manager.get_registered_immutable_types()
        assert len(types) == 1
        assert Path in types
    
    def test_custom_type_in_nested_structure(self) -> None:
        """Test custom types work in nested structures."""
        from pathlib import Path
        
        manager = NexusManager()
        manager.register_immutable_type(Path)
        
        data = {
            "paths": [Path("/home"), Path("/var")],
            "config": {"root": Path("/etc")}
        }
        
        error, result = check_and_convert_to_immutable(data, manager)
        assert error is None
        
        # Dict and list converted, but Paths unchanged
        assert isinstance(result, immutables.Map)
        assert isinstance(result["paths"], tuple)
        assert isinstance(result["paths"][0], Path)
        assert result["paths"][0] == Path("/home")
        assert isinstance(result["config"], immutables.Map)
        assert isinstance(result["config"]["root"], Path)
    
    def test_multiple_custom_types(self) -> None:
        """Test registering multiple custom types."""
        from pathlib import Path
        
        class CustomImmutable:
            def __init__(self, value: int):
                self._value = value
        
        manager = NexusManager()
        manager.register_immutable_type(Path)
        manager.register_immutable_type(CustomImmutable)
        
        assert manager.is_registered_immutable_type(Path)
        assert manager.is_registered_immutable_type(CustomImmutable)
        
        p = Path("/tmp")
        c = CustomImmutable(42)
        
        error1, result1 = check_and_convert_to_immutable(p, manager)
        assert error1 is None
        assert result1 is p
        
        error2, result2 = check_and_convert_to_immutable(c, manager)
        assert error2 is None
        assert result2 is c
    
    def test_registry_initialization(self) -> None:
        """Test initializing manager with registered types."""
        from pathlib import Path
        
        manager = NexusManager(registered_immutable_types={Path})
        
        assert manager.is_registered_immutable_type(Path)
        p = Path("/tmp")
        error, result = check_and_convert_to_immutable(p, manager)
        assert error is None
        assert result is p


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_none_in_collections(self) -> None:
        """Test None values in collections."""
        lst = [1, None, 3]
        error, result = check_and_convert_to_immutable(lst)
        assert error is None
        assert result == (1, None, 3)
        
        d = {"a": None, "b": 2}
        error, result = check_and_convert_to_immutable(d)
        assert error is None
        assert result["a"] is None
    
    def test_mixed_number_types(self) -> None:
        """Test mixed int, float, complex."""
        data = [1, 2.5, 1+2j]
        error, result = check_and_convert_to_immutable(data)
        assert error is None
        assert result == (1, 2.5, 1+2j)
    
    def test_unicode_strings(self) -> None:
        """Test unicode strings."""
        data = {"greeting": "Hello 世界 🌍"}
        error, result = check_and_convert_to_immutable(data)
        assert error is None
        assert isinstance(result, immutables.Map)
        assert result["greeting"] == "Hello 世界 🌍"
    
    def test_large_structure(self) -> None:
        """Test that large structures can be converted."""
        # Create a reasonably large structure
        data = {f"key_{i}": list(range(100)) for i in range(100)}
        error, result = check_and_convert_to_immutable(data)
        assert error is None
        assert isinstance(result, immutables.Map)
        assert len(result) == 100 # type: ignore
        # Spot check one value
        assert isinstance(result["key_0"], tuple)
        assert len(result["key_0"]) == 100 # type: ignore
    
    def test_nexus_manager_parameter_is_optional(self) -> None:
        """Test that nexus_manager parameter is optional everywhere."""
        # Should work without nexus_manager
        error, result = check_and_convert_to_immutable(42)
        assert error is None
        assert result == 42
        
        # Should also work with None
        error, result = check_and_convert_to_immutable(42, None)
        assert error is None
        assert result == 42
    
    def test_error_messages_are_descriptive(self) -> None:
        """Test that error messages are descriptive."""
        class CustomObject:
            pass
        
        obj = CustomObject()
        error, _ = check_and_convert_to_immutable(obj)
        assert error is not None
        assert "CustomObject" in error
        assert "cannot be made immutable" in error


class TestStringNotConvertedToSequence:
    """Test that strings are not treated as sequences."""
    
    def test_string_not_converted_to_tuple(self) -> None:
        """Test that strings are NOT converted to tuples of characters."""
        s = "hello"
        error, result = check_and_convert_to_immutable(s)
        assert error is None
        assert result == "hello"
        assert isinstance(result, str)
        # NOT ('h', 'e', 'l', 'l', 'o')
    
    def test_string_in_collection(self) -> None:
        """Test strings inside collections remain strings."""
        data = ["hello", "world"]
        error, result = check_and_convert_to_immutable(data)
        assert error is None
        assert result == ("hello", "world")
        assert isinstance(result[0], str)
