"""
Base test class for observables tests that handles global state reset.
"""

import unittest

try:
    from observables._utils.nexus_manager import DEFAULT_NEXUS_MANAGER
except ImportError:
    DEFAULT_NEXUS_MANAGER = None # type: ignore


class ObservableTestCase(unittest.TestCase):
    """Base test case that resets global state between tests."""
    
    def setUp(self):
        """Reset global state before each test."""
        super().setUp()
        if DEFAULT_NEXUS_MANAGER is not None:
            DEFAULT_NEXUS_MANAGER.reset()
