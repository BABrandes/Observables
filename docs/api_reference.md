# API Reference

This document provides comprehensive API documentation for the Observables library, with emphasis on bidirectional linking and state validation features.

## 📦 **Core Modules**

### **Import Statements**

```python
# Main observable types (Modern X-prefixed aliases - RECOMMENDED)
from observables import (
    XValue,           # Single values
    XList,            # Lists (immutable tuple internally)
    XDict,            # Dicts (immutable Map internally)
    XSet,             # Sets (immutable frozenset internally)
    XSelectionDict,   # Selection dictionaries
    XSelectionSet,    # Selection sets
    XFunction,        # Custom synchronization functions
    XOneWayFunction,  # One-way transformations
)

# Legacy names (DEPRECATED - use X-prefixed aliases instead)
from observables import (
    ObservableSingleValue,
    ObservableList,
    ObservableDict,
    ObservableSet,
    ObservableSelectionDict,
    ObservableSelectionSet,
    ObservableFunction,
    ObservableOneWayFunction,
)

# Hook types (for advanced usage)
from observables import Hook, ReadOnlyHook, FloatingHook, Nexus

# Protocol types (for type hints)
from observables import (
    XValueProtocol,
    XListProtocol,
    XDictProtocol,
    XSetProtocol,
    XSelectionDictProtocol,
    XSelectionOptionsProtocol,
)
```

## 🔄 **Initial Sync Modes**

Controls how values are synchronized when observables are first linked together. Initial sync mode is specified using string literals in the linking methods.

**Available Modes:**

- `"use_caller_value"` - Use the caller's current value for initial synchronization. After linking, the target observable will adopt the caller's value.
- `"use_target_value"` - Use the target's current value for initial synchronization. After linking, the caller observable will adopt the target's value.

### **Usage Examples**

```python
source = XValue(100)
target = XValue(200)

# Use caller's value (100) for initial synchronization
source.link(target.hook, "value", "use_caller_value")
print(target.value)  # 100

# Use target's value (200) for initial synchronization
source.link(target.hook, "value", "use_target_value")
print(source.value)  # 200
```

After the initial linking completes, both observables share the same underlying storage and all subsequent changes propagate bidirectionally regardless of which mode was used initially.

## 🏗️ **Observable Base Classes**

All observable types inherit from base classes that provide core linking and validation functionality.

### **Core Methods**

#### **`link(hook, component_key, initial_sync_mode)`**

Links this observable to another observable's hook, creating bidirectional synchronization.

**Parameters:**
- `hook: Hook[T] | ReadOnlyHook[T] | CarriesSingleHookProtocol[T]` - The hook to link to
- `component_key: str` - Name of the component being linked (e.g., "value", "selected_option")
- `initial_sync_mode: Literal["use_caller_value", "use_target_value"]` - How to synchronize initial values

**Returns:** `None`

**Raises:**
- `ValueError` - If linking would create invalid state
- `TypeError` - If hook types are incompatible

**Example:**
```python
obs1 = XValue(10)
obs2 = XValue(20)

# Link obs1 to obs2 with bidirectional sync
obs1.link(obs2.hook, "value", "use_caller_value")

# Now changes propagate in both directions
obs1.value = 100
print(obs2.value)  # 100

obs2.value = 200
print(obs1.value)  # 200
```

#### **`link_many(hooks, initial_sync_mode)`**

Atomically links multiple components to hooks from other observables. This method prevents validation errors that can occur when linking components with dependencies.

**Parameters:**
- `hooks: Mapping[str, Hook[T] | ReadOnlyHook[T]]` - Dictionary mapping component names to hooks
- `initial_sync_mode: Literal["use_caller_value", "use_target_value"]` - How to synchronize initial values

**Returns:** `None`

**Raises:**
- `ValueError` - If linking would create invalid state
- `TypeError` - If hook types are incompatible

**Use Cases:**
- Linking observables with multiple dependent components
- Preventing temporary invalid states during multi-component linking
- Atomic updates that require consistency across multiple properties

