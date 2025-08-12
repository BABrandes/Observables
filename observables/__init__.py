"""
Observables Library - A Python library for reactive programming and bidirectional bindings.

This library provides a comprehensive set of observable data structures that support
bidirectional bindings, automatic synchronization, and reactive programming patterns.
It's designed to make it easy to create reactive applications where data changes
automatically propagate through a network of interconnected objects.

Core Features:
- Bidirectional bindings between observables with automatic synchronization
- Component-based architecture for flexible observable composition
- Automatic change propagation and synchronization
- Listener notification system for change events
- Type-safe generic implementations with full type hints
- Custom validation support with verification methods
- Performance-optimized change detection and binding management
- Memory-efficient binding cleanup and listener management

Architecture:
The library uses a component-based architecture where observables are composed of:
- Component values: The actual data being observed
- Binding handlers: Manage bidirectional connections between observables
- Verification methods: Validate data changes before applying them
- Copy methods: Control how data is duplicated during binding operations

Available Observable Types:
- ObservableSingleValue: Wrapper around any single value with validation
- ObservableList: Reactive list with full list interface compatibility
- ObservableSet: Reactive set with full set interface compatibility
- ObservableDict: Reactive dictionary with full dict interface compatibility
- ObservableSelectionOption: Combined options set and selected value management
- ObservableEnum: Reactive enum with options management and validation

Example Usage:
    >>> from observables import ObservableSingleValue, ObservableList
    
    >>> # Create reactive values
    >>> name = ObservableSingleValue("John")
    >>> age = ObservableSingleValue(25)
    
    >>> # Add listeners for change notifications
    >>> name.add_listeners(lambda: print("Name changed!"))
    >>> age.add_listeners(lambda: print("Age changed!"))
    
    >>> # Create bidirectional bindings
    >>> name_copy = ObservableSingleValue(name)
    >>> name_copy.set_value("Jane")  # Updates both observables
    Name changed!
    
    >>> # Reactive lists
    >>> todo_list = ObservableList(["Buy groceries", "Walk dog"])
    >>> todo_copy = ObservableList(todo_list)
    >>> todo_copy.append("Read book")  # Updates both lists
    
    >>> print(name.value, age.value, todo_list.value)
    Jane 25 ['Buy groceries', 'Walk dog', 'Read book']

For more information, see the individual class documentation or run the demo:
    python observables/examples/demo.py
"""

from ._build_in_observables.observable_dict import ObservableDict
from ._build_in_observables.observable_list import ObservableList
from ._build_in_observables.observable_set import ObservableSet
from ._build_in_observables.observable_single_value import ObservableSingleValue
from ._build_in_observables.observable_enum import ObservableEnum
from ._other_observables.observable_selection_option import ObservableSelectionOption
from ._utils.observable import Observable
from ._utils._internal_binding_handler import SyncMode

__all__ = [
    'ObservableDict',
    'ObservableList',
    'ObservableSet',
    'ObservableSingleValue',
    'ObservableEnum',
    'ObservableSelectionOption',
    'Observable',
    'SyncMode',
]

# Package metadata
try:
    from ._version import __version__, __version_tuple__
except ImportError:
    __version__ = "0.2.6"
    __version_tuple__ = (0, 2, 6)

__author__ = 'Benedikt Axel Brandes'
__year__ = '2025'

# Package description
__description__ = 'A Python library for reactive programming and bidirectional bindings'
__keywords__ = ['observable', 'reactive', 'binding', 'data-binding', 'reactive-programming']
__url__ = 'https://github.com/yourusername/observables'
__project_urls__ = {
    'Bug Reports': 'https://github.com/yourusername/observables/issues',
    'Source': 'https://github.com/yourusername/observables',
    'Documentation': 'https://github.com/yourusername/observables#readme',
}

# Development status
__classifiers__ = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache 2.0 Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]
