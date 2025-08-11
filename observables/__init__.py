"""
Observables are objects that can be observed by observers.
Observers are objects that observe observables.
Subjects are objects that are observed by observers.

Observables are objects that can be observed by observers.
Observers are objects that observe observables.
Subjects are objects that are observed by observers.
"""

from ._build_in_observables.observable_dict import ObservableDict
from ._build_in_observables.observable_list import ObservableList
from ._build_in_observables.observable_set import ObservableSet
from ._build_in_observables.observable_single_value import ObservableSingleValue
from ._other_observables.observable_selection_option import ObservableSelectionOption
from ._utils._internal_binding_handler import SyncMode

__all__ = [
    'ObservableDict',
    'ObservableList',
    'ObservableSet',
    'ObservableSingleValue',
    'ObservableSelectionOption',
    'SyncMode',
]
__version__ = '0.1.1'
__author__ = 'Benedikt Axel Brandes'
__year__ = '2025'
