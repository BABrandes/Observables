#!/usr/bin/env python3
"""
Demo script showcasing the observables library features.
"""

import time
from typing import Callable

from observables import (
    ObservableSingleValue,
    ObservableList,
    ObservableDict,
    ObservableSet,
    ObservableSelectionOption,
    SyncMode,
)


def print_separator(title: str) -> None:
    """Print a formatted separator with title."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def demo_basic_usage() -> None:
    """Demonstrate basic observable usage."""
    print_separator("Basic Usage")
    
    # Create observable values
    name = ObservableSingleValue("John")
    age = ObservableSingleValue(25)
    scores = ObservableList([85, 90, 78])
    user_data = ObservableDict({"city": "New York", "country": "USA"})
    
    # Add listeners
    def on_name_change():
        print(f"  Name changed to: {name.value}")
    
    def on_age_change():
        print(f"  Age changed to: {age.value}")
    
    def on_scores_change():
        print(f"  Scores changed to: {scores.list_value}")
    
    def on_user_data_change():
        print(f"  User data changed to: {user_data.value}")
    
    name.add_listeners(on_name_change)
    age.add_listeners(on_age_change)
    scores.add_listeners(on_scores_change)
    user_data.add_listeners(on_user_data_change)
    
    print("Initial values:")
    print(f"  Name: {name.value}")
    print(f"  Age: {age.value}")
    print(f"  Scores: {scores.list_value}")
    print(f"  User data: {user_data.value}")
    
    print("\nMaking changes:")
    name.set_value("Jane")
    age.set_value(26)
    scores.append(95)
    user_data["city"] = "Los Angeles"


def demo_bidirectional_bindings() -> None:
    """Demonstrate bidirectional bindings."""
    print_separator("Bidirectional Bindings")
    
    # Create two observables
    price_usd = ObservableSingleValue(100.0)
    price_eur = ObservableSingleValue(85.0)
    
    # Add listeners to see changes
    def on_usd_change():
        print(f"  USD price changed to: ${price_usd.value}")
    
    def on_eur_change():
        print(f"  EUR price changed to: €{price_eur.value}")
    
    price_usd.add_listeners(on_usd_change)
    price_eur.add_listeners(on_eur_change)
    
    print("Initial prices:")
    print(f"  USD: ${price_usd.value}")
    print(f"  EUR: €{price_eur.value}")
    
    # Bind them together (EUR will update when USD changes)
    print("\nBinding USD to EUR...")
    price_usd.bind_to_observable(
        price_eur, 
        initial_sync_mode=SyncMode.UPDATE_SELF_FROM_OBSERVABLE
    )
    
    print("\nNow changing USD price:")
    price_usd.set_value(110.0)
    
    print("\nNow changing EUR price:")
    price_eur.set_value(95.0)


def demo_observable_collections() -> None:
    """Demonstrate observable collections."""
    print_separator("Observable Collections")
    
    # Observable List
    print("Observable List:")
    todo_list = ObservableList(["Buy groceries", "Walk dog"])
    todo_list.add_listeners(lambda: print(f"  Todo list updated: {todo_list.list_value}"))
    
    print(f"  Initial: {todo_list.list_value}")
    todo_list.append("Read book")
    todo_list[0] = "Buy organic groceries"
    todo_list.remove("Walk dog")
    
    # Observable Dictionary
    print("\nObservable Dictionary:")
    config = ObservableDict({"theme": "dark", "language": "en"})
    config.add_listeners(lambda: print(f"  Config updated: {config.value}"))
    
    print(f"  Initial: {config.value}")
    config["theme"] = "light"
    config.update({"language": "de", "timezone": "UTC"})
    config.remove_item("timezone")
    
    # Observable Set
    print("\nObservable Set:")
    tags = ObservableSet({"python", "library"})
    tags.add_listeners(lambda: print(f"  Tags updated: {tags.value}"))
    
    print(f"  Initial: {tags.value}")
    tags.add("observable")
    tags.add("reactive")
    tags.remove("library")


def demo_selection_options() -> None:
    """Demonstrate selection options."""
    print_separator("Selection Options")
    
    # Create a selection with available options
    country_selector = ObservableSelectionOption(
        options=["USA", "Canada", "UK", "Germany"],
        selected_option="USA"
    )
    
    country_selector.add_listeners(
        lambda: print(f"  Selection changed to: {country_selector.selected_option}")
    )
    
    print(f"Available options: {country_selector.options}")
    print(f"Selected option: {country_selector.selected_option}")
    
    print("\nChanging selection:")
    country_selector.selected_option = "Canada"
    country_selector.selected_option = "UK"
    
    print("\nAdding new options:")
    country_selector.options = ["USA", "Canada", "UK", "Germany", "France", "Spain"]
    
    print("\nChanging to new option:")
    country_selector.selected_option = "France"


def demo_binding_chains() -> None:
    """Demonstrate binding chains."""
    print_separator("Binding Chains")
    
    # Create a chain of observables
    a = ObservableSingleValue(1)
    b = ObservableSingleValue(1)
    c = ObservableSingleValue(1)
    
    # Add listeners
    def on_a_change():
        print(f"  A changed to: {a.value}")
    
    def on_b_change():
        print(f"  B changed to: {b.value}")
    
    def on_c_change():
        print(f"  C changed to: {c.value}")
    
    a.add_listeners(on_a_change)
    b.add_listeners(on_b_change)
    c.add_listeners(on_c_change)
    
    print("Initial values:")
    print(f"  A: {a.value}, B: {b.value}, C: {c.value}")
    
    # Bind them in a chain
    print("\nBinding A → B → C...")
    a.bind_to_observable(b)
    b.bind_to_observable(c)
    
    print("\nChanging A (should propagate through chain):")
    a.set_value(10)
    
    print(f"\nFinal values:")
    print(f"  A: {a.value}, B: {b.value}, C: {c.value}")


def demo_validation() -> None:
    """Demonstrate custom validation."""
    print_separator("Custom Validation")
    
    def validate_age(age: int) -> bool:
        return 0 <= age <= 150
    
    def validate_positive_number(value: float) -> bool:
        return value > 0
    
    # Create observables with validators
    age = ObservableSingleValue(25, validator=validate_age)
    price = ObservableSingleValue(10.99, validator=validate_positive_number)
    
    print(f"Initial age: {age.value}")
    print(f"Initial price: ${price.value}")
    
    print("\nTrying to set invalid values:")
    try:
        age.set_value(200)  # Should fail
    except ValueError as e:
        print(f"  Age validation failed: {e}")
    
    try:
        price.set_value(-5.0)  # Should fail
    except ValueError as e:
        print(f"  Price validation failed: {e}")
    
    print(f"\nFinal values:")
    print(f"  Age: {age.value}")
    print(f"  Price: ${price.value}")


def demo_performance() -> None:
    """Demonstrate performance characteristics."""
    print_separator("Performance Demo")
    
    # Create many observables
    print("Creating 1000 observables...")
    start_time = time.time()
    
    observables = []
    for i in range(1000):
        obs = ObservableSingleValue(i)
        observables.append(obs)
    
    creation_time = time.time() - start_time
    print(f"  Creation time: {creation_time:.4f} seconds")
    
    # Test binding performance
    print("\nTesting binding performance...")
    start_time = time.time()
    
    for i in range(0, 999, 2):
        observables[i].bind_to_observable(observables[i + 1])
    
    binding_time = time.time() - start_time
    print(f"  Binding time: {binding_time:.4f} seconds")
    
    # Test change propagation
    print("\nTesting change propagation...")
    start_time = time.time()
    
    observables[0].set_value(9999)
    
    propagation_time = time.time() - start_time
    print(f"  Propagation time: {propagation_time:.4f} seconds")
    
    print(f"\nTotal observables: {len(observables)}")
    print(f"Total bindings: {len(observables) // 2}")


def main() -> None:
    """Run all demos."""
    print("Observables Library Demo")
    print("=" * 60)
    
    try:
        demo_basic_usage()
        demo_bidirectional_bindings()
        demo_observable_collections()
        demo_selection_options()
        demo_binding_chains()
        demo_validation()
        demo_performance()
        
        print_separator("Demo Complete")
        print("All demos completed successfully!")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
