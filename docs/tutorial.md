# Observables Tutorial: Mastering Bidirectional Linking and State Validation

This tutorial will guide you through the core concepts of the Observables library, with hands-on examples demonstrating bidirectional linking and rigorous state validation.

## 🚀 **Getting Started**

### **Installation**

```bash
pip install observables
```

### **Basic Import**

```python
from observables import (
    ObservableSingleValue,
    ObservableSelectionOption
)
```

## 📚 **Chapter 1: Understanding Bidirectional Linking**

### **What is Bidirectional Linking?**

Unlike traditional reactive libraries where data flows in one direction, Observables provides **true bidirectional linking**. When two observables are linked together, they share the same underlying storage, ensuring changes propagate in both directions automatically.

### **Your First Bidirectional Linking**

```python
# Create two observables with different values
temperature_celsius = ObservableSingleValue(25.0)
temperature_fahrenheit = ObservableSingleValue(77.0)

print("Before linking:")
print(f"Celsius: {temperature_celsius.value}")       # 25.0
print(f"Fahrenheit: {temperature_fahrenheit.value}") # 77.0

# Join them together - celsius pushes its value to fahrenheit
# Using "use_caller_value" means the caller's value (celsius) takes precedence
temperature_celsius.join(
    temperature_fahrenheit.hook, 
    "value", 
    "use_caller_value"
)

print("\nAfter linking:")
print(f"Celsius: {temperature_celsius.value}")       # 25.0
print(f"Fahrenheit: {temperature_fahrenheit.value}") # 25.0 (now shares same value)

# 🔄 Change from celsius - fahrenheit updates automatically
temperature_celsius.value = 30.0
print("\nAfter changing celsius:")
print(f"Celsius: {temperature_celsius.value}")       # 30.0
print(f"Fahrenheit: {temperature_fahrenheit.value}") # 30.0

# 🔄 Change from fahrenheit - celsius updates automatically
temperature_fahrenheit.value = 100.0
print("\nAfter changing fahrenheit:")
print(f"Celsius: {temperature_celsius.value}")       # 100.0
print(f"Fahrenheit: {temperature_fahrenheit.value}") # 100.0
```

**Key Insight**: Once bound, both observables share the same storage. Changes from either side propagate to the other automatically.

### **Understanding Initial Sync Modes**

The initial sync mode determines which value takes precedence when observables are first bound. This is specified using string literals:

- **`"use_caller_value"`**: The caller's current value overwrites the target's value
- **`"use_target_value"`**: The target's current value overwrites the caller's value

```python
# Create observables with different values
obs1 = XValue("Hello")
obs2 = XValue("World")

# Using "use_caller_value": obs1's value overwrites obs2's value
obs1.join(obs2.hook, "value", "use_caller_value")
print(f"After use_caller_value: obs1='{obs1.value}', obs2='{obs2.value}'")
# Output: obs1='Hello', obs2='Hello'

# Reset for next example
obs1.isolate()
obs1.value = "Hello"
obs2.value = "World"

# Using "use_target_value": obs1 takes obs2's value
obs1.join(obs2.hook, "value", "use_target_value")
print(f"After use_target_value: obs1='{obs1.value}', obs2='{obs2.value}'")
# Output: obs1='World', obs2='World'
```

After the initial linking, both modes result in true bidirectional synchronization. The mode only determines which value is used at the moment of linking.

### **Exercise 1: Create Your First Linking**

Try creating a simple linking between two observables:

```python
# 🎯 Exercise: Create two observables and link them
# 1. Create a username observable with your name
# 2. Create a display_name observable with a placeholder
# 3. Link them so username pushes to display_name
# 4. Change the username and observe both values

# Your code here:
username = XValue("Your Name")
display_name = XValue("Placeholder")

# Join username to display_name
username.join(display_name.hook, "value", "use_caller_value")

# Test bidirectional linking
print(f"Username: {username.value}")
print(f"Display: {display_name.value}")

username.value = "Alice"
print(f"After username change - Username: {username.value}, Display: {display_name.value}")

display_name.value = "Bob"
print(f"After display change - Username: {username.value}, Display: {display_name.value}")
```

