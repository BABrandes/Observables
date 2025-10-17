# Observables Library Documentation

The Observables library provides a Python framework for reactive programming with centralized value storage and automatic transitive binding. The architecture stores each value in a single central location rather than duplicating data across observables.

> **⚠️ IMPORTANT: DEVELOPMENT STATUS**
> 
> This library is currently **under active development** and is **NOT production ready**.
> 
> - API may change without notice
> - Not yet battle-tested in production environments
> - Comprehensive test coverage (599 tests) but limited real-world usage
> - Use at your own risk for experimental and development purposes
> 
> Feedback, contributions, and bug reports are welcome!

## Architecture Overview

### **Core Components**

**Observables** contain data and expose it through hooks. They do not bind directly to each other.

**Hooks** are the connection points between observables. When you bind observables, you connect their hooks.

**HookNexus** is the central storage that:
- Stores the actual value
- Manages all hooks connected to that value
- Maintains references to all hooks that should see the same value
- Ensures all connected hooks stay synchronized

**NexusManager** (also called HookManager) facilitates:
- Value updates across all connected hooks
- Validation when values change
- Synchronization of hook connections
- Thread-safe operations across the system
- Orchestrates all three notification mechanisms

### **Three Notification Philosophies**

The observables system provides three distinct notification mechanisms, each designed for different communication patterns:

#### **1. Listeners (Synchronous Unidirectional)**
- **Pattern**: Observer pattern with callbacks
- **Execution**: Synchronous - runs immediately during value changes
- **Direction**: Unidirectional - listeners cannot validate or reject changes
- **Registration**: `observable.add_listeners(callback)`
- **Use Case**: UI updates, logging, simple reactions to state changes
- **Thread Safety**: Protected by the same lock as value submission
- **Characteristics**: Simple, fast, blocking

#### **2. Publish-Subscribe (Asynchronous Unidirectional)**
- **Pattern**: Publisher/Subscriber with asyncio integration
- **Execution**: Asynchronous - runs in event loop (non-blocking)
- **Direction**: Unidirectional - subscribers cannot validate or reject publications
- **Registration**: `publisher.add_subscriber(subscriber)`
- **Publication Modes**:
  - `async` (default): Non-blocking, returns immediately, reactions in background
  - `sync`: Blocking, waits for all async reactions to complete
  - `direct`: Synchronous without asyncio, fastest for simple callbacks
- **Use Case**: Decoupled components, async I/O, database syncing, network calls
- **Thread Safety**: Each subscriber reaction runs independently in event loop
- **Characteristics**: Decoupled, non-blocking, ideal for I/O operations

#### **3. Hooks (Synchronous Bidirectional with Validation)**
- **Pattern**: Value synchronization with bidirectional binding
- **Execution**: Synchronous - integrated into value submission flow
- **Direction**: Bidirectional - any connected hook can validate and reject changes
- **Connection**: `observable.connect_hook(target_hook, key, sync_mode)`
- **Use Case**: Maintaining invariants, bidirectional data binding, enforcing valid state
- **Thread Safety**: Protected by the same lock as value submission
- **Characteristics**: Validates before changes, enforces consistency, bidirectional

### **Key Features**

- **Centralized Storage**: Each value is stored once in a HookNexus
- **Hook-Based Binding**: Observables bind via their hooks, not directly
- **Transitive Binding**: When A's hook connects to B's hook and B's hook connects to C's hook, all three share the same HookNexus
- **Automatic Synchronization**: NexusManager ensures all hooks referencing a HookNexus see the same value
- **Multiple Notification Paths**: Choose the right notification mechanism for your use case

## How It Works

### **Binding Process**

When you connect two observables:
1. Each observable exposes its data through a hook
2. You call `observable1.connect_hook(observable2.hook, "value", "use_caller_value")`
3. Behind the scenes, the hooks merge to reference the same HookNexus
4. Both observables now read and write to the same central storage

### **Value Updates and Notifications**

When you change a value, the NexusManager orchestrates a comprehensive 6-phase submission flow:

**Phase 1: Value Equality Check**
- Compares new values with current values (unless forced)

**Phase 2: Value Completion**
- Completes missing related values (e.g., dict item → full dict)

**Phase 3: Value Collection**
- Collects affected observables, hooks, and publishers

**Phase 4: Value Validation**
- Validates all values before any changes
- If validation fails, entire submission is rejected (atomicity)

**Phase 5: Value Update**
- Updates all HookNexus instances with new values
- All connected hooks see changes simultaneously

**Phase 6: Notifications** (Four mechanisms in order)
1. **Invalidation** (Synchronous): Observable state recomputation
2. **Reactions** (Synchronous): Hook reaction callbacks
3. **Publishing** (Asynchronous): Subscriber notifications via asyncio tasks (non-blocking!)
4. **Listeners** (Synchronous): Observer pattern callbacks

This multi-phase approach ensures consistency, validation, and proper notification of all affected components while supporting both synchronous and asynchronous notification patterns.

### **Transitive Binding**

