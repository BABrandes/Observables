"""
Observables - Transitive Synchronization and Shared-State Fusion for Python

⚠️ DEVELOPMENT STATUS: NOT PRODUCTION READY
This library is under active development. API may change without notice.
Use for experimental and development purposes only.

A reactive synchronization framework for Python.
This provides a universal mechanism for maintaining coherent shared state across 
independent objects, enabling transitive, non-directional synchronization through 
Nexus fusion.

Each Hook references a Nexus — a shared synchronization core that holds and propagates 
state. Hooks do not own their Nexus; instead, multiple hooks may share it, forming a 
dynamic network of coherence.

When two hooks are joined, their respective Nexuses undergo a fusion process:
    • The original Nexuses are destroyed.
    • A new, unified Nexus is created to hold the shared value and synchronization logic.
    • Both hooks now belong to the same fusion domain.

Joining is symmetric, transitive, and non-directional:
    1. A.join(B) → creates Nexus_AB
    2. C.join(D) → creates Nexus_CD
    3. B.join(C) → fuses both domains → Nexus_ABCD

All hooks A, B, C, and D now share the same Nexus — even though A and D were never 
joined directly.

A hook can later be isolated, which:
    • Removes it from its current fusion domain,
    • Creates a new, independent Nexus initialized with the hook's current value,
    • Leaves the remaining hooks still joined and synchronized.

After B.isolate(),
    • A, C, and D remain synchronized through Nexus_ACD,
    • B operates independently via its new Nexus.

This forms a dynamic equivalence network: any hooks that are directly or indirectly 
joined share one coherent Nexus, while isolated hooks maintain independent state.

This framework underpins total synchronization in higher-level components such as 
XValue, XDict, XList, XSet, and XFunction, which expose multiple hooks for 
fine-grained reactivity — ready for integration into GUI or distributed systems.

**Modern API (Recommended):**
For new code, use the clean X-prefixed aliases:
- XValue, XList, XSet - Basic observables
- XSelectionDict, XSelectionOption - Selection management
- XTransfer, XSync - Advanced transformations

**Legacy API (Deprecated):**
The verbose Observable* names are kept for backwards compatibility but are deprecated.
Use the X-prefixed aliases instead.

Core Features:
- Centralized value storage with shared references (no data duplication)
- Bidirectional bindings through hook group merging
- Automatic change propagation through centralized value updates
- Listener notification system for change events
- Type-safe generic implementations with full type hints
- Custom validation support with verification methods
- Memory-efficient single source of truth architecture
- Thread-safe binding management with RLock protection

Architecture:
The library uses a hook-based architecture where:
- Nexus: Shared synchronization core that holds and propagates state
- Hooks: References to Nexuses (multiple hooks can share one Nexus)
- Observables: User-facing interfaces that expose hooks for joining
- Joining: Nexus fusion creating transitive synchronization domains

Nexus Fusion Process:
When observables are joined (via .join()), their Nexuses undergo fusion:
    1. Original Nexuses are destroyed
    2. A new, unified Nexus is created
    3. Both hooks now share the same fusion domain
This creates transitive synchronization: joining A→B and B→C automatically 
synchronizes A and C, even though they were never directly joined.

Protocols and Interfaces:
The library provides several protocols that can be used for type hints and interface definitions:
- CarriesDistinctHook: Base protocol for all observable types
- CarriesDistinctSingleValueHook: Protocol for single value observables
- CarriesDistinctListHook: Protocol for list observables
- CarriesDistinctSetHook: Protocol for set observables
- CarriesDistinctDictHook: Protocol for dictionary like observables
- CarriesDistinctTupleHook: Protocol for tuple observables

Available Observable Types:
- ObservableSingleValue: Wrapper around any single value with validation
- ObservableList: Reactive list with full list interface compatibility
- ObservableSet: Reactive set with full set interface compatibility
- ObservableDict: Reactive dictionary with full dict interface compatibility
- ObservableTuple: Reactive tuple with individual element binding support
- ObservableSelectionOption: Combined options set and selected value management
- ObservableMultiSelectionOption: Combined available options set and multiple selected values management
- ObservableEnum: Reactive enum with options management and validation

Example Usage (Modern API):
    >>> from observables import XValue, XList, XSet
    
    >>> # Create reactive values (each has its own central Nexus)
    >>> name = XValue("John")
    >>> age = XValue(25)
    
    >>> # Add listeners for change notifications
    >>> name.add_listener(lambda: print("Name changed!"))
    >>> age.add_listener(lambda: print("Age changed!"))
    
    >>> # Create bidirectional binding (merges hook groups, no value copying)
    >>> name_copy = XValue(name)
    >>> name_copy.value = "Jane"  # Updates central value, both observables see it
    Name changed!
    
    >>> # Reactive lists (immutable tuples internally)
    >>> todo_list = XList(["Buy groceries", "Walk dog"])
    >>> todo_copy = XList(todo_list)
    >>> todo_copy.append("Read book")  # Creates new tuple, both observables see it
    
    >>> print(name.value, age.value, todo_list.value)
    Jane 25 ('Buy groceries', 'Walk dog', 'Read book')

    >>> # Using protocols for type hints
    >>> from observables import XValueProtocol, XListProtocol
    
    >>> def process_value(obs: XValueProtocol[str]) -> str:
    ...     return obs.value.upper()
    
    >>> def process_list(obs: XListProtocol[str]) -> tuple[str, ...]:
    ...     return tuple(item.upper() for item in obs.value)
    
    >>> # One-way transformations with XOneWayFunction
    >>> from observables import XOneWayFunction
    >>> 
    >>> celsius = XValue(0.0)
    >>> converter = XOneWayFunction(
    ...     function_input_hooks={'celsius': celsius.hook},
    ...     function_output_hook_keys={'fahrenheit', 'kelvin'},
    ...     function_callable=lambda inputs: {
    ...         'fahrenheit': inputs['celsius'] * 9/5 + 32,
    ...         'kelvin': inputs['celsius'] + 273.15
    ...     }
    ... )
    >>> celsius.value = 100.0
    >>> print(converter.get_output_hook('fahrenheit').value)  # 212.0

For more information, see the individual class documentation or run the demo:
    python observables/examples/demo.py

Advanced Usage:
    For building custom observables or extending the library, import from the core module:
    >>> from observables.core import BaseObservable, Hook, HookNexus
    >>> # Create custom observable types with low-level components
"""