## 📚 **Chapter 2: The Nexus - Central Storage System**

### **Understanding Shared Storage**

The secret to bidirectional joining is the **Nexus** - a central storage system where values live:

```python
# Create observables - each starts with its own Nexus
obs1 = ObservableSingleValue(10)
obs2 = ObservableSingleValue(20)

print("Before linking - separate storage:")
print(f"obs1 Nexus ID: {id(obs1._component_hooks['single_value'].nexus)}")
print(f"obs2 Nexus ID: {id(obs2._component_hooks['single_value'].nexus)}")
# Different IDs = separate storage

# Bind them together
obs1.join(obs2.hook, "value", "use_caller_value")

print("\nAfter linking - shared storage:")
print(f"obs1 Nexus ID: {id(obs1._component_hooks['single_value'].nexus)}")
print(f"obs2 Nexus ID: {id(obs2._component_hooks['single_value'].nexus)}")
# Same ID = shared storage! This is why joining is bidirectional.

# Verify they share the same value
print(f"obs1 value: {obs1.value}")  # 10
print(f"obs2 value: {obs2.value}")  # 10

# Changes propagate because they access the same storage
obs1.value = 100
print(f"After obs1 change: obs1={obs1.value}, obs2={obs2.value}")
```

### **Transitive Joining Networks**

When you join A→B and B→C, A automatically connects to C:

```python
# Create a chain of observables
user_name = XValue("John")
header_display = XValue("Header")
sidebar_display = XValue("Sidebar")
footer_display = XValue("Footer")

print("Before linking - all separate:")
for name, obs in [("user", user_name), ("header", header_display), 
                  ("sidebar", sidebar_display), ("footer", footer_display)]:
    hook_id = id(obs._component_hooks['single_value'].nexus)
    print(f"{name}: {obs.value} (Nexus: {hook_id})")

# Create joining chain: user → header → sidebar → footer
user_name.join(header_display.hook, "value", "use_caller_value")
header_display.join(sidebar_display.hook, "value", "use_caller_value")
sidebar_display.join(footer_display.hook, "value", "use_caller_value")

print("\nAfter chaining - all connected:")
for name, obs in [("user", user_name), ("header", header_display), 
                  ("sidebar", sidebar_display), ("footer", footer_display)]:
    hook_id = id(obs._component_hooks['single_value'].nexus)
    print(f"{name}: {obs.value} (Nexus: {hook_id})")

# 🎯 Change from ANY observable - ALL others update
user_name.value = "Alice"
print(f"\nAfter user_name change:")
print(f"  user_name: {user_name.value}")
print(f"  header_display: {header_display.value}")
print(f"  sidebar_display: {sidebar_display.value}")
print(f"  footer_display: {footer_display.value}")

# 🎯 Change from the END of the chain - propagates to ALL
footer_display.value = "Bob"
print(f"\nAfter footer_display change:")
print(f"  user_name: {user_name.value}")
print(f"  header_display: {header_display.value}")
print(f"  sidebar_display: {sidebar_display.value}")
print(f"  footer_display: {footer_display.value}")
```

### **Exercise 2: Build a Joining Network**

```python
# 🎯 Exercise: Create a 4-observable network
# 1. Create observables for: input_field, validation_display, save_button_text, status_message
# 2. Join them in a chain
# 3. Change the input_field and verify all others update
# 4. Change status_message and verify all others update

# Your code here:
input_field = XValue("")
validation_display = XValue("")
save_button_text = XValue("")
status_message = XValue("")

# Build the joining chain
input_field.join(validation_display.hook, "value", "use_caller_value")
validation_display.join(save_button_text.hook, "value", "use_caller_value")
save_button_text.join(status_message.hook, "value", "use_caller_value")

# Test the network
input_field.value = "user@example.com"
print("All observables after input change:")
print(f"  Input: {input_field.value}")
print(f"  Validation: {validation_display.value}")
print(f"  Button: {save_button_text.value}")
print(f"  Status: {status_message.value}")
```

