#!/usr/bin/env python3

from observables._build_in_observables.observable_enum import ObservableEnum
from observables._utils.sync_mode import SyncMode

# Define test enums
from enum import Enum

class TestColor(Enum):
    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'

def debug_binding():
    print("=== Debugging ObservableEnum Binding ===")
    
    # Create observables
    obs1 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
    obs2 = ObservableEnum(TestColor.BLUE, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
    obs3 = ObservableEnum(TestColor.GREEN, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
    
    print(f"Initial state:")
    print(f"  obs1.enum_value = {obs1.enum_value}")
    print(f"  obs2.enum_value = {obs2.enum_value}")
    print(f"  obs3.enum_value = {obs3.enum_value}")
    
    print(f"\nBinding obs2 to obs1...")
    obs2.bind_to(obs1)
    
    print(f"After binding obs2 to obs1:")
    print(f"  obs1.enum_value = {obs1.enum_value}")
    print(f"  obs2.enum_value = {obs2.enum_value}")
    print(f"  obs3.enum_value = {obs3.enum_value}")
    
    print(f"\nBinding obs3 to obs1...")
    obs3.bind_to(obs1)
    
    print(f"After binding obs3 to obs1:")
    print(f"  obs1.enum_value = {obs1.enum_value}")
    print(f"  obs2.enum_value = {obs2.enum_value}")
    print(f"  obs3.enum_value = {obs3.enum_value}")
    
    print(f"\nChanging obs1.enum_value to GREEN...")
    obs1.enum_value = TestColor.GREEN
    
    print(f"After changing obs1 to GREEN:")
    print(f"  obs1.enum_value = {obs1.enum_value}")
    print(f"  obs2.enum_value = {obs2.enum_value}")
    print(f"  obs3.enum_value = {obs3.enum_value}")
    
    print(f"\nChanging obs2.enum_value to RED...")
    obs2.enum_value = TestColor.RED
    
    print(f"After changing obs2 to RED:")
    print(f"  obs1.enum_value = {obs1.enum_value}")
    print(f"  obs2.enum_value = {obs2.enum_value}")
    print(f"  obs3.enum_value = {obs3.enum_value}")

if __name__ == "__main__":
    debug_binding()
