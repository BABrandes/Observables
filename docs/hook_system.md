# Hook System Technical Documentation

This document provides detailed technical information about the Observables library's hook system architecture, binding mechanics, and internal implementation details.

## 🏗️ Architecture Overview

The Observables library is built around a sophisticated hook-based architecture that provides automatic synchronization, change propagation, and binding management. The system is designed to be efficient, thread-safe, and maintainable.

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Observable Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  ObservableSingleValue  ObservableList  ObservableDict        │
│  ObservableSet         ObservableTuple  ObservableEnum         │
│  ObservableSelectionOption  ObservableMultiSelectionOption     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Hook Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  Hook[T]  ←→  HookNexus[T]  ←→  HookLike[T]                  │
│     │              │                    │                      │
│     └──────────────┼────────────────────┘                      │
│                    ▼                                            │
│            CarriesDistinct*Hook Protocols                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Binding System                             │
├─────────────────────────────────────────────────────────────────┤
│  Initial Sync  ←→  HookNexus Merging  ←→  Validation          │
└─────────────────────────────────────────────────────────────────┘
```

## 🔗 Hook System Deep Dive

### Hook Class

The `Hook[T]` class is the fundamental unit of the binding system. Each hook represents a single data component that can be synchronized with other hooks.

#### Key Properties

- **`owner`**: The observable object that owns this hook
- **`get_callback`**: Function to retrieve the current value
- **`set_callback`**: Function to set a new value
- **`hook_group`**: The group this hook belongs to
- **`can_send`**: Whether this hook can provide values
- **`can_receive`**: Whether this hook can accept values

#### Hook States

```python
class Hook[T]:
    def __init__(self, owner, get_callback, set_callback):
        self._owner = owner
        self._get_callback = get_callback
        self._set_callback = set_callback
        self._hook_nexus = HookNexus(initial_value)  # Starts with its own nexus
        self._lock = threading.Lock()
```

### HookNexus - Central Value Storage

`HookNexus[T]` is the central storage point for a value, with multiple hooks referencing it. When hooks are bound together, they merge to reference the same HookNexus.

#### Nexus Management

```python
class HookNexus[T]:
    def __init__(self, initial_value: T):
        self._value = initial_value       # The central value
        self._hooks = WeakSet()           # All hooks referencing this nexus
        self._lock = threading.Lock()     # Thread safety
    
    def replace_nexus(old_nexus: "HookNexus[T]", new_nexus: "HookNexus[T]"):
        """Transfer all hooks from old_nexus to new_nexus."""
        # Move all hooks to reference the new nexus
```

#### Nexus Operations

1. **Merge**: Transfer hooks from one nexus to another when binding
2. **Replace**: Update a hook to reference a different nexus
3. **Synchronize**: All hooks referencing a nexus see the same value
4. **Validate**: Check that value changes are valid for all hooks

### Binding Mechanics

#### Connection Process

When two hooks are connected via `connect_hooks()`:

1. **Validation**: Ensure hooks are compatible and not None
2. **Value Synchronization**: If values differ, invalidate the target group
3. **Nexus Merging**: Transfer hooks to reference a single shared nexus
4. **Consistency Check**: Verify all hooks referencing the nexus are synchronized

```python
@staticmethod
def connect_hooks(from_hook: "HookLike[T]", to_hook: "HookLike[T]"):
    """Connect two hooks together."""
    # Validate that hooks are not None
    if from_hook is None or to_hook is None:
        raise ValueError("Cannot connect None hooks")
    
    # Ensure that the value in both hook nexuss is the same
    if from_hook.value != to_hook.value:
        success, msg = to_hook.hook_group.invalidate(from_hook.value)
        if not success:
            raise ValueError(msg)
    
    # Then merge the hook nexuss
    merged_hook_group = HookNexus[T].merge_hook_groups(
        from_hook.hook_group, to_hook.hook_group
    )
    
    # Check if all hooks are synced
    success, msg = HookNexus[T].check_all_hooks_synced(merged_hook_group)
    if not success:
        raise ValueError(msg)
```

#### Transitive Binding

The system automatically handles transitive binding:

```python
# If A ↔ B and B ↔ C, then A ↔ C automatically
# This happens because all three hooks end up in the same group

# Step 1: A ↔ B
# Group A: [Hook_A, Hook_B]