## 📚 **Chapter 3: Rigorous State Validation**

### **Why Validation Matters**

The Observables library **never allows invalid states**. This prevents bugs, data corruption, and ensures your application remains in a consistent state.

### **Selection Option Validation**

Let's explore validation with `ObservableSelectionOption`:

```python
# Create a color selector with specific available options
color_selector = ObservableSelectionOption("red", {"red", "green", "blue"})

print(f"Initial state:")
print(f"  Selected: {color_selector.selected_option}")
print(f"  Available: {color_selector.available_options}")

# ✅ Valid change - "green" is in available options
color_selector.selected_option = "green"
print(f"\nAfter valid change:")
print(f"  Selected: {color_selector.selected_option}")

# ❌ Invalid change - "purple" is not in available options
try:
    color_selector.selected_option = "purple"
    print("ERROR: This should not print!")
except ValueError as e:
    print(f"\n❌ Validation caught invalid change: {e}")

# State remains valid after rejected change
print(f"State after rejected change:")
print(f"  Selected: {color_selector.selected_option}")  # Still "green"
print(f"  Available: {color_selector.available_options}")
```

### **Atomic Multi-Component Updates**

For complex observables, all components are validated together:

```python
# Create a product selector
product_selector = ObservableSelectionOption("laptop", {"laptop", "phone", "tablet"})

print(f"Initial product state:")
print(f"  Selected: {product_selector.selected_option}")
print(f"  Available: {product_selector.available_options}")

# ✅ Valid atomic update - selected option is in new available options
product_selector.set_selected_option_and_available_options(
    "smartwatch", 
    {"smartwatch", "laptop", "phone"}  # smartwatch is included
)
print(f"\nAfter valid atomic update:")
print(f"  Selected: {product_selector.selected_option}")
print(f"  Available: {product_selector.available_options}")

# ❌ Invalid atomic update - selected option not in new available options
try:
    product_selector.set_selected_option_and_available_options(
        "laptop",  # laptop would be valid...
        {"smartwatch", "phone"}  # ...but it's not in these new options
    )
    print("ERROR: This should not print!")
except ValueError as e:
    print(f"\n❌ Atomic validation caught invalid update: {e}")

# State remains consistent after rejected atomic update
print(f"State after rejected atomic update:")
print(f"  Selected: {product_selector.selected_option}")  # Still "smartwatch"
print(f"  Available: {product_selector.available_options}")  # Still includes smartwatch
```

### **Validation During Joining**

Validation is enforced even when joining observables:

```python
# Create compatible observables
theme1 = ObservableSelectionOption("dark", {"dark", "light", "auto"})
theme2 = ObservableSelectionOption("light", {"light", "dark"})

print("Before linking:")
print(f"  theme1: {theme1.selected_option} from {theme1.available_options}")
print(f"  theme2: {theme2.selected_option} from {theme2.available_options}")

# ✅ Joining succeeds - both have "dark" as an option
theme1.join(theme2.selected_option_hook, "selected_option", "use_caller_value")

print("\nAfter successful joining:")
print(f"  theme1: {theme1.selected_option}")
print(f"  theme2: {theme2.selected_option}")  # Now "dark" (from theme1)

# Create incompatible observable
incompatible_theme = ObservableSelectionOption("high_contrast", {"high_contrast", "colorblind"})

# ❌ Joining fails - "high_contrast" is not available in theme1's options
try:
    theme1.join(incompatible_theme.selected_option_hook, "selected_option", "use_target_value")
    print("ERROR: This should not print!")
except ValueError as e:
    print(f"\n❌ Joining validation failed: {e}")

# Original joining remains intact
print(f"Original joining still works:")
print(f"  theme1: {theme1.selected_option}")
print(f"  theme2: {theme2.selected_option}")
```

### **Exercise 3: Validation in Action**