from ._xobjects.x_any_value import ObservableSingleValue

from ._xobjects.list_like.x_list import ObservableList, ObservableListProtocol

from ._xobjects.set_like.x_set import ObservableSet, ObservableSetProtocol
from ._xobjects.set_like.x_selection_set import ObservableSelectionSet
from ._xobjects.set_like.x_optional_selection_set import ObservableOptionalSelectionSet
from ._xobjects.set_like.x_multi_selection_set import ObservableMultiSelectionSet
from ._xobjects.set_like.protocols import ObservableOptionalSelectionOptionProtocol, ObservableSelectionOptionsProtocol, ObservableMultiSelectionOptionsProtocol

from ._xobjects.function_like.function_values import FunctionValues
from ._xobjects.function_like.x_function import ObservableFunction as ObservableSync
from ._xobjects.function_like.x_one_way_function import ObservableOneWayFunction

from ._xobjects.dict_like.x_selection_dict import ObservableSelectionDict
from ._xobjects.dict_like.x_optional_selection_dict import ObservableOptionalSelectionDict
from ._xobjects.dict_like.x_selection_dict_with_default import ObservableDefaultSelectionDict
from ._xobjects.dict_like.x_optional_selection_dict_with_default import ObservableOptionalDefaultSelectionDict
from ._xobjects.dict_like.x_dict import ObservableDict
from ._xobjects.dict_like.protocols import ObservableDictProtocol, ObservableSelectionDictProtocol, ObservableOptionalSelectionDictProtocol, ObservableDefaultSelectionDictProtocol, ObservableOptionalDefaultSelectionDictProtocol

from ._xobjects.complex.xobject_rooted_paths import ObservableRootedPaths
from ._xobjects.complex.xobject_block_none import ObservableBlockNone
from ._xobjects.complex.xobject_subscriber import ObservableSubscriber

from ._hooks.floating_hook import FloatingHook
from ._hooks.hook_aliases import Hook, ReadOnlyHook

from ._publisher_subscriber.publisher_protocol import PublisherProtocol
from ._publisher_subscriber.value_publisher import ValuePublisher
from ._publisher_subscriber.publisher import Publisher

from ._nexus_system.update_function_values import UpdateFunctionValues
from ._nexus_system.system_analysis import write_report

from ._carries_hooks.x_object_serializable_mixin import XObjectSerializableMixin


# Modern, clean aliases (recommended for new code)

XValue = ObservableSingleValue
XList = ObservableList
XSet = ObservableSet
XDict = ObservableDict

XSelectionDict = ObservableSelectionDict
XOptionalSelectionDict = ObservableOptionalSelectionDict
XDefaultSelectionDict = ObservableDefaultSelectionDict
XOptionalDefaultSelectionDict = ObservableOptionalDefaultSelectionDict

