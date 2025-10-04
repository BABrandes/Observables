from .nexus_manager import NexusManager
import math
from typing import Any

from united_system import RealUnitedScalar

def _values_are_equal(value1: Any, value2: Any) -> bool:
    """
    Compare two values for equality.

    Special case handling for:
    - RealUnitedScalar values
    - math.isnan values
    """

    # Handle RealUnitedScalar values
    if isinstance(value1, RealUnitedScalar) and isinstance(value2, RealUnitedScalar):
        if value1.dimension != value2.dimension:
            return False
        value1 = value1.value_in_canonical_unit
        value2 = value2.value_in_canonical_unit

    # Handle NaN values specifically
    if isinstance(value1, float) and isinstance(value2, float):
        if math.isnan(value1) and math.isnan(value2):
            return True
        if math.isnan(value1) or math.isnan(value2):
            return False

    
    # For all other cases, use regular equality
    return value1 == value2

DEFAULT_NEXUS_MANAGER: "NexusManager" = NexusManager(value_equality_callback=_values_are_equal)