**Example:**
```python
from observables import XSelectionDict

# Create two selection observables
obs1 = XSelectionDict({"color": "red", "size": "large"})
obs2 = XSelectionDict({"color": "blue", "size": "small"})

# Link both components atomically
obs1.link_many({
    "color": obs2.hook,
    "size": obs2.hook  # Note: both map to same hook for this example
}, "use_target_value")

# obs1 now has obs2's values
print(f"obs1 color: {obs1.value['color']}")    # "blue"
print(f"obs1 size: {obs1.value['size']}")      # "small"

# Changes propagate bidirectionally
obs1.value = {"color": "green", "size": "medium"}
print(f"obs2 color: {obs2.value['color']}")     # "green"
print(f"obs2 size: {obs2.value['size']}")       # "medium"
```

**Why Use link_many:**
- **Prevents validation errors**: Linking multiple components atomically avoids temporary invalid states
- **Atomic operation**: All linkings succeed or fail together
- **Better performance**: Single validation pass for all components

### **Listener System**

All observables support listener notifications for value changes.

#### **`add_listener(*callbacks)`**

Add one or more listener callbacks that are called when the observable's value changes.

**Parameters:**
- `callbacks: Callable[[], None]` - Functions to call when value changes

**Returns:** `None`

**Example:**
```python
def on_value_change():
    print(f"Value changed to: {obs.value}")

obs = XValue(10)
obs.add_listener(on_value_change)

obs.value = 20  # Prints: "Value changed to: 20"
```

#### **`remove_listener(*callbacks)`**

Remove one or more listener callbacks.

**Parameters:**
- `callbacks: Callable[[], None]` - Functions to remove

**Returns:** `None`

#### **`remove_all_listeners()`**

Remove all listener callbacks.

**Returns:** `set[Callable[[], None]]` - Set of removed callbacks

### **Property Access**

#### **`value` (property)**

Get or set the observable's current value.

#### **`hook` (property)**

Get the observable's hook for linking operations.

# Create linking chain
obs1.link(obs2.hook, "value", "use_caller_value")
obs2.link(obs3.hook, "value", "use_caller_value")

# All three observables are now connected in a chain
obs1.value = 100
print(obs2.value)  # 100 (connected to obs1)
print(obs3.value)  # 100 (connected through obs2)
```

## 🔢 **ObservableSingleValue[T]** (XValue[T])

Observable wrapper for single values with bidirectional linking and validation.

### **Constructor**

```python
# Create with direct value
obs1 = XValue(42)

# Create with validation
def validate_age(age: int) -> tuple[bool, str]:
    return (0 <= age <= 150, "Age must be between 0 and 150")

obs2 = XValue(25, validator=validate_age)

# Create linked to another observable (bidirectional linking)
obs3 = XValue(obs1)  # Shares storage with obs1
```

**Parameters:**
- `value_or_hook_or_observable`: Initial value, hook to link to, or another observable to link to
- `validator: Optional[Callable[[T], tuple[bool, str]]]` - Validation function (returns (is_valid, message))
- `logger: Optional[Logger]` - Logger for debugging

### **Properties**

#### **`value: T`**

The current value. Reading and writing this property maintains bidirectional sync.

**Validation:** Custom validation can be added through the validator function in the constructor.


## 📋 **ObservableList[T]** (XList[T])

Observable wrapper for lists with bidirectional linking and item-level validation.

### **Constructor**

```python
# Create with direct value
obs1 = XList([1, 2, 3])

# Create with validation
def validate_list(items: list[int]) -> tuple[bool, str]:
    return (all(x > 0 for x in items), "All items must be positive")

obs2 = XList([1, 2, 3], validator=validate_list)

# Create linked to another observable
obs3 = XList(obs1)  # Shares storage with obs1
```

### **Properties**

#### **`value: tuple[T, ...]`**

The current list as an immutable tuple. Returns a tuple to prevent external mutation.

**Note:** Lists are internally stored as immutable tuples for consistency with the hook system.

**Example:**
```python
obs = XList([1, 2, 3])
print(obs.value)  # (1, 2, 3)

