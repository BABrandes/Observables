# Examples and Use Cases

This document provides comprehensive examples and real-world use cases for the Observables library, demonstrating the power of the transitive binding system and hook "bus" architecture.

## 🎯 Real-World Scenarios

### 1. Configuration Management System

A configuration system where multiple components need to stay synchronized:

```python
from observables import ObservableDict, ObservableSingleValue
from typing import Dict, Any

class ConfigurationManager:
    def __init__(self):
        # Main configuration
        self.main_config = ObservableDict({
            "theme": "dark",
            "language": "en",
            "timezone": "UTC"
        })
        
        # UI configuration (bound to main)
        self.ui_config = ObservableDict({
            "theme": "dark",
            "language": "en"
        })
        
        # API configuration (bound to main)
        self.api_config = ObservableDict({
            "language": "en",
            "timezone": "UTC"
        })
        
        # Bind configurations together
        self.ui_config.bind_to(self.main_config)
        self.api_config.bind_to(self.main_config)
        
        # Add listeners for logging
        self.main_config.add_listeners(self._log_config_change)
    
    def _log_config_change(self):
        print(f"Configuration changed: {self.main_config.dict}")
    
    def update_theme(self, theme: str):
        """Update theme across all configurations."""
        self.main_config["theme"] = theme
        # UI and API configs automatically update due to transitive binding!

# Usage
config_manager = ConfigurationManager()

# Change theme - all configs update automatically
config_manager.update_theme("light")
# Result: main_config["theme"] = "light"
#         ui_config["theme"] = "light"  
#         api_config["theme"] = "light" (if theme was in api_config)
```

### 2. Multi-Component GUI Application

A GUI application with multiple views that need to stay synchronized:

```python
from observables import ObservableSingleValue, ObservableList
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    age: int

class UserProfileView:
    def __init__(self):
        self.name_field = ObservableSingleValue("")
        self.email_field = ObservableSingleValue("")
        self.age_field = ObservableSingleValue(0)
        
        # Bind all fields together
        self.name_field.bind_to(self.email_field)
        self.email_field.bind_to(self.age_field)
        
        # Add listeners for UI updates
        self.name_field.add_listeners(self._update_name_display)
        self.email_field.add_listeners(self._update_email_display)
        self.age_field.add_listeners(self._update_age_display)
    
    def _update_name_display(self):
        print(f"Name display updated: {self.name_field.single_value}")
    
    def _update_email_display(self):
        print(f"Email display updated: {self.email_field.single_value}")
    
    def _update_age_display(self):
        print(f"Age display updated: {self.age_field.single_value}")
    
    def load_user(self, user: User):
        """Load user data - all fields update automatically."""
        self.name_field.single_value = user.name
        # Due to transitive binding, email and age also update!

class UserListViewModel:
    def __init__(self):
        self.users = ObservableList([])
        self.selected_user = ObservableSingleValue(None)
        
        # Bind to profile view
        self.profile_view = UserProfileView()
        self.selected_user.bind_to(self.profile_view.name_field)
    
    def select_user(self, user: User):
        """Select a user - profile view updates automatically."""
        self.selected_user.single_value = user
        # Profile view automatically loads user data!

# Usage
view_model = UserListViewModel()
user = User("John Doe", "john@example.com", 30)

# Select user - all views update automatically
view_model.select_user(user)
# Result: profile view displays John Doe's information
```

### 3. Data Pipeline with Multiple Stages

A data processing pipeline where each stage needs to stay synchronized:

```python
from observables import ObservableSingleValue, ObservableList
from typing import List, Dict, Any

class DataPipeline:
    def __init__(self):
        # Raw data
        self.raw_data = ObservableList([])
        
        # Processed data
        self.processed_data = ObservableList([])
        
        # Filtered data
        self.filtered_data = ObservableList([])
        
        # Final results
        self.results = ObservableList([])
        
        # Bind pipeline stages together
        self.raw_data.bind_to(self.processed_data)
        self.processed_data.bind_to(self.filtered_data)
        self.filtered_data.bind_to(self.results)
        
        # Add processing listeners
        self.raw_data.add_listeners(self._process_data)
        self.processed_data.add_listeners(self._filter_data)
        self.filtered_data.add_listeners(self._generate_results)
    
    def _process_data(self):
        """Process raw data."""
        raw = self.raw_data.list
        processed = [item.upper() for item in raw if isinstance(item, str)]
        self.processed_data.list_value = processed
    
    def _filter_data(self):
        """Filter processed data."""
        processed = self.processed_data.list
        filtered = [item for item in processed if len(item) > 3]
        self.filtered_data.list_value = filtered
    
    def _generate_results(self):
        """Generate final results."""
        filtered = self.filtered_data.list
        results = [f"Result: {item}" for item in filtered]
        self.results.list_value = results
    
    def add_data(self, data: List[str]):
        """Add new data to the pipeline."""
        self.raw_data.list_value = data
        # All stages automatically process the data!

# Usage
pipeline = DataPipeline()

# Add data - entire pipeline processes automatically
pipeline.add_data(["hello", "world", "python"])
# Result: raw_data = ["hello", "world", "python"]
#         processed_data = ["HELLO", "WORLD", "PYTHON"]
#         filtered_data = ["HELLO", "WORLD", "PYTHON"]
#         results = ["Result: HELLO", "Result: WORLD", "Result: PYTHON"]
```

### 4. Form Validation with Cross-Field Dependencies

A form system where field validation depends on other fields:

```python
from observables import ObservableSingleValue, ObservableSelectionOption
from typing import Dict, List, Callable

class FormValidator:
    def __init__(self):
        self.errors = ObservableDict({})
        self.is_valid = ObservableSingleValue(False)
        
        # Bind validation state
        self.errors.add_listeners(self._update_validity)
    
    def _update_validity(self):
        """Update validity based on error count."""
        self.is_valid.single_value = len(self.errors.dict) == 0

class UserForm:
    def __init__(self):
        # Form fields
        self.username = ObservableSingleValue("")
        self.email = ObservableSingleValue("")
        self.password = ObservableSingleValue("")
        self.confirm_password = ObservableSingleValue("")
        self.country = ObservableSelectionOption("US", {"US", "CA", "UK"})
        self.state = ObservableSingleValue("")
        
        # Validator
        self.validator = FormValidator()
        
        # Bind fields for validation
        self.username.add_listeners(self._validate_username)
        self.email.add_listeners(self._validate_email)
        self.password.add_listeners(self._validate_password)
        self.confirm_password.add_listeners(self._validate_password_confirmation)
        self.country.add_listeners(self._validate_state)
        self.state.add_listeners(self._validate_state)
        
        # Bind password fields together
        self.password.bind_to(self.confirm_password)
        
        # Bind validation results
        self.validator.is_valid.add_listeners(self._on_validation_change)
    
    def _validate_username(self):
        """Validate username field."""
        username = self.username.single_value
        if len(username) < 3:
            self.validator.errors["username"] = "Username must be at least 3 characters"
        elif "username" in self.validator.errors.dict:
            del self.validator.errors.dict["username"]
    
    def _validate_email(self):
        """Validate email field."""
        email = self.email.single_value
        if "@" not in email:
            self.validator.errors["email"] = "Invalid email format"
        elif "email" in self.validator.errors.dict:
            del self.validator.errors.dict["email"]
    
    def _validate_password(self):
        """Validate password field."""
        password = self.password.single_value
        if len(password) < 8:
            self.validator.errors["password"] = "Password must be at least 8 characters"
        elif "password" in self.validator.errors.dict:
            del self.validator.errors.dict["password"]
    
    def _validate_password_confirmation(self):
        """Validate password confirmation."""
        password = self.password.single_value
        confirm = self.confirm_password.single_value
        if password != confirm:
            self.validator.errors["password_confirmation"] = "Passwords do not match"
        elif "password_confirmation" in self.validator.errors.dict:
            del self.validator.errors.dict["password_confirmation"]
    
    def _validate_state(self):
        """Validate state based on country."""
        country = self.country.selected_option
        state = self.state.single_value
        
        if country == "US" and not state:
            self.validator.errors["state"] = "State is required for US"
        elif country == "CA" and not state:
            self.validator.errors["state"] = "Province is required for Canada"
        elif "state" in self.validator.errors.dict:
            del self.validator.errors.dict["state"]
    
    def _on_validation_change(self):
        """Handle validation state changes."""
        if self.validator.is_valid.single_value:
            print("✅ Form is valid!")
        else:
            print(f"❌ Form has {len(self.validator.errors.dict)} errors:")
            for field, error in self.validator.errors.dict.items():
                print(f"  - {field}: {error}")

# Usage
form = UserForm()

# Fill out form - validation happens automatically
form.username.single_value = "john"
form.email.single_value = "john@example.com"
form.password.single_value = "password123"
form.country.selected_option = "US"
form.state.single_value = "CA"

# Form automatically validates and shows results
```

