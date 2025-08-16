# Observables Library Documentation

Welcome to the comprehensive documentation for the Observables library! This library provides a powerful and flexible way to create observable objects with automatic change notifications and a sophisticated **transitive binding system** built on a **hook "bus" architecture**.

## 📖 Documentation Structure

### 🚀 [Main Documentation](index.md)
**Start here!** Complete overview of the library with:
- Quick start guide
- Core concepts explanation
- Basic examples
- API reference
- Installation instructions

### 🏗️ [Hook System Technical Details](hook_system.md)
Deep technical dive into the architecture:
- Hook system components
- Binding mechanics
- Group management
- Performance characteristics
- Debugging and troubleshooting
- Future enhancements

### 🎯 [Examples and Use Cases](examples_and_use_cases.md)
Real-world applications and patterns:
- Configuration management systems
- Multi-component GUI applications
- Data processing pipelines
- Form validation systems
- State management patterns
- Advanced binding patterns
- Performance tips
- Testing strategies

## 🧠 Key Concepts

### Transitive Binding System
The library implements **transitive binding**, which means that if A is bound to B, and B is bound to C, then A is automatically connected to C. This creates a powerful network of synchronized observables.

### Hook "Bus" Architecture
The system uses a sophisticated **hook "bus" system** that acts as a central communication hub:
- **Hooks**: Represent data components of observables
- **Hook Groups**: Collections of hooks that share the same data state
- **Bus Communication**: Changes automatically propagate through the entire system
- **Automatic Synchronization**: All hooks in a group maintain the same value

### Key Principles
1. **All-or-Nothing Within Groups**: Hooks in the same group are all synchronized together
2. **Transitive Propagation**: Changes automatically propagate through the entire binding chain
3. **No Granular Disconnection**: You cannot selectively disconnect specific pairs within a merged group
4. **Automatic Group Management**: The system automatically manages hook groups and their connections

## 🚀 Quick Start

```python
from observables import ObservableSingleValue, ObservableList

# Create observables
name = ObservableSingleValue("John")
age = ObservableSingleValue(25)
scores = ObservableList([85, 90, 78])

# Add listeners
def on_name_change():
    print(f"Name changed to: {name.single_value}")

name.add_listeners(on_name_change)

# Changes automatically trigger notifications
name.single_value = "Jane"  # Prints: "Name changed to: Jane"

# Create bindings
age.bind_to(name)  # Now age and name are synchronized
age.single_value = 30  # name.single_value automatically becomes 30
```

## 🔗 Binding Examples

### Simple Binding
```python
obs1 = ObservableSingleValue(10)
obs2 = ObservableSingleValue(20)

# Bind them together
obs1.bind_to(obs2)
# Now obs1.value == obs2.value == 20
```

### Transitive Binding
```python
obs1 = ObservableSingleValue(10)
obs2 = ObservableSingleValue(20)
obs3 = ObservableSingleValue(30)

# Build chain: obs1 ↔ obs2 ↔ obs3
obs1.bind_to(obs2)
obs2.bind_to(obs3)

# Now ALL three are bound together due to transitive binding!
obs1.single_value = 100
# Result: obs1.value == obs2.value == obs3.value == 100
```

### Disconnection
```python
# Continuing from above...
obs2.disconnect()

# Now:
# - obs1 and obs3 remain bound together (transitive binding)
# - obs2 is isolated in its own group
# - obs2 no longer affects or is affected by obs1 and obs3
```

## 📚 Available Observable Types

- **`ObservableSingleValue[T]`**: Single values with validation
- **`ObservableList[T]`**: Observable lists with change notifications
- **`ObservableDict[K, V]`**: Observable dictionaries
- **`ObservableSet[T]`**: Observable sets
- **`ObservableTuple[T]**: Observable tuples
- **`ObservableSelectionOption[T]`**: Single selection from options
- **`ObservableMultiSelectionOption[T]`**: Multiple selection from options
- **`ObservableEnum[T]`**: Enum-based selections

## 🎯 Common Use Cases

- **GUI Applications**: Automatic UI updates when data changes
- **Data Synchronization**: Keep multiple data sources in sync
- **Configuration Management**: Reactive configuration with validation
- **State Management**: Centralized state with automatic propagation
- **Event-Driven Architecture**: Decoupled components with change notifications
- **Multi-Component Systems**: Complex binding relationships
- **Form Validation**: Cross-field validation with dependencies
- **Data Pipelines**: Multi-stage processing with synchronization

## ⚠️ Important Notes

1. **Transitive Binding**: Remember that binding is transitive - if A↔B and B↔C, then A↔C
2. **No Granular Control**: You cannot selectively disconnect specific pairs within a merged group
3. **Available Options Don't Merge**: The system only synchronizes selected values, not available options
4. **Hook Group Management**: The system automatically manages hook groups - don't try to manipulate them directly
5. **Disconnection Isolation**: When you disconnect a hook, it becomes completely isolated

## 🔧 Getting Help

- **Start with the [Main Documentation](index.md)** for basic concepts
- **Check [Examples and Use Cases](examples_and_use_cases.md)** for practical patterns
- **Dive into [Hook System Details](hook_system.md)** for advanced topics
- **Run the tests** to see working examples
- **Check the source code** for implementation details

## 🤝 Contributing

Contributions are welcome! Please see the main [README](../README.md) for contribution guidelines.

---

**Happy coding with Observables! 🚀✨**
