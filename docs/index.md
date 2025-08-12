# Observables Library Documentation

Welcome to the Observables library documentation! This library provides a powerful and flexible way to create observable objects with automatic change notifications and bidirectional bindings.

## Quick Start

```python
from observables import ObservableSingleValue, ObservableList, ObservableDict

# Create observable values
name = ObservableSingleValue("John")
age = ObservableSingleValue(25)
scores = ObservableList([85, 90, 78])

# Add listeners
def on_name_change():
    print(f"Name changed to: {name.value}")

name.add_listeners(on_name_change)

# Changes automatically trigger notifications
name.set_value("Jane")  # Prints: "Name changed to: Jane"
```

## Features

- **Observable Collections**: `ObservableDict`, `ObservableList`, `ObservableSet`
- **Single Value Observables**: `ObservableSingleValue` for primitive types
- **Selection Options**: `ObservableSelectionOption` for dropdown-like behavior
- **Automatic Change Notifications**: Listeners are automatically notified when values change
- **Bidirectional Bindings**: Create synchronized connections between observables
- **Type Safety**: Full type hints and generic support
- **Thread Safe**: Designed for use in multi-threaded applications

## Installation

```bash
pip install observables
```

For development dependencies:

```bash
pip install observables[dev]
```

## Core Concepts

### Observables
Observables are objects that can be observed by listeners. When an observable's value changes, all registered listeners are automatically notified.

### Listeners
Listeners are callbacks that are executed when an observable changes. They can be any callable object (functions, methods, lambdas).

### Bindings
Bindings create synchronized connections between observables. When one observable changes, all bound observables automatically update to maintain consistency.

## Examples

### Basic Usage
```python
from observables import ObservableSingleValue

# Create an observable
counter = ObservableSingleValue(0)

# Add a listener
def on_counter_change():
    print(f"Counter is now: {counter.value}")

counter.add_listeners(on_counter_change)

# Change the value
counter.set_value(5)  # Prints: "Counter is now: 5"
```

### Bidirectional Bindings
```python
from observables import ObservableSingleValue, SyncMode

# Create two observables
a = ObservableSingleValue(10)
b = ObservableSingleValue(10)

# Bind them together
a.bind_to_observable(b)

# Now changing one updates the other
a.set_value(20)
print(b.value)  # 20

b.set_value(30)
print(a.value)  # 30
```

### Observable Collections
```python
from observables import ObservableList, ObservableDict

# Observable List
todo_list = ObservableList(["Buy groceries", "Walk dog"])
todo_list.add_listeners(lambda: print("Todo list updated!"))

todo_list.append("Read book")  # Triggers notification

# Observable Dictionary
config = ObservableDict({"theme": "dark", "language": "en"})
config.add_listeners(lambda: print("Config changed!"))

config["theme"] = "light"  # Triggers notification
```

## API Reference

### ObservableSingleValue
- `value`: Get the current value
- `set_value(value)`: Set a new value
- `add_listeners(*callbacks)`: Add change notification callbacks
- `remove_listeners(*callbacks)`: Remove specific callbacks
- `bind_to_observable(other, sync_mode)`: Create bidirectional binding

### ObservableList
- `list`: Get the current list value
- `append(item)`: Add an item to the end
- `remove(item)`: Remove an item
- `insert(index, item)`: Insert an item at a specific position
- All standard list methods are supported

### ObservableDict
- `dict`: Get the current dictionary value
- `set_item(key, value)`: Set a key-value pair
- `get_item(key, default)`: Get a value by key
- `remove_item(key)`: Remove a key-value pair
- All standard dict methods are supported

### ObservableSet
- `set`: Get the current set value
- `add(item)`: Add an item
- `remove(item)`: Remove an item
- All standard set methods are supported

### ObservableSelectionOption
- `options`: Get/set available options
- `selected_option`: Get/set the selected option
- `add_listeners(*callbacks)`: Add change notification callbacks

## Use Cases

- **GUI Applications**: Automatic UI updates when data changes
- **Data Synchronization**: Keep multiple data sources in sync
- **Configuration Management**: Reactive configuration with validation
- **State Management**: Centralized state with automatic propagation
- **Event-Driven Architecture**: Decoupled components with change notifications

## Contributing

Contributions are welcome! Please see our [Contributing Guide](contributing.md) for details.

## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](../LICENSE) file for details.
