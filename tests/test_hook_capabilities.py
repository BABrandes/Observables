import unittest
from typing import Any, Callable
from observables._utils.hook import Hook
from observables._utils.sync_mode import SyncMode


class TestHookCapabilities(unittest.TestCase):
    """Test hooks with different capabilities (receiving-only, sending-only, both)."""

    def test_receiving_only_hook(self):
        """Test a hook that can only receive values (has set_callback but no get_callback)."""
        received_values = []
        
        def set_callback(value: str) -> None:
            received_values.append(value)
        
        # Create hook with only set_callback (receiving-only)
        receiving_hook = Hook[str](
            get_callback=None,
            set_callback=set_callback,
            owner="receiving_hook"
        )
        
        # Verify flags are set correctly
        self.assertTrue(receiving_hook._is_receiving)
        self.assertFalse(receiving_hook._is_sending)
        
        # Test that it can receive values
        receiving_hook._set_callback("test_value")
        self.assertEqual(received_values, ["test_value"])
        
        # Test that it cannot provide values (should raise error)
        with self.assertRaises(TypeError):
            receiving_hook._get_callback()

    def test_sending_only_hook(self):
        """Test a hook that can only send values (has get_callback but no set_callback)."""
        def get_callback() -> str:
            return "constant_value"
        
        # Create hook with only get_callback (sending-only)
        sending_hook = Hook[str](
            get_callback=get_callback,
            set_callback=None,
            owner="sending_hook"
        )
        
        # Verify flags are set correctly
        self.assertFalse(sending_hook._is_receiving)
        self.assertTrue(sending_hook._is_sending)
        
        # Test that it can provide values
        value = sending_hook._get_callback()
        self.assertEqual(value, "constant_value")
        
        # Test that it cannot receive values (should raise error)
        with self.assertRaises(TypeError):
            sending_hook._set_callback("test_value")

    def test_bidirectional_hook(self):
        """Test a hook that can both send and receive values (has both callbacks)."""
        stored_value = "initial_value"
        received_values = []
        
        def get_callback() -> str:
            return stored_value
        
        def set_callback(value: str) -> None:
            nonlocal stored_value
            stored_value = value
            received_values.append(value)
        
        # Create hook with both callbacks (bidirectional)
        bidirectional_hook = Hook[str](
            get_callback=get_callback,
            set_callback=set_callback,
            owner="bidirectional_hook"
        )
        
        # Verify flags are set correctly
        self.assertTrue(bidirectional_hook._is_receiving)
        self.assertTrue(bidirectional_hook._is_sending)
        
        # Test that it can provide values
        value = bidirectional_hook._get_callback()
        self.assertEqual(value, "initial_value")
        
        # Test that it can receive values
        bidirectional_hook._set_callback("new_value")
        self.assertEqual(stored_value, "new_value")
        self.assertEqual(received_values, ["new_value"])
        
        # Verify the value was updated
        value = bidirectional_hook._get_callback()
        self.assertEqual(value, "new_value")

    def test_binding_receiving_to_sending(self):
        """Test binding a receiving-only hook to a sending-only hook."""
        received_values = []
        
        def get_callback() -> str:
            return "source_value"
        
        def set_callback(value: str) -> None:
            received_values.append(value)
        
        # Create hooks
        sending_hook = Hook[str](
            get_callback=get_callback,
            set_callback=None,
            owner="sending_hook"
        )
        
        receiving_hook = Hook[str](
            get_callback=None,
            set_callback=set_callback,
            owner="receiving_hook"
        )
        
        # Bind receiving hook to sending hook
        receiving_hook.establish_binding(sending_hook, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Verify binding was established
        self.assertTrue(receiving_hook.is_bound_to(sending_hook))
        self.assertTrue(sending_hook.is_bound_to(receiving_hook))
        
        # Verify value was synced during binding
        self.assertEqual(received_values, ["source_value"])

    def test_binding_sending_to_receiving(self):
        """Test binding a sending-only hook to a receiving-only hook."""
        stored_value = "target_value"
        received_values = []
        
        def get_callback() -> str:
            return "source_value"
        
        def set_callback(value: str) -> None:
            nonlocal stored_value
            stored_value = value
            received_values.append(value)
        
        # Create hooks
        sending_hook = Hook[str](
            get_callback=get_callback,
            set_callback=None,
            owner="sending_hook"
        )
        
        receiving_hook = Hook[str](
            get_callback=None,
            set_callback=set_callback,
            owner="receiving_hook"
        )
        
        # Bind sending hook to receiving hook
        sending_hook.establish_binding(receiving_hook, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        
        # Verify binding was established
        self.assertTrue(sending_hook.is_bound_to(receiving_hook))
        self.assertTrue(receiving_hook.is_bound_to(sending_hook))
        
        # Verify value was synced during binding
        self.assertEqual(received_values, ["source_value"])
        self.assertEqual(stored_value, "source_value")

    def test_binding_bidirectional_hooks(self):
        """Test binding two bidirectional hooks together."""
        stored_value1 = "value1"
        stored_value2 = "value2"
        received_values1 = []
        received_values2 = []
        
        def get_callback1() -> str:
            return stored_value1
        
        def set_callback1(value: str) -> None:
            nonlocal stored_value1
            stored_value1 = value
            received_values1.append(value)
        
        def get_callback2() -> str:
            return stored_value2
        
        def set_callback2(value: str) -> None:
            nonlocal stored_value2
            stored_value2 = value
            received_values2.append(value)
        
        # Create bidirectional hooks
        hook1 = Hook[str](
            get_callback=get_callback1,
            set_callback=set_callback1,
            owner="hook1"
        )
        
        hook2 = Hook[str](
            get_callback=get_callback2,
            set_callback=set_callback2,
            owner="hook2"
        )
        
        # Bind hook1 to hook2
        hook1.establish_binding(hook2, SyncMode.UPDATE_SELF_FROM_OBSERVABLE)
        
        # Verify binding was established
        self.assertTrue(hook1.is_bound_to(hook2))
        self.assertTrue(hook2.is_bound_to(hook1))
        
        # Verify value was synced during binding
        self.assertEqual(stored_value1, "value2")
        self.assertEqual(received_values1, ["value2"])

    def test_invalid_binding_combinations(self):
        """Test that invalid binding combinations raise appropriate errors."""
        def get_callback() -> str:
            return "value"
        
        def set_callback(value: str) -> None:
            pass
        
        # Create hooks
        sending_hook = Hook[str](
            get_callback=get_callback,
            set_callback=None,
            owner="sending_hook"
        )
        
        receiving_hook = Hook[str](
            get_callback=None,
            set_callback=set_callback,
            owner="receiving_hook"
        )
        
        # Test: Cannot update observable from non-sending hook (receiving_hook has no get_callback)
        with self.assertRaises(ValueError) as cm:
            receiving_hook.establish_binding(sending_hook, SyncMode.UPDATE_OBSERVABLE_FROM_SELF)
        self.assertIn("not sending", str(cm.exception))

    def test_hook_with_auxiliary_information(self):
        """Test hooks with auxiliary information."""
        # Create a simple callback that doesn't require auxiliary information
        def get_callback() -> str:
            return "value_test"
        
        def set_callback(value: str) -> None:
            pass
        
        aux_info = {'suffix': 'test', 'last_set': None}
        
        hook = Hook[str](
            get_callback=get_callback,
            set_callback=set_callback,
            auxiliary_information=aux_info,
            owner="aux_hook"
        )
        
        # Verify flags are set correctly
        self.assertTrue(hook._is_receiving)
        self.assertTrue(hook._is_sending)
        
        # Test get_callback
        value = hook._get_callback()
        self.assertEqual(value, "value_test")
        
        # Test set_callback
        hook._set_callback("new_value")

    def test_hook_protocol_compliance(self):
        """Test that hooks properly implement the HookLike protocol."""
        def get_callback() -> str:
            return "test_value"
        
        def set_callback(value: str) -> None:
            pass
        
        hook = Hook[str](
            get_callback=get_callback,
            set_callback=set_callback,
            owner="test_hook"
        )
        
        # Test that all required protocol methods exist and work
        self.assertTrue(hasattr(hook, 'establish_binding'))
        self.assertTrue(hasattr(hook, 'remove_binding'))
        self.assertTrue(hasattr(hook, 'is_bound_to'))
        self.assertTrue(hasattr(hook, 'notify_bindings'))
        self.assertTrue(hasattr(hook, 'check_binding_state_consistency'))
        self.assertTrue(hasattr(hook, 'check_values_synced'))
        self.assertTrue(hasattr(hook, 'value'))
        self.assertTrue(hasattr(hook, 'connected_hooks'))
        self.assertTrue(hasattr(hook, 'auxiliary_information'))
        self.assertTrue(hasattr(hook, 'owner'))


if __name__ == '__main__':
    unittest.main()
