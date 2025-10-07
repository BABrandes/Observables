from .nexus_manager import NexusManager
import math

from united_system import RealUnitedScalar

def _value_equality_callback_float(value1: float, value2: float) -> bool:

    if math.isnan(value1) and math.isnan(value2):
        return True
    if math.isnan(value1) or math.isnan(value2):
        return False

    # For all other cases, use regular equality
    return value1 == value2

def _value_equality_callback_real_united_scalar(value1: RealUnitedScalar, value2: RealUnitedScalar) -> bool:

    if value1.dimension != value2.dimension:
        return False
    return _value_equality_callback_float(value1.value_in_canonical_unit(), value2.value_in_canonical_unit())

DEFAULT_NEXUS_MANAGER: "NexusManager" = NexusManager(
    value_equality_callbacks={
        RealUnitedScalar: _value_equality_callback_real_united_scalar,
        float: _value_equality_callback_float,
    }
)