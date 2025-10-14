"""
Base test class for observables tests that handles global state reset.
"""

import unittest

from observables.core import DEFAULT_NEXUS_MANAGER

class ObservableTestCase(unittest.TestCase):
    """Base test case that resets global state between tests."""
    
    def setUp(self):
        """Reset global state before each test."""
        super().setUp()
        DEFAULT_NEXUS_MANAGER.reset()
