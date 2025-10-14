#!/usr/bin/env python3
"""
ObservableTransfer Examples

This file demonstrates various use cases for the ObservableTransfer class,
showing how it can be used to create powerful transformations between
multiple observable inputs and outputs.
"""

from observables import (
    ObservableTransfer, ObservableDict, ObservableSingleValue, 
    ObservableList, ObservableSet
)
from typing import Dict, Any


def example_1_dictionary_access():
    """
    Example 1: Dictionary Access Pattern
    
    Transform a dictionary and key into a value.
    This is the classic use case mentioned in the requirements.
    """
    print("=== Example 1: Dictionary Access ===")
    
    # Create source observables
    data_dict = ObservableDict({"name": "Alice", "age": 30, "city": "New York"})
    key_obs = ObservableSingleValue("name")
    
    # Create transfer observable for dictionary access
    dict_access = ObservableTransfer(
        input_hooks={
            "dict": data_dict.value_hook,
            "key": key_obs.hook
        },
        output_hooks={
            "value": None,  # Will be computed
            "exists": False  # Will be computed
        },
        forward_callable=lambda inputs: {
            "value": inputs["dict"].get(inputs["key"]),
            "exists": inputs["key"] in inputs["dict"]
        }
    )
    
    # Access current value
    print(f"dict['{key_obs.single_value}'] = {dict_access.get_output_value('value')}")
    print(f"Key exists: {dict_access.get_output_value('exists')}")
    
    # Change key
    key_obs.single_value = "age"
    print(f"dict['{key_obs.single_value}'] = {dict_access.get_output_value('value')}")
    print(f"Key exists: {dict_access.get_output_value('exists')}")
    
    # Change dictionary
    data_dict["age"] = 31
    print(f"After updating dict: dict['{key_obs.single_value}'] = {dict_access.get_output_value('value')}")
    
    # Access non-existent key
    key_obs.single_value = "salary"
    print(f"dict['{key_obs.single_value}'] = {dict_access.get_output_value('value')}")
    print(f"Key exists: {dict_access.get_output_value('exists')}")
    print()


def example_2_mathematical_operations():
    """
    Example 2: Mathematical Operations
    
    Transform multiple numbers into various calculated results.
    """
    print("=== Example 2: Mathematical Operations ===")
    
    # Create number observables
    x = ObservableSingleValue(5.0)
    y = ObservableSingleValue(3.0)
    
    # Create transfer for mathematical operations
    math_calc = ObservableTransfer(
        input_hooks={
            "x": x.single_value_hook,
            "y": y.single_value_hook
        },
        output_hooks={
            "sum": 0.0,
            "product": 0.0,
            "quotient": 0.0,
            "power": 0.0
        },
        forward_callable=lambda inputs: {
            "sum": inputs["x"] + inputs["y"],
            "product": inputs["x"] * inputs["y"],
            "quotient": inputs["x"] / inputs["y"] if inputs["y"] != 0 else float('inf'),
            "power": inputs["x"] ** inputs["y"]
        }
    )
    
    def print_results():
        print(f"x = {x.single_value}, y = {y.single_value}")
        print(f"  sum = {math_calc.get_output_value('sum')}")
        print(f"  product = {math_calc.get_output_value('product')}")
        print(f"  quotient = {math_calc.get_output_value('quotient')}")
        print(f"  power = {math_calc.get_output_value('power')}")
    
    print_results()
    
    # Change values
    x.single_value = 10.0
    print_results()
    
    y.single_value = 2.0
    print_results()
    print()


def example_3_string_formatting():
    """
    Example 3: String Formatting
    
    Transform template and variables into formatted strings.
    """
    print("=== Example 3: String Formatting ===")
    
    # Create template and variable observables
    template = ObservableSingleValue("Hello, {name}! You have {count} messages.")
    name = ObservableSingleValue("Bob")
    count = ObservableSingleValue(5)
    
    # Create transfer for string formatting
    formatter = ObservableTransfer(
        input_hooks={
            "template": template.single_value_hook,
            "name": name.single_value_hook,
            "count": count.single_value_hook
        },
        output_hooks={
            "formatted": "",
            "length": 0
        },
        forward_callable=lambda inputs: {
            "formatted": inputs["template"].format(
                name=inputs["name"], 
                count=inputs["count"]
            ),
            "length": len(inputs["template"].format(
                name=inputs["name"], 
                count=inputs["count"]
            ))
        }
    )
    
    def print_formatted():
        print(f"Template: {template.single_value}")
        print(f"Formatted: {formatter.get_output_value('formatted')}")
        print(f"Length: {formatter.get_output_value('length')}")
    
    print_formatted()
    
    # Change variables
    name.single_value = "Charlie"
    count.single_value = 12
    print_formatted()
    
    # Change template
    template.single_value = "Hi {name}, you've got {count} new notifications!"
    print_formatted()
    print()


