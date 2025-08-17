#!/usr/bin/env python3

from observables._build_in_observables.observable_enum import ObservableEnum
from observables._utils.sync_mode import SyncMode

# Define test enums
from enum import Enum

class TestColor(Enum):
    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'

def debug_binding_alternative():
    print("=== Debugging Alternative Binding Approaches ===")
    
    # Create observables
    obs1 = ObservableEnum(TestColor.RED, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
    obs2 = ObservableEnum(TestColor.BLUE, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
    obs3 = ObservableEnum(TestColor.GREEN, {TestColor.RED, TestColor.GREEN, TestColor.BLUE})
    
    print(f"Initial state:")
    print(f"  obs1.enum_value = {obs1.enum_value}")
    print(f"  obs2.enum_value = {obs2.enum_value}")
    print(f"  obs3.enum_value = {obs3.enum_value}")
    
    print(f"\nTrying alternative approach: bind obs1 to obs2 first...")
    obs1.bind_to(obs2)
    
    print(f"After binding obs1 to obs2:")
    print(f"  obs1.enum_value = {obs1.enum_value}")
    print(f"  obs2.enum_value = {obs2.enum_value}")
    print(f"  obs3.enum_value = {obs3.enum_value}")
    
    print(f"\nNow bind obs3 to obs2...")
    obs3.bind_to(obs2)
    
    print(f"After binding obs3 to obs2:")
    print(f"  obs1.enum_value = {obs1.enum_value}")
    print(f"  obs2.enum_value = {obs2.enum_value}")
    print(f"  obs3.enum_value = {obs3.enum_value}")
    
    print(f"\nChanging obs2.enum_value to GREEN...")
    obs2.enum_value = TestColor.GREEN
    
    print(f"After changing obs2 to GREEN:")
    print(f"  obs1.enum_value = {obs1.enum_value}")
    print(f"  obs2.enum_value = {obs2.enum_value}")
    print(f"  obs3.enum_value = {obs3.enum_value}")

if __name__ == "__main__":
    debug_binding_alternative()
