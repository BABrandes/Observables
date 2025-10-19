# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Major API Modernization
- **Modern X-Prefixed API**: Clean, concise names (`XValue`, `XList`, `XSet`, `XDict`, etc.)
- **Complete Immutability**: All collections use immutable types internally
  - `XList` uses `tuple` internally
  - `XSet` uses `frozenset` internally
  - `XDict` uses `MappingProxyType` internally
- **Typed Parameter Objects**: Eliminates parameter order confusion
  - `FunctionValues[K, V]` for user-facing function callables
  - `UpdateFunctionValues[K, V]` for internal update callbacks
- **Function Observables**: New function-like observables
  - `XFunction` (alias for `ObservableSync`) - bidirectional synchronization with constraints
  - `XOneWayFunction` - one-way transformations from inputs to outputs
- **Hook API Consistency**: All `__init__` methods accept `Hook | ReadOnlyHook`
  - Internal checks use `ManagedHookProtocol` for implementation flexibility
  - Cleaner separation between public API and internal implementation

### Changed
- **Breaking**: All collections now return immutable types
  - `ObservableList.value` returns `tuple` instead of `list`
  - `ObservableSet.value` returns `frozenset` instead of `set`
  - `ObservableDict.dict` returns `MappingProxyType` instead of `dict`
  - `ObservableSelectionOption.available_options` returns `frozenset` instead of `set`
- **Breaking**: `add_values_to_be_updated_callback` signature simplified
  - Old: `callback(self_ref, current_values, submitted_values)`
  - New: `callback(self_ref, update_values: UpdateFunctionValues)`
- **Breaking**: `ObservableFunction` (formerly `ObservableSync`) simplified
  - Removed confusing `essential_sync_value_keys` parameter
  - Function callable now always receives `FunctionValues` object
  - Old: `function(submitted_values, current_values)`
  - New: `function(values: FunctionValues)`
- Refactored value access in `HookNexus`: `.value` now returns references, `.value_copy()` for explicit copies
- Reorganized module structure with `function_like`, `dict_like`, `list_like`, `set_like`, `complex` directories

### Deprecated
- All `Observable*` names deprecated in favor of `X*` aliases
- `XTransfer` deprecated in favor of `XOneWayFunction`
- `XSync` deprecated in favor of `XFunction`

## [0.2.0] - 2025-01-XX

### Added
- Component-based observable architecture
- Enhanced binding system with automatic synchronization
- Improved verification methods for data validation
- Better memory management and binding cleanup
- Enhanced type safety and generic support

### Changed
- Refactored entire codebase to use component-based architecture
- Updated Observable base class to support component composition
- Improved binding handler system for better performance
- Enhanced error handling and validation

## [0.1.1] - 2025-01-XX

### Added
- Initial beta release
- Basic observable functionality
- Core binding system
- Listener management
- Type safety features

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [0.1.1] - 2025-01-XX

### Added
- Initial beta release
- Basic observable functionality
- Core binding system
- Listener management
- Type safety features

## [0.1.0] - 2025-01-XX

### Added
- Initial development version
- Basic observable classes
- Simple listener system
