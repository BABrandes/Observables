# Quick Start Guide

Get up and running with the Observables library in just 5 minutes! This guide covers the essential concepts and patterns you need to build reactive applications with guaranteed bidirectional binding and rigorous state validation.

## 🚀 **Installation**

```bash
pip install observables
```

## 📋 **Basic Imports**

```python
from observables import (
    ObservableSingleValue,
    ObservableSelectionOption,
    ObservableList
)
```

## 🎯 **1. Your First Observable**

Start with the simplest observable - a single value:

```python
# Create an observable value
username = ObservableSingleValue("John")

# Read the value
print(username.single_value)  # "John"

# Change the value
username.single_value = "Alice"
print(username.single_value)  # "Alice"

# Add a listener
def on_username_change():
    print(f"Username changed to: {username.single_value}")

username.add_listener(on_username_change)

# Changes trigger listeners
username.single_value = "Bob"  # Prints: "Username changed to: Bob"
```

## 🔄 **2. Bidirectional Binding**

Connect two observables so changes propagate in both directions:

```python
# Create two observables
primary_name = ObservableSingleValue("Initial")
display_name = ObservableSingleValue("Display")

# Bind them bidirectionally
# The third parameter specifies initial sync mode:
# - "use_caller_value": Use the caller's current value
# - "use_target_value": Use the target's current value
primary_name.attach(
    display_name.single_value_hook, 
    "single_value", 
    "use_caller_value"
)

print(f"After binding:")
print(f"  Primary: {primary_name.single_value}")   # "Initial"
print(f"  Display: {display_name.single_value}")   # "Initial" (updated from primary)

# ✅ Change primary - display updates automatically
primary_name.single_value = "Changed from primary"
print(f"  Primary: {primary_name.single_value}")   # "Changed from primary"
print(f"  Display: {display_name.single_value}")   # "Changed from primary"

# ✅ Change display - primary updates automatically
display_name.single_value = "Changed from display"
print(f"  Primary: {primary_name.single_value}")   # "Changed from display"
print(f"  Display: {display_name.single_value}")   # "Changed from display"
```

**Key Insight**: Once bound, both observables share the same storage. Changes from either side propagate automatically.

## 🛡️ **3. State Validation**

Observables enforce valid states and reject invalid changes:

```python
# Create a selection observable with validation
theme_selector = ObservableSelectionOption("dark", {"dark", "light", "auto"})

print(f"Initial theme: {theme_selector.selected_option}")  # "dark"

# ✅ Valid change
theme_selector.selected_option = "light"
print(f"Changed to: {theme_selector.selected_option}")     # "light"

# ❌ Invalid change - automatically rejected
try:
    theme_selector.selected_option = "rainbow"  # Not in available options
    print("This won't print!")
except ValueError as e:
    print(f"Validation error: {e}")

# State remains valid after rejection
print(f"Still valid: {theme_selector.selected_option}")    # "light"
```

## 🌐 **4. Network Formation**

Build networks of connected observables that sync automatically:

```python
# Create a network of UI components
header_title = ObservableSingleValue("Home")
page_title = ObservableSingleValue("Page")
navigation_title = ObservableSingleValue("Nav")

# Connect them in a chain
header_title.attach(page_title.single_value_hook, "single_value", "use_caller_value")
page_title.attach(navigation_title.single_value_hook, "single_value", "use_caller_value")

# 🎯 Change the header - all others update automatically
header_title.single_value = "Dashboard"
print(f"Header: {header_title.single_value}")        # "Dashboard"
print(f"Page: {page_title.single_value}")            # "Dashboard"  
print(f"Navigation: {navigation_title.single_value}") # "Dashboard"

# 🎯 Change navigation - all others update automatically  
navigation_title.single_value = "Settings"
print(f"Header: {header_title.single_value}")        # "Settings"
print(f"Page: {page_title.single_value}")            # "Settings"
print(f"Navigation: {navigation_title.single_value}") # "Settings"
```

