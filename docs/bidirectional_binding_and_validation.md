# Bidirectional Binding and State Validation

The Observables library provides a revolutionary approach to reactive programming with **guaranteed bidirectional binding** and **rigorous state validation**. This document explains how these core features work and why they make the library exceptionally robust and reliable.

## 🔄 **True Bidirectional Binding**

### **What Makes Our Binding Truly Bidirectional?**

Unlike traditional reactive libraries that implement one-way data flow, Observables provides **genuine bidirectional binding** through a centralized storage system. When observables are bound together, they share the **same underlying storage (HookNexus)**, ensuring that changes propagate in both directions automatically.

```python
from observables import ObservableSingleValue, InitialSyncMode

# Create two observables
temperature_celsius = ObservableSingleValue(25.0)
temperature_fahrenheit = ObservableSingleValue(77.0)

# Bind them together - they now share the same storage
temperature_celsius.attach(
    temperature_fahrenheit.single_value_hook, 
    "single_value", 
    InitialSyncMode.PUSH_TO_TARGET
)

# ✅ Change from celsius - fahrenheit updates automatically
temperature_celsius.single_value = 30.0
print(temperature_fahrenheit.single_value)  # 30.0 (same value, shared storage)

# ✅ Change from fahrenheit - celsius updates automatically  
temperature_fahrenheit.single_value = 100.0
print(temperature_celsius.single_value)   # 100.0 (same value, shared storage)
```

### **The HookNexus: Central Storage Architecture**

The secret to true bidirectional binding is the **HookNexus** - a central storage system where values are stored exactly once:

```python
# Each observable starts with its own HookNexus
obs1 = ObservableSingleValue(10)
obs2 = ObservableSingleValue(20)

print(f"Before binding:")
print(f"  obs1 HookNexus ID: {id(obs1._component_hooks['single_value'].hook_nexus)}")
print(f"  obs2 HookNexus ID: {id(obs2._component_hooks['single_value'].hook_nexus)}")
# Different IDs = separate storage

# Bind them together
obs1.attach(obs2.single_value_hook, "single_value", InitialSyncMode.PUSH_TO_TARGET)

print(f"After binding:")
print(f"  obs1 HookNexus ID: {id(obs1._component_hooks['single_value'].hook_nexus)}")
print(f"  obs2 HookNexus ID: {id(obs2._component_hooks['single_value'].hook_nexus)}")
# Same ID = shared storage! ✅

# Now changes propagate bidirectionally because they share the same storage
obs1.single_value = 100
print(f"obs2.single_value: {obs2.single_value}")  # 100 ✅

obs2.single_value = 200  
print(f"obs1.single_value: {obs1.single_value}")  # 200 ✅
```

### **Transitive Binding Networks**

Bidirectional binding extends transitively across entire networks:

```python
# Create a network of observables
user_name = ObservableSingleValue("John")
display_name = ObservableSingleValue("John")
header_name = ObservableSingleValue("John")
sidebar_name = ObservableSingleValue("John")

# Create binding chain
user_name.attach(display_name.single_value_hook, "single_value", InitialSyncMode.PUSH_TO_TARGET)
display_name.attach(header_name.single_value_hook, "single_value", InitialSyncMode.PUSH_TO_TARGET)
header_name.attach(sidebar_name.single_value_hook, "single_value", InitialSyncMode.PUSH_TO_TARGET)

# ✅ All four observables now share the same HookNexus
# Changes from ANY observable propagate to ALL others bidirectionally

# Change from the first one
user_name.single_value = "Alice"
print(f"All names updated:")
print(f"  user_name: {user_name.single_value}")         # Alice
print(f"  display_name: {display_name.single_value}")   # Alice
print(f"  header_name: {header_name.single_value}")     # Alice
print(f"  sidebar_name: {sidebar_name.single_value}")   # Alice

# Change from the last one - propagates to all others
sidebar_name.single_value = "Bob"
print(f"All names updated from sidebar:")
print(f"  user_name: {user_name.single_value}")         # Bob
print(f"  display_name: {display_name.single_value}")   # Bob
print(f"  header_name: {header_name.single_value}")     # Bob
print(f"  sidebar_name: {sidebar_name.single_value}")   # Bob
```