obs.value = (4, 5, 6)  # Note: assign tuple, not list
print(obs.value)  # (4, 5, 6)
```

#### **`hook: Hook[tuple[T, ...]]`**

Hook providing access to the list for linking operations.

### **Methods**

#### **`append(item: T)`**

Appends an item to the list (creates new tuple).

#### **`extend(items: Iterable[T])`**

Extends the list with multiple items.

#### **`insert(index: int, item: T)`**

Inserts an item at the specified index.

#### **`remove(item: T)`**

Removes the first occurrence of an item.

#### **`pop(index: int = -1) -> T`**

Removes and returns an item at the specified index.

#### **`clear()`**

Removes all items from the list.

**Example:**
```python
obs1 = XList([1, 2, 3])
obs2 = XList([])

# Link lists bidirectionally
obs1.link(obs2.hook, "value", "use_caller_value")

# Changes propagate in both directions
obs1.append(4)
print(obs2.value)  # (1, 2, 3, 4)

obs2.remove(2)
print(obs1.value)  # (1, 3, 4)
```

## 🗂️ **ObservableDict[K, V]** (XDict[K, V])

Observable wrapper for dictionaries with bidirectional linking and key-value validation.

### **Constructor**

```python
# Create with direct value
obs1 = XDict({"a": 1, "b": 2})

# Create with validation
def validate_dict(data: dict[str, int]) -> tuple[bool, str]:
    return (all(v > 0 for v in data.values()), "All values must be positive")

obs2 = XDict({"x": 1, "y": 2}, validator=validate_dict)

# Create linked to another observable
obs3 = XDict(obs1)  # Shares storage with obs1
```

### **Properties**

#### **`value: Mapping[K, V]`**

The current dictionary as an immutable mapping.

#### **`hook: Hook[Mapping[K, V]]`**

Hook providing access to the dictionary for linking operations.

### **Dictionary Operations**

Supports standard dictionary operations with automatic synchronization:

```python
obs = ObservableDict({"a": 1, "b": 2})

# Dictionary-style access
obs["c"] = 3           # Add key-value pair
print(obs["a"])        # Get value: 1
del obs["b"]           # Delete key
print("a" in obs)      # Check membership: True

# Iteration
for key in obs:
    print(key, obs[key])

# Methods
obs.update({"d": 4, "e": 5})
keys = obs.keys()
values = obs.values()
items = obs.items()
```

## 🎯 **ObservableSelectionOption[T]** (XSelectionSet[T])

Observable for selecting one option from a set of available options, with rigorous validation.

### **Constructor**

```python
# Create with direct values
selector1 = XSelectionSet("red", {"red", "green", "blue"})

# Create with validation
def validate_selection(choice: str, options: frozenset[str]) -> tuple[bool, str]:
    return (choice in options, f"Must select from: {options}")

selector2 = XSelectionSet("red", {"red", "green", "blue"}, validator=validate_selection)

# Create linked to another observable
selector3 = XSelectionSet(selector1)  # Shares storage with selector1
```

**Parameters:**
- `selected_option`: Initial selection or source observable
- `available_options`: Available options (optional if linking)
- `validator`: Optional validation function
- `logger`: Optional logger for debugging

**Validation Rules:**
- Selected option must always be in available options
- Available options cannot be empty
- Selected option cannot be None (use `XOptionalSelectionSet` for None support)

### **Properties**

#### **`value: T`**

The currently selected option. Must be present in `available_options`.

**Validation:** Automatically enforced - setting invalid option raises `ValueError`

#### **`available_options: frozenset[T]`**

The set of available options as an immutable frozenset.

#### **`hook: Hook[T]`**

Hook for the selected option, used for linking operations.

### **Methods**

#### **`set_selected_option_and_available_options(selected_option: T, available_options: Set[T])`**

Atomically updates both selected option and available options with validation.

**Parameters:**
- `selected_option: T` - New selected option
- `available_options: Set[T]` - New available options

**Raises:** `ValueError` - If selected option is not in available options

**Example:**
```python
selector = ObservableSelectionOption("red", {"red", "green", "blue"})