def example_4_bidirectional_transformation():
    """
    Example 4: Bidirectional Transformation
    
    Transform between Celsius and Fahrenheit with reverse capability.
    """
    print("=== Example 4: Bidirectional Temperature Conversion ===")
    
    # Create temperature observables
    celsius = ObservableSingleValue(20.0)
    
    # Create bidirectional transfer
    temp_converter = ObservableTransfer(
        input_hooks={
            "celsius": celsius.single_value_hook
        },
        output_hooks={
            "fahrenheit": 68.0,
            "kelvin": 293.15
        },
        forward_callable=lambda inputs: {
            "fahrenheit": inputs["celsius"] * 9/5 + 32,
            "kelvin": inputs["celsius"] + 273.15
        },
        reverse_callable=lambda outputs: {
            "celsius": (outputs["fahrenheit"] - 32) * 5/9
        }
    )
    
    def print_temperatures():
        print(f"Celsius: {celsius.single_value}°C")
        print(f"Fahrenheit: {temp_converter.get_output_value('fahrenheit'):.1f}°F")
        print(f"Kelvin: {temp_converter.get_output_value('kelvin'):.2f}K")
    
    print_temperatures()
    
    # Change Celsius
    celsius.single_value = 0.0
    print("After setting to 0°C:")
    print_temperatures()
    
    # Change Fahrenheit (uses reverse transformation)
    temp_converter.set_output_value("fahrenheit", 100.0)
    print("After setting to 100°F:")
    print_temperatures()
    print()


def example_5_list_statistics():
    """
    Example 5: List Statistics
    
    Transform a list into various statistical measures.
    """
    print("=== Example 5: List Statistics ===")
    
    # Create list observable
    numbers = ObservableList([1, 2, 3, 4, 5])
    
    # Create transfer for statistics
    stats = ObservableTransfer(
        input_hooks={
            "numbers": numbers.list_hook
        },
        output_hooks={
            "count": 0,
            "sum": 0,
            "average": 0.0,
            "min": 0,
            "max": 0
        },
        forward_callable=lambda inputs: {
            "count": len(inputs["numbers"]),
            "sum": sum(inputs["numbers"]) if inputs["numbers"] else 0,
            "average": sum(inputs["numbers"]) / len(inputs["numbers"]) if inputs["numbers"] else 0,
            "min": min(inputs["numbers"]) if inputs["numbers"] else 0,
            "max": max(inputs["numbers"]) if inputs["numbers"] else 0
        }
    )
    
    def print_stats():
        print(f"Numbers: {numbers.list_value}")
        print(f"  Count: {stats.get_output_value('count')}")
        print(f"  Sum: {stats.get_output_value('sum')}")
        print(f"  Average: {stats.get_output_value('average'):.2f}")
        print(f"  Min: {stats.get_output_value('min')}")
        print(f"  Max: {stats.get_output_value('max')}")
    
    print_stats()
    
    # Add numbers
    numbers.append(10)
    numbers.append(15)
    print("After adding 10 and 15:")
    print_stats()
    
    # Remove a number
    numbers.remove(1)
    print("After removing 1:")
    print_stats()
    print()


