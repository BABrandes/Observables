"""
Observables - Centralized Reactive Programming

⚠️ DEVELOPMENT STATUS: NOT PRODUCTION READY
This library is under active development. API may change without notice.
Use for experimental and development purposes only.

A Python library for reactive programming and centralized value management.
This library provides observable data structures that support bidirectional bindings 
through a centralized value storage system. Unlike traditional reactive libraries that 
duplicate data across observables, this system stores values in centralized HookNexus 
objects that observables reference, ensuring efficient synchronization.

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
- Nexus: Central storage for actual data values
- Hooks: References/views to central values
- Observables: User-facing interfaces that access values through hooks
- Binding: Merging hook groups so multiple observables reference the same central value

Central Value Storage:
The system stores each value in exactly one Nexus and creates hooks that reference 
these central values. When observables are bound (via .link()), their hook groups are 
merged, ensuring all bound observables view the same central data. This approach reduces 
memory usage and provides atomic updates across all bound observables.

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

from ._observables.observable_single_value import ObservableSingleValue, ObservableSingleValueProtocol

from ._observables.list_like.observable_list import ObservableList, ObservableListProtocol

from ._observables.set_like.observable_set import ObservableSet, ObservableSetProtocol
from ._observables.set_like.observable_selection_set import ObservableSelectionSet
from ._observables.set_like.observable_optional_selection_set import ObservableOptionalSelectionSet
from ._observables.set_like.observable_multi_selection_set import ObservableMultiSelectionSet
from ._observables.set_like.protocols import ObservableOptionalSelectionOptionProtocol, ObservableSelectionOptionsProtocol, ObservableMultiSelectionOptionsProtocol

from ._observables.function_like.function_values import FunctionValues
from ._observables.function_like.observable_function import ObservableFunction as ObservableSync
from ._observables.function_like.observable_one_way_function import ObservableOneWayFunction

from ._observables.dict_like.observable_selection_dict import ObservableSelectionDict
from ._observables.dict_like.observable_optional_selection_dict import ObservableOptionalSelectionDict
from ._observables.dict_like.observable_default_selection_dict import ObservableDefaultSelectionDict
from ._observables.dict_like.observable_optional_default_selection_dict import ObservableOptionalDefaultSelectionDict
from ._observables.dict_like.observable_dict import ObservableDict
from ._observables.dict_like.protocols import ObservableDictProtocol, ObservableSelectionDictProtocol, ObservableOptionalSelectionDictProtocol, ObservableDefaultSelectionDictProtocol, ObservableOptionalDefaultSelectionDictProtocol

from ._observables.complex.observable_rooted_paths import ObservableRootedPaths
from ._observables.complex.observable_raise_none import ObservableRaiseNone
from ._observables.complex.observable_subscriber import ObservableSubscriber

from ._hooks.floating_hook import FloatingHook
from ._hooks.hook_aliases import Hook, ReadOnlyHook

from ._publisher_subscriber.publisher_protocol import PublisherProtocol
from ._publisher_subscriber.value_publisher import ValuePublisher
from ._publisher_subscriber.publisher import Publisher

from ._nexus_system.update_function_values import UpdateFunctionValues
from ._nexus_system.system_analysis import write_report

from ._carries_hooks.observable_serializable import ObservableSerializable


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
XRaiseNone = ObservableRaiseNone
XSubscriber = ObservableSubscriber

# Protocol aliases

XValueProtocol = ObservableSingleValueProtocol
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
    'XRaiseNone',
    'XSubscriber',
    
    # Modern protocol aliases
    'XValueProtocol',
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
    'ObservableRaiseNone',
    'ObservableSubscriber',
    
    # Legacy protocols (DEPRECATED)
    'ObservableListProtocol',
    'ObservableDictProtocol',
    'ObservableSetProtocol',
    'ObservableSingleValueProtocol',
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
    'ObservableSerializable',
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