## 📝 **5. Real-World Example: User Profile Form**

Let's build a practical form with validation:

```python
class UserProfileForm:
    def __init__(self):
        # Form fields
        self.name = ObservableSingleValue("")
        self.email = ObservableSingleValue("")
        self.role = ObservableSelectionOption("user", {"user", "admin", "moderator"})
        
        # Display fields (bound to form fields)
        self.display_name = ObservableSingleValue("")
        self.header_email = ObservableSingleValue("")
        
        # Validation state
        self.is_valid = ObservableSingleValue(False)
        
        # Bind form fields to display fields
        self.name.attach(self.display_name.single_value_hook, "single_value", "use_caller_value")
        self.email.attach(self.header_email.single_value_hook, "single_value", "use_caller_value")
        
        # Add validation listeners
        self.name.add_listener(self._validate)
        self.email.add_listener(self._validate)
        self.role.add_listener(self._validate)
    
    def _validate(self):
        """Validate the form."""
        name_valid = len(self.name.single_value) >= 2
        email_valid = "@" in self.email.single_value
        role_valid = self.role.selected_option in {"user", "admin", "moderator"}
        
        self.is_valid.single_value = name_valid and email_valid and role_valid
    
    def print_status(self):
        """Print current form status."""
        print(f"Form Fields:")
        print(f"  Name: '{self.name.single_value}'")
        print(f"  Email: '{self.email.single_value}'")
        print(f"  Role: '{self.role.selected_option}'")
        print(f"Display Fields (auto-synced):")
        print(f"  Display Name: '{self.display_name.single_value}'")
        print(f"  Header Email: '{self.header_email.single_value}'")
        print(f"Valid: {self.is_valid.single_value}")
        print()

# Create and test the form
form = UserProfileForm()

print("Initial state:")
form.print_status()

print("Filling out form...")
form.name.single_value = "Alice Johnson"
form.print_status()

form.email.single_value = "alice@example.com"
form.print_status()

form.role.selected_option = "admin"
form.print_status()

print("Testing invalid role...")
try:
    form.role.selected_option = "superuser"  # Not in available options
except ValueError as e:
    print(f"Validation prevented invalid role: {e}")
    
form.print_status()
```

## 🔧 **6. Atomic Multi-Component Binding**

When working with observables that have multiple dependent components (like selection options), use `connect_multiple` for atomic binding:

```python
from observables import ObservableSelectionOption

# Create two selection observables with different setups
user_preferences = ObservableSelectionOption("dark", {"dark", "light", "auto"})
display_settings = ObservableSelectionOption("blue", {"blue", "red", "green"})

# ❌ Individual binding might cause validation conflicts
# user_preferences.attach(display_settings.selected_option_hook, "selected_option", "use_target_value")
# user_preferences.attach(display_settings.available_options_hook, "available_options", "use_target_value")

# ✅ Atomic binding prevents validation conflicts
user_preferences.connect_multiple({
    "selected_option": display_settings.selected_option_hook,
    "available_options": display_settings.available_options_hook
}, "use_target_value")

print(f"User preferences now has:")
print(f"  Selected: {user_preferences.selected_option}")      # "blue"
print(f"  Available: {user_preferences.available_options}")   # {"blue", "red", "green"}

# Changes propagate bidirectionally
user_preferences.selected_option = "red"
print(f"Display settings updated: {display_settings.selected_option}")  # "red"
```

**Why Use connect_multiple:**
- **Prevents validation errors** during binding
- **Atomic operation** - all components update together
- **Better performance** than sequential binding

## 🔧 **7. Essential Patterns**

### **Pattern 1: Conditional Binding**

