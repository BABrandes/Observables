"""
Observables Core - Advanced API for extending the library

This module contains the core components and base classes for building on top of the 
Observables library. These are lower-level abstractions meant for users who want to 
create custom observable types or extend the library's functionality.

Core Components:
- BaseObservable: Base class for all observable types
- Hook/HookLike: Core hook implementations and protocols
- OwnedHook/OwnedHookLike: Owned hook implementations and protocols
- HookNexus: Central storage for actual data values
- BaseCarriesHooks/CarriesHooksLike: Base classes for hook carriers
- HookWithReactionMixin: Mixin for adding reaction capabilities to hooks
- HookWithValidationMixin: Mixin for adding validation capabilities to hooks
- BaseListening/BaseListeningLike: Base classes for listener management
- DEFAULT_NEXUS_MANAGER: The default nexus manager instance
- default_nexus_manager: Module containing configuration (e.g., FLOAT_ACCURACY)

Example Usage:
    >>> from observables.core import BaseObservable, Hook, HookNexus
    >>> 
    >>> # Create a custom observable type
    >>> class MyCustomObservable(BaseObservable):
    ...     def __init__(self, initial_value):
    ...         super().__init__()
    ...         self._hook = Hook(HookNexus(initial_value))
    ...     
    ...     @property
    ...     def value(self):
    ...         return self._hook.get_value()
    ...     
    ...     @value.setter
    ...     def value(self, new_value):
    ...         self._hook.set_value(new_value)

Configuring Float Tolerance:
    >>> from observables import core
    >>> # Adjust tolerance for your use case
    >>> core.default_nexus_manager.FLOAT_ACCURACY = 1e-6  # More lenient for UI
    >>> # This must be done before creating observables

For normal usage of the library, import from the main package:
    >>> from observables import ObservableSingleValue, ObservableList
"""

from ._utils.base_observable import BaseObservable
from ._hooks.hook import Hook
from ._hooks.hook_like import HookLike
from ._utils.hook_nexus import HookNexus
from ._hooks.owned_hook import OwnedHook
from ._hooks.owned_hook_like import OwnedHookLike
from ._hooks.floating_hook import FloatingHook
from ._hooks.floating_hook_like import FloatingHookLike
from ._utils.base_carries_hooks import BaseCarriesHooks, CarriesHooksLike
from ._hooks.hook_with_reaction_mixin import HookWithReactionMixin
from ._hooks.hook_with_validation_mixin import HookWithValidationMixin
from ._utils.base_listening import BaseListening, BaseListeningLike
from ._utils.nexus_manager import NexusManager
from ._utils import default_nexus_manager

# Re-export the module for easy access to configuration
# Users should modify: observables.core.default_nexus_manager.FLOAT_ACCURACY
# or import directly: from observables._utils import default_nexus_manager

DEFAULT_NEXUS_MANAGER = default_nexus_manager.DEFAULT_NEXUS_MANAGER

__all__ = [
    'BaseObservable',
    'Hook',
    'HookLike',
    'HookNexus',
    'OwnedHook',
    'OwnedHookLike',
    'FloatingHook',
    'FloatingHookLike',
    'BaseCarriesHooks',
    'CarriesHooksLike',
    'HookWithReactionMixin',
    'HookWithValidationMixin',
    'BaseListening',
    'BaseListeningLike',
    'NexusManager',
    'DEFAULT_NEXUS_MANAGER',
    'default_nexus_manager',  # Export module for configuration access
]