```python
# 🎯 Exercise: Test validation with different scenarios
# 1. Create a payment method selector with ["credit_card", "debit_card", "paypal"]
# 2. Try valid and invalid selections
# 3. Use atomic updates to change both selection and options
# 4. Create a second selector and test joining validation

# Your code here:
payment_method = ObservableSelectionOption("credit_card", {"credit_card", "debit_card", "paypal"})

# Test valid change
print(f"Initial: {payment_method.selected_option}")
payment_method.selected_option = "paypal"
print(f"After valid change: {payment_method.selected_option}")

# Test invalid change
try:
    payment_method.selected_option = "bitcoin"
except ValueError as e:
    print(f"Invalid change caught: {e}")

# Test atomic update
payment_method.set_selected_option_and_available_options("bank_transfer", {"bank_transfer", "credit_card"})
print(f"After atomic update: {payment_method.selected_option}")

# Test joining validation
another_payment = ObservableSelectionOption("cash", {"cash", "check"})
try:
    payment_method.join(another_payment.selected_option_hook, "selected_option", "use_target_value")
except ValueError as e:
    print(f"Joining validation failed: {e}")
```

## 📚 **Chapter 4: Network Management and Disconnection**

### **Understanding Detachment**

When you detach an observable from a network, it gets its own isolated storage:

```python
# Create a network of 4 observables
obs_a = ObservableSingleValue("A")
obs_b = ObservableSingleValue("B")
obs_c = ObservableSingleValue("C")
obs_d = ObservableSingleValue("D")

# Build joining chain: A ↔ B ↔ C ↔ D
obs_a.join(obs_b.hook, "value", "use_caller_value")
obs_b.join(obs_c.hook, "value", "use_caller_value")
obs_c.join(obs_d.hook, "value", "use_caller_value")

print("Network after creation (all share same value):")
for name, obs in [("A", obs_a), ("B", obs_b), ("C", obs_c), ("D", obs_d)]:
    print(f"  {name}: {obs.value}")

# Verify they all share the same Nexus
all_same_nexus = all(
    id(obs._component_hooks['single_value'].nexus) == 
    id(obs_a._component_hooks['single_value'].nexus)
    for obs in [obs_b, obs_c, obs_d]
)
print(f"All share same Nexus: {all_same_nexus}")

# Detach B from the network
obs_b.detach()

print("\nAfter detaching B:")
print(f"  B is isolated: {obs_b.value}")

# Test that A, C, D remain connected
obs_a.value = "Changed"
print(f"After changing A:")
print(f"  A: {obs_a.value}")
print(f"  B: {obs_b.value}")  # Isolated, unchanged
print(f"  C: {obs_c.value}")  # Connected to A
print(f"  D: {obs_d.value}")  # Connected to A

# Verify B is truly isolated
obs_b.value = "B_Isolated"
print(f"\nAfter changing isolated B:")
print(f"  A: {obs_a.value}")  # Unchanged
print(f"  B: {obs_b.value}")  # Changed
print(f"  C: {obs_c.value}")  # Unchanged
print(f"  D: {obs_d.value}")  # Unchanged
```

### **Strategic Network Disconnection**

You can strategically disconnect parts of networks:

```python
# Create a form with multiple sections
user_info = ObservableSingleValue("John Doe")
header_name = ObservableSingleValue("John Doe")
profile_name = ObservableSingleValue("John Doe")
settings_name = ObservableSingleValue("John Doe")

# Join everything initially
user_info.join(header_name.hook, "value", "use_caller_value")
header_name.join(profile_name.hook, "value", "use_caller_value")
profile_name.join(settings_name.hook, "value", "use_caller_value")

print("All joined initially:")
user_info.value = "Alice Smith"
print(f"  User Info: {user_info.value}")
print(f"  Header: {header_name.value}")
print(f"  Profile: {profile_name.value}")
print(f"  Settings: {settings_name.value}")

# Disconnect settings to allow independent editing
settings_name.detach()
settings_name.value = "Custom Display Name"

print("\nAfter disconnecting settings:")
print(f"  User Info: {user_info.value}")
print(f"  Header: {header_name.value}")
print(f"  Profile: {profile_name.value}")
print(f"  Settings: {settings_name.value}")  # Independent

# Changes to main network don't affect settings
user_info.value = "Bob Johnson"
print(f"\nAfter changing user info:")
print(f"  User Info: {user_info.value}")
print(f"  Header: {header_name.value}")
print(f"  Profile: {profile_name.value}")
print(f"  Settings: {settings_name.value}")  # Still independent
```