```python
# Create observables for different modes
simple_mode = ObservableSingleValue("Simple")
advanced_mode = ObservableSingleValue("Advanced")
display = ObservableSingleValue("Current")

# Switch between modes conditionally
use_advanced = True

if use_advanced:
    advanced_mode.attach(display.single_value_hook, "single_value", "use_caller_value")
else:
    simple_mode.attach(display.single_value_hook, "single_value", "use_caller_value")

print(f"Display shows: {display.single_value}")  # "Advanced"
```

### **Pattern 2: Atomic Multi-Component Updates**

```python
# Update multiple related components atomically
product_selector = ObservableSelectionOption("laptop", {"laptop", "phone", "tablet"})

# ✅ Valid atomic update - both selection and options change together
product_selector.set_selected_option_and_available_options(
    "smartwatch", 
    {"smartwatch", "laptop", "headphones"}
)

print(f"Selected: {product_selector.selected_option}")      # "smartwatch"
print(f"Available: {product_selector.available_options}")   # {"smartwatch", "laptop", "headphones"}
```

### **Pattern 3: Network Disconnection**

```python
# Create connected observables
obs1 = ObservableSingleValue("Connected")
obs2 = ObservableSingleValue("Connected")
obs3 = ObservableSingleValue("Connected")

# Connect them
obs1.attach(obs2.single_value_hook, "single_value", "use_caller_value")
obs2.attach(obs3.single_value_hook, "single_value", "use_caller_value")

# Disconnect the middle one
obs2.detach()

# obs1 and obs3 remain connected!
obs1.single_value = "Updated"
print(f"obs1: {obs1.single_value}")  # "Updated"
print(f"obs2: {obs2.single_value}")  # "Connected" (isolated)
print(f"obs3: {obs3.single_value}")  # "Updated" (still connected to obs1)
```

## 🎯 **7. Quick Reference**

### **Observable Types**
- `ObservableSingleValue[T]` - Single values
- `ObservableSelectionOption[T]` - Single selection from options
- `ObservableList[T]` - Lists with item-level operations
- `ObservableDict[K, V]` - Dictionaries
- `ObservableSet[T]` - Sets

### **Binding Methods**
- `attach(hook, component_name, sync_mode)` - Bind to another observable
- `connect_multiple(hook_dict, sync_mode)` - Atomically bind multiple components
- `detach()` - Disconnect from all bindings
- `is_attached_to(other)` - Check if bound to another observable

### **Initial Sync Modes**

When binding observables, you specify which value to use for the initial synchronization using string literals:

- `"use_caller_value"` - Use the caller's current value for initial synchronization. After binding, the target observable will adopt the caller's value.
- `"use_target_value"` - Use the target's current value for initial synchronization. After binding, the caller observable will adopt the target's value.

Example:
```python
source = ObservableSingleValue(10)
target = ObservableSingleValue(20)

# Using "use_caller_value": target becomes 10
source.attach(target.single_value_hook, "single_value", "use_caller_value")

# Using "use_target_value": source would become 20
# source.attach(target.single_value_hook, "single_value", "use_target_value")
```

### **Common Hooks**
- `single_value_hook` - For single values
- `selected_option_hook` - For selection option
- `available_options_hook` - For available options
- `list_value_hook` - For entire lists

## 🚀 **Next Steps**

You now know the fundamentals! Ready to dive deeper?

1. **[Tutorial](tutorial.md)** - Comprehensive step-by-step guide
2. **[API Reference](api_reference.md)** - Complete API documentation
3. **[Bidirectional Binding Deep Dive](bidirectional_binding_and_validation.md)** - Advanced concepts
4. **[Examples and Use Cases](examples_and_use_cases.md)** - Real-world applications

## 💡 **Key Takeaways**

- **Bidirectional Binding**: Changes propagate in both directions automatically
- **State Validation**: Invalid states are rejected immediately
- **Network Formation**: Complex networks form automatically through transitive binding
- **Shared Storage**: Bound observables share the same underlying storage (HookNexus)
- **Memory Efficient**: Values are stored once, referenced multiple times

Start building reactive applications with guaranteed consistency and automatic synchronization! 🚀
