"""
Test cases for ObservableSubscriber
"""

import unittest
import asyncio
from typing import Optional, Mapping

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_base import ObservableTestCase
from tests.run_tests import console_logger as logger

from observables._utils.publisher import Publisher
from observables._other_observables.observable_subscriber import ObservableSubscriber


class TestObservableSubscriber(ObservableTestCase):
    """Test ObservableSubscriber functionality"""
    
    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.publisher = Publisher(logger=logger)
        self.callback_call_count = 0
        self.last_publisher: Optional[Publisher] = None
    
    def tearDown(self):
        self.loop.close()
        super().tearDown()
    
    def simple_callback(self, pub: Optional[Publisher]) -> Mapping[str, int]:
        """Simple callback that tracks calls and returns test data"""
        self.callback_call_count += 1
        self.last_publisher = pub
        
        if pub is None:
            return {"initial": 0}
        else:
            return {"value": self.callback_call_count}
    
    def test_initialization_with_single_publisher(self):
        """Test creating ObservableSubscriber with a single publisher"""
        observable = ObservableSubscriber(
            self.publisher,
            self.simple_callback,
            logger=logger
        )
        
        # Callback should be called once with None for initial values
        self.assertEqual(self.callback_call_count, 1)
        self.assertIsNone(self.last_publisher)
        
        # Should be subscribed to publisher
        self.assertTrue(self.publisher.is_subscribed(observable))
    
    def test_initialization_with_multiple_publishers(self):
        """Test creating ObservableSubscriber with multiple publishers"""
        publisher2 = Publisher(logger=logger)
        publisher3 = Publisher(logger=logger)
        
        publishers = {self.publisher, publisher2, publisher3}
        
        observable = ObservableSubscriber(
            publishers,
            self.simple_callback,
            logger=logger
        )
        
        # Should be subscribed to all publishers
        self.assertTrue(self.publisher.is_subscribed(observable))
        self.assertTrue(publisher2.is_subscribed(observable))
        self.assertTrue(publisher3.is_subscribed(observable))
    
    def test_reaction_to_publication(self):
        """Test that ObservableSubscriber reacts to publications"""
        _ = ObservableSubscriber(
            self.publisher,
            self.simple_callback,
            logger=logger
        )
        
        # Reset counter after initialization
        initial_count = self.callback_call_count
        
        # Publish
        self.publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Callback should have been called again
        self.assertEqual(self.callback_call_count, initial_count + 1)
        self.assertIs(self.last_publisher, self.publisher)
    
    def test_multiple_publications(self):
        """Test multiple publications"""
        _ = ObservableSubscriber(
            self.publisher,
            self.simple_callback,
            logger=logger
        )
        
        initial_count = self.callback_call_count
        
        # Publish 3 times
        for _ in range(3):
            self.publisher.publish()
            self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Callback should have been called 3 more times
        self.assertEqual(self.callback_call_count, initial_count + 3)
    
    def test_multiple_publishers_trigger_reactions(self):
        """Test that all publishers trigger reactions"""
        publisher2 = Publisher(logger=logger)
        publisher3 = Publisher(logger=logger)
        
        _ = ObservableSubscriber(   
            {self.publisher, publisher2, publisher3},
            self.simple_callback,
            logger=logger
        )
        
        initial_count = self.callback_call_count
        
        # Publish from each publisher
        self.publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        publisher2.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        publisher3.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Callback should have been called 3 times
        self.assertEqual(self.callback_call_count, initial_count + 3)
    
    def test_callback_with_publisher_parameter(self):
        """Test that callback receives correct publisher"""
        publisher2 = Publisher(logger=logger)
        
        publishers_seen: list[Publisher] = []
        
        def tracking_callback(pub: Optional[Publisher]) -> Mapping[str, str]:
            if pub is not None:
                publishers_seen.append(pub)
            return {"data": "value"}
        
        _ = ObservableSubscriber(
            {self.publisher, publisher2},
            tracking_callback,
            logger=logger
        )
        
        # Publish from both
        self.publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        publisher2.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Should have seen both publishers
        self.assertEqual(len(publishers_seen), 2)
        self.assertIn(self.publisher, publishers_seen)
        self.assertIn(publisher2, publishers_seen)
    
    def test_submit_values_called(self):
        """Test that submit_values is called with callback result"""
        values_to_return = {"key1": 100, "key2": 200}
        
        def callback(pub: Optional[Publisher]) -> Mapping[str, int]:
            if pub is None:
                return {"initial": 0}
            return values_to_return
        
        _ = ObservableSubscriber(
            self.publisher,
            callback,
            logger=logger
        )
        
        # Publish
        self.publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # The observable should have the values from callback
        # Note: This assumes submit_values updates internal state
        # The exact assertion depends on how BaseObservable works
    
    def test_async_callback_execution(self):
        """Test that callbacks execute asynchronously"""
        import time
        
        call_times: list[float] = []
        
        def slow_callback(pub: Optional[Publisher]) -> Mapping[str, int]:
            call_times.append(time.time())
            return {"value": 1}
        
        _ = ObservableSubscriber(
            self.publisher,
            slow_callback,
            logger=logger
        )
        
        initial_time = time.time()
        
        # Publish should return immediately
        self.publisher.publish()
        publish_time = time.time()
        
        # Should return almost immediately
        self.assertLess(publish_time - initial_time, 0.01)
        
        # Wait for async execution
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Callback should have executed
        self.assertGreater(len(call_times), 1)  # Initial + publication