# Step 2: B ↔ C  
# Group A: [Hook_A, Hook_B, Hook_C]  # Groups automatically merge
```

### Disconnection Process

When a hook detachs:

1. **Validation**: Check if the hook is already detached
2. **Group Removal**: Remove the hook from its current group
3. **Isolation**: Create a new isolated group containing only the detached hook
4. **Group Cleanup**: Remaining hooks in the original group stay bound together

```python
def detach(self) -> None:
    """Disconnect this hook from the binding system."""
    # Check if already detached
    if len(self._hook_group._hooks) <= 1:
        raise ValueError("Hook is already detached")
    
    # Remove from current group
    self._hook_group.remove_hook(self)
    
    # Create new isolated group
    new_group = HookNexus([self])
    self._hook_group = new_group
    
    # The remaining hooks in the old group will continue to be bound together
```

## 🔄 Synchronization Modes

The system supports different initial synchronization behaviors:

### use_target_value Mode

The calling observable takes the target's value upon binding:

```python
obs1.connect_hook(obs2.hook, "value", "use_target_value")
# Result: obs1.value = obs2.value
```

### use_caller_value Mode

The target observable takes the calling observable's value upon binding:

```python
obs1.connect_hook(obs2.hook, "value", "use_caller_value")  
# Result: obs2.value = obs1.value
```

## 🧪 Validation and Error Handling

### Value Validation

Before merging hook nexuss, the system validates that all hooks can maintain consistent values:

```python
def invalidate(self, source_hook_or_value: "HookLike[T]" | T) -> tuple[bool, str]:
    """Invalidate the current value and set a new one."""
    # Implementation details for validation...
```

### Consistency Checks

After merging groups, the system ensures all hooks are properly synchronized:

```python
@staticmethod
def check_all_hooks_synced(hook_group: "HookNexus[T]") -> tuple[bool, str]:
    """Check if all hooks in a group are synchronized."""
    # Implementation details for consistency checking...
```

## 🚫 Important Limitations

### No Granular Control

The system does not support selective detachion of specific pairs within a merged group:

```python
# This is NOT supported:
# obs1 ↔ obs2 ↔ obs3
# obs1.detach_from(obs2)  # Only detach obs1 from obs2

# Instead, you must detach the entire hook:
# obs1.detach()  # obs1 becomes isolated, obs2 ↔ obs3 remains
```

### Available Options Don't Merge

For selection-based observables, only selected values are synchronized:

```python
# These synchronize:
obs1.selected_option = "Red"
obs2.selected_option = "Red"  # Automatically synchronized

# These do NOT merge:
obs1.available_options = {"Red", "Green", "Blue"}
obs2.available_options = {"Red", "Green"}  # Remains separate
```

## 🔒 Thread Safety

The hook system is designed to be thread-safe:

- **Lock-based synchronization** on critical operations
- **Atomic group operations** to prevent race conditions
- **Safe concurrent binding** and detachion
- **Protected value access** during synchronization

```python
def connect_hooks(from_hook: "HookLike[T]", to_hook: "HookLike[T]"):
    """Thread-safe connection of hooks."""
    with from_hook._lock:
        with to_hook._lock:
            # Perform connection operations atomically
            # ...
```

## 📊 Performance Characteristics

### Time Complexity

- **Binding**: O(1) for simple connections, O(n) for group merging
- **Value Propagation**: O(n) where n is the number of hooks in a group
- **Disconnection**: O(1) for hook removal, O(n) for group splitting

### Memory Usage

- **Hook Objects**: Minimal overhead per hook
- **Group Management**: Shared state reduces memory duplication
- **Listener Management**: Efficient callback storage and execution

### Optimization Strategies

1. **Group Merging**: Minimize unnecessary group operations
2. **Value Caching**: Cache computed values when possible
3. **Lazy Evaluation**: Defer expensive operations until needed
4. **Batch Operations**: Group multiple changes together

## 🐛 Debugging and Troubleshooting

### Common Issues

1. **Circular Bindings**: The system prevents circular binding attempts
2. **Value Inconsistency**: Validation errors when hooks cannot maintain consistent values
3. **Group Corruption**: Automatic cleanup prevents group state corruption

### Debug Tools

```python
# Check hook nexus membership
print(hook.hook_group._hooks)

# Verify binding status
print(hook.is_connected_to(other_hook))

# Check group consistency
success, message = hook_group.check_all_hooks_synced()
```

### Logging and Monitoring

The system provides detailed logging for debugging:

```python
import logging
logging.getLogger('observables.hook').setLevel(logging.DEBUG)
```

## 🔮 Future Enhancements

### Planned Features

1. **Selective Disconnection**: Support for granular binding control
2. **Binding Priorities**: Configurable synchronization priorities
3. **Conditional Binding**: Binding based on runtime conditions
4. **Performance Profiling**: Built-in performance monitoring tools

### Extension Points

The hook system is designed to be extensible:

- **Custom Hook Types**: Implement new hook behaviors
- **Advanced Validation**: Custom validation logic
- **Binding Strategies**: Alternative binding algorithms
- **Group Management**: Custom group organization strategies