# ✅ Valid atomic update
selector.set_selected_option_and_available_options("yellow", {"yellow", "red", "green"})

# ❌ Invalid update - rejected
try:
    selector.set_selected_option_and_available_options("purple", {"red", "green"})
except ValueError as e:
    print(f"Validation error: {e}")
```

### **Bidirectional Linking Example**

```python
# Create two selection observables
primary = ObservableSelectionOption("option1", {"option1", "option2", "option3"})
secondary = ObservableSelectionOption("option1", {"option1", "option2"})

# Link selected options bidirectionally
primary.link(secondary.selected_option_hook, "selected_option", "use_caller_value")

# Changes propagate in both directions
primary.selected_option = "option2"
print(secondary.selected_option)  # "option2"

secondary.selected_option = "option1"  
print(primary.selected_option)     # "option1"

# Available options remain separate (only selected option is bound)
print(primary.available_options)   # {"option1", "option2", "option3"}
print(secondary.available_options) # {"option1", "option2"}
```

## 🎯❓ **ObservableOptionalSelectionOption[T]**

Like `ObservableSelectionOption`, but allows `None` as a valid selection.

### **Constructor**

```python
def __init__(
    self, 
    selected_option: Union[Optional[T], ObservableOptionalSelectionOptionProtocol[T]], 
    available_options: Optional[Union[Set[T], HookProtocol[Set[T]]]] = None,
    logger: Optional[Logger] = None
)
```

### **Key Differences from ObservableSelectionOption**

- `selected_option` can be `None`
- Validation allows `None` selections
- Type hints use `Optional[T]` for selected option

**Example:**
```python
# ✅ None is allowed
optional_selector = ObservableOptionalSelectionOption(None, {"red", "green", "blue"})
print(optional_selector.selected_option)  # None

# ✅ Regular selection also works
optional_selector.selected_option = "red"
print(optional_selector.selected_option)  # "red"

# ✅ Can set back to None
optional_selector.selected_option = None
print(optional_selector.selected_option)  # None
```

## 🎯📊 **ObservableMultiSelectionOption[T]**

Observable for selecting multiple options from a set of available options.

### **Constructor**

```python
def __init__(
    self, 
    selected_options: Union[Set[T], HookProtocol[Set[T]]], 
    available_options: Union[Set[T], HookProtocol[Set[T]]],
    logger: Optional[Logger] = None
)
```

### **Properties**

#### **`selected_options: Set[T]`**

The set of currently selected options. Must be a subset of `available_options`.

#### **`available_options: Set[T]`**

The set of available options.

### **Validation Rules**

- Selected options must be a subset of available options
- Both sets can be empty
- Atomic updates ensure consistency

**Example:**
```python
multi_selector = ObservableMultiSelectionOption(
    {"red", "green"}, 
    {"red", "green", "blue", "yellow"}
)

# ✅ Valid selection - subset of available
multi_selector.selected_options = {"blue", "yellow"}

# ❌ Invalid selection - contains unavailable option
try:
    multi_selector.selected_options = {"red", "purple"}
except ValueError as e:
    print(f"Validation error: {e}")
```

## 🏷️ **ObservableEnum[E]**

Observable wrapper for enum values with option validation.

### **Constructor**

```python
def __init__(
    self, 
    enum_value: Union[E, HookProtocol[E]], 
    enum_options: Optional[Union[Set[E], HookProtocol[Set[E]]]] = None,
    logger: Optional[Logger] = None
)
```

**Parameters:**
- `enum_value: Union[E, HookProtocol[E]]` - Initial enum value or hook
- `enum_options: Optional[Union[Set[E], HookProtocol[Set[E]]]]` - Available enum options
- `logger: Optional[Logger]` - Logger for debugging

**Automatic Enum Detection:** If `enum_options` is not provided, all values from the enum class are used.

### **Properties**

#### **`enum_value: E`**

The current enum value. Must be present in `enum_options`.

#### **`enum_options: Set[E]`**

The set of available enum options.

### **Example**

```python
from enum import Enum

