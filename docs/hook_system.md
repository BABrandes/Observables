# Hook System Technical Documentation

This document provides detailed technical information about the Observables library's hook system architecture, binding mechanics, and internal implementation details.

## 🏗️ Architecture Overview

The Observables library is built around a sophisticated protocol-based hook architecture that provides automatic synchronization, change propagation, and binding management. The system is designed to be efficient, thread-safe, maintainable, and highly extensible.

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
│                    Protocol-Based Hook Layer                   │
├─────────────────────────────────────────────────────────────────┤
│  HookLike[T] (Base Protocol)                                   │
│  ├── HookWithOwnerLike[T]                                      │
│  ├── HookWithIsolatedValidationLike[T]                         │
│  └── HookWithReactionLike[T]                                   │
│                                                                 │
│  Hook Implementations:                                          │
│  ├── Hook[T] (Standalone)                                      │
│  ├── OwnedHook[T] (Hook + HookWithOwnerLike)                   │
│  └── FloatingHook[T] (Hook + Validation + Reaction)            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     HookNexus & Binding System                 │
├─────────────────────────────────────────────────────────────────┤
│  HookNexus[T]  ←→  NexusManager  ←→  Validation & Sync         │
└─────────────────────────────────────────────────────────────────┘
```

## 🔗 Hook System Deep Dive

### Protocol-Based Architecture

The new hook system uses Python's `Protocol` classes to define clear interfaces for different hook capabilities. This design provides excellent type safety, extensibility, and maintainability.

#### Core Protocols

##### `HookLike[T]` - Base Protocol

The foundation protocol that all hooks must implement:

```python
@runtime_checkable
class HookLike(BaseListeningLike, Protocol[T]):
    """Protocol for hook objects."""
    
    @property
    def nexus_manager(self) -> "NexusManager": ...
    @property
    def value(self) -> T: ...
    @property
    def value_reference(self) -> T: ...
    @property
    def previous_value(self) -> T: ...
    @property
    def hook_nexus(self) -> "HookNexus[T]": ...
    @property
    def lock(self) -> RLock: ...
    
    def connect_hook(self, target_hook: "HookLike[T]", 
                    initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> tuple[bool, str]: ...
    def disconnect(self) -> None: ...
    def is_connected_to(self, hook: "HookLike[T]") -> bool: ...
```

##### `HookWithOwnerLike[T]` - Owner Protocol

For hooks that belong to observables:

```python
@runtime_checkable
class HookWithOwnerLike(HookLike[T], Protocol[T]):
    """Protocol for hook objects that have an owner."""
    
    @property
    def owner(self) -> "CarriesHooksLike[Any, Any]": ...
```

##### `HookWithIsolatedValidationLike[T]` - Validation Protocol

For hooks with custom validation logic:

```python
@runtime_checkable
class HookWithIsolatedValidationLike(HookLike[T], Protocol[T]):
    """Protocol for hook objects that can validate values in isolation."""
    
    def validate_value_in_isolation(self, value: T) -> tuple[bool, str]: ...
```

##### `HookWithReactionLike[T]` - Reaction Protocol

For hooks that react to value changes:

```python
@runtime_checkable
class HookWithReactionLike(HookLike[T], Protocol[T]):
    """Protocol for hook objects that can react to value changes."""
    
    def react_to_value_changed(self) -> None: ...
```

### Hook Implementations

#### `Hook[T]` - Standalone Hook

The basic hook implementation for standalone use:

```python
class Hook(HookLike[T], BaseListening, Generic[T]):
    """A standalone hook."""
    
    def __init__(self, value: T, nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER, 
                 logger: Optional[logging.Logger] = None):
        BaseListening.__init__(self, logger)
        self._value = value
        self._nexus_manager = nexus_manager
        self._hook_nexus = HookNexus(value, hooks={self}, nexus_manager=nexus_manager, logger=logger)
        self._lock = RLock()
```

#### `OwnedHook[T]` - Observable Hook

For hooks that belong to observables:

```python
class OwnedHook(Hook[T], HookWithOwnerLike[T], BaseListening, Generic[T]):
    """A hook that belongs to an observable."""
    
    def __init__(self, owner: CarriesHooksLike[Any, Any], initial_value: T, 
                 logger: Optional[Logger] = None, nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER):
        BaseListening.__init__(self, logger)
        Hook.__init__(self, initial_value, nexus_manager=nexus_manager, logger=logger)
        self._owner = owner
```

#### `FloatingHook[T]` - Advanced Hook

For hooks with validation and reaction capabilities:

```python
class FloatingHook(Hook[T], HookWithIsolatedValidationLike[T], HookWithReactionLike[T], BaseListening, Generic[T]):
    """A floating hook with validation and reaction capabilities."""
    
    def __init__(self, value: T, reaction_callback: Optional[Callable[[], tuple[bool, str]]] = None,
                 isolated_validation_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
                 logger: Optional[Logger] = None, nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER):
        self._reaction_callback = reaction_callback
        self._isolated_validation_callback = isolated_validation_callback
        BaseListening.__init__(self, logger)
        Hook.__init__(self, value=value, nexus_manager=nexus_manager, logger=logger)
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

## 🎯 Benefits of the New Protocol-Based Architecture

### Type Safety and Extensibility

The new protocol-based design provides several key advantages:

#### 1. **Clear Interface Contracts**
```python
# Protocols define clear contracts
def process_hook(hook: HookLike[str]) -> None:
    # Can work with any hook implementation
    value = hook.value
    hook.submit_value("new_value")

# Type checker ensures compatibility
hook: HookWithOwnerLike[int] = OwnedHook(owner, 42)
process_hook(hook)  # ✅ Type safe
```

#### 2. **Composition Over Inheritance**
```python
# Easy to create new hook types by combining protocols
class CachedHook(Hook[T], HookWithCachingLike[T]):
    """Hook with caching capabilities."""
    pass

class PersistentHook(Hook[T], HookWithPersistenceLike[T]):
    """Hook with persistence capabilities."""
    pass

# Multiple capabilities
class AdvancedHook(Hook[T], HookWithCachingLike[T], HookWithPersistenceLike[T]):
    """Hook with both caching and persistence."""
    pass
```

#### 3. **Runtime Type Checking**
```python
# Protocols are runtime checkable
if isinstance(hook, HookWithOwnerLike):
    owner = hook.owner
    print(f"Hook belongs to: {owner}")

if isinstance(hook, HookWithIsolatedValidationLike):
    success, msg = hook.validate_value_in_isolation(new_value)
    if not success:
        raise ValueError(msg)
```

#### 4. **Easy Testing and Mocking**
```python
# Easy to create test doubles
class MockHook:
    def __init__(self, value):
        self._value = value
    
    @property
    def value(self):
        return self._value
    
    def submit_value(self, value):
        self._value = value

# MockHook automatically implements HookLike protocol
mock_hook: HookLike[str] = MockHook("test")
```

### Performance Benefits

1. **Protocol Overhead**: Minimal runtime overhead compared to traditional inheritance
2. **Memory Efficiency**: No additional memory per protocol interface
3. **Fast Dispatch**: Direct method calls without virtual function overhead
4. **Optimized Type Checking**: `@runtime_checkable` provides efficient isinstance checks

### Maintainability Benefits

1. **Single Responsibility**: Each protocol has one clear purpose
2. **Easy Debugging**: Clear separation of concerns makes issues easier to trace
3. **Documentation**: Protocols serve as living documentation
4. **Backward Compatibility**: Existing code continues to work unchanged

## 🔮 Future Enhancements

### Planned Features

1. **Selective Disconnection**: Support for granular binding control
2. **Binding Priorities**: Configurable synchronization priorities
3. **Conditional Binding**: Binding based on runtime conditions
4. **Performance Profiling**: Built-in performance monitoring tools

### Extension Points

The new protocol-based hook system is highly extensible:

#### **New Protocol Capabilities**
```python
# Easy to add new capabilities
class HookWithCachingLike(HookLike[T], Protocol[T]):
    def cache_value(self) -> None: ...
    def get_cached_value(self) -> Optional[T]: ...

class HookWithPersistenceLike(HookLike[T], Protocol[T]):
    def save_to_storage(self) -> None: ...
    def load_from_storage(self) -> None: ...

class HookWithMetricsLike(HookLike[T], Protocol[T]):
    def get_metrics(self) -> Dict[str, Any]: ...
    def reset_metrics(self) -> None: ...
```

#### **Custom Hook Implementations**
```python
# Combine protocols for specialized hooks
class DatabaseHook(Hook[T], HookWithPersistenceLike[T], HookWithMetricsLike[T]):
    """Hook that persists to database and tracks metrics."""
    pass

class CacheHook(Hook[T], HookWithCachingLike[T], HookWithMetricsLike[T]):
    """Hook with caching and performance metrics."""
    pass
```

#### **Advanced Validation Strategies**
- **Custom Hook Types**: Implement new hook behaviors
- **Advanced Validation**: Custom validation logic with protocol composition
- **Binding Strategies**: Alternative binding algorithms
- **Group Management**: Custom group organization strategies

