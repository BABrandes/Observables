# API Reference

This document provides comprehensive API documentation for the Observables library, with emphasis on bidirectional binding and state validation features.

## 📦 **Core Modules**

### **Import Statements**

```python
# Main observable types
from observables import (
    ObservableSingleValue,
    ObservableList,
    ObservableDict,
    ObservableSet,
    ObservableTuple,
    ObservableEnum,
    ObservableOptionalEnum,
    ObservableSelectionOption,
    ObservableOptionalSelectionOption,
    ObservableMultiSelectionOption
)

# Hook types (for advanced usage)
from observables import Hook, HookLike, OwnedHook, FloatingHook, HookNexus
from observables import HookWithOwnerLike, HookWithIsolatedValidationLike, HookWithReactionLike

# Utility types
from observables import BaseObservable
```

## 🔄 **Initial Sync Modes**

Controls how values are synchronized when observables are first bound together. Initial sync mode is specified using string literals in the binding methods.

**Available Modes:**

- `"use_caller_value"` - Use the caller's current value for initial synchronization. After binding, the target observable will adopt the caller's value.
- `"use_target_value"` - Use the target's current value for initial synchronization. After binding, the caller observable will adopt the target's value.

### **Usage Examples**

```python
source = ObservableSingleValue(100)
target = ObservableSingleValue(200)

# Use caller's value (100) for initial synchronization
source.connect_hook(target.hook, "value", "use_caller_value")
print(target.value)  # 100

# Use target's value (200) for initial synchronization  
source.connect_hook(target.hook, "value", "use_target_value")
print(source.value)  # 200
```

After the initial binding completes, both observables share the same underlying storage and all subsequent changes propagate bidirectionally regardless of which mode was used initially.

## 🏗️ **BaseObservable Class**

Base class for all observable types, providing core binding and validation functionality.

### **Core Methods**

#### **`attach(hook, component_name, initial_sync_mode, logger=None)`**

Binds this observable to another observable's hook, creating bidirectional synchronization.

**Parameters:**
- `hook: HookLike[T]` - The hook to bind to
- `component_name: str` - Name of the component being bound
- `initial_sync_mode: Literal["use_caller_value", "use_target_value"]` - How to synchronize initial values
- `logger: Optional[Logger]` - Logger for debugging (optional)

**Returns:** `None`

**Raises:** 
- `ValueError` - If binding would create invalid state
- `TypeError` - If hook types are incompatible

**Example:**
```python
obs1 = ObservableSingleValue(10)
obs2 = ObservableSingleValue(20)

# Bind obs1 to obs2 with bidirectional sync
obs1.connect_hook(obs2.hook, "value", "use_caller_value")

# Now changes propagate in both directions
obs1.value = 100
print(obs2.value)  # 100

obs2.value = 200  
print(obs1.value)  # 200
```

#### **`connect_hooks(hook_dict, initial_sync_mode, logger=None)`**

Atomically binds multiple components to hooks from another observable. This method prevents validation errors that can occur when binding components with dependencies.

**Parameters:**
- `hook_dict: Dict[str, HookLike]` - Dictionary mapping component names to hooks
- `initial_sync_mode: Literal["use_caller_value", "use_target_value"]` - How to synchronize initial values
- `logger: Optional[Logger]` - Logger for debugging (optional)

**Returns:** `None`

**Raises:** 
- `ValueError` - If binding would create invalid state
- `TypeError` - If hook types are incompatible

**Use Cases:**
- Binding observables with multiple dependent components (e.g., selected_option + available_options)
- Preventing temporary invalid states during multi-component binding
- Atomic updates that require consistency across multiple properties

**Example:**
```python
from observables import ObservableSelectionOption

# Create two selection observables with different available options
obs1 = ObservableSelectionOption("red", {"red", "green", "blue"})
obs2 = ObservableSelectionOption("yellow", {"yellow", "orange", "purple"})

# Bind both selected_option AND available_options atomically
obs1.connect_hooks({
    "selected_option": obs2.selected_option_hook,
    "available_options": obs2.available_options_hook
}, "use_target_value")

# obs1 now has obs2's values: selected="yellow", options={"yellow", "orange", "purple"}
print(f"Selected: {obs1.selected_option}")        # "yellow"
print(f"Available: {obs1.available_options}")     # {"yellow", "orange", "purple"}

# Changes propagate bidirectionally
obs1.selected_option = "orange"
print(f"obs2 selected: {obs2.selected_option}")   # "orange"
```

**Why Use connect_hooks:**
- **Prevents validation errors**: Binding available_options before selected_option could temporarily create invalid states
- **Atomic operation**: All bindings succeed or fail together
- **Better performance**: Single validation pass for all components

#### **`detach()`**

Disconnects this observable from all bindings, creating an isolated HookNexus.

**Returns:** `None`

**Raises:** `ValueError` - If observable is not currently bound