### **Exercise 4: Network Management**

```python
# 🎯 Exercise: Practice network management
# 1. Create 5 observables for different UI components
# 2. Connect them all in a chain
# 3. Disconnect the middle one
# 4. Verify the ends are still connected
# 5. Reconnect the middle one to one of the ends

# Your code here:
nav_title = ObservableSingleValue("Home")
page_header = ObservableSingleValue("Home")
breadcrumb = ObservableSingleValue("Home")
sidebar_title = ObservableSingleValue("Home")
footer_link = ObservableSingleValue("Home")

# Join all in chain
nav_title.join(page_header.hook, "value", "use_caller_value")
page_header.join(breadcrumb.hook, "value", "use_caller_value")
breadcrumb.join(sidebar_title.hook, "value", "use_caller_value")
sidebar_title.join(footer_link.hook, "value", "use_caller_value")

# Test network
nav_title.value = "Dashboard"
print("All joined:")
print(f"  Nav: {nav_title.value}")
print(f"  Header: {page_header.value}")
print(f"  Breadcrumb: {breadcrumb.value}")
print(f"  Sidebar: {sidebar_title.value}")
print(f"  Footer: {footer_link.value}")

# Disconnect middle (breadcrumb)
breadcrumb.detach()

# Verify ends still connected
nav_title.value = "Profile"
print("\nAfter disconnecting breadcrumb:")
print(f"  Nav: {nav_title.value}")
print(f"  Header: {page_header.value}")
print(f"  Breadcrumb: {breadcrumb.value}")  # Should be unchanged
print(f"  Sidebar: {sidebar_title.value}")  # Should update
print(f"  Footer: {footer_link.value}")     # Should update
```

## 📚 **Chapter 5: Advanced Patterns and Real-World Applications**

### **Form Validation with Cross-Field Dependencies**

Let's build a realistic form validation system:

```python
from observables import ObservableSingleValue, ObservableSelectionOption

class UserRegistrationForm:
    def __init__(self):
        # Form fields
        self.username = ObservableSingleValue("")
        self.email = ObservableSingleValue("")
        self.password = ObservableSingleValue("")
        self.confirm_password = ObservableSingleValue("")
        self.country = ObservableSelectionOption("", {"US", "CA", "UK", "DE"})
        
        # Validation states
        self.is_form_valid = ObservableSingleValue(False)
        self.validation_message = ObservableSingleValue("Please fill out the form")
        
        # Bind password fields for consistency checking
        self.password.add_listener(self._validate_passwords)
        self.confirm_password.add_listener(self._validate_passwords)
        
        # Bind all fields for overall form validation
        self.username.add_listener(self._validate_form)
        self.email.add_listener(self._validate_form)
        self.country.add_listener(self._validate_form)
    
    def _validate_passwords(self):
        """Check password consistency."""
        if self.password.value and self.confirm_password.value:
            if self.password.value != self.confirm_password.value:
                self.validation_message.value = "Passwords do not match"
                self.is_form_valid.value = False
            else:
                self._validate_form()  # Re-check overall form
    
    def _validate_form(self):
        """Validate entire form."""
        # Check all required fields
        if not self.username.value:
            self.validation_message.value = "Username is required"
            self.is_form_valid.value = False
            return
        
        if not self.email.value or "@" not in self.email.value:
            self.validation_message.value = "Valid email is required"
            self.is_form_valid.value = False
            return
        
        if not self.password.value or len(self.password.value) < 8:
            self.validation_message.value = "Password must be at least 8 characters"
            self.is_form_valid.value = False
            return
        
        if not self.country.selected_option:
            self.validation_message.value = "Please select a country"
            self.is_form_valid.value = False
            return
        
        # Check password confirmation
        if self.password.value != self.confirm_password.value:
            self.validation_message.value = "Passwords do not match"
            self.is_form_valid.value = False
            return
        
        # All validations passed
        self.validation_message.value = "Form is valid!"
        self.is_form_valid.value = True

# Usage
form = UserRegistrationForm()

def print_form_status():
    print(f"Valid: {form.is_form_valid.value}")
    print(f"Message: {form.validation_message.value}")
    print()

# Test form validation
print("Initial state:")
print_form_status()

form.username.value = "johndoe"
print("After username:")
print_form_status()

form.email.value = "john@example.com"
print("After email:")
print_form_status()

form.password.value = "secretpassword"
print("After password:")
print_form_status()

form.confirm_password.value = "wrongpassword"
print("After wrong confirm password:")
print_form_status()

form.confirm_password.value = "secretpassword"
print("After correct confirm password:")
print_form_status()

form.country.selected_option = "US"
print("After country selection:")
print_form_status()
```

