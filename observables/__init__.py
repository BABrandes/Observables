"""
Observables - Centralized Reactive Programming

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
The library uses a revolutionary hook-based architecture where:
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
"""

from ._build_in_observables.observable_dict import ObservableDict, ObservableDictLike
from ._build_in_observables.observable_list import ObservableList, ObservableListLike
from ._build_in_observables.observable_set import ObservableSet, ObservableSetLike
from ._build_in_observables.observable_single_value import ObservableSingleValue, ObservableSingleValueLike
from ._build_in_observables.observable_tuple import ObservableTuple, ObservableTupleLike
from ._other_observables.observable_selection_option import ObservableSelectionOption, ObservableSelectionOptionLike, ObservableOptionalSelectionOption, ObservableOptionalSelectionOptionLike
from ._other_observables.observable_selection_enum import ObservableSelectionEnum, ObservableOptionalSelectionEnum
from ._other_observables.observable_multi_selection_option import ObservableMultiSelectionOption, ObservableMultiSelectionOptionLike
from ._other_observables.observable_transfer import ObservableTransfer
from ._other_observables.observable_sync import ObservableSync
from ._other_observables.observable_selection_dict import ObservableSelectionDict, ObservableOptionalSelectionDict, ObservableDefaultSelectionDict, ObservableOptionalDefaultSelectionDict
from ._other_observables.observable_rooted_paths import ObservableRootedPaths
from ._utils.base_observable import BaseObservable
from ._utils.initial_sync_mode import InitialSyncMode
from ._hooks.owned_hook import OwnedHook
from ._hooks.hook_like import HookLike
from ._utils.hook_nexus import HookNexus
from ._hooks.owned_hook_like import OwnedHookLike
from ._hooks.floating_hook import FloatingHook
from ._utils.system_analysis import write_report    
from ._utils.base_carries_hooks import CarriesHooksLike
from ._utils.nexus_manager import NexusManager
from ._utils.default_nexus_manager import DEFAULT_NEXUS_MANAGER
from ._utils.base_carries_hooks import BaseCarriesHooks
from ._utils.observable_serializable import ObservableSerializable
from ._other_observables.observable_raise_none import ObservableRaiseNone

__all__ = [
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
    'ObservableDictLike',
    'ObservableListLike',
    'ObservableSetLike',
    'ObservableSingleValueLike',
    'ObservableTupleLike',
    'ObservableSelectionOptionLike',
    'ObservableOptionalSelectionOptionLike',
    'ObservableMultiSelectionOptionLike',
    'ObservableSelectionDict',
    'ObservableOptionalSelectionDict',
    'ObservableDefaultSelectionDict',
    'ObservableOptionalDefaultSelectionDict',
    'ObservableRootedPaths',
    'ObservableSelectionEnum',
    'ObservableOptionalSelectionEnum',
    'BaseObservable',
    'OwnedHook',
    'HookLike',
    'HookNexus',
    'OwnedHookLike',
    'FloatingHook',
    'BaseCarriesHooks',
    'CarriesHooksLike',
    'InitialSyncMode',
    'ObservableSerializable',
    'write_report',
    'NexusManager',
    'DEFAULT_NEXUS_MANAGER',
    'ObservableRootedPaths',
    'ObservableRaiseNone',
]

# Package metadata
try:
    from ._version import __version__, __version_tuple__
except ImportError:
    __version__ = "3.0.38"
    __version_tuple__ = (3, 0, 38)

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
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]
