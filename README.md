# Observables - Centralized Reactive Programming

A Python library for creating observable objects with **centralized value storage** and **automatic transitive binding**. Unlike traditional reactive libraries that duplicate data across observables, this system stores each value in exactly one central location, providing efficient and reliable state management.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI version](https://badge.fury.io/py/observables.svg)](https://badge.fury.io/py/observables)
[![Tests](https://github.com/yourusername/observables/workflows/Tests/badge.svg)](https://github.com/yourusername/observables/actions)

## 🚀 **Centralized Architecture**

**This library uses a unique centralized value storage approach:**

- **🎯 Single Source of Truth**: Each value is stored in exactly one `HookNexus`
- **🔄 Transitive Binding**: When you bind A→B and B→C, A automatically connects to C
- **🔀 Dynamic Centralization**: HookNexus instances merge when observables bind
- **💾 Memory Efficient**: Values are never copied between observables
- **⚡ Atomic Updates**: All bound observables see changes simultaneously

## 🌟 **Key Features**

### **🔄 Bidirectional Binding**
This library provides bidirectional binding through shared storage:

```python
# Create two observables
temp_celsius = ObservableSingleValue(25.0)
temp_fahrenheit = ObservableSingleValue(77.0)

# Bind them bidirectionally
temp_celsius.attach(temp_fahrenheit.hook_value, "value", InitialSyncMode.USE_CALLER_VALUE)

# 🔄 Changes propagate in BOTH directions
temp_celsius.value = 30.0
print(temp_fahrenheit.value)  # 30.0 (celsius → fahrenheit)

temp_fahrenheit.value = 100.0
print(temp_celsius.value)     # 100.0 (fahrenheit → celsius)
```

### **🛡️ State Validation**
Invalid states are prevented through built-in validation:

```python
# Selection options with validation
color_selector = ObservableSelectionOption("red", {"red", "green", "blue"})

# ✅ Valid selection
color_selector.selected_option = "green"  # Works

# ❌ Invalid selection - automatically rejected
try:
    color_selector.selected_option = "purple"  # Not in available options
except ValueError as e:
    print(f"Validation enforced: {e}")

# State remains valid after rejection
print(color_selector.selected_option)  # Still "green"
```

### **🔄 Transitive Binding**
Create complex networks automatically:

```python
# Create three observables
obs1 = ObservableSingleValue(100)
obs2 = ObservableSingleValue(200)
obs3 = ObservableSingleValue(300)

# Bind obs1 to obs2, then obs2 to obs3
obs1.attach(obs2.hook_value, "value", InitialSyncMode.USE_CALLER_VALUE)
obs2.attach(obs3.hook_value, "value", InitialSyncMode.USE_CALLER_VALUE)

# obs1 is automatically connected to obs3 through transitive binding

obs1.value = 500
print(obs2.value)  # 500 (through direct binding)
print(obs3.value)  # 500 (through transitive binding!)
```

### **🔀 Dynamic Centralization**
The system automatically centralizes storage when observables are bound:

```python
# Initially, each observable has its own HookNexus
obs1 = ObservableSingleValue(100)
obs2 = ObservableSingleValue(200)

print(f"Initial HookNexus IDs:")
print(f"  Obs1: {id(obs1._component_hooks['value'].hook_nexus)}")
print(f"  Obs2: {id(obs2._component_hooks['value'].hook_nexus)}")
# Output: Different IDs - separate storage

# Bind them together (merges their HookNexus instances)
obs1.bind_to(obs2, InitialSyncMode.SELF_IS_UPDATED)

print(f"After binding - HookNexus IDs:")
print(f"  Obs1: {id(obs1._component_hooks['value'].hook_nexus)}")
print(f"  Obs2: {id(obs2._component_hooks['value'].hook_nexus)}")
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
obs1.bind_to(obs2, InitialSyncMode.SELF_IS_UPDATED)
obs2.bind_to(obs3, InitialSyncMode.SELF_IS_UPDATED)

# Now all three share the same HookNexus
print(f"Memory efficiency:")
print(f"  Traditional: 3 × 10,000 = 30,000 items stored")
print(f"  Our system: 1 × 10,000 = 10,000 items stored")
print(f"  Savings: 20,000 items = 160,000 bytes (64-bit)")
```

## Features

- **🎯 Centralized Value Storage**: Revolutionary HookNexus architecture
- **🔄 Transitive Binding**: Automatic network formation
- **🔀 Dynamic Centralization**: HookNexus instances merge automatically
- **💾 Memory Efficient**: Zero data duplication
- **⚡ High Performance**: Centralized operations scale efficiently
- **🔒 Thread Safe**: Designed for multi-threaded applications
- **📝 Type Safe**: Full type hints and generic support
- **✅ Well Tested**: Comprehensive test suite with 100% pass rate

## Installation

```bash
pip install observables
```

For development dependencies:

```bash
pip install observables[dev]
```

## Quick Start

### Basic Usage

```python
from observables import ObservableSingleValue, ObservableList, ObservableDict

# Create observable values (each has its own central HookNexus)
name = ObservableSingleValue("John")
age = ObservableSingleValue(25)
scores = ObservableList([85, 90, 78])
user_data = ObservableDict({"city": "New York", "country": "USA"})

# Add listeners
def on_name_change():
    print(f"Name changed to: {name.value}")

def on_age_change():
    print(f"Age changed to: {age.value}")

name.add_listeners(on_name_change)
age.add_listeners(on_age_change)

# Changes automatically trigger notifications
name.value = "Jane"  # Prints: "Name changed to: Jane"
age.value = 26       # Prints: "Age changed to: 26"
```

### Transitive Binding (Automatic Network Formation)

```python
from observables import ObservableSingleValue, InitialSyncMode

# Create three observables
obs1 = ObservableSingleValue(100)
obs2 = ObservableSingleValue(200)
obs3 = ObservableSingleValue(300)

# Bind them in a chain - this creates transitive behavior!
obs1.bind_to(obs2, InitialSyncMode.SELF_IS_UPDATED)
obs2.bind_to(obs3, InitialSyncMode.SELF_IS_UPDATED)

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

### Memory-Efficient Data Sharing

```python
from observables import ObservableList, InitialSyncMode

# Create a large dataset (stored once in central HookNexus)
large_dataset = ObservableList(list(range(10000)))

# Create multiple views that reference the same data
view1 = ObservableList(large_dataset)  # References same data
view2 = ObservableList(large_dataset)  # References same data
view3 = ObservableList(large_dataset)  # References same data

# Bind them together (all share same HookNexus)
view1.bind_to(view2, InitialSyncMode.SELF_IS_UPDATED)
view2.bind_to(view3, InitialSyncMode.SELF_IS_UPDATED)

# All views automatically stay synchronized
# Memory usage: 1 copy of data + 3 lightweight references
view1.append(99999)
print(f"All views updated: {len(view1.value)} = {len(view2.value)} = {len(view3.value)}")
```

## 🎯 **Use Cases**

### **Perfect For:**
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
- **Efficient Cleanup**: Unused HookNexus instances are automatically cleaned up

## 🔍 **How It Works**

### **1. Centralized Storage**
Each value is stored in exactly one `HookNexus` - a central storage unit that coordinates all observables referencing that value.

### **2. Hook References**
Observables don't store values directly. Instead, they hold `Hook` objects that reference values stored in central `HookNexus` instances.

### **3. Automatic Merging**
When observables bind, their `HookNexus` instances merge, creating shared storage. This enables automatic transitive binding.

### **4. Dynamic Adaptation**
The system automatically adapts to your binding patterns, centralizing storage where possible and creating isolated storage when needed.

## 📚 **Available Observable Types**

### **Built-in Types**
- **`ObservableSingleValue[T]`**: Single values with validation
- **`ObservableList[T]`**: Observable lists with item-level binding
- **`ObservableDict[K, V]`**: Observable dictionaries
- **`ObservableSet[T]`**: Observable sets
- **`ObservableTuple[T, ...]`**: Observable tuples

### **Specialized Types**
- **`ObservableSelectionOption[T]`**: Single selection from available options
- **`ObservableMultiSelectionOption[T]`**: Multiple selections from available options
- **`ObservableEnum[T]`**: Enum values with option validation

## 🔧 **API Reference**

### **Core Binding Methods**

#### **`bind_to(observable, initial_sync_mode=InitialSyncMode.SELF_IS_UPDATED)`**
Binds this observable to another observable, merging their HookNexus instances.

**Parameters:**
- `observable`: The target observable to bind to
- `initial_sync_mode`: How values should be synchronized initially

**Initial Sync Modes:**
- `SELF_IS_UPDATED`: This observable gets the target's value
- `SELF_UPDATES`: Target gets this observable's value

#### **`detach()`**
Disconnects this observable from all bindings, creating its own isolated HookNexus.

### **Hook Properties**

Each observable provides hooks for different aspects of its data:

- **`hook_value`**: Access to observable values for all types

## 💡 **Best Practices**

### **1. Leverage Transitive Binding**
```python
# Instead of manually binding every pair
obs1.bind_to(obs2)
obs2.bind_to(obs3)
obs1.bind_to(obs3)  # ❌ Redundant!

# Just create the chain - transitive binding handles the rest
obs1.bind_to(obs2)
obs2.bind_to(obs3)
# ✅ obs1 automatically connects to obs3
```

### **2. Use Centralized Storage for Large Data**
```python
# Perfect for sharing large datasets across multiple views
large_dataset = ObservableList([...])  # Stored once

view1 = ObservableList(large_dataset)  # References same data
view2 = ObservableList(large_dataset)  # References same data
view3 = ObservableList(large_dataset)  # References same data

# All views automatically stay synchronized
# Memory usage: 1 copy of data + 3 lightweight references
```

### **3. Break Bindings When No Longer Needed**
```python
# When an observable is no longer needed in the network
obs1.detach()

# This creates a new HookNexus for obs1
# Other observables remain connected through their shared HookNexus
```

## 🚀 **Get Started**

```bash
pip install observables
```

```python
from observables import ObservableSingleValue, ObservableList

# Create observables with centralized storage
name = ObservableSingleValue("John")
scores = ObservableList([85, 90, 78])

# Add listeners
name.add_listeners(lambda: print(f"Name changed to: {name.value}"))
scores.add_listeners(lambda: print(f"Scores updated: {scores.value}"))

# Create bindings (automatic HookNexus merging)
name_display = ObservableSingleValue("")
name_display.bind_to(name, InitialSyncMode.SELF_IS_UPDATED)

# Changes propagate automatically
name.value = "Jane"  # Updates both name and name_display
scores.append(95)           # Triggers listener notification
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

- **🎯 Single Source of Truth**: Each value stored in exactly one `HookNexus`
- **🔄 Transitive Binding**: Automatic network formation (A→B + B→C = A→C)
- **🔀 Dynamic Centralization**: Storage merges when observables bind
- **💾 Memory Efficient**: No data copying between observables
- **⚡ Atomic Updates**: All bound observables update simultaneously