### **Configuration Management with Environment Validation**

```python
class DatabaseConfig:
    def __init__(self):
        # Environment determines validation rules
        self.environment = ObservableSelectionOption("development", {"development", "staging", "production"})
        
        # Configuration values
        self.host = ObservableSingleValue("localhost")
        self.port = ObservableSingleValue(5432)
        self.ssl_enabled = ObservableSingleValue(False)
        self.pool_size = ObservableSingleValue(5)
        
        # Validation state
        self.config_valid = ObservableSingleValue(True)
        self.validation_errors = ObservableSingleValue([])
        
        # Listen for changes to validate
        self.environment.add_listener(self._validate_config)
        self.host.add_listener(self._validate_config)
        self.ssl_enabled.add_listener(self._validate_config)
        self.pool_size.add_listener(self._validate_config)
    
    def _validate_config(self):
        """Validate configuration based on environment."""
        errors = []
        env = self.environment.selected_option
        
        if env == "production":
            if self.host.value in ["localhost", "127.0.0.1"]:
                errors.append("Production cannot use localhost")
            
            if not self.ssl_enabled.value:
                errors.append("Production requires SSL")
            
            if self.pool_size.value < 10:
                errors.append("Production requires pool size >= 10")
        
        elif env == "staging":
            if self.host.value == "localhost":
                errors.append("Staging should not use localhost")
            
            if self.pool_size.value < 5:
                errors.append("Staging requires pool size >= 5")
        
        # Update validation state
        self.validation_errors.value = errors
        self.config_valid.value = len(errors) == 0
    
    def apply_environment_defaults(self):
        """Apply appropriate defaults for the current environment."""
        env = self.environment.selected_option
        
        if env == "production":
            self.host.value = "prod-db.company.com"
            self.ssl_enabled.value = True
            self.pool_size.value = 20
        elif env == "staging":
            self.host.value = "staging-db.company.com"
            self.ssl_enabled.value = True
            self.pool_size.value = 10
        else:  # development
            self.host.value = "localhost"
            self.ssl_enabled.value = False
            self.pool_size.value = 5

# Usage
config = DatabaseConfig()

def print_config_status():
    print(f"Environment: {config.environment.selected_option}")
    print(f"Host: {config.host.value}")
    print(f"SSL: {config.ssl_enabled.value}")
    print(f"Pool Size: {config.pool_size.value}")
    print(f"Valid: {config.config_valid.value}")
    if config.validation_errors.value:
        print(f"Errors: {config.validation_errors.value}")
    print()

print("Development config:")
config.apply_environment_defaults()
print_config_status()

print("Switching to production:")
config.environment.selected_option = "production"
print_config_status()

print("Applying production defaults:")
config.apply_environment_defaults()
print_config_status()

print("Testing invalid production config:")
config.host.value = "localhost"  # This triggers validation error
print_config_status()
```

### **Exercise 5: Build a Complete Application**