When you bind A→B→C:
1. A's hook and B's hook merge to reference HookNexus #1
2. B's hook and C's hook merge to reference HookNexus #2
3. Since B's hook is involved in both, all three hooks end up referencing the same HookNexus
4. Result: A, B, and C all share one central storage point

## Examples

### **1. Transitive Binding - Automatic Network Formation**
```python
# Create three observables
obs1 = ObservableSingleValue(100)
obs2 = ObservableSingleValue(200)
obs3 = ObservableSingleValue(300)

# Bind obs1 to obs2, then obs2 to obs3
obs1.connect_hook(obs2.hook, "value", "use_caller_value")
obs2.connect_hook(obs3.hook, "value", "use_caller_value")

# obs1 is automatically connected to obs3
# This happens through HookNexus merging during the binding process

obs1.value = 500
print(obs2.value)  # 500 (through direct binding)
print(obs3.value)  # 500 (through transitive binding!)

# Break the middle connection
obs2.detach()

# obs1 and obs3 remain connected (transitive binding preserved)
obs1.value = 1000
print(obs3.value)  # 1000 (transitive connection maintained)
print(obs2.value)  # 500 (unchanged, no longer bound)
```

### **2. HookNexus Merging - Dynamic Centralization**
```python
# Initially, each observable has its own HookNexus
obs1 = ObservableSingleValue(100)
obs2 = ObservableSingleValue(200)

print(f"Initial HookNexus IDs:")
print(f"  Obs1: {id(obs1._primary_hooks['value'].hook_nexus)}")
print(f"  Obs2: {id(obs2._primary_hooks['value'].hook_nexus)}")
# Output: Different IDs - separate storage

# Bind them together (their hooks now reference the same HookNexus)
obs1.connect_hook(obs2.hook, "value", "use_caller_value")

print(f"After binding - HookNexus IDs:")
print(f"  Obs1: {id(obs1._primary_hooks['value'].hook_nexus)}")
print(f"  Obs2: {id(obs2._primary_hooks['value'].hook_nexus)}")
# Output: Same ID - shared storage!

# When obs2 detaches, it gets its own HookNexus again
obs2.detach()
print(f"After obs2 detach:")
print(f"  Obs1: {id(obs1._primary_hooks['value'].hook_nexus)}")
print(f"  Obs2: {id(obs2._primary_hooks['value'].hook_nexus)}")
# Output: Different IDs again - separate storage
```

### **3. Memory Efficiency - Zero Data Duplication**
```python
# Traditional approach: Each observable stores its own copy
# Our approach: Single central storage, observables just reference it

large_dataset = list(range(10000))  # 10,000 items

# Create multiple observables that will share the same data
obs1 = ObservableList(large_dataset)
obs2 = ObservableList(large_dataset)
obs3 = ObservableList(large_dataset)

# Bind them together - hooks reference the same HookNexus
obs1.connect_hook(obs2.value_hook, "value", "use_target_value")
obs2.connect_hook(obs3.value_hook, "value", "use_target_value")

# Now all three share the same HookNexus
print(f"Memory efficiency:")
print(f"  Traditional: 3 × 10,000 = 30,000 items stored")
print(f"  Our system: 1 × 10,000 = 10,000 items stored")
print(f"  Savings: 20,000 items = 160,000 bytes (64-bit)")

# Modifying the data propagates to all three
obs1.append(99999)
print(f"All three updated simultaneously:")
print(f"  Obs1 length: {len(obs1.value)}")
print(f"  Obs2 length: {len(obs2.value)}")
print(f"  Obs3 length: {len(obs3.value)}")
```

## Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Observable A   │     │  Observable B   │     │  Observable C   │
│                 │     │                 │     │                 │
│   Hook ─────────┼─────┼──── Hook ───────┼─────┼───── Hook       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │       HookNexus           │
                    │                           │
                    │  • Stores the value       │
                    │  • Manages hook refs      │
                    │  • Coordinates updates    │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                         ┌────────────────┐
                         │ NexusManager   │
                         │                │
                         │ • Validates    │
                         │ • Updates      │
                         │ • Notifies     │
                         └────────────────┘
```

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

#### **`connect_hook(hook, to_key, initial_sync_mode)`**
Connects this observable's hook to another observable's hook. After connection, both hooks reference the same HookNexus for bidirectional synchronization.

**Parameters:**
- `hook: HookLike` - The hook of the target observable to connect to
- `to_key: str` - The key of the hook on this observable (e.g., "value")
- `initial_sync_mode: Literal["use_caller_value", "use_target_value"]` - Which value to use for initial synchronization

**Initial Sync Modes:**
- `"use_caller_value"`: Caller's value takes precedence, target adopts it
- `"use_target_value"`: Target's value takes precedence, caller adopts it

**Example:**
```python
obs1 = ObservableSingleValue(100)
obs2 = ObservableSingleValue(200)

# obs2 gets obs1's value (100)
obs1.connect_hook(obs2.hook, "value", "use_caller_value")
print(obs2.value)  # 100