**Example:**
```python
obs1 = ObservableSingleValue(10)
obs2 = ObservableSingleValue(20)
obs3 = ObservableSingleValue(30)

# Create binding chain
obs1.connect_hook(obs2.hook, "value", "use_caller_value")
obs2.connect_hook(obs3.hook, "value", "use_caller_value")

# Detach obs2 - obs1 and obs3 remain connected
obs2.detach()

obs1.value = 100
print(obs2.value)  # 20 (isolated)
print(obs3.value)  # 100 (still connected to obs1)
```

#### **`is_attached_to(other_observable)`**

Checks if this observable is bound to another observable.

**Parameters:**
- `other_observable: BaseObservable` - Observable to check binding with

**Returns:** `bool` - True if bound, False otherwise

**Example:**
```python
obs1 = ObservableSingleValue(10)
obs2 = ObservableSingleValue(20)

print(obs1.is_attached_to(obs2))  # False

obs1.connect_hook(obs2.hook, "value", "use_caller_value")
print(obs1.is_attached_to(obs2))  # True
```

### **Listener Management**

#### **`add_listener(callback)`**

Adds a listener function that will be called when the observable changes.

**Parameters:**
- `callback: Callable[[], None]` - Function to call on changes

**Returns:** `None`

**Example:**
```python
obs = ObservableSingleValue(10)

def on_change():
    print(f"Value changed to: {obs.value}")

obs.add_listener(on_change)
obs.value = 20  # Prints: "Value changed to: 20"
```

#### **`remove_listener(callback)`**

Removes a previously added listener.

**Parameters:**
- `callback: Callable[[], None]` - Function to remove

**Returns:** `None`

#### **`remove_all_listeners()`**

Removes all listeners from this observable.

**Returns:** `None`

## 🔢 **ObservableSingleValue[T]**

Observable wrapper for single values with bidirectional binding and validation.

### **Constructor**

```python
def __init__(self, single_value: Union[T, HookLike[T]], logger: Optional[Logger] = None)
```

**Parameters:**
- `single_value: Union[T, HookLike[T]]` - Initial value or hook to bind to
- `logger: Optional[Logger]` - Logger for debugging

**Example:**
```python
# Create with direct value
obs1 = ObservableSingleValue(42)

# Create bound to another observable
obs2 = ObservableSingleValue(obs1.value_hook)  # Shares storage with obs1
```

### **Properties**

#### **`single_value: T`**

The current value. Reading and writing this property maintains bidirectional sync.

**Validation:** Custom validation can be added by overriding `_validate_single_value()`

**Example:**
```python
obs = ObservableSingleValue("hello")
print(obs.value)  # "hello"

obs.value = "world"
print(obs.value)  # "world"
```

#### **`single_value_hook: HookLike[T]`**

Hook providing access to the single value for binding operations.

**Example:**
```python
obs1 = ObservableSingleValue(10)
obs2 = ObservableSingleValue(20)

# Bind using hooks
obs1.connect_hook(obs2.hook, "value", "use_caller_value")
```

### **Methods**

#### **`set_single_value(value: T)`**

Sets the single value with validation.

**Parameters:**
- `value: T` - New value to set

**Raises:** `ValueError` - If value fails validation

## 📋 **ObservableList[T]**

Observable wrapper for lists with bidirectional binding and item-level validation.

### **Constructor**

```python
def __init__(self, list_value: Union[List[T], HookLike[List[T]]], logger: Optional[Logger] = None)
```

### **Properties**

#### **`list_value: List[T]`**

The current list. Returns a copy to prevent external mutation.

**Example:**
```python
obs = ObservableList([1, 2, 3])
print(obs.value)  # [1, 2, 3]

obs.value = [4, 5, 6]
print(obs.value)  # [4, 5, 6]
```

#### **`list_value_hook: HookLike[List[T]]`**

Hook providing access to the list for binding operations.

### **Methods**

#### **`append(item: T)`**

Appends an item to the list with validation.

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
obs1 = ObservableList([1, 2, 3])
obs2 = ObservableList([])

# Bind lists bidirectionally
obs1.connect_hook(obs2.value_hook, "list_value", "use_caller_value")

# Changes propagate in both directions
obs1.append(4)
print(obs2.value)  # [1, 2, 3, 4]