XSelectionSet = ObservableSelectionSet
XOptionalSelectionSet = ObservableOptionalSelectionSet
XMultiSelectionSet = ObservableMultiSelectionSet

XFunction = ObservableSync
XOneWayFunction = ObservableOneWayFunction

XRootedPaths = ObservableRootedPaths
XBlockNone = ObservableBlockNone
XSubscriber = ObservableSubscriber

# Protocol aliases
XListProtocol = ObservableListProtocol
XSetProtocol = ObservableSetProtocol
XDictProtocol = ObservableDictProtocol

XSelectionOptionsProtocol = ObservableSelectionOptionsProtocol
XOptionalSelectionOptionProtocol = ObservableOptionalSelectionOptionProtocol
XMultiSelectionOptionsProtocol = ObservableMultiSelectionOptionsProtocol

XSelectionDictProtocol = ObservableSelectionDictProtocol
XOptionalSelectionDictProtocol = ObservableOptionalSelectionDictProtocol
XDefaultSelectionDictProtocol = ObservableDefaultSelectionDictProtocol
XOptionalDefaultSelectionDictProtocol = ObservableOptionalDefaultSelectionDictProtocol

__all__ = [
    # Modern clean aliases (RECOMMENDED - use these for new code!)
    'XValue',
    'XList',
    'XSet',
    'XDict',
    'XSelectionDict',
    'XOptionalSelectionDict',
    'XDefaultSelectionDict',
    'XOptionalDefaultSelectionDict',
    'XSelectionSet',
    'XOptionalSelectionSet',
    'XMultiSelectionSet',
    'XFunction',
    'XOneWayFunction',
    'XRootedPaths',
    'XBlockNone',
    'XSubscriber',
    
    # Modern protocol aliases
    'XDictProtocol',
    'XListProtocol',
    'XSetProtocol',
    'XSelectionOptionsProtocol',
    'XOptionalSelectionOptionProtocol',
    'XMultiSelectionOptionsProtocol',
    
    # Legacy names (DEPRECATED - kept for backwards compatibility)
    'ObservableList',
    'ObservableSet',
    'ObservableDict',
    'ObservableSingleValue',
    'ObservableSelectionSet',
    'ObservableOptionalSelectionSet',
    'ObservableMultiSelectionSet',
    'ObservableSync',
    'ObservableOneWayFunction',
    'ObservableSelectionDict',
    'ObservableOptionalSelectionDict',
    'ObservableDefaultSelectionDict',
    'ObservableOptionalDefaultSelectionDict',
    'ObservableRootedPaths',
    'ObservableBlockNone',
    'ObservableSubscriber',
    
    # Legacy protocols (DEPRECATED)
    'ObservableListProtocol',
    'ObservableDictProtocol',
    'ObservableSetProtocol',
    'ObservableSelectionOptionsProtocol',
    'ObservableOptionalSelectionOptionProtocol',
    'ObservableMultiSelectionOptionsProtocol',
    'ObservableSelectionDictProtocol',
    'ObservableOptionalSelectionDictProtocol',
    'ObservableDefaultSelectionDictProtocol',
    'ObservableOptionalDefaultSelectionDictProtocol',

    # Hooks (user-facing)
    'FloatingHook',
    'Hook',
    'ReadOnlyHook',
    
    # Function utilities
    'FunctionValues',
    'UpdateFunctionValues',

    # Publisher/Subscriber
    'PublisherProtocol',
    'ValuePublisher',
    'Publisher',

    # Utilities
    'XObjectSerializableMixin',
    'write_report',
]

# Package metadata
try:
    from ._version import __version__, __version_tuple__
except ImportError:
    __version__ = "5.0.10"
    __version_tuple__ = (5, 0, 10)

__author__ = 'Benedikt Axel Brandes'
__year__ = '2025'

# Package description
__description__ = 'Centralized Reactive Programming - A Python library for reactive programming and centralized value management'
__keywords__ = ['observable', 'reactive', 'binding', 'data-binding', 'reactive-programming']
__url__ = 'https://github.com/benediktbrandes/observables'
__project_urls__ = {
    'Bug Reports': 'https://github.com/benediktbrandes/observables/issues',
    'Source': 'https://github.com/benediktbrandes/observables',
    'Documentation': 'https://github.com/benediktbrandes/observables#readme',
}

# Development status
__classifiers__ = [
    'Development Status :: 3 - Alpha',  # Not production ready
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]