### **Network Resilience**

The bidirectional binding survives disconnections in the middle of chains:

```python
# Create a chain: A ↔ B ↔ C ↔ D
obs_a = ObservableSingleValue(1)
obs_b = ObservableSingleValue(1) 
obs_c = ObservableSingleValue(1)
obs_d = ObservableSingleValue(1)

# Build the chain
obs_a.attach(obs_b.single_value_hook, "single_value", InitialSyncMode.PUSH_TO_TARGET)
obs_b.attach(obs_c.single_value_hook, "single_value", InitialSyncMode.PUSH_TO_TARGET)
obs_c.attach(obs_d.single_value_hook, "single_value", InitialSyncMode.PUSH_TO_TARGET)

# All four share the same HookNexus
print(f"All HookNexus IDs are the same:")
print(f"  A: {id(obs_a._component_hooks['single_value'].hook_nexus)}")
print(f"  B: {id(obs_b._component_hooks['single_value'].hook_nexus)}")
print(f"  C: {id(obs_c._component_hooks['single_value'].hook_nexus)}")
print(f"  D: {id(obs_d._component_hooks['single_value'].hook_nexus)}")

# Disconnect B from the network
obs_b.detach()

# A, C, and D remain connected! B is isolated.
obs_a.single_value = 100
print(f"After B disconnects:")
print(f"  A: {obs_a.single_value}")  # 100 ✅
print(f"  B: {obs_b.single_value}")  # 1 (isolated) ✅
print(f"  C: {obs_c.single_value}")  # 100 ✅
print(f"  D: {obs_d.single_value}")  # 100 ✅
```

## ⚡ **Rigorous State Validation**

### **Validation is Always Enforced**

The Observables library **rigorously enforces valid states** at all times. Invalid states are rejected immediately, preventing data corruption and ensuring system integrity.

```python
from observables import ObservableSelectionOption

# Create a selection with available options
color_selector = ObservableSelectionOption("red", {"red", "green", "blue"})

# ✅ Valid selection - accepted
color_selector.selected_option = "green"
print(f"Selected: {color_selector.selected_option}")  # green

# ❌ Invalid selection - rejected with clear error
try:
    color_selector.selected_option = "purple"  # Not in available options
except ValueError as e:
    print(f"Validation error: {e}")
    # Output: "Selected option purple not in options {'red', 'green', 'blue'}"

# State remains valid after rejection
print(f"Current selection: {color_selector.selected_option}")  # green (unchanged)
```

### **Atomic Validation Across Bound Observables**

When observables are bound together, validation happens **atomically** across the entire network:

```python
# Create two bound selection observables
primary_selector = ObservableSelectionOption("red", {"red", "green", "blue"})
secondary_selector = ObservableSelectionOption("red", {"red", "green", "yellow"})

# Bind them together
primary_selector.attach(
    secondary_selector.selected_option_hook, 
    "selected_option", 
    InitialSyncMode.PUSH_TO_TARGET
)

# ✅ Valid change - works across both observables
primary_selector.selected_option = "green"
print(f"Primary: {primary_selector.selected_option}")    # green
print(f"Secondary: {secondary_selector.selected_option}") # green

# ❌ Invalid change - rejected for the entire network
try:
    primary_selector.selected_option = "purple"  # Not valid for either
except ValueError as e:
    print(f"Network validation failed: {e}")

# Both observables maintain their valid state
print(f"Primary remains: {primary_selector.selected_option}")    # green
print(f"Secondary remains: {secondary_selector.selected_option}") # green
```

### **Complex Multi-Component Validation**

For observables with multiple components, **all components are validated together**:

```python
from observables import ObservableSelectionOption

# Create a complex observable with selected option and available options
product_selector = ObservableSelectionOption("laptop", {"laptop", "phone", "tablet"})

# ✅ Valid atomic update - both components are compatible
product_selector.set_selected_option_and_available_options(
    "smartwatch", 
    {"smartwatch", "laptop", "phone"}
)
print(f"Selected: {product_selector.selected_option}")           # smartwatch
print(f"Available: {product_selector.available_options}")        # {'smartwatch', 'laptop', 'phone'}

# ❌ Invalid atomic update - selected option not in new available options
try:
    product_selector.set_selected_option_and_available_options(
        "laptop",  # This would be valid...
        {"smartwatch", "phone"}  # ...but laptop is not in these options
    )
except ValueError as e:
    print(f"Atomic validation failed: {e}")
    # Output: "Selected option laptop not in options {'smartwatch', 'phone'}"

# State remains consistent after validation failure
print(f"Selected: {product_selector.selected_option}")           # smartwatch (unchanged)
print(f"Available: {product_selector.available_options}")        # {'smartwatch', 'laptop', 'phone'} (unchanged)
```

### **Validation During Binding Operations**

Validation is enforced even during binding operations, ensuring compatibility:

```python
# Create observables with compatible initial states
config_a = ObservableSelectionOption("production", {"production", "staging", "development"})
config_b = ObservableSelectionOption("staging", {"staging", "development", "test"})

# ✅ Binding succeeds because current values can be made compatible
config_a.attach(config_b.selected_option_hook, "selected_option", InitialSyncMode.PUSH_TO_TARGET)
print(f"After binding - both have: {config_a.selected_option}")  # staging

# Create incompatible observables
config_c = ObservableSelectionOption("invalid_option", {"option1", "option2"})

# ❌ Binding fails due to validation
try:
    config_a.attach(config_c.selected_option_hook, "selected_option", InitialSyncMode.PULL_FROM_TARGET)
except ValueError as e:
    print(f"Binding validation failed: {e}")
    # Output: "Selected option invalid_option not in options {'staging', 'development', 'test'}"

# Original binding remains intact after failed binding attempt
print(f"Config A still: {config_a.selected_option}")  # staging
print(f"Config B still: {config_b.selected_option}")  # staging
```

## 🔒 **Consistency Guarantees**

### **No Partially Invalid States**

The system **never allows** partially invalid states, even temporarily:

```python
from observables import ObservableSelectionOption

# Create a complex observable
user_preferences = ObservableSelectionOption("dark", {"dark", "light", "auto"})

# Add a listener to demonstrate consistency
state_log = []
def log_state():
    state_log.append({
        "selected": user_preferences.selected_option,
        "available": user_preferences.available_options.copy()
    })

user_preferences.add_listener(log_state)

# ✅ Valid update - listener sees consistent state
user_preferences.set_selected_option_and_available_options("high_contrast", {"high_contrast", "dark", "light"})

# Check that listener never saw an invalid intermediate state
for i, state in enumerate(state_log):
    selected = state["selected"]
    available = state["available"]
    is_valid = selected in available
    print(f"State {i}: selected='{selected}', valid={is_valid}")
    assert is_valid, f"Invalid state detected: {selected} not in {available}"
```

### **Thread-Safe Validation**

Validation is thread-safe, preventing race conditions during concurrent updates:

```python
import threading
import time
from observables import ObservableSelectionOption

# Create a shared observable
shared_config = ObservableSelectionOption("config1", {"config1", "config2", "config3"})

validation_errors = []

def concurrent_update(config_name, available_options):
    """Attempt to update configuration concurrently."""
    try:
        shared_config.set_selected_option_and_available_options(config_name, available_options)
        print(f"✅ Thread {threading.current_thread().name}: Updated to {config_name}")
    except ValueError as e:
        validation_errors.append(f"❌ Thread {threading.current_thread().name}: {e}")

# Start concurrent threads
threads = [
    threading.Thread(target=concurrent_update, args=("config2", {"config2", "config3"})),
    threading.Thread(target=concurrent_update, args=("invalid", {"config1", "config2"})),
    threading.Thread(target=concurrent_update, args=("config3", {"config1", "config3"})),
]

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

# Check results - validation was enforced even under concurrent access
print(f"Final state: {shared_config.selected_option}")
print(f"Validation errors: {len(validation_errors)}")
for error in validation_errors:
    print(f"  {error}")

# State remains valid regardless of concurrent access attempts
assert shared_config.selected_option in shared_config.available_options
```

## 🛡️ **Error Handling and Recovery**

### **Graceful Error Messages**

The system provides clear, actionable error messages:

```python
from observables import ObservableSelectionOption

# Create observable with specific constraints  
payment_method = ObservableSelectionOption("credit_card", {"credit_card", "debit_card", "paypal"})

# Attempt invalid operations with clear error messages
test_cases = [
    ("bitcoin", "Invalid payment method"),
    ("", "Empty selection not allowed"),
    ("CREDIT_CARD", "Case sensitive validation"),
]

for invalid_selection, description in test_cases:
    try:
        payment_method.selected_option = invalid_selection
    except ValueError as e:
        print(f"{description}:")
        print(f"  Attempted: '{invalid_selection}'")
        print(f"  Error: {e}")
        print(f"  Current valid state: '{payment_method.selected_option}'")
        print()
```

### **Validation with Custom Logic**

You can implement custom validation logic while maintaining the same guarantees:

```python
from observables import ObservableSingleValue
from typing import Any

class ValidatedTemperature(ObservableSingleValue[float]):
    """Temperature observable with range validation."""
    
    def __init__(self, initial_temp: float, min_temp: float = -273.15, max_temp: float = 1000.0):
        self.min_temp = min_temp
        self.max_temp = max_temp
        
        # Validate initial value
        if not self._is_valid_temperature(initial_temp):
            raise ValueError(f"Initial temperature {initial_temp} outside valid range [{min_temp}, {max_temp}]")
        
        super().__init__(initial_temp)
        
        # Add validation to all value changes
        self._original_set_value = self._set_single_value
        self._set_single_value = self._validated_set_value
    
    def _is_valid_temperature(self, temp: float) -> bool:
        """Check if temperature is within valid range."""
        return self.min_temp <= temp <= self.max_temp
    
    def _validated_set_value(self, value: float) -> None:
        """Set value with validation."""
        if not self._is_valid_temperature(value):
            raise ValueError(f"Temperature {value} outside valid range [{self.min_temp}, {self.max_temp}]")
        self._original_set_value(value)

# Usage with validation
room_temp = ValidatedTemperature(22.0, min_temp=-10.0, max_temp=50.0)

# ✅ Valid temperature
room_temp.single_value = 25.0
print(f"Room temperature: {room_temp.single_value}°C")

# ❌ Invalid temperature - rejected
try:
    room_temp.single_value = 100.0  # Too hot!
except ValueError as e:
    print(f"Validation error: {e}")

# State remains valid
print(f"Temperature remains: {room_temp.single_value}°C")  # 25.0

# Binding also respects custom validation
outdoor_temp = ValidatedTemperature(15.0, min_temp=-40.0, max_temp=60.0)

# ✅ Compatible ranges - binding succeeds
room_temp.attach(outdoor_temp.single_value_hook, "single_value", InitialSyncMode.PUSH_TO_TARGET)

# ❌ Updates that violate validation are rejected
try:
    outdoor_temp.single_value = 75.0  # Valid for outdoor but invalid for room
except ValueError as e:
    print(f"Binding validation error: {e}")
```

## 🎯 **Real-World Validation Scenarios**

### **Form Validation with Cross-Field Dependencies**

