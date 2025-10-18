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
- HookNexus: Central storage for actual data values
- Hooks: References/views to central values
- Observables: User-facing interfaces that access values through hooks
- Binding: Merging hook groups so multiple observables reference the same central value

Central Value Storage:
The system stores each value in exactly one HookNexus and creates hooks that reference 
these central values. When observables are bound, their hook groups are merged, ensuring 
all bound observables view the same central data. This approach reduces memory usage and 
provides atomic updates across all bound observables.

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

Example Usage:
    >>> from observables import ObservableSingleValue, ObservableList
    
    >>> # Create reactive values (each has its own central HookNexus)
    >>> name = ObservableSingleValue("John")
    >>> age = ObservableSingleValue(25)
    
    >>> # Add listeners for change notifications
    >>> name.add_listeners(lambda: print("Name changed!"))
    >>> age.add_listeners(lambda: print("Age changed!"))
    
    >>> # Create bidirectional binding (merges hook groups, no value copying)
    >>> name_copy = ObservableSingleValue(name)
    >>> name_copy.single_value = "Jane"  # Updates central value, both observables see it
    Name changed!
    
    >>> # Reactive lists (same central value principle)
    >>> todo_list = ObservableList(["Buy groceries", "Walk dog"])
    >>> todo_copy = ObservableList(todo_list)
    >>> todo_copy.append("Read book")  # Updates central list, both observables see it
    
    >>> print(name.single_value, age.single_value, todo_list.list_value)
    Jane 25 ['Buy groceries', 'Walk dog', 'Read book']

    >>> # Using protocols for type hints
    >>> from observables import CarriesDistinctSingleValueHook, CarriesDistinctListHook
    
    >>> def process_observable(obs: CarriesDistinctSingleValueHook[str]) -> str:
    ...     return obs.distinct_single_value_reference.upper()
    
    >>> def process_list_observable(obs: CarriesDistinctListHook[str]) -> list[str]:
    ...     return [item.upper() for item in obs.distinct_list_reference]

For more information, see the individual class documentation or run the demo:
    python observables/examples/demo.py

Advanced Usage:
    For building custom observables or extending the library, import from the core module:
    >>> from observables.core import BaseObservable, Hook, HookNexus
    >>> # Create custom observable types with low-level components
"""

from ._observables_basic.observable_dict import ObservableDict, ObservableDictProtocol
from ._observables_basic.observable_list import ObservableList, ObservableListProtocol
from ._observables_basic.observable_set import ObservableSet, ObservableSetProtocol
from ._observables_basic.observable_single_value import ObservableSingleValue, ObservableSingleValueProtocol
from ._observables_basic.observable_tuple import ObservableTuple, ObservableTupleProtocol
from ._observables_advanced.observable_selection_option import ObservableSelectionOption, ObservableSelectionOptionProtocol, ObservableOptionalSelectionOption, ObservableOptionalSelectionOptionProtocol
from ._observables_advanced.observable_selection_enum import ObservableSelectionEnum, ObservableOptionalSelectionEnum  
from ._observables_advanced.observable_multi_selection_option import ObservableMultiSelectionOption, ObservableMultiSelectionOptionProtocol
from ._observables_advanced.observable_transfer import ObservableTransfer
from ._observables_advanced.observable_sync import ObservableSync
from ._observables_advanced.dictionaries.observable_selection_dict import ObservableSelectionDict
from ._observables_advanced.dictionaries.observable_optional_selection_dict import ObservableOptionalSelectionDict
from ._observables_advanced.dictionaries.observable_default_selection_dict import ObservableDefaultSelectionDict
from ._observables_advanced.dictionaries.observable_optional_default_selection_dict import ObservableOptionalDefaultSelectionDict
from ._observables_advanced.observable_rooted_paths import ObservableRootedPaths
from ._observables_advanced.observable_raise_none import ObservableRaiseNone
from ._hooks.floating_hook import FloatingHook
from ._hooks.hook_protocols.full_hook_protocol import FullHookProtocol as Hook
from ._hooks.hook_protocols.read_only_hook_protocol import ReadOnlyHookProtocol as ReadOnlyHook
from ._nexus_system.system_analysis import write_report
from ._carries_hooks.observable_serializable import ObservableSerializable
from ._observables_advanced.observable_subscriber import ObservableSubscriber
from ._publisher_subscriber.publisher_protocol import PublisherProtocol
from ._publisher_subscriber.value_publisher import ValuePublisher
from ._publisher_subscriber.publisher import Publisher

__all__ = [
    # Observable types
    'ObservableDict',
    'ObservableList',
    'ObservableSet',
    'ObservableSingleValue',
    'ObservableTuple',
    'ObservableSelectionOption',
    'ObservableOptionalSelectionOption',
    'ObservableMultiSelectionOption',
    'ObservableTransfer',
    'ObservableSync',
    'ObservableSelectionDict',
    'ObservableOptionalSelectionDict',
    'ObservableDefaultSelectionDict',
    'ObservableOptionalDefaultSelectionDict',
    'ObservableRootedPaths',
    'ObservableSelectionEnum',
    'ObservableOptionalSelectionEnum',
    'ObservableRaiseNone',
    'ObservableSubscriber',

    # Protocol types for type hints
    'ObservableDictProtocol',
    'ObservableListProtocol',
    'ObservableSetProtocol',
    'ObservableSingleValueProtocol',
    'ObservableTupleProtocol',
    'ObservableSelectionOptionProtocol',
    'ObservableOptionalSelectionOptionProtocol',
    'ObservableMultiSelectionOptionProtocol',

    # hooks (user-facing)
    'FloatingHook',
    'Hook',
    'ReadOnlyHook',

    # Other
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
    __version__ = "4.3.0"
    __version_tuple__ = (4, 3, 0)

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