def example_6_complex_business_logic():
    """
    Example 6: Complex Business Logic
    
    Transform multiple business inputs into derived state.
    """
    print("=== Example 6: E-commerce Order Calculator ===")
    
    # Create business observables
    item_price = ObservableSingleValue(29.99)
    quantity = ObservableSingleValue(2)
    discount_percent = ObservableSingleValue(10.0)
    tax_rate = ObservableSingleValue(8.5)  # 8.5%
    shipping_cost = ObservableSingleValue(5.99)
    
    # Create transfer for order calculation
    order_calc = ObservableTransfer(
        input_hooks={
            "item_price": item_price.single_value_hook,
            "quantity": quantity.single_value_hook,
            "discount_percent": discount_percent.single_value_hook,
            "tax_rate": tax_rate.single_value_hook,
            "shipping_cost": shipping_cost.single_value_hook
        },
        output_hooks={
            "subtotal": 0.0,
            "discount_amount": 0.0,
            "discounted_subtotal": 0.0,
            "tax_amount": 0.0,
            "total": 0.0
        },
        forward_callable=lambda inputs: {
            "subtotal": inputs["item_price"] * inputs["quantity"],
            "discount_amount": (inputs["item_price"] * inputs["quantity"]) * (inputs["discount_percent"] / 100),
            "discounted_subtotal": (inputs["item_price"] * inputs["quantity"]) * (1 - inputs["discount_percent"] / 100),
            "tax_amount": (inputs["item_price"] * inputs["quantity"]) * (1 - inputs["discount_percent"] / 100) * (inputs["tax_rate"] / 100),
            "total": (inputs["item_price"] * inputs["quantity"]) * (1 - inputs["discount_percent"] / 100) * (1 + inputs["tax_rate"] / 100) + inputs["shipping_cost"]
        }
    )
    
    def print_order():
        print(f"Item Price: ${item_price.single_value:.2f}")
        print(f"Quantity: {quantity.single_value}")
        print(f"Discount: {discount_percent.single_value}%")
        print(f"Tax Rate: {tax_rate.single_value}%")
        print(f"Shipping: ${shipping_cost.single_value:.2f}")
        print("---")
        print(f"Subtotal: ${order_calc.get_output_value('subtotal'):.2f}")
        print(f"Discount: -${order_calc.get_output_value('discount_amount'):.2f}")
        print(f"After Discount: ${order_calc.get_output_value('discounted_subtotal'):.2f}")
        print(f"Tax: ${order_calc.get_output_value('tax_amount'):.2f}")
        print(f"TOTAL: ${order_calc.get_output_value('total'):.2f}")
    
    print_order()
    
    # Change quantity
    quantity.single_value = 3
    print("\nAfter changing quantity to 3:")
    print_order()
    
    # Increase discount
    discount_percent.single_value = 20.0
    print("\nAfter increasing discount to 20%:")
    print_order()
    print()


def example_7_chained_transformations():
    """
    Example 7: Chained Transformations
    
    Show how multiple ObservableTransfer instances can be chained together.
    """
    print("=== Example 7: Chained Transformations ===")
    
    # Create source data
    raw_text = ObservableSingleValue("  Hello, World!  ")
    
    # First transformation: text cleaning
    text_cleaner = ObservableTransfer(
        input_hooks={
            "raw_text": raw_text.single_value_hook
        },
        output_hooks={
            "cleaned_text": "",
            "original_length": 0
        },
        forward_callable=lambda inputs: {
            "cleaned_text": inputs["raw_text"].strip().lower(),
            "original_length": len(inputs["raw_text"])
        }
    )
    
    # Second transformation: text analysis
    text_analyzer = ObservableTransfer(
        input_hooks={
            "text": text_cleaner.get_output_hook("cleaned_text"),
            "original_length": text_cleaner.get_output_hook("original_length")
        },
        output_hooks={
            "word_count": 0,
            "char_count": 0,
            "compression_ratio": 0.0
        },
        forward_callable=lambda inputs: {
            "word_count": len(inputs["text"].split()) if inputs["text"] else 0,
            "char_count": len(inputs["text"]),
            "compression_ratio": len(inputs["text"]) / inputs["original_length"] if inputs["original_length"] > 0 else 1.0
        }
    )
    
    def print_analysis():
        print(f"Raw text: '{raw_text.single_value}'")
        print(f"Cleaned: '{text_cleaner.get_output_value('cleaned_text')}'")
        print(f"Word count: {text_analyzer.get_output_value('word_count')}")
        print(f"Character count: {text_analyzer.get_output_value('char_count')}")
        print(f"Compression ratio: {text_analyzer.get_output_value('compression_ratio'):.2%}")
    
    print_analysis()
    
    # Change input
    raw_text.single_value = "   THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG   "
    print("\nAfter changing text:")
    print_analysis()
    print()


def main():
    """Run all examples."""
    print("ObservableTransfer Examples")
    print("=" * 50)
    print()
    
    example_1_dictionary_access()
    example_2_mathematical_operations()
    example_3_string_formatting()
    example_4_bidirectional_transformation()
    example_5_list_statistics()
    example_6_complex_business_logic()
    example_7_chained_transformations()
    
    print("All examples completed!")


if __name__ == "__main__":
    main()
