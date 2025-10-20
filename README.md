# Observables - Transitive Synchronization and Shared-State Fusion for Python

A reactive synchronization framework for Python that provides a universal mechanism for 
maintaining coherent shared state across independent objects, enabling transitive, 
non-directional synchronization through Nexus fusion.

**Core Concept:**
Each Hook references a Nexus — a shared synchronization core. When hooks are joined, 
their Nexuses fuse into a unified domain, creating transitive synchronization networks. 
Joining A→B and B→C automatically synchronizes A and C, even though they were never 
directly joined. The library provides full immutability using frozen data structures 
for thread safety and data integrity.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI version](https://badge.fury.io/py/observables.svg)](https://badge.fury.io/py/observables)
[![Tests](https://github.com/yourusername/observables/workflows/Tests/badge.svg)](https://github.com/yourusername/observables/actions)

> **⚠️ DEVELOPMENT STATUS: NOT PRODUCTION READY**
> 
> This library is currently under active development and is **not yet suitable for production use**.
> The API may change without notice, and while we have comprehensive test coverage (531 tests, 69% coverage),
> the library has not been battle-tested in production environments.
> 
> **Use at your own risk.** Contributions, feedback, and bug reports are welcome!

## ✨ What's New

### **Modern X-Prefixed API**
Clean, concise names for better developer experience:
```python
from observables import XValue, XList, XSet, XDict  # Modern ✅
from observables import ObservableSingleValue, ObservableList  # Legacy (deprecated) ❌
```

### **Complete Immutability**
Thread-safe by design with immutable collections:
- `XList` → `tuple` internally
- `XSet` → `frozenset` internally
- `XDict` → `Map (from immutables)` internally

### **Typed Parameter Objects**
No more parameter order confusion:
```python
from observables import FunctionValues

def my_function(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
    # Clear, typed access to submitted and current values
    if 'field' in values.submitted:
        return (True, {'other': values.current['other'] + 1})
    return (True, {})
```

## Architecture

The library uses a centralized value storage approach with three distinct notification philosophies:

### **Centralized Storage**
- **Centralized Storage**: Each value is stored in exactly one Nexus
- **Hook-Based Binding**: Observables connect through hooks, managed by NexusManager
- **Transitive Binding**: When you bind A→B and B→C, all three share the same Nexus
- **No Data Copying**: Values are never duplicated between observables
- **Atomic Updates**: All connected hooks see changes simultaneously

### **Three Notification Philosophies**

The system supports three distinct notification mechanisms, each optimized for different use cases:

#### **1. Listeners (Synchronous Unidirectional)**
- Callbacks registered via `add_listener()` on observables or hooks
- Execute synchronously during value changes
- **Unidirectional**: Listeners observe changes but cannot validate or reject them
- **Use Case**: UI updates, logging, simple reactions to state changes
- **Example**: `observable.add_listener(lambda: print(observable.value))`

#### **2. Publish-Subscribe (Asynchronous Unidirectional)**
- Based on Publisher/Subscriber pattern with asyncio
- Execute asynchronously via event loop (non-blocking)
- **Unidirectional**: Subscribers react to publications but cannot validate or reject them
- **Three Modes**:
  - `async` (default): Non-blocking, returns immediately, reactions in background
  - `sync`: Blocking, waits for all async reactions to complete
  - `direct`: Pure synchronous calls, no asyncio overhead, fastest option
- **Use Case**: Decoupled components, async I/O operations, external system notifications
- **Example**: `publisher.publish(mode="async")  # Non-blocking!`

#### **3. Hooks (Synchronous Bidirectional with Validation)**
- Connected hooks share values through Nexus
- Validation occurs before value changes (enforces valid state)
- **Bidirectional**: Any connected hook can reject changes via validation
- **Use Case**: Maintaining invariants across connected state, bidirectional data binding
- **Example**: `obs1.link(obs2.hook, "value", "use_caller_value")`

## Key Features

### **Bidirectional Binding**
Observables connected through hooks share the same Nexus storage:

```python
from observables import XValue

# Create two observables
temp_celsius = XValue(25.0)
temp_fahrenheit = XValue(77.0)

# Bind them bidirectionally - celsius value takes precedence
temp_celsius.link(temp_fahrenheit.hook, "value", "use_caller_value")

# 🔄 Changes propagate in BOTH directions
temp_celsius.value = 30.0
print(temp_fahrenheit.value)  # 30.0 (celsius → fahrenheit)

temp_fahrenheit.value = 100.0
print(temp_celsius.value)     # 100.0 (fahrenheit → celsius)
```

### **🛡️ State Validation with Immutable Collections**
Invalid states are prevented through built-in validation:

```python
from observables import XSelectionOption

# Selection options with validation (internally uses immutable frozenset)
color_selector = XSelectionOption("red", {"red", "green", "blue"})

# ✅ Valid selection
color_selector.selected_option = "green"  # Works

# ❌ Invalid selection - automatically rejected
try:
    color_selector.selected_option = "purple"  # Not in available options
except ValueError as e:
    print(f"Validation enforced: {e}")

# State remains valid after rejection
print(color_selector.selected_option)  # Still "green"

# Available options are immutable
print(type(color_selector.available_options))  # <class 'frozenset'>
```

### **⚡ Function Observables with Typed Parameters**
Create computed values and maintain constraints:

```python
from observables import XValue, XFunction, XOneWayFunction, FunctionValues

# XFunction - bidirectional sync with constraints
def sum_constraint(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
    """Maintain field1 + field2 = 100."""
    result = {}
    
    if 'field1' in values.submitted:
        result['field2'] = 100 - values.submitted['field1']
    elif 'field2' in values.submitted:
        result['field1'] = 100 - values.submitted['field2']
    
    return (True, result)

field1 = XValue(30)
field2 = XValue(70)

sync = XFunction(
    function_input_hooks={'field1': field1.hook, 'field2': field2.hook},
    function_callable=sum_constraint
)

field1.value = 40  # field2 automatically becomes 60!

# XOneWayFunction - one-way transformations
converter = XOneWayFunction(
    function_input_hooks={'celsius': field1.hook},
    function_output_hook_keys={'fahrenheit', 'kelvin'},
    function_callable=lambda inputs: {
        'fahrenheit': inputs['celsius'] * 9/5 + 32,
        'kelvin': inputs['celsius'] + 273.15
    }
)

# When field1 changes, fahrenheit and kelvin update automatically
print(converter.get_output_hook('fahrenheit').value)  # 104.0
```

**Learn More**: Both `FunctionValues` and `UpdateFunctionValues` are typed, immutable dataclasses that eliminate parameter order confusion:
- `values.submitted` - What changed
- `values.current` - Complete current state

### **🔄 Transitive Binding**
Create complex networks automatically:

```python
from observables import XValue

# Create three observables
obs1 = XValue(100)
obs2 = XValue(200)
obs3 = XValue(300)

# Bind obs1 to obs2, then obs2 to obs3
obs1.link(obs2.hook, "value", "use_caller_value")
obs2.link(obs3.hook, "value", "use_caller_value")

# obs1 is automatically connected to obs3 through transitive binding

obs1.value = 500
print(obs2.value)  # 500 (through direct binding)
print(obs3.value)  # 500 (through transitive binding!)
```

### **🔀 Dynamic Centralization**
The system automatically centralizes storage when observables are bound:

```python
from observables import XValue

# Initially, each observable has its own Nexus
obs1 = XValue(100)
obs2 = XValue(200)

print(f"Initial Nexus IDs:")
print(f"  Obs1: {id(obs1._primary_hooks['value'].nexus)}")
print(f"  Obs2: {id(obs2._primary_hooks['value'].nexus)}")
# Output: Different IDs - separate storage

# Bind them together (merges their Nexus instances)
# Using "use_target_value" means obs1 adopts obs2's value
obs1.link(obs2.hook, "value", "use_target_value")

print(f"After binding - Nexus IDs:")
print(f"  Obs1: {id(obs1._primary_hooks['value'].nexus)}")
print(f"  Obs2: {id(obs2._primary_hooks['value'].nexus)}")
# Output: Same ID - shared storage!
```

### **💾 Memory Efficiency**
Efficient sharing of large datasets across multiple views:

```python
large_dataset = list(range(10000))  # 10,000 items

# Create multiple observables that will share the same data
obs1 = ObservableList(large_dataset)
obs2 = ObservableList(large_dataset)
obs3 = ObservableList(large_dataset)

# Bind them together
obs1.link(obs2.value_hook, "value", "use_target_value")
obs2.link(obs3.value_hook, "value", "use_target_value")

# Now all three share the same Nexus
print(f"Memory efficiency:")
print(f"  Traditional: 3 × 10,000 = 30,000 items stored")
print(f"  Our system: 1 × 10,000 = 10,000 items stored")
print(f"  Savings: 20,000 items = 160,000 bytes (64-bit)")
```

## Features

- **🎯 Centralized Value Storage**: Nexus architecture for shared state
- **🔄 Transitive Binding**: Automatic network formation
- **🔀 Dynamic Centralization**: Nexus instances merge automatically
- **💾 Memory Efficient**: Zero data duplication
- **⚡ High Performance**: Centralized operations scale efficiently
- **🔒 Thread Safe & Immutable**: All collections use immutable types internally
- **📝 Type Safe**: Full type hints and generic support with typed parameter objects
- **✨ Modern API**: Clean X-prefixed names (`XValue`, `XList`, `XSet`)
- **🎯 Typed Parameters**: `FunctionValues` and `UpdateFunctionValues` for clarity
- **✅ Well Tested**: 531 tests passing with 69% coverage

## Installation

```bash
pip install observables
```

For development dependencies:

```bash
pip install observables[dev]
```

## Quick Start

### Basic Usage - Modern X-Prefixed API

```python
from observables import XValue, Publisher
from observables.core import Subscriber

# Create observable values (each has its own central Nexus)
temperature = XValue(20.0)
display_temp = XValue(0.0)

# 1️⃣ LISTENERS (Synchronous Unidirectional)
# Simple callbacks that react to changes
def on_temp_change():
    print(f"🔔 Listener: Temperature changed to {temperature.value}°C")

temperature.add_listener(on_temp_change)

# 2️⃣ PUBLISH-SUBSCRIBE (Asynchronous Unidirectional)  
# Non-blocking async reactions for I/O operations
class DatabaseSubscriber(Subscriber):
    def _react_to_publication(self, publisher, mode):
        print(f"💾 Subscriber: Saving temperature to database...")
        # In real code: await save_to_database(temperature.value)

# Observables can also be publishers!
if isinstance(temperature, Publisher):
    temperature.add_subscriber(DatabaseSubscriber())

# 3️⃣ HOOKS (Synchronous Bidirectional with Validation)
# True bidirectional binding with state validation
display_temp.link(temperature.hook, "value", "use_target_value")

# Now observe all three in action:
print("\nChanging temperature to 25°C...")
temperature.value = 25.0
# Output:
# 🔔 Listener: Temperature changed to 25°C (synchronous)
# 💾 Subscriber: Saving temperature to database... (async, non-blocking)
# display_temp.value == 25.0 (bidirectional sync via hooks)

# Bidirectional! Change display, updates source
display_temp.value = 30.0
print(f"Original temperature: {temperature.value}°C")  # 30.0!
```

> **📝 Note:** Use the modern `X`-prefixed names (`XValue`, `XList`, `XSet`) for new code.
> Legacy `Observable*` names are deprecated but still supported for backwards compatibility.

### Publish-Subscribe Pattern (Async Notifications)

The library includes a powerful publish-subscribe pattern for asynchronous, non-blocking notifications:

```python
from observables import Publisher
from observables.core import Subscriber

# Create a publisher (observables can also be publishers!)
data_source = Publisher()

# Create subscribers for async operations
class DatabaseSync(Subscriber):
    def _react_to_publication(self, publisher, mode):
        # In async/sync mode, can use await
        # In direct mode, runs synchronously
        print(f"💾 Syncing to database... (mode: {mode})")

class NetworkNotifier(Subscriber):
    def _react_to_publication(self, publisher, mode):
        print(f"📡 Sending network notification... (mode: {mode})")

# Subscribe
data_source.add_subscriber(DatabaseSync())
data_source.add_subscriber(NetworkNotifier())

# Three publication modes:

# 1. Async mode (default) - non-blocking
data_source.publish(mode="async")  
print("Published! (reactions happening in background)")
# Continues immediately, reactions happen in event loop

# 2. Sync mode - blocking with asyncio
data_source.publish(mode="sync")
print("All async reactions completed!")
# Waits for all reactions before continuing

# 3. Direct mode - synchronous, no asyncio overhead
data_source.publish(mode="direct")
print("All reactions completed!")
# Fastest option for simple synchronous callbacks
```

### Transitive Binding (Automatic Network Formation)

```python
from observables import XValue

# Create three observables
obs1 = XValue(100)
obs2 = XValue(200)
obs3 = XValue(300)

# Bind them in a chain - this creates transitive behavior!
obs1.link(obs2.hook, "value", "use_target_value")
obs2.link(obs3.hook, "value", "use_target_value")

# Now obs1 is automatically connected to obs3!
obs1.value = 500
print(obs2.value)  # 500
print(obs3.value)  # 500 (transitive binding!)

# Break the middle connection
obs2.detach()

# obs1 and obs3 remain connected (transitive binding preserved)
obs1.value = 1000
print(obs3.value)  # 1000
print(obs2.value)  # 500 (unchanged, no longer bound)
```

### Memory-Efficient Data Sharing with Immutable Collections

```python
from observables import XList

# Create a large dataset (stored once in central Nexus as immutable tuple)
large_dataset = XList(list(range(10000)))

# Create multiple views that reference the same data
view1 = XList(large_dataset)  # References same data
view2 = XList(large_dataset)  # References same data
view3 = XList(large_dataset)  # References same data

# Bind them together (all share same Nexus)
view1.link(view2.hook, "value", "use_target_value")
view2.link(view3.hook, "value", "use_target_value")

# All views automatically stay synchronized
# Internally uses immutable tuple for thread safety
# Memory usage: 1 copy of data + 3 lightweight references
view1.append(99999)  # Creates new tuple, all views see it
print(f"All views updated: {len(view1.value)} = {len(view2.value)} = {len(view3.value)}")
print(f"Values are immutable: {type(view1.value)}")  # <class 'tuple'>
```

## 🎯 **Use Cases**

### **Common Use Cases:**
- **UI State Management**: Multiple components sharing the same data
- **Configuration Systems**: Centralized settings with automatic propagation
- **Data Pipelines**: Complex data flow networks with automatic synchronization
- **Real-time Applications**: Live data updates across multiple consumers
- **Large Data Sharing**: Efficient sharing of large datasets across views

### **Example Scenarios:**
- **Dashboard Applications**: Multiple widgets showing the same data
- **Form Systems**: Multiple form fields bound to the same data model
- **Game State Management**: Multiple systems sharing game state
- **Configuration Management**: Multiple services using the same settings
- **Data Visualization**: Multiple charts showing the same dataset

## 🚀 **Performance Benefits**

### **Memory Efficiency**
- **Scalable**: Memory usage scales with unique values, not observables
- **Efficient**: No data copying during binding operations
- **Predictable**: Memory usage is deterministic and easy to calculate

### **Operation Efficiency**
- **Single Validation**: Each change validated once, not per observable
- **Atomic Updates**: All bound observables updated simultaneously
- **No Synchronization Overhead**: No need to sync multiple copies

### **Network Efficiency**
- **Automatic Transitive Behavior**: No manual management of complex networks
- **Dynamic Centralization**: System adapts to your binding patterns
- **Efficient Cleanup**: Unused Nexus instances are automatically cleaned up

## 🔍 **How It Works**

### **1. Centralized Storage**
Each value is stored in exactly one `Nexus` - a central storage unit that coordinates all observables referencing that value.

### **2. Hook References**
Observables don't store values directly. Instead, they hold `Hook` objects that reference values stored in central `Nexus` instances.

### **3. Automatic Merging**
When observables bind, their `Nexus` instances merge, creating shared storage. This enables automatic transitive binding.

### **4. Dynamic Adaptation**
The system automatically adapts to your binding patterns, centralizing storage where possible and creating isolated storage when needed.

## 📚 **Available Observable Types**

### **Basic Types (Modern X-Prefixed API)**
- **`XValue[T]`**: Single values with validation
- **`XList[T]`**: Observable lists (internally immutable `tuple`)
- **`XDict[K, V]`**: Observable dictionaries (internally immutable `Map (from immutables)`)
- **`XSet[T]`**: Observable sets (internally immutable `frozenset`)

### **Selection Types**
- **`XSelectionDict[K, V]`**: Dictionary with selected key/value pair
- **`XSelectionOption[T]`**: Single selection from available options (immutable `frozenset`)
- **`XMultiSelectionOption[T]`**: Multiple selections from available options
- **`XSelectionEnum[E]`**: Enum values with option validation

### **Function Types**
- **`XFunction`**: Synchronize multiple hooks with custom constraints
- **`XOneWayFunction`**: One-way transformation from inputs to outputs

### **Advanced Types**
- **`XRaiseNone`**: Enforce non-None values with runtime checking
- **`XRootedPaths`**: Manage file paths with root directory
- **`XSubscriber`**: React to publications from publishers

### **Utility Types**
- **`FunctionValues[K, V]`**: Typed parameter object for user-facing function callables
- **`UpdateFunctionValues[K, V]`**: Typed parameter object for internal update callbacks
- **`Hook[T]`**: Writable hook for bidirectional binding
- **`ReadOnlyHook[T]`**: Read-only hook for one-way connections

> **💡 Immutability:** All collections (`XList`, `XSet`, `XDict`) use immutable types internally
> for thread safety and data integrity, while providing familiar mutable-like APIs.
>
> **🎯 Typed Parameters:** Use `FunctionValues` for custom functions and `UpdateFunctionValues`
> for internal callbacks - eliminates parameter order confusion!

## 🔧 **API Reference**

### **Core Binding Methods**

#### **`link(hook, to_key, initial_sync_mode)`**
Binds this observable to another observable's hook, merging their Nexus instances for bidirectional synchronization.

**Parameters:**
- `hook: HookLike` - The hook of the target observable to bind to
- `to_key: str` - Name of the component being bound (e.g., "value")
- `initial_sync_mode: Literal["use_caller_value", "use_target_value"]` - Which value to use initially

**Initial Sync Modes:**
- `"use_caller_value"`: Caller's value takes precedence, target adopts it
- `"use_target_value"`: Target's value takes precedence, caller adopts it

**Example:**
```python
from observables import XValue

source = XValue(10)
target = XValue(20)

# Connect source to target - target becomes 10
source.link(target.hook, "value", "use_caller_value")
print(target.value)  # 10
```

#### **`detach()`**
Disconnects this observable from all bindings, creating its own isolated Nexus.

### **Hook Properties**

Each observable provides hooks for different aspects of its data:

- **`XValue`**: `.hook` - Access to the single value
- **`XList`**: `.hook` - Access to the list (immutable tuple), `.length_hook` - Access to list length
- **`XSet`**: `.hook` - Access to the set (immutable frozenset), `.length_hook` - Access to set size  
- **`XDict`**: `.dict_hook` - Access to the dict (immutable Map (from immutables))
- **`XSelectionDict`**: `.dict_hook`, `.key_hook`, `.value_hook` - Dictionary selection components
- **`XSelectionOption`**: `.selected_option_hook`, `.available_options_hook` (immutable frozenset)

## 💡 **Best Practices**

### **1. Use Modern X-Prefixed API**
```python
from observables import XValue, XList, XSet, XDict

# ✅ Modern, clean API (recommended)
value = XValue(42)
items = XList([1, 2, 3])  # Returns immutable tuple
tags = XSet({"python", "reactive"})  # Returns immutable frozenset

# ❌ Legacy API (deprecated, but still works)
from observables import ObservableSingleValue, ObservableList
value = ObservableSingleValue(42)
items = ObservableList([1, 2, 3])
```

### **2. Leverage Transitive Binding**
```python
# Instead of manually binding every pair
obs1 = XValue(100)
obs2 = XValue(200)
obs3 = XValue(300)

obs1.link(obs2.hook, "value", "use_caller_value")
obs2.link(obs3.hook, "value", "use_caller_value")
# ✅ obs1 automatically connects to obs3 (no need to bind obs1 to obs3)
```

### **3. Embrace Immutability for Thread Safety**
```python
# All collections are internally immutable
list_obs = XList([1, 2, 3])
set_obs = XSet({1, 2, 3})
dict_obs = XDict({"a": 1, "b": 2})

# Values are immutable types
print(type(list_obs.value))  # <class 'tuple'>
print(type(set_obs.value))   # <class 'frozenset'>
print(type(dict_obs.dict))   # <class 'mappingproxy'>

# Mutation methods create new immutable instances
list_obs.append(4)  # Creates new tuple (1, 2, 3, 4)
set_obs.add(4)      # Creates new frozenset
```

### **4. Break Bindings When No Longer Needed**
```python
# When an observable is no longer needed in the network
obs1.detach()

# This creates a new Nexus for obs1
# Other observables remain connected through their shared Nexus
```

## 🚀 **Get Started**

```bash
pip install observables
```

```python
from observables import XValue, XList

# Create observables with centralized storage
name = XValue("John")
scores = XList([85, 90, 78])  # Internally uses immutable tuple

# Add listeners
name.add_listener(lambda: print(f"Name changed to: {name.value}"))
scores.add_listener(lambda: print(f"Scores updated: {scores.value}"))

# Create bindings (automatic Nexus merging)
name_display = XValue("")
name_display.link(name.hook, "value", "use_target_value")

# Changes propagate automatically
name.value = "Jane"  # Updates both name and name_display
scores.append(95)    # Creates new tuple, triggers listener
print(scores.value)  # (85, 90, 78, 95) - immutable tuple!
```

## 🔄 **Migration Guide**

### Migrating to Modern API

The new X-prefixed API is simple to adopt:

| Old API (Deprecated) | New API (Recommended) | Internal Type |
|---------------------|----------------------|---------------|
| `ObservableSingleValue` | `XValue` | Any type |
| `ObservableList` | `XList` | `tuple` |
| `ObservableSet` | `XSet` | `frozenset` |
| `ObservableDict` | `XDict` | `Map (from immutables)` |
| `ObservableSelectionOption` | `XSelectionOption` | `frozenset` for options |
| `ObservableMultiSelectionOption` | `XMultiSelectionOption` | `frozenset` |
| `ObservableSync` | `XFunction` | N/A |
| `ObservableTransfer` | `XOneWayFunction` | N/A |

### Key Breaking Changes

**1. Collections Return Immutable Types:**
```python
# Old API
lst = ObservableList([1, 2, 3])
print(type(lst.value))  # <class 'list'>
lst.value.append(4)     # Direct mutation worked

# New API
lst = XList([1, 2, 3])
print(type(lst.value))  # <class 'tuple'>
# lst.value.append(4)   # ❌ AttributeError - tuples are immutable
lst.append(4)           # ✅ Use observable's methods instead
```

**2. Function Callable Signatures:**
```python
# Old API
def my_func(submitted_values, current_values):
    if 'field1' in submitted_values:
        return (True, {'field2': current_values['field2'] + 1})
    return (True, {})

# New API
from observables import FunctionValues

def my_func(values: FunctionValues[str, int]):
    if 'field1' in values.submitted:
        return (True, {'field2': values.current['field2'] + 1})
    return (True, {})
```

## 📖 **Documentation**

### **Getting Started**
- **[Quick Start Guide](docs/quickstart.md)** - Get up and running in 5 minutes
- **[Tutorial](docs/tutorial.md)** - Step-by-step guide to mastering bidirectional binding and state validation
- **[API Reference](docs/api_reference.md)** - Complete API documentation with examples

### **Core Concepts**
- **[Bidirectional Binding and State Validation](docs/bidirectional_binding_and_validation.md)** - Deep dive into true bidirectional binding and rigorous state validation
- **[Hook System Technical Documentation](docs/hook_system.md)** - Technical details about the hook architecture and binding mechanics
- **[Examples and Use Cases](docs/examples_and_use_cases.md)** - Comprehensive examples and real-world scenarios

## 🔗 **Learn More**

- **Demo Script**: Run `python observables/examples/demo.py` to see the system in action
- **Documentation**: Comprehensive docs at `docs/index.md`
- **Test Suite**: Explore `tests/` to understand the system's capabilities
- **Source Code**: Dive into the implementation in `observables/`

## 🌟 **Why Choose Observables?**

### **Unique Architecture**
- **Centralized Storage**: Eliminates data duplication between observables
- **Transitive Binding**: Complex networks form automatically
- **Memory Efficient**: Scales with unique values, not observable instances

### **Developer Experience**
- **Predictable**: Clear synchronization behavior
- **Maintainable**: Automatic management of complex relationships
- **Performant**: Efficient centralized operations

### **Production Ready**
- **Thread Safe**: Designed for multi-threaded applications
- **Type Safe**: Full type hints and generic support
- **Well Tested**: Comprehensive test suite

---

**Centralized Reactive Programming for Python** - where values are stored once and networks form automatically.

**Key advantages of centralized value storage:**

- **🎯 Single Source of Truth**: Each value stored in exactly one `Nexus`
- **🔄 Transitive Binding**: Automatic network formation (A→B + B→C = A→C)
- **🔀 Dynamic Centralization**: Storage merges when observables bind
- **💾 Memory Efficient**: No data copying between observables
- **⚡ Atomic Updates**: All bound observables update simultaneously