### 5. State Management for Web Application

A state management system similar to Redux or Vuex:

```python
from observables import ObservableDict, ObservableSingleValue
from typing import Dict, Any, List, Callable

class Store:
    def __init__(self):
        self.state = ObservableDict({})
        self.subscribers: List[Callable] = []
        
        # Bind state changes to subscribers
        self.state.add_listeners(self._notify_subscribers)
    
    def _notify_subscribers(self):
        """Notify all subscribers of state changes."""
        for subscriber in self.subscribers:
            subscriber(self.state.dict)
    
    def subscribe(self, callback: Callable):
        """Subscribe to state changes."""
        self.subscribers.append(callback)
    
    def dispatch(self, action: str, payload: Any):
        """Dispatch an action to update state."""
        if action == "SET_USER":
            self.state["user"] = payload
        elif action == "SET_THEME":
            self.state["theme"] = payload
        elif action == "ADD_TODO":
            if "todos" not in self.state.dict:
                self.state["todos"] = []
            self.state["todos"].append(payload)

class UserComponent:
    def __init__(self, store: Store):
        self.store = store
        self.user_display = ObservableSingleValue("")
        
        # Bind to store state
        self.store.subscribe(self._on_state_change)
    
    def _on_state_change(self, state: Dict[str, Any]):
        """Handle state changes."""
        if "user" in state:
            user = state["user"]
            self.user_display.single_value = f"Welcome, {user['name']}!"

class ThemeComponent:
    def __init__(self, store: Store):
        self.store = store
        self.theme_display = ObservableSingleValue("")
        
        # Bind to store state
        self.store.subscribe(self._on_state_change)
    
    def _on_state_change(self, state: Dict[str, Any]):
        """Handle state changes."""
        if "theme" in state:
            theme = state["theme"]
            self.theme_display.single_value = f"Current theme: {theme}"

class TodoComponent:
    def __init__(self, store: Store):
        self.store = store
        self.todo_list = ObservableSingleValue([])
        
        # Bind to store state
        self.store.subscribe(self._on_state_change)
    
    def _on_state_change(self, state: Dict[str, Any]):
        """Handle state changes."""
        if "todos" in state:
            todos = state["todos"]
            self.todo_list.single_value = todos

# Usage
store = Store()

# Create components
user_component = UserComponent(store)
theme_component = ThemeComponent(store)
todo_component = TodoComponent(store)

# Dispatch actions - all components update automatically
store.dispatch("SET_USER", {"name": "John Doe", "email": "john@example.com"})
store.dispatch("SET_THEME", "dark")
store.dispatch("ADD_TODO", {"id": 1, "text": "Learn Observables", "completed": False})

# All components automatically reflect the new state
```

## 🔧 Advanced Patterns

### 1. Conditional Binding

Binding observables based on runtime conditions:

```python
from observables import ObservableSingleValue, ObservableSelectionOption

class ConditionalBindingExample:
    def __init__(self):
        self.mode = ObservableSelectionOption("simple", {"simple", "advanced"})
        self.simple_value = ObservableSingleValue(10)
        self.advanced_value = ObservableSingleValue(100)
        self.display_value = ObservableSingleValue(10)
        
        # Bind based on mode
        self.mode.add_listeners(self._update_binding)
        self._update_binding()
    
    def _update_binding(self):
        """Update binding based on current mode."""
        if self.mode.selected_option == "simple":
            # Bind to simple value
            self.simple_value.bind_to(self.display_value)
        else:
            # Bind to advanced value
            self.advanced_value.bind_to(self.display_value)
```

### 2. Binding Chains with Validation

Creating binding chains with validation at each step:

```python
from observables import ObservableSingleValue

class ValidationChain:
    def __init__(self):
        self.input_value = ObservableSingleValue(0)
        self.validated_value = ObservableSingleValue(0)
        self.processed_value = ObservableSingleValue(0)
        self.final_value = ObservableSingleValue(0)
        
        # Create validation chain
        self.input_value.add_listeners(self._validate_input)
        self.validated_value.add_listeners(self._process_value)
        self.processed_value.add_listeners(self._finalize_value)
    
    def _validate_input(self):
        """Validate input value."""
        value = self.input_value.single_value
        if isinstance(value, (int, float)) and value >= 0:
            self.validated_value.single_value = value
        else:
            self.validated_value.single_value = 0
    
    def _process_value(self):
        """Process validated value."""
        value = self.validated_value.single_value
        self.processed_value.single_value = value * 2
    
    def _finalize_value(self):
        """Finalize processed value."""
        value = self.processed_value.single_value
        self.final_value.single_value = f"Result: {value}"

# Usage
chain = ValidationChain()
chain.input_value.single_value = 5
# Result: input_value = 5
#         validated_value = 5
#         processed_value = 10
#         final_value = "Result: 10"
```

### 3. Bidirectional Binding with Transformations

Bidirectional binding with value transformations:

```python
from observables import ObservableSingleValue

class TransformBinding:
    def __init__(self):
        self.celsius = ObservableSingleValue(0)
        self.fahrenheit = ObservableSingleValue(32)
        
        # Bind with transformations
        self.celsius.add_listeners(self._celsius_to_fahrenheit)
        self.fahrenheit.add_listeners(self._fahrenheit_to_celsius)
    
    def _celsius_to_fahrenheit(self):
        """Convert Celsius to Fahrenheit."""
        c = self.celsius.single_value
        f = (c * 9/5) + 32
        self.fahrenheit.single_value = f
    
    def _fahrenheit_to_celsius(self):
        """Convert Fahrenheit to Celsius."""
        f = self.fahrenheit.single_value
        c = (f - 32) * 5/9
        self.celsius.single_value = c

# Usage
temp_converter = TransformBinding()

# Set Celsius - Fahrenheit updates automatically
temp_converter.celsius.single_value = 25
print(temp_converter.fahrenheit.single_value)  # 77.0

# Set Fahrenheit - Celsius updates automatically
temp_converter.fahrenheit.single_value = 98.6
print(temp_converter.celsius.single_value)  # 37.0
```

## 🚀 Performance Tips

### 1. Batch Updates

Group multiple changes together to minimize notifications:

```python
# Instead of:
obs1.single_value = 1
obs2.single_value = 2
obs3.single_value = 3

# Use batch operations when possible:
with obs1.batch_update():
    obs1.single_value = 1
    obs2.single_value = 2
    obs3.single_value = 3
```

### 2. Selective Binding

Only bind observables that actually need to be synchronized:

```python
# Don't bind everything together unnecessarily
# Only bind observables that represent the same logical data
```

### 3. Efficient Listeners

Keep listeners lightweight and efficient:

```python
# Good: Lightweight listener
def on_change():
    self.update_display()

# Avoid: Heavy operations in listeners
def on_change():
    self.heavy_database_operation()  # This runs on every change!
```

## 🧪 Testing Patterns

### 1. Testing Transitive Binding

```python
def test_transitive_binding():
    obs1 = ObservableSingleValue(10)
    obs2 = ObservableSingleValue(20)
    obs3 = ObservableSingleValue(30)
    
    # Build chain
    obs1.bind_to(obs2)
    obs2.bind_to(obs3)
    
    # Test transitive binding
    obs1.single_value = 100
    assert obs2.single_value == 100
    assert obs3.single_value == 100
    
    # Test reverse propagation
    obs3.single_value = 200
    assert obs1.single_value == 200
    assert obs2.single_value == 200
```

### 2. Testing Disconnection

```python
def test_disconnection_behavior():
    obs1 = ObservableSingleValue(10)
    obs2 = ObservableSingleValue(20)
    obs3 = ObservableSingleValue(30)
    
    # Build chain
    obs1.bind_to(obs2)
    obs2.bind_to(obs3)
    
    # Disconnect middle
    obs2.disconnect()
    
    # Test isolation
    obs1.single_value = 100
    assert obs2.single_value == 20  # Isolated
    assert obs3.single_value == 100  # Still bound to obs1
```

These examples demonstrate the power and flexibility of the Observables library's transitive binding system and hook "bus" architecture. The system automatically handles complex synchronization scenarios while maintaining clean, maintainable code.