```python
from observables import ObservableSingleValue, ObservableSelectionOption

class UserRegistrationForm:
    """User registration form with comprehensive validation."""
    
    def __init__(self):
        # Form fields
        self.username = ObservableSingleValue("")
        self.email = ObservableSingleValue("")
        self.password = ObservableSingleValue("")
        self.confirm_password = ObservableSingleValue("")
        self.country = ObservableSelectionOption("", {"US", "CA", "UK", "DE", "FR"})
        self.age = ObservableSingleValue(0)
        
        # Validation state
        self.is_valid = ObservableSingleValue(False)
        self.validation_errors = ObservableSingleValue([])
        
        # Bind password fields for cross-validation
        self.password.add_listener(self._validate_passwords)
        self.confirm_password.add_listener(self._validate_passwords)
        
        # Bind all fields for overall validation
        self.username.add_listener(self._validate_form)
        self.email.add_listener(self._validate_form)
        self.country.add_listener(self._validate_form)
        self.age.add_listener(self._validate_form)
    
    def _validate_passwords(self):
        """Validate password consistency."""
        if self.password.single_value != self.confirm_password.single_value:
            if "password_mismatch" not in self.validation_errors.single_value:
                errors = self.validation_errors.single_value.copy()
                errors.append("password_mismatch")
                self.validation_errors.single_value = errors
        else:
            if "password_mismatch" in self.validation_errors.single_value:
                errors = self.validation_errors.single_value.copy()
                errors.remove("password_mismatch")
                self.validation_errors.single_value = errors
    
    def _validate_form(self):
        """Validate entire form."""
        errors = []
        
        # Username validation
        if len(self.username.single_value) < 3:
            errors.append("username_too_short")
        
        # Email validation
        if "@" not in self.email.single_value:
            errors.append("invalid_email")
        
        # Age validation
        if self.age.single_value < 13:
            errors.append("age_too_young")
        elif self.age.single_value > 120:
            errors.append("age_too_old")
        
        # Country validation
        if not self.country.selected_option:
            errors.append("country_required")
        
        # Update validation state atomically
        self.validation_errors.single_value = errors
        self.is_valid.single_value = len(errors) == 0
    
    def submit(self):
        """Submit form if valid."""
        self._validate_form()  # Final validation
        self._validate_passwords()
        
        if self.is_valid.single_value and "password_mismatch" not in self.validation_errors.single_value:
            print("✅ Form submitted successfully!")
            return True
        else:
            all_errors = self.validation_errors.single_value.copy()
            if "password_mismatch" in [err for err in all_errors]:
                all_errors.append("password_mismatch")
            
            print("❌ Form validation failed:")
            for error in set(all_errors):
                print(f"  - {error}")
            return False

# Usage
form = UserRegistrationForm()

# Fill out form with valid data
form.username.single_value = "johndoe"
form.email.single_value = "john@example.com"
form.password.single_value = "secretpassword"
form.confirm_password.single_value = "secretpassword"
form.country.selected_option = "US"
form.age.single_value = 25

# Submit form
success = form.submit()
print(f"Form submission: {'Success' if success else 'Failed'}")
```

### **Configuration System with Environment Validation**

```python
from observables import ObservableSelectionOption, ObservableSingleValue

class DatabaseConfig:
    """Database configuration with environment-specific validation."""
    
    def __init__(self):
        # Environment determines available options
        self.environment = ObservableSelectionOption("development", {"development", "staging", "production"})
        
        # Database settings that depend on environment
        self.host = ObservableSingleValue("localhost")
        self.port = ObservableSingleValue(5432)
        self.ssl_required = ObservableSingleValue(False)
        self.pool_size = ObservableSingleValue(5)
        
        # Bind environment changes to validation
        self.environment.add_listener(self._validate_environment_constraints)
        self.host.add_listener(self._validate_environment_constraints)
        self.port.add_listener(self._validate_environment_constraints)
        self.ssl_required.add_listener(self._validate_environment_constraints)
        self.pool_size.add_listener(self._validate_environment_constraints)
    
    def _validate_environment_constraints(self):
        """Enforce environment-specific constraints."""
        env = self.environment.selected_option
        
        if env == "production":
            # Production requirements
            if self.host.single_value in ["localhost", "127.0.0.1"]:
                raise ValueError("Production environment cannot use localhost")
            
            if not self.ssl_required.single_value:
                raise ValueError("Production environment requires SSL")
            
            if self.pool_size.single_value < 10:
                raise ValueError("Production environment requires pool size >= 10")
        
        elif env == "staging":
            # Staging requirements
            if self.host.single_value == "localhost":
                raise ValueError("Staging environment cannot use localhost")
            
            if self.pool_size.single_value < 5:
                raise ValueError("Staging environment requires pool size >= 5")
        
        # Development has no special constraints
    
    def apply_environment_defaults(self):
        """Apply environment-specific defaults."""
        env = self.environment.selected_option
        
        if env == "production":
            self.host.single_value = "prod-db.company.com"
            self.port.single_value = 5432
            self.ssl_required.single_value = True
            self.pool_size.single_value = 20
        
        elif env == "staging":
            self.host.single_value = "staging-db.company.com"
            self.port.single_value = 5432
            self.ssl_required.single_value = True
            self.pool_size.single_value = 10
        
        elif env == "development":
            self.host.single_value = "localhost"
            self.port.single_value = 5432
            self.ssl_required.single_value = False
            self.pool_size.single_value = 5

# Usage
config = DatabaseConfig()

# ✅ Valid development configuration
config.apply_environment_defaults()
print(f"Development config: {config.host.single_value}:{config.port.single_value}")

# ✅ Switch to staging with validation
config.environment.selected_option = "staging"
config.apply_environment_defaults()
print(f"Staging config: {config.host.single_value}:{config.port.single_value}")

# ❌ Invalid production configuration
config.environment.selected_option = "production"
try:
    config.host.single_value = "localhost"  # Not allowed in production
except ValueError as e:
    print(f"Production validation error: {e}")

# ✅ Valid production configuration
config.apply_environment_defaults()
print(f"Production config: {config.host.single_value}:{config.port.single_value}")
```

