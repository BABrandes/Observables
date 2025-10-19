"""
Basic memory management tests for the observables library.

These tests verify essential memory management without being too strict
about edge cases that may be implementation-dependent.
"""

import gc
import weakref
from typing import Any
import pytest
from observables import ObservableSingleValue, ObservableList, ObservableSet
from observables.core import ComplexObservableBase


class TestEssentialMemoryManagement:
    """Test essential memory management scenarios."""

    def test_simple_observable_cleanup(self):
        """Test that simple observables are cleaned up."""
        obs = ObservableSingleValue("test")
        obs_ref = weakref.ref(obs)
        
        del obs
        gc.collect()
        
        assert obs_ref() is None, "Simple observable was not cleaned up"

    def test_observable_with_simple_listeners(self):
        """Test cleanup with simple listeners."""
        obs = ObservableSingleValue("test")
        
        call_count = [0]
        def listener():
            call_count[0] += 1
        
        obs.add_listener(listener)
        obs.value = "modified"
        assert call_count[0] == 1
        
        obs_ref = weakref.ref(obs)
        listener_ref = weakref.ref(listener)
        
        del obs, listener
        gc.collect()
        
        assert obs_ref() is None, "Observable with listener was not cleaned up"
        assert listener_ref() is None, "Listener was not cleaned up"

    def test_simple_binding_cleanup(self):
        """Test cleanup of simply bound observables."""
        obs1 = ObservableSingleValue("value1")
        obs2 = ObservableSingleValue("value2")
        
        # Bind them
        obs1._link(obs2.hook, "value", "use_caller_value")  # type: ignore
        
        # Test binding works
        obs1.value = "new_value"
        assert obs2.value == "new_value"
        
        obs1_ref = weakref.ref(obs1)
        obs2_ref = weakref.ref(obs2)
        
        del obs1, obs2
        gc.collect()
        
        assert obs1_ref() is None, "Bound observable 1 was not cleaned up"
        assert obs2_ref() is None, "Bound observable 2 was not cleaned up"

    def test_secondary_hook_basic_cleanup(self):
        """Test basic cleanup of observables with secondary hooks."""
        obs_list = ObservableList([1, 2, 3])
        
        # Access secondary hook
        length_hook = obs_list._get_hook_by_key("length")  # type: ignore
        initial_length = length_hook.value
        assert initial_length == 3
        
        # Modify to trigger secondary hook update
        obs_list.append(4)
        assert length_hook.value == 4
        
        obs_ref = weakref.ref(obs_list)
        
        del obs_list, length_hook
        gc.collect()
        
        assert obs_ref() is None, "Observable with secondary hook was not cleaned up"

    def test_many_simple_observables(self):
        """Test that creating many observables doesn't leak memory."""
        # Get baseline
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create and destroy many observables
        for batch in range(5):
            observables: list[ObservableSingleValue[Any]] = []
            for i in range(100):
                obs = ObservableSingleValue(f"value_{batch}_{i}")
                observables.append(obs)
            
            # Use the observables
            for obs in observables:
                obs.value = f"modified_{batch}"
            
            # Clear batch
            observables.clear()
            
            # Periodic cleanup
            if batch % 2 == 0:
                gc.collect()
        
        # Final cleanup
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Allow reasonable growth but not excessive
        growth = final_objects - initial_objects
        assert growth < 1000, f"Excessive memory growth: {growth} objects"

    def test_detached_observables_cleanup(self):
        """Test cleanup after detaching bindings."""
        obs1 = ObservableSingleValue("value1")
        obs2 = ObservableSingleValue("value2")
        
        # Bind, test, detach
        obs1._link(obs2.hook, "value", "use_caller_value")  # type: ignore
        obs1.value = "bound_value"
        assert obs2.value == "bound_value"
        
        obs1._unlink("value")  # type: ignore
        obs1.value = "detached_value"
        assert obs2.value == "bound_value"  # Should not change
        
        obs1_ref = weakref.ref(obs1)
        obs2_ref = weakref.ref(obs2)
        
        del obs1, obs2
        gc.collect()
        
        assert obs1_ref() is None, "Detached observable 1 was not cleaned up"
        assert obs2_ref() is None, "Detached observable 2 was not cleaned up"


class TestMemoryStressScenarios:
    """Test memory management under stress."""

    @pytest.mark.slow
    def test_binding_memory_stress(self):
        """Stress test memory with many binding operations."""
        weak_refs: list[weakref.ref[ObservableSingleValue[Any]]] = []
        
        for cycle in range(20):
            # Create observables for this cycle
            cycle_observables: list[ObservableSingleValue[Any]] = []
            for i in range(10):
                obs = ObservableSingleValue(f"cycle_{cycle}_value_{i}")
                cycle_observables.append(obs)
                weak_refs.append(weakref.ref(obs))
            
            # Create some bindings
            for i in range(len(cycle_observables) - 1):
                cycle_observables[i]._link(  # type: ignore
                    cycle_observables[i + 1].hook,
                    "value",
                    "use_caller_value"
                )
            
            # Use the chain
            cycle_observables[0].value = f"chain_value_{cycle}"
            
            # Clear cycle
            cycle_observables.clear()
            
            # Periodic cleanup
            if cycle % 5 == 0:
                gc.collect()
        
        # Final cleanup
        for _ in range(3):
            gc.collect()
        
        # Check that most observables were cleaned up
        alive_count = sum(1 for ref in weak_refs if ref() is not None)
        total_count = len(weak_refs)
        cleanup_rate = (total_count - alive_count) / total_count
        
        # Expect at least 80% cleanup rate
        assert cleanup_rate >= 0.8, f"Poor cleanup rate: {cleanup_rate:.1%} ({alive_count}/{total_count} still alive)"

    def test_mixed_observable_types_memory(self):
        """Test memory management with mixed observable types."""
        observables: list[ComplexObservableBase[Any, Any, Any, Any, Any]] = []
        weak_refs: list[weakref.ref[ComplexObservableBase[Any, Any, Any, Any, Any]]] = []
        
        # Create mixed observable types
        for i in range(20):
            obs_single = ObservableSingleValue(f"single_{i}")
            obs_list = ObservableList([i, i+1])
            obs_set = ObservableSet({i, i+1})
            
            observables.extend([obs_single, obs_list, obs_set])
            weak_refs.extend([
                weakref.ref(obs_single),
                weakref.ref(obs_list),
                weakref.ref(obs_set)
            ])
            
            # Trigger secondary hooks
            obs_list.append(i+2)
            obs_set.add(i+2)
        
        # Clear observables
        observables.clear()
        
        # Cleanup
        for _ in range(3):
            gc.collect()
        
        # Verify cleanup
        alive_count = sum(1 for ref in weak_refs if ref() is not None)
        total_count = len(weak_refs)
        
        # Allow some tolerance for complex scenarios
        assert alive_count <= total_count * 0.2, f"Too many objects alive: {alive_count}/{total_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
