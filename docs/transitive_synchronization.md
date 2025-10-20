# Transitive Synchronization and Shared-State Fusion

## Overview

The Observables library is a **reactive synchronization framework for Python** that provides 
a universal mechanism for maintaining coherent shared state across independent objects, 
enabling transitive, non-directional synchronization through Nexus fusion.

This document explains the core architectural principles that make this library unique.

## Core Concepts

### Hooks and Nexuses

Each **Hook** references a **Nexus** — a shared synchronization core that holds and propagates 
state. Hooks do not own their Nexus; instead, multiple hooks may share it, forming a dynamic 
network of coherence.

```
Hook_A ──┐
         ├──► Nexus_1 (value: 42)
Hook_B ──┘

Hook_C ──► Nexus_2 (value: 100)
```

In this example:
- `Hook_A` and `Hook_B` share `Nexus_1` and are synchronized
- `Hook_C` has its own independent `Nexus_2`

### Nexus Fusion Process

When two hooks are joined, their respective Nexuses undergo a **fusion process**:

1. **The original Nexuses are destroyed**
2. **A new, unified Nexus is created** to hold the shared value and synchronization logic
3. **Both hooks now belong to the same fusion domain**

```python
# Before joining
Hook_A ──► Nexus_1 (value: 42)
Hook_B ──► Nexus_2 (value: 100)

# After Hook_A.join(Hook_B)
Hook_A ──┐
         ├──► Nexus_AB (value: 100)  # New unified Nexus
Hook_B ──┘

# Nexus_1 and Nexus_2 are destroyed
```

During fusion, one value is chosen (based on `initial_sync_mode`), and both hooks now 
reference the same Nexus.

## Transitive Synchronization

Joining is **symmetric**, **transitive**, and **non-directional**. This is the key innovation 
of the library.

### Example: Building a Fusion Network

```python
from observables import XValue

# Create four independent observables
A = XValue(1)
B = XValue(2)
C = XValue(3)
D = XValue(4)

# Step 1: Join A and B
A.join(B)  # Creates Nexus_AB
# Now: A and B both have value 2 (or 1, depending on sync mode)

# Step 2: Join C and D
C.join(D)  # Creates Nexus_CD
# Now: C and D both have value 4 (or 3, depending on sync mode)

# Step 3: Join B and C (the magic happens here)
B.join(C)  # Fuses Nexus_AB and Nexus_CD → creates Nexus_ABCD

# Result: All four observables (A, B, C, D) now share the same Nexus
# Even though A and D were never directly joined!
```

**Visual representation:**

```
Initial state:
A(1)  B(2)  C(3)  D(4)

After A.join(B):
A ─── B     C(3)  D(4)
 (2)  (2)

After C.join(D):
A ─── B     C ─── D
 (2)  (2)    (4)  (4)

After B.join(C):
A ─── B ─── C ─── D
 (4)  (4)   (4)  (4)

All share Nexus_ABCD!
```

### The Transitive Property

The key insight is: **If you join any hook from one group to any hook from another group, 
all hooks in both groups become synchronized.**

This is because joining triggers Nexus fusion, which merges entire fusion domains, not just 
individual hooks.

## Isolation

A hook can later be **isolated**, which:

1. **Removes it from its current fusion domain**
2. **Creates a new, independent Nexus** initialized with the hook's current value
3. **Leaves the remaining hooks still joined and synchronized**

```python
# Continuing from the previous example
# A, B, C, D all share Nexus_ABCD with value 4

B.isolate()

# After isolation:
# A, C, D share Nexus_ACD with value 4
# B has its own Nexus_B with value 4 (but changes won't propagate)

A.value = 10
print(A.value, B.value, C.value, D.value)
# Output: 10 10 10 4
#         A   B   C   D
# B is isolated and didn't receive the update
```

**Visual representation:**

```
Before B.isolate():
A ─── B ─── C ─── D
 (4)  (4)   (4)  (4)
    Nexus_ABCD

After B.isolate():
      B(4)          ← Isolated with Nexus_B
      
A ─── C ─── D     ← Still synchronized via Nexus_ACD
 (4)  (4)  (4)
```

## Dynamic Equivalence Networks

This forms a **dynamic equivalence network**: any hooks that are directly or indirectly joined 
share one coherent Nexus, while isolated hooks maintain independent state.

Think of it as equivalence classes in mathematics:
- Hooks in the same fusion domain are equivalent (they share state)
- Joining creates the union of equivalence classes
- Isolation splits off an element into its own class

## Practical Applications

### GUI Synchronization

```python
from observables import XValue

# Model values
username_model = XValue("")
email_model = XValue("")

# Multiple UI components all join to the same model
text_field_1.text_observable.join(username_model)
text_field_2.text_observable.join(username_model)
label.text_observable.join(username_model)

# Now all three UI components stay synchronized with the model
# AND with each other, even though they weren't directly joined
```

### Complex Multi-Component Observables

Higher-level observables like `XDict`, `XList`, `XSet`, and `XFunction` expose **multiple hooks** 
for fine-grained reactivity:

```python
from observables import XDict

dict_a = XDict({"x": 1, "y": 2})
dict_b = XDict({"x": 10, "y": 20})

# Join the entire dictionaries
dict_a.join(dict_b)

# Now dict_a and dict_b share the same Nexus
# Changes to dict_a propagate to dict_b and vice versa
dict_a["x"] = 100
print(dict_b["x"])  # Output: 100
```

But you can also join individual hooks:

```python
dict_c = XDict({"x": 5})

# Join just the "keys" hooks
dict_a.keys_hook.join(dict_c.keys_hook)

# Now the key sets are synchronized (but not the values)
```

### Distributed Systems

Because synchronization is transitive and non-directional, you can build complex distributed 
state networks where components synchronize through intermediate nodes, without every component 
needing direct connections to every other component.

## Implementation Details

### Thread Safety

All Nexus operations (fusion, value updates, isolation) are protected by the `NexusManager`'s 
`RLock`, ensuring thread-safe operation.

### Value Validation

During Nexus fusion, the `NexusManager`:
1. Attempts to submit the chosen value to the new unified Nexus
2. Validates the value using all validation callbacks from both original Nexuses
3. If validation fails, the fusion is aborted and both hooks remain independent

This ensures that invalid states never propagate through the fusion network.

### Memory Management

Nexuses use weak references to hooks, preventing circular reference memory leaks. When all 
hooks referencing a Nexus are garbage collected, the Nexus itself is automatically cleaned up.

## Summary

The Observables library implements **transitive synchronization through Nexus fusion**:

- **Hooks** reference **Nexuses** (shared synchronization cores)
- **Joining** hooks triggers **Nexus fusion** (old destroyed, new unified Nexus created)
- This creates **transitive synchronization**: A→B + B→C automatically synchronizes A and C
- **Isolation** removes a hook from its fusion domain
- This forms **dynamic equivalence networks** of coherent state

This architecture underpins total synchronization in higher-level components such as `XValue`, 
`XDict`, `XList`, `XSet`, and `XFunction`, which expose multiple hooks for fine-grained 
reactivity — ready for integration into GUI or distributed systems.