class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

# Create with all enum options
color_obs = ObservableEnum(Color.RED)
print(color_obs.enum_options)  # {Color.RED, Color.GREEN, Color.BLUE}

# Create with limited options
limited_color = ObservableEnum(Color.RED, {Color.RED, Color.BLUE})
print(limited_color.enum_options)  # {Color.RED, Color.BLUE}

# ✅ Valid change
color_obs.enum_value = Color.GREEN

# ❌ Invalid change for limited options
try:
    limited_color.enum_value = Color.GREEN  # Not in limited options
except ValueError as e:
    print(f"Validation error: {e}")
```

## 🏷️❓ **ObservableOptionalEnum[E]**

Like `ObservableEnum`, but allows `None` as a valid enum value.

### **Key Differences**

- `enum_value` can be `None`
- Validation allows `None` values
- Type hints use `Optional[E]`

## 🔧 **Advanced API**

### **Hook Classes and Protocols**

#### **`HookProtocol[T]`** - Base Protocol

The foundation protocol that all hooks must implement. Provides the core interface for value management, linking, and synchronization.

**Key Properties:**
- `nexus_manager: NexusManager` - The nexus manager this hook belongs to
- `value: T` - The current value (returns a copy)
- `value_reference: T` - The value reference (do not modify!)
- `previous_value: T` - The previous value
- `nexus: Nexus[T]` - The hook nexus this hook belongs to
- `lock: RLock` - Thread safety lock

**Key Methods:**
- `link(target_hook: HookProtocol[T], initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> tuple[bool, str]`
- `dislink() -> None`
- `is_linked_to(hook: HookProtocol[T]) -> bool`

#### **`Hook[T]`** - Standalone Hook

Basic hook implementation for standalone use without an owner.

**Constructor:**
```python
def __init__(
    self, 
    value: T, 
    nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER,
    logger: Optional[Logger] = None
)
```

#### **`OwnedHook[T]`** - Observable Hook

Hook implementation for hooks that belong to observables.

**Constructor:**
```python
def __init__(
    self, 
    owner: CarriesHooksProtocol[Any, Any], 
    initial_value: T, 
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Additional Properties:**
- `owner: CarriesHooksProtocol[Any, T]` - The observable that owns this hook

#### **`FloatingHook[T]`** - Advanced Hook

Hook with validation and reaction capabilities for advanced use cases.

**Constructor:**
```python
def __init__(
    self, 
    value: T, 
    reaction_callback: Optional[Callable[[], tuple[bool, str]]] = None,
    isolated_validation_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
    logger: Optional[Logger] = None,
    nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER
)
```

**Additional Methods:**
- `validate_value_in_isolation(value: T) -> tuple[bool, str]`
- `react_to_value_changed() -> None`

#### **Hook Protocols**

##### **`HookWithOwnerProtocol[T]`**
Protocol for hooks that have an owner (implemented by `OwnedHook`).

##### **`HookWithIsolatedValidationProtocol[T]`**
Protocol for hooks with custom validation logic (implemented by `FloatingHook`).

##### **`HookWithReactionProtocol[T]`**
Protocol for hooks that react to value changes (implemented by `FloatingHook`).

#### **`Nexus[T]`**

Central storage for values shared between bound hooks.

**Key Methods:**
- `submit_value(value: T, source_hook: Hook[T]) -> Tuple[bool, str]`
- `submit_multiple_values(values: Dict[Hook[T], T]) -> Tuple[bool, str]`

### **Custom Observable Implementation**

You can create custom observable types by extending `BaseObservable` and using the new hook architecture:

```python
from observables import BaseObservable, OwnedHook
from observables import HookWithOwnerLike
from typing import Optional, Tuple
import logging

class ObservableTemperature(BaseObservable):
    """Custom observable with temperature validation using the new hook architecture."""
    
    def __init__(self, celsius: float, min_temp: float = -273.15, max_temp: float = 1000.0, logger: Optional[logging.Logger] = None):
        self.min_temp = min_temp
        self.max_temp = max_temp
        
        # Create owned hook with validation
        self._temperature_hook = OwnedHook(
            owner=self,
            initial_value=celsius,
            logger=logger
        )
        
        # Initialize base class with the hook
        super().__init__({"temperature": self._temperature_hook}, logger)
        
        # Validate initial value
        if not self._is_valid_temperature(celsius):
            raise ValueError(f"Initial temperature {celsius} outside range [{min_temp}, {max_temp}]")
    
    def _validate_temperature(self, temp: float) -> Tuple[bool, str]:
        """Validate temperature range."""
        if self._is_valid_temperature(temp):
            return True, "Valid temperature"
        return False, f"Temperature {temp} outside range [{self.min_temp}, {self.max_temp}]"
    
    def _is_valid_temperature(self, temp: float) -> bool:
        """Check if temperature is valid."""
        return self.min_temp <= temp <= self.max_temp
    
    @property
    def temperature(self) -> float:
        """Get current temperature."""
        return self._temperature_hook.value
    
    @temperature.setter
    def temperature(self, value: float) -> None:
        """Set temperature with validation."""
        # Validate before setting
        if not self._is_valid_temperature(value):
            raise ValueError(f"Temperature {value} outside range [{self.min_temp}, {self.max_temp}]")
        self._temperature_hook.submit_value(value)
    
    @property
    def temperature_hook(self) -> HookWithOwnerProtocol[float]:
        """Get temperature hook for binding."""
        return self._temperature_hook

# Usage with the new architecture
room_temp = ObservableTemperature(22.0, min_temp=10.0, max_temp=35.0)
outdoor_temp = ObservableTemperature(15.0, min_temp=-20.0, max_temp=45.0)

# Bind temperatures bidirectionally using the new connect_hook method
room_temp.link(outdoor_temp.temperature_hook, "temperature", "use_caller_value")

# Changes propagate with validation
room_temp.temperature = 25.0
print(outdoor_temp.temperature)  # 25.0

# Validation prevents invalid states
try:
    outdoor_temp.temperature = 50.0  # Outside room_temp's valid range
except ValueError as e:
    print(f"Validation error: {e}")

# Advanced usage with FloatingHook for custom validation
from observables import FloatingHook

def validate_temperature_range(temp: float) -> Tuple[bool, str]:
    """Custom validation function."""
    if -50.0 <= temp <= 100.0:
        return True, "Valid temperature"
    return False, f"Temperature {temp} outside safe range [-50, 100]"

def on_temperature_change() -> Tuple[bool, str]:
    """Reaction to temperature changes."""
    print("Temperature changed!")
    return True, "Reaction completed"

# Create a floating hook with custom validation and reaction
floating_temp = FloatingHook(
    value=20.0,
    isolated_validation_callback=validate_temperature_range,
    reaction_callback=on_temperature_change
)

# Use the floating hook
floating_temp.submit_value(25.0)  # Triggers validation and reaction
```

## 🛠️ **Debugging and Logging**

### **Logger Integration**

All observable classes accept an optional `logger` parameter for debugging:

```python
import logging

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)

# Create observable with logging
obs = ObservableSingleValue(10, logger=logger)

# Operations will log detailed information
obs.value = 20  # Logs validation and update details
```

### **Validation State Inspection**

```python
def debug_observable_state(obs):
    """Print detailed state information."""
    print(f"Observable type: {type(obs).__name__}")
    for name, hook in obs._component_hooks.items():
        print(f"  {name}: {hook.value}")
        print(f"    Nexus ID: {id(hook.nexus)}")
        print(f"    Bound hooks: {len(hook.nexus._hooks)}")
```

## ⚡ **Performance Considerations**

### **Best Practices for High-Performance Applications**

#### **Avoid Loggers in Performance-Critical Code**

Loggers add significant overhead to operations. Avoid them in performance-sensitive scenarios:

```python
# ❌ Slow: Logger adds overhead to every operation
obs = ObservableSingleValue(0, logger=logger)
for i in range(1000):
    obs.value = i  # Each operation logs detailed information

# ✅ Fast: No logger for performance-critical operations  
obs = ObservableSingleValue(0)  # No logger parameter
for i in range(1000):
    obs.value = i  # Direct operations without logging overhead

# ✅ Conditional logging: Use logger only when debugging
DEBUG = False
logger = logging.getLogger(__name__) if DEBUG else None
obs = ObservableSingleValue(0, logger=logger)
```

#### **Use connect_hooks for Atomic Multi-Component Binding**

When binding observables with multiple dependent components, use `connect_hooks` for better performance and reliability:

```python
# ❌ Slower: Sequential binding with potential validation conflicts
obs1.link(obs2.selected_option_hook, "selected_option", "use_target_value")
obs1.link(obs2.available_options_hook, "available_options", "use_target_value")

# ✅ Faster: Atomic multi-binding
obs1.connect_hooks({
    "selected_option": obs2.selected_option_hook,
    "available_options": obs2.available_options_hook
}, "use_target_value")
```

#### **Batch Operations When Possible**

```python
# ❌ Slower: Multiple individual operations
for item in items:
    observable_list.append(item)

# ✅ Faster: Single batch operation
observable_list.extend(items)

# ❌ Slower: Multiple validation passes
observable_selector.selected_option = "new_option"
observable_selector.available_options = {"new_option", "other_option"}

# ✅ Faster: Single atomic update
observable_selector.set_selected_option_and_available_options(
    "new_option", 
    {"new_option", "other_option"}
)
```

#### **Choose Appropriate Initial Sync Modes**

Select the sync mode that minimizes unnecessary value transfers:

```python
# If you want to keep the caller's values
obs1.link(obs2.hook, "component", "use_caller_value")

# If you want to adopt the target's values
obs1.link(obs2.hook, "component", "use_target_value")
```

#### **Performance Test Guidelines**

When writing performance tests, avoid loggers and focus on core operations:

```python
import time

# ✅ Accurate performance test
start_time = time.time()
for _ in range(1000):
    obs = ObservableSingleValue(0)  # No logger
    obs.value = 42
end_time = time.time()

# ❌ Inaccurate performance test (logger overhead dominates)
start_time = time.time()
for _ in range(1000):
    obs = ObservableSingleValue(0, logger=logger)  # Logger adds overhead
    obs.value = 42
end_time = time.time()
```

## 🔍 **Error Handling**

### **Common Exceptions**

#### **`ValueError`**
Raised when validation fails or invalid operations are attempted.

**Common causes:**
- Setting invalid selection option
- Binding incompatible observables
- Atomic operations with inconsistent state

#### **`TypeError`**
Raised when incorrect types are provided.

**Common causes:**
- Wrong hook type in binding
- Incompatible value types

### **Error Recovery**

```python
# Graceful error handling
try:
    selector.selected_option = "invalid_option"
except ValueError as e:
    print(f"Selection failed: {e}")
    # Observable maintains previous valid state
    print(f"Current selection: {selector.selected_option}")

# Validation with fallback
def safe_update_selection(selector, new_option, fallback_option):
    """Safely update selection with fallback."""
    try:
        selector.selected_option = new_option
        return True
    except ValueError:
        try:
            selector.selected_option = fallback_option
            return False
        except ValueError:
            # Even fallback failed - keep current state
            return False
```

---

This API reference provides comprehensive documentation for all public interfaces, with emphasis on the bidirectional linking capabilities and rigorous validation features that make the Observables library unique and robust.