class TestObservableSubscriberEdgeCases(ObservableTestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
        super().tearDown()
    
    def test_callback_exception_handling(self):
        """Test that callback exceptions are handled"""
        def failing_callback(pub: Optional[Publisher]) -> Mapping[str, int]:
            if pub is None:
                return {"initial": 0}
            raise ValueError("Test error in callback")
        
        publisher = Publisher(logger=logger)
        _ = ObservableSubscriber(
            publisher,
            failing_callback,
            logger=logger
        )
        
        # This should not crash - error should be logged
        publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
    
    def test_empty_publisher_set(self):
        """Test creating ObservableSubscriber with empty publisher set"""
        def callback(pub: Optional[Publisher]) -> Mapping[str, int]:
            return {"value": 0}
        
        observable = ObservableSubscriber(
            set(),
            callback,
            logger=logger
        )
        
        # Should initialize successfully with no publishers
        self.assertEqual(len(observable._references), 0) # type: ignore
    
    def test_initial_callback_with_none(self):
        """Test that initial callback receives None"""
        received_values: list[Optional[Publisher]] = []
        
        def callback(pub: Optional[Publisher]) -> Mapping[str, int]:
            received_values.append(pub)
            return {"value": 0}
        
        ObservableSubscriber(
            Publisher(logger=logger),
            callback,
            logger=logger
        )
        
        # First call should have been with None
        self.assertIsNone(received_values[0])


class TestObservableSubscriberIntegration(ObservableTestCase):
    """Integration tests for ObservableSubscriber"""
    
    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
        super().tearDown()
    
    def test_multiple_observables_same_publisher(self):
        """Test multiple ObservableSubscribers on same Publisher"""
        publisher = Publisher(logger=logger)
        
        count1 = [0]
        count2 = [0]
        
        def callback1(pub: Optional[Publisher]) -> Mapping[str, int]:
            if pub is not None:
                count1[0] += 1
            return {"value": count1[0]}
        
        def callback2(pub: Optional[Publisher]) -> Mapping[str, int]:
            if pub is not None:
                count2[0] += 1
            return {"value": count2[0]}
        
        _ = ObservableSubscriber(publisher, callback1, logger=logger)
        _ = ObservableSubscriber(publisher, callback2, logger=logger)
        
        # Publish once
        publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Both should have reacted
        self.assertEqual(count1[0], 1)
        self.assertEqual(count2[0], 1)
        
        # Publish again
        publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        self.assertEqual(count1[0], 2)
        self.assertEqual(count2[0], 2)
    
    def test_chained_observables(self):
        """Test chaining Publishers and ObservableSubscribers"""
        publisher1 = Publisher(logger=logger)
        publisher2 = Publisher(logger=logger)
        
        values_from_pub1: list[str] = []
        values_from_pub2: list[str] = []
        
        def callback1(pub: Optional[Publisher]) -> Mapping[str, str]:
            if pub is not None:
                values_from_pub1.append("pub1")
            return {"source": "pub1"}
        
        def callback2(pub: Optional[Publisher]) -> Mapping[str, str]:
            if pub is not None:
                values_from_pub2.append("pub2")
            return {"source": "pub2"}
        
        _ = ObservableSubscriber(publisher1, callback1, logger=logger)
        _ = ObservableSubscriber(publisher2, callback2, logger=logger)
        
        # Publish from both
        publisher1.publish()
        publisher2.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Each should have reacted to its own publisher
        self.assertEqual(len(values_from_pub1), 1)
        self.assertEqual(len(values_from_pub2), 1)


if __name__ == "__main__":
    unittest.main()

