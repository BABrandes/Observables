"""
Observables Core - Advanced API for extending the library

⚠️ DEVELOPMENT STATUS: NOT PRODUCTION READY
This library is under active development. API may change without notice.
Use for experimental and development purposes only.

This module contains the core components and base classes for building on top of the 
Observables library. These are lower-level abstractions meant for users who want to 
create custom observable types or extend the library's functionality.

Core Components:
- BaseObservable: Base class for all observable types
- Hook/HookLike: Core hook implementations and protocols
- OwnedHook/HookWithOwnerLike: Owned hook implementations and protocols
- FloatingHook: Advanced hook with validation and reaction capabilities
- HookNexus: Central storage for actual data values
- BaseCarriesHooks/CarriesHooksLike: Base classes for hook carriers
- HookWithIsolatedValidationLike: Protocol for hooks with custom validation
- HookWithReactionLike: Protocol for hooks that react to changes
- BaseListening/BaseListeningLike: Base classes for listener management
- DEFAULT_NEXUS_MANAGER: The default nexus manager instance
- default_nexus_manager: Module containing configuration (e.g., FLOAT_ACCURACY)

Example Usage with New Protocol-Based Architecture:
    >>> from observables.core import BaseObservable, OwnedHook, HookWithOwnerLike
    >>> 
    >>> # Create a custom observable type using the new architecture
    >>> class MyCustomObservable(BaseObservable):
    ...     def __init__(self, initial_value):
    ...         # Create owned hook
    ...         self._value_hook = OwnedHook(owner=self, initial_value=initial_value)
    ...         super().__init__({"value": self._value_hook})
    ...     
    ...     @property
    ...     def value(self):
    ...         return self._value_hook.value
    ...     
    ...     @value.setter
    ...     def value(self, new_value):
    ...         self._value_hook.submit_value(new_value)
    ...     
    ...     @property
    ...     def value_hook(self) -> HookWithOwnerLike[Any]:
    ...         return self._value_hook

Advanced Usage with FloatingHook:
    >>> from observables.core import FloatingHook
    >>> 
    >>> def validate_value(value):
    ...     return value >= 0, "Value must be non-negative"
    >>> 
    >>> def on_change():
    ...     print("Value changed!")
    ...     return True, "Reaction completed"
    >>> 
    >>> # Create floating hook with validation and reaction
    >>> hook = FloatingHook(
    ...     value=42,
    ...     isolated_validation_callback=validate_value,
    ...     reaction_callback=on_change
    ... )

Configuring Float Tolerance:
    >>> from observables import core
    >>> # Adjust tolerance for your use case
    >>> core.default_nexus_manager.FLOAT_ACCURACY = 1e-6  # More lenient for UI
    >>> # This must be done before creating observables

For normal usage of the library, import from the main package:
    >>> from observables import ObservableSingleValue, ObservableList
"""

from ._utils.base_observable import BaseObservable
from ._hooks.hook_with_owner_like import HookWithOwnerLike
from ._hooks.hook_with_reaction_like import HookWithReactionLike
from ._hooks.hook_with_isolated_validation_like import HookWithIsolatedValidationLike
from ._utils.hook_nexus import HookNexus
from ._hooks.owned_hook import OwnedHook
from ._utils.base_carries_hooks import BaseCarriesHooks, CarriesHooksLike
from ._utils.base_listening import BaseListening, BaseListeningLike
from ._utils.nexus_manager import NexusManager
from ._utils.subscriber import Subscriber
from ._utils import default_nexus_manager

# Re-export the module for easy access to configuration
# Users should modify: observables.core.default_nexus_manager.FLOAT_ACCURACY
# or import directly: from observables._utils import default_nexus_manager

DEFAULT_NEXUS_MANAGER = default_nexus_manager.DEFAULT_NEXUS_MANAGER

__all__ = [
    'BaseObservable',
    'HookWithOwnerLike',
    'HookWithReactionLike',
    'HookWithIsolatedValidationLike',
    'HookNexus',
    'OwnedHook',
    'BaseCarriesHooks',
    'CarriesHooksLike',
    'BaseListening',
    'BaseListeningLike',
    'NexusManager',
    'DEFAULT_NEXUS_MANAGER',
    'default_nexus_manager',  # Export module for configuration access
    'Subscriber',
]