## 🔍 **Debugging Validation Issues**

### **Enabling Debug Logging**

```python
import logging
from observables import ObservableSelectionOption

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create observable with logger
debug_selector = ObservableSelectionOption("option1", {"option1", "option2"}, logger=logger)

# Operations will now log detailed validation information
debug_selector.selected_option = "option2"  # Logs: Validation passed
try:
    debug_selector.selected_option = "invalid"  # Logs: Validation failed
except ValueError:
    pass
```

### **Validation State Inspection**

```python
from observables import ObservableSelectionOption

def inspect_validation_state(observable, operation_description):
    """Helper function to inspect validation state."""
    print(f"\n{operation_description}:")
    print(f"  Selected: {observable.selected_option}")
    print(f"  Available: {observable.available_options}")
    print(f"  Valid: {observable.selected_option in observable.available_options}")
    
    if hasattr(observable, '_component_hooks'):
        hook_nexus = observable._component_hooks['selected_option'].hook_nexus
        print(f"  HookNexus ID: {id(hook_nexus)}")
        print(f"  Hook count: {len(hook_nexus._hooks) if hasattr(hook_nexus, '_hooks') else 'N/A'}")

# Usage
selector = ObservableSelectionOption("red", {"red", "green", "blue"})
inspect_validation_state(selector, "Initial state")

selector.selected_option = "green"
inspect_validation_state(selector, "After valid change")

try:
    selector.selected_option = "purple"
except ValueError:
    pass
inspect_validation_state(selector, "After invalid change attempt")
```

## 🚀 **Performance Considerations**

### **Validation Overhead**

The validation system is designed for minimal overhead:

- **Atomic Operations**: Validation happens once per change, not per bound observable
- **Efficient Checks**: Simple membership tests and constraint validation
- **Caching**: Validation results are cached when possible
- **Thread Safety**: Minimal locking overhead with optimized critical sections

### **Optimization Tips**

```python
# ✅ Good: Batch related changes together
selector.set_selected_option_and_available_options("new_option", {"new_option", "other_option"})

# ❌ Avoid: Separate operations that might create temporary invalid states
# selector.available_options = {"new_option", "other_option"}  # Might invalidate current selection
# selector.selected_option = "new_option"                      # Then fix selection

# ✅ Good: Validate once when building networks
if all(is_compatible(obs) for obs in observables_to_bind):
    for i in range(len(observables_to_bind) - 1):
        observables_to_bind[i].bind_to(observables_to_bind[i + 1])

# ✅ Good: Use appropriate initial sync modes to minimize validation
obs1.attach(obs2.hook, "component", InitialSyncMode.PUSH_TO_TARGET)  # Sync from obs1 to obs2
```

---

## 🎯 **Key Takeaways**

1. **True Bidirectional Binding**: Changes propagate in both directions through shared HookNexus storage
2. **Rigorous Validation**: Invalid states are never allowed, even temporarily
3. **Atomic Operations**: Multi-component changes are validated and applied atomically
4. **Network Resilience**: Binding networks survive partial disconnections
5. **Thread Safety**: All validation and binding operations are thread-safe
6. **Clear Error Messages**: Validation failures provide actionable feedback
7. **Performance Optimized**: Minimal overhead with efficient validation algorithms

The combination of guaranteed bidirectional binding and rigorous state validation makes the Observables library exceptionally robust for building reliable, maintainable reactive applications.
