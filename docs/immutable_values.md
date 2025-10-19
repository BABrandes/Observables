# Immutable Values for Storage

The observables nexus system now provides utilities to ensure data immutability for values stored in hook nexuses. This prevents accidental modification of shared state and ensures data integrity.

## Overview

The `immutable_values` module provides three main functions:

- **`make_immutable(value)`**: Convert a value to an immutable form
- **`is_immutable_type(value)`**: Check if a value is already immutable
- **`validate_immutable(value)`**: Validate immutability without conversion

## Supported Types

### Already Immutable (Returned As-Is)

These types are inherently immutable and require no conversion:

- **Primitives**: `int`, `float`, `str`, `bool`, `None`, `bytes`, `complex`
- **Frozen collections**: `frozenset`, `tuple` (with immutable contents)
- **Frozen dataclasses**: Classes decorated with `@dataclass(frozen=True)`
- **Immutables library types**: `immutables.Map`

### Converted to Immutable

These mutable types are automatically converted:

| Mutable Type | Immutable Type | Notes |
|--------------|----------------|-------|
| `dict` | `immutables.Map` | Recursive conversion |
| `list` | `tuple` | Recursive conversion |
| `set` | `frozenset` | Elements must be hashable |

### Unsupported Types

Custom mutable objects will raise `ImmutabilityError` unless they are frozen dataclasses.

## Usage Examples

### Basic Usage

```python
from observables._nexus_system.immutable_values import make_immutable

# Primitives pass through unchanged
x = make_immutable(42)  # Returns: 42
s = make_immutable("hello")  # Returns: "hello"

# Mutable collections are converted
lst = make_immutable([1, 2, 3])  # Returns: (1, 2, 3)
d = make_immutable({"a": 1})  # Returns: immutables.Map({'a': 1})
```

### Frozen Dataclasses

```python
from dataclasses import dataclass
from observables._nexus_system.immutable_values import make_immutable

@dataclass(frozen=True)
class Point:
    x: int
    y: int

p = Point(10, 20)
# Frozen dataclasses are recognized as immutable
result = make_immutable(p)  # Returns the same Point object
```

### Complex Nested Structures

```python
from observables._nexus_system.immutable_values import make_immutable

# Complex nested structure
data = {
    "users": [
        {"name": "Alice", "roles": {"admin", "user"}},
        {"name": "Bob", "roles": {"user"}},
    ],
    "metadata": {
        "version": 1,
        "tags": {"python", "observable"}
    }
}

# All nested structures are converted recursively
immutable_data = make_immutable(data)
# Result:
# - Root dict → immutables.Map
# - users list → tuple
# - Each user dict → immutables.Map
# - roles sets → frozenset
# - metadata dict → immutables.Map
# - tags set → frozenset
```

### Working with immutables.Map

```python
import immutables

config = immutables.Map({"host": "localhost", "port": 8080})

# Access like a dict
host = config["host"]  # "localhost"

# Immutable - creates new Map on modification
new_config = config.set("port", 9090)
# config["port"] is still 8080
# new_config["port"] is 9090

# Iterate like a dict
for key, value in config.items():
    print(f"{key}: {value}")
```

### Validation

```python
from observables._nexus_system.immutable_values import (
    is_immutable_type,
    validate_immutable
)

# Check if a type is immutable
is_immutable_type(42)  # True
is_immutable_type([1, 2, 3])  # False

# Validate with detailed message
is_valid, msg = validate_immutable((1, 2, 3))
# is_valid: True
# msg: "Value is immutable"

is_valid, msg = validate_immutable((1, [2, 3]))
# is_valid: False
# msg: "Tuple contains mutable item: Value of type list is mutable..."
```

## Error Handling