```python
# 🎯 Final Exercise: Build a mini shopping cart application
# 1. Create observables for: selected_product, quantity, price, total
# 2. Create a product catalog with validation
# 3. Implement automatic total calculation
# 4. Add form validation for quantity limits

class ShoppingCart:
    def __init__(self):
        # Product catalog
        self.available_products = {
            "laptop": 999.99,
            "mouse": 29.99,
            "keyboard": 79.99,
            "monitor": 299.99
        }
        
        # Cart state
        self.selected_product = ObservableSelectionOption("laptop", set(self.available_products.keys()))
        self.quantity = ObservableSingleValue(1)
        self.unit_price = ObservableSingleValue(self.available_products["laptop"])
        self.total_price = ObservableSingleValue(self.available_products["laptop"])
        
        # Validation state
        self.is_valid = ObservableSingleValue(True)
        self.error_message = ObservableSingleValue("")
        
        # Bind product selection to price updates
        self.selected_product.add_listener(self._update_price)
        self.quantity.add_listener(self._calculate_total)
        self.unit_price.add_listener(self._calculate_total)
        self.quantity.add_listener(self._validate_quantity)
    
    def _update_price(self):
        """Update unit price when product changes."""
        product = self.selected_product.selected_option
        if product in self.available_products:
            self.unit_price.value = self.available_products[product]
    
    def _calculate_total(self):
        """Calculate total price."""
        if self.is_valid.value:
            total = self.unit_price.value * self.quantity.value
            self.total_price.value = round(total, 2)
    
    def _validate_quantity(self):
        """Validate quantity limits."""
        qty = self.quantity.value
        
        if qty <= 0:
            self.error_message.value = "Quantity must be positive"
            self.is_valid.value = False
        elif qty > 10:
            self.error_message.value = "Maximum quantity is 10"
            self.is_valid.value = False
        else:
            self.error_message.value = ""
            self.is_valid.value = True
        
        # Recalculate total if valid
        if self.is_valid.value:
            self._calculate_total()
    
    def print_cart_status(self):
        """Print current cart status."""
        print(f"Product: {self.selected_product.selected_option}")
        print(f"Quantity: {self.quantity.value}")
        print(f"Unit Price: ${self.unit_price.value}")
        print(f"Total: ${self.total_price.value}")
        print(f"Valid: {self.is_valid.value}")
        if self.error_message.value:
            print(f"Error: {self.error_message.value}")
        print()

# Test the shopping cart
cart = ShoppingCart()

print("Initial cart:")
cart.print_cart_status()

print("Changing quantity to 3:")
cart.quantity.value = 3
cart.print_cart_status()

print("Switching to mouse:")
cart.selected_product.selected_option = "mouse"
cart.print_cart_status()

print("Invalid quantity (15):")
cart.quantity.value = 15
cart.print_cart_status()

print("Back to valid quantity (2):")
cart.quantity.value = 2
cart.print_cart_status()
```

## 🎯 **Key Takeaways**

Congratulations! You've learned the core concepts of the Observables library:

### **1. True Bidirectional Joining**
- Changes propagate in both directions automatically
- Observables share the same Nexus storage when joined
- No need for manual synchronization

### **2. Transitive Joining Networks**
- Joining A→B and B→C automatically connects A to C
- Networks survive partial disconnections
- Strategic detachment allows flexible network management

### **3. Rigorous State Validation**
- Invalid states are never allowed, even temporarily
- Multi-component updates are validated atomically
- Joining operations respect validation rules

### **4. Practical Applications**
- Form validation with cross-field dependencies
- Configuration management with environment-specific rules
- Real-time applications with automatic synchronization

### **Next Steps**

- Explore the [API Reference](api_reference.md) for detailed method documentation
- Check out [Examples and Use Cases](examples_and_use_cases.md) for more complex scenarios
- Read [Bidirectional Joining and State Validation](bidirectional_binding_and_validation.md) for deeper technical insights
- Review the [Hook System Technical Documentation](hook_system.md) for advanced usage

The Observables library provides a solid foundation for building reactive applications with guaranteed consistency and automatic synchronization. Happy coding! 🚀