# obs1 gets obs2's value (200)
obs1.connect_hook(obs2.hook, "value", "use_target_value")
print(obs1.value)  # 200
```

#### **`detach()`**
Disconnects this observable from all bindings, creating its own isolated HookNexus.

**Example:**
```python
obs1 = ObservableSingleValue(100)
obs2 = ObservableSingleValue(200)
obs1.connect_hook(obs2.hook, "value", "use_target_value")

# Disconnect obs1
obs1.detach()

# Changes no longer propagate
obs1.value = 300
print(obs2.value)  # 200 (unchanged)
```

### **Hook Properties**

Each observable type exposes hooks for accessing its data:

#### **`ObservableSingleValue`**
- `.hook` - Access to the value

#### **`ObservableList`**
- `.value_hook` - Access to the list
- `.length_hook` - Access to the list length (read-only)

#### **`ObservableDict`**
- `.value_hook` - Access to the dictionary
- `.length_hook` - Access to the dictionary size (read-only)

#### **`ObservableSet`**
- `.value_hook` - Access to the set
- `.length_hook` - Access to the set size (read-only)

#### **`ObservableTuple`**
- `.value_hook` - Access to the tuple
- `.length_hook` - Access to the tuple length (read-only)

#### **`ObservableSelectionOption`**
- `.selected_option_hook` - Access to the selected option
- `.available_options_hook` - Access to the available options set

#### **`ObservableMultiSelectionOption`**
- `.selected_options_hook` - Access to the set of selected options
- `.available_options_hook` - Access to the available options set

Note: Secondary hooks like `length_hook` are computed from primary hooks and cannot be directly modified.

## 💡 **Best Practices**

### **1. Leverage Transitive Binding**
```python
# Instead of manually binding every pair
obs1.connect_hook(obs2.hook, "value", "use_caller_value")
obs2.connect_hook(obs3.hook, "value", "use_caller_value")
obs1.connect_hook(obs3.hook, "value", "use_caller_value")  # ❌ Redundant!

# Just create the chain - transitive binding handles the rest
obs1.connect_hook(obs2.hook, "value", "use_caller_value")
obs2.connect_hook(obs3.hook, "value", "use_caller_value")
# ✅ obs1 automatically connects to obs3
```

### **2. Use Centralized Storage for Large Data**
```python
# Useful for sharing large datasets across multiple views
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

## Performance Characteristics

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

## 🔍 **Advanced Concepts**

### **HookNexus Lifecycle**
1. **Creation**: Each observable starts with its own HookNexus
2. **Merging**: When observables bind, their HookNexus instances merge
3. **Sharing**: Bound observables share the same central storage
4. **Separation**: When bindings break, observables get new HookNexus instances

### **Transitive Binding Rules**
- **Automatic**: Transitive connections form automatically
- **Persistent**: Transitive connections survive intermediate binding changes
- **Efficient**: No additional overhead for transitive behavior

### **Validation and Consistency**
- **Centralized**: Validation happens in HookNexus, not per observable
- **Consistent**: All bound observables see the same validation results
- **Efficient**: Single validation per change, not per bound observable

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

## Technical Details

### **Architecture Benefits**
- Centralized value storage eliminates data duplication
- Transitive binding creates complex networks automatically
- Memory usage scales with unique values, not observable count

### **Implementation**
- Thread-safe operations using locks
- Full type hints and generic support
- Comprehensive test suite (549 tests passing)

## Getting Started

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
name_display.connect_hook(name.hook, "value", "use_target_value")

# Changes propagate automatically
name.value = "Jane"  # Updates both name and name_display
scores.append(95)           # Triggers listener notification
```

## 📖 **Documentation**

### **Getting Started**
- **[Quick Start Guide](quickstart.md)** - Get up and running in 5 minutes
- **[Tutorial](tutorial.md)** - Step-by-step guide to mastering bidirectional binding and state validation
- **[API Reference](api_reference.md)** - Complete API documentation with examples

### **Core Concepts**
- **[Bidirectional Binding and State Validation](bidirectional_binding_and_validation.md)** - Deep dive into true bidirectional binding and rigorous state validation
- **[Hook System Technical Documentation](hook_system.md)** - Technical details about the hook architecture and binding mechanics
- **[Examples and Use Cases](examples_and_use_cases.md)** - Comprehensive examples and real-world scenarios

## 🔗 **Learn More**

- **Demo Script**: Run `python observables/examples/demo.py` to see the system in action
- **Test Suite**: Explore `tests/` to understand the system's capabilities
- **Source Code**: Dive into the implementation in `observables/`

## Key Characteristics

### **Bidirectional Binding**
When observables are connected through their hooks, they share the same HookNexus. Changes propagate in both directions automatically.

### **State Validation**
The system validates all value changes before applying them. Invalid operations are rejected with descriptive error messages.

### **Transitive Binding**
When you bind A→B→C, all three observables end up referencing the same HookNexus. The system handles transitive connections automatically.

### **Centralized Storage**
Values are stored once in HookNexus instances. Multiple observables reference the same storage, eliminating synchronization issues.