```python
from observables._nexus_system.immutable_values import (
    make_immutable,
    ImmutabilityError
)

# Custom objects raise ImmutabilityError
class CustomObject:
    def __init__(self, value: int):
        self.value = value

obj = CustomObject(42)

try:
    make_immutable(obj)
except ImmutabilityError as e:
    print(f"Cannot make immutable: {e}")
    # "Value of type CustomObject cannot be made immutable..."

# Non-frozen dataclasses also raise ImmutabilityError
from dataclasses import dataclass

@dataclass  # Note: NOT frozen
class MutablePoint:
    x: int
    y: int

p = MutablePoint(10, 20)

try:
    make_immutable(p)
except ImmutabilityError as e:
    print(f"Not frozen: {e}")
    # "Dataclass MutablePoint is not frozen. Only frozen dataclasses..."
```

## Integration with Nexus System

When storing values in hook nexuses, you can ensure immutability:

```python
from observables._hooks.floating_hook import FloatingHook
from observables._nexus_system.immutable_values import make_immutable

# Create a hook with mutable data
data = {"users": ["Alice", "Bob"], "count": 2}

# Make data immutable before storage
immutable_data = make_immutable(data)

# Store in hook
hook = FloatingHook(immutable_data)

# The stored value is now protected from modification
# hook.value is an immutables.Map, not a dict
```

## Performance Considerations

- **Primitives and frozen types**: No overhead (returned as-is)
- **Small collections**: Minimal overhead for conversion
- **Large nested structures**: Conversion is recursive and may have noticeable cost
- **Repeated access**: Once converted, no further overhead

### Best Practices

1. **Convert once**: Make values immutable at the point of creation or before storage
2. **Use frozen dataclasses**: Design data classes as frozen from the start
3. **Prefer immutables.Map**: For frequently updated dictionaries, work with `immutables.Map` directly
4. **Validate early**: Use `validate_immutable()` to catch issues during development

## Type Checking

The module is fully typed and works well with static type checkers:

```python
from typing import Any
from observables._nexus_system.immutable_values import make_immutable

def store_config(config: dict[str, Any]) -> None:
    # Type checker knows this returns an immutables.Map-like object
    immutable_config = make_immutable(config)
    # Store in your system...
```

## Advantages of Immutability

1. **Thread Safety**: Immutable values are inherently thread-safe
2. **Cache Keys**: Can be safely used as dict keys or in sets (if hashable)
3. **Debugging**: Easier to reason about code when values can't change unexpectedly
4. **Performance**: Some operations on immutable structures can be optimized
5. **Data Integrity**: Prevents accidental modification of shared state

## Comparison with Other Approaches

### vs. `copy.deepcopy()`

- **Deepcopy**: Creates mutable copies, still modifiable
- **make_immutable**: Creates immutable versions, guaranteed safe

### vs. Manual tuple/frozenset conversion

- **Manual**: Error-prone, easy to miss nested structures
- **make_immutable**: Automatic recursive conversion

### vs. `types.Map (from immutables)`

- **Map (from immutables)**: Read-only view, original dict still modifiable
- **immutables.Map**: True immutable data structure

## API Reference

### `make_immutable(value: T) -> T`

Convert a value to an immutable form.

**Parameters:**
- `value`: The value to make immutable

**Returns:**
- An immutable version of the value

**Raises:**
- `ImmutabilityError`: If the value cannot be made immutable

### `is_immutable_type(value: Any) -> bool`

Check if a value is of an immutable type.

**Parameters:**
- `value`: The value to check

**Returns:**
- `True` if immutable, `False` otherwise

### `validate_immutable(value: Any) -> tuple[bool, str]`

Validate that a value is immutable without converting it.

**Parameters:**
- `value`: The value to validate

**Returns:**
- Tuple of `(is_valid, message)`

### `ImmutabilityError`

Exception raised when a value cannot be made immutable.

Inherits from `TypeError`.

## See Also

- [immutables library documentation](https://github.com/MagicStack/immutables)
- [Nexus System Overview](./nexus_system.md)
- [Hook System Documentation](./hook_system.md)

