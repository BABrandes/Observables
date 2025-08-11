# Observables

A Python library for creating observable objects with automatic change notifications and bidirectional bindings.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/observables.svg)](https://badge.fury.io/py/observables)
[![Tests](https://github.com/yourusername/observables/workflows/Tests/badge.svg)](https://github.com/yourusername/observables/actions)

## Features

- **Observable Collections**: `ObservableDict`, `ObservableList`, `ObservableSet`
- **Single Value Observables**: `ObservableSingleValue` for primitive types
- **Selection Options**: `ObservableSelectionOption` for dropdown-like behavior
- **Automatic Change Notifications**: Listeners are automatically notified when values change
- **Bidirectional Bindings**: Create synchronized connections between observables
- **Type Safety**: Full type hints and generic support
- **Thread Safe**: Designed for use in multi-threaded applications
- **Memory Efficient**: Automatic cleanup of listeners and bindings

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

# Create observable values
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
name.set_value("Jane")  # Prints: "Name changed to: Jane"
age.set_value(26)       # Prints: "Age changed to: 26"
```

### Bidirectional Bindings

```python
from observables import ObservableSingleValue, SyncMode

# Create two observables
price_usd = ObservableSingleValue(100.0)
price_eur = ObservableSingleValue(85.0)

# Bind them together (EUR will update when USD changes)
price_usd.bind_to_observable(
    price_eur, 
    initial_sync_mode=SyncMode.UPDATE_VALUE_FROM_OBSERVABLE
)

# Now changing one updates the other
price_usd.set_value(110.0)
print(price_eur.value)  # 110.0

# The binding works both ways
price_eur.set_value(95.0)
print(price_usd.value)  # 95.0
```

### Observable Collections

```python
from observables import ObservableList, ObservableDict

# Observable List
todo_list = ObservableList(["Buy groceries", "Walk dog"])
todo_list.add_listeners(lambda: print("Todo list updated!"))

todo_list.append("Read book")  # Triggers notification
todo_list[0] = "Buy organic groceries"  # Triggers notification

# Observable Dictionary
config = ObservableDict({"theme": "dark", "language": "en"})
config.add_listeners(lambda: print("Config changed!"))

config["theme"] = "light"  # Triggers notification
config.update({"language": "de", "timezone": "UTC"})  # Triggers notification
```

### Selection Options

```python
from observables import ObservableSelectionOption

# Create a selection with available options
country_selector = ObservableSelectionOption(
    options=["USA", "Canada", "UK", "Germany"],
    selected_option="USA"
)

country_selector.add_listeners(lambda: print(f"Selected: {country_selector.selected_option}"))

# Change selection
country_selector.selected_option = "Canada"  # Triggers notification

# Change available options
country_selector.options = ["USA", "Canada", "UK", "Germany", "France"]
```

## Advanced Features

### Custom Validation

```python
from observables import ObservableSingleValue

def validate_age(age):
    return 0 <= age <= 150

age = ObservableSingleValue(25, validator=validate_age)

# This will raise a ValueError
age.set_value(200)  # ValueError: Invalid value: 200
```

### Binding Chains

```python
from observables import ObservableSingleValue, SyncMode

# Create a chain of observables
a = ObservableSingleValue(1)
b = ObservableSingleValue(1)
c = ObservableSingleValue(1)

# Bind them in a chain
a.bind_to_observable(b)
b.bind_to_observable(c)

# Changing 'a' propagates through the chain
a.set_value(10)
print(f"a: {a.value}, b: {b.value}, c: {c.value}")  # a: 10, b: 10, c: 10
```

### Conditional Bindings

```python
from observables import ObservableSingleValue, ObservableDict

# Create observables
is_enabled = ObservableSingleValue(True)
value = ObservableSingleValue(42)
config = ObservableDict({"enabled": True, "value": 42})

# Only bind when enabled
def update_binding():
    if is_enabled.value:
        value.bind_to_observable(config["value"])
    else:
        value.unbind_from_observable(config["value"])

is_enabled.add_listeners(update_binding)
```

## API Reference

### Core Classes

- **`ObservableSingleValue[T]`**: Observable wrapper for single values
- **`ObservableList[T]`**: Observable list with change notifications
- **`ObservableDict[K, V]`**: Observable dictionary with change notifications
- **`ObservableSet[T]`**: Observable set with change notifications
- **`ObservableSelectionOption[T]`**: Observable selection from options

### Binding Modes

- **`SyncMode.UPDATE_VALUE_FROM_OBSERVABLE`**: Target gets initial value from source
- **`SyncMode.UPDATE_OBSERVABLE_FROM_SELF`**: Source gets initial value from target

### Common Methods

All observable classes support:

- `add_listeners(*callbacks)`: Add change notification callbacks
- `remove_listeners(*callbacks)`: Remove specific callbacks
- `remove_all_listeners()`: Remove all callbacks
- `bind_to_observable(other, sync_mode)`: Create bidirectional binding
- `unbind_from_observable(other)`: Remove binding

## Use Cases

- **GUI Applications**: Automatic UI updates when data changes
- **Data Synchronization**: Keep multiple data sources in sync
- **Configuration Management**: Reactive configuration with validation
- **State Management**: Centralized state with automatic propagation
- **Event-Driven Architecture**: Decoupled components with change notifications

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
git clone https://github.com/yourusername/observables.git
cd observables
pip install -e .[dev]
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
black observables tests
isort observables tests
flake8 observables tests
mypy observables
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## Acknowledgments

- Inspired by reactive programming patterns
- Built with modern Python features and type hints
- Designed for performance and ease of use