obs2.remove(2)
print(obs1.value)  # [1, 3, 4]
```

## 🗂️ **ObservableDict[K, V]**

Observable wrapper for dictionaries with bidirectional binding and key-value validation.

### **Constructor**

```python
def __init__(self, dict_value: Union[Dict[K, V], HookLike[Dict[K, V]]], logger: Optional[Logger] = None)
```

### **Properties**

#### **`dict_value: Dict[K, V]`**

The current dictionary. Returns a copy to prevent external mutation.

#### **`dict_value_hook: HookLike[Dict[K, V]]`**

Hook providing access to the dictionary for binding operations.

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

## 🎯 **ObservableSelectionOption[T]**

Observable for selecting one option from a set of available options, with rigorous validation.

### **Constructor**

```python
def __init__(
    self, 
    selected_option: Union[T, ObservableSelectionOptionLike[T]], 
    available_options: Optional[Union[Set[T], HookLike[Set[T]]]] = None,
    logger: Optional[Logger] = None
)
```

**Parameters:**
- `selected_option: Union[T, ObservableSelectionOptionLike[T]]` - Initial selection or source observable
- `available_options: Optional[Union[Set[T], HookLike[Set[T]]]]` - Available options (optional if binding)
- `logger: Optional[Logger]` - Logger for debugging

**Validation Rules:**
- Selected option must always be in available options
- Available options cannot be empty
- Selected option cannot be None (use `ObservableOptionalSelectionOption` for None support)

### **Properties**

#### **`selected_option: T`**

The currently selected option. Must be present in `available_options`.

**Validation:** Automatically enforced - setting invalid option raises `ValueError`

#### **`available_options: Set[T]`**

The set of available options. Returns a copy to prevent external mutation.

#### **`selected_option_hook: HookLike[T]`**

Hook for the selected option, used for binding operations.

#### **`available_options_hook: HookLike[Set[T]]`**

Hook for the available options, used for binding operations.

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

### **Bidirectional Binding Example**

```python
# Create two selection observables
primary = ObservableSelectionOption("option1", {"option1", "option2", "option3"})
secondary = ObservableSelectionOption("option1", {"option1", "option2"})

# Bind selected options bidirectionally
primary.connect_hook(secondary.selected_option_hook, "selected_option", "use_caller_value")

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
    selected_option: Union[Optional[T], ObservableOptionalSelectionOptionLike[T]], 
    available_options: Optional[Union[Set[T], HookLike[Set[T]]]] = None,
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
    selected_options: Union[Set[T], HookLike[Set[T]]], 
    available_options: Union[Set[T], HookLike[Set[T]]],
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
    enum_value: Union[E, HookLike[E]], 
    enum_options: Optional[Union[Set[E], HookLike[Set[E]]]] = None,
    logger: Optional[Logger] = None
)
```

**Parameters:**
- `enum_value: Union[E, HookLike[E]]` - Initial enum value or hook
- `enum_options: Optional[Union[Set[E], HookLike[Set[E]]]]` - Available enum options
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

#### **`HookLike[T]`** - Base Protocol

The foundation protocol that all hooks must implement. Provides the core interface for value management, binding, and synchronization.

**Key Properties:**
- `nexus_manager: NexusManager` - The nexus manager this hook belongs to
- `value: T` - The current value (returns a copy)
- `value_reference: T` - The value reference (do not modify!)
- `previous_value: T` - The previous value
- `hook_nexus: HookNexus[T]` - The hook nexus this hook belongs to
- `lock: RLock` - Thread safety lock

**Key Methods:**
- `connect_hook(target_hook: HookLike[T], initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> tuple[bool, str]`
- `disconnect() -> None`
- `is_connected_to(hook: HookLike[T]) -> bool`

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
    owner: CarriesHooksLike[Any, Any], 
    initial_value: T, 
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Additional Properties:**
- `owner: CarriesHooksLike[Any, T]` - The observable that owns this hook

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

##### **`HookWithOwnerLike[T]`**
Protocol for hooks that have an owner (implemented by `OwnedHook`).

##### **`HookWithIsolatedValidationLike[T]`**
Protocol for hooks with custom validation logic (implemented by `FloatingHook`).

##### **`HookWithReactionLike[T]`**
Protocol for hooks that react to value changes (implemented by `FloatingHook`).

#### **`HookNexus[T]`**

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
    def temperature_hook(self) -> HookWithOwnerLike[float]:
        """Get temperature hook for binding."""
        return self._temperature_hook

# Usage with the new architecture
room_temp = ObservableTemperature(22.0, min_temp=10.0, max_temp=35.0)
outdoor_temp = ObservableTemperature(15.0, min_temp=-20.0, max_temp=45.0)

# Bind temperatures bidirectionally using the new connect_hook method
room_temp.connect_hook(outdoor_temp.temperature_hook, "temperature", "use_caller_value")

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
        print(f"    HookNexus ID: {id(hook.hook_nexus)}")
        print(f"    Bound hooks: {len(hook.hook_nexus._hooks)}")
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
obs1.connect_hook(obs2.selected_option_hook, "selected_option", "use_target_value")
obs1.connect_hook(obs2.available_options_hook, "available_options", "use_target_value")

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
obs1.connect_hook(obs2.hook, "component", "use_caller_value")

# If you want to adopt the target's values
obs1.connect_hook(obs2.hook, "component", "use_target_value")
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

This API reference provides comprehensive documentation for all public interfaces, with emphasis on the bidirectional binding capabilities and rigorous validation features that make the Observables library unique and robust.
