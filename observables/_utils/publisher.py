"""
Publisher module for the Publisher-Subscriber pattern implementation.

This module provides a lightweight, async-enabled Publisher class that manages
subscriptions and publishes updates to subscribers using weak references for
automatic memory management.

Example:
    Basic usage::

        from observables._utils.publisher import Publisher
        from observables._utils.subscriber import Subscriber
        
        # Create a publisher
        publisher = Publisher(logger=logger)
        
        # Create and subscribe a subscriber
        subscriber = MySubscriber()
        publisher.add_subscriber(subscriber)
        
        # Publish to all subscribers
        publisher.publish()
"""

from typing import Optional, TYPE_CHECKING
import weakref
import asyncio
from logging import Logger
from .stores_weak_references import StoresWeakReferences

if TYPE_CHECKING:
    from .subscriber import Subscriber

class Publisher(StoresWeakReferences["Subscriber"]):
    """
    A Publisher that manages subscribers and publishes updates asynchronously.
    
    The Publisher uses weak references to track subscribers, enabling automatic
    cleanup when subscribers are garbage collected. It supports threshold-based
    cleanup (time and size) to maintain performance with many subscribers.
    
    Publications are executed asynchronously, allowing subscribers to react
    independently without blocking the publisher or each other.
    
    Attributes:
        _logger (Optional[Logger]): Logger for error reporting.
        _references (set): Set of weak references to subscribers (inherited).
        _cleanup_interval (float): Time threshold for cleanup (inherited).
        _max_subscribers_before_cleanup (int): Size threshold for cleanup (inherited).
    
    Example:
        Basic publisher usage::
        
            import logging
            from observables._utils.publisher import Publisher
            
            # Create publisher with logging
            logger = logging.getLogger(__name__)
            publisher = Publisher(
                logger=logger,
                cleanup_interval=60.0,  # Cleanup every 60 seconds
                max_subscribers_before_cleanup=100  # Or when 100 subscribers
            )
            
            # Add subscribers
            publisher.add_subscriber(subscriber1)
            publisher.add_subscriber(subscriber2)
            
            # Check subscription
            if publisher.is_subscribed(subscriber1):
                print("Subscriber is subscribed")
            
            # Publish to all subscribers
            publisher.publish()
            
            # Remove a subscriber
            publisher.remove_subscriber(subscriber1)
    """

    def __init__(
        self,
        logger: Optional[Logger] = None,
        cleanup_interval: float = 60.0,  # seconds
        max_subscribers_before_cleanup: int = 100
        ) -> None:
        """
        Initialize a new Publisher.
        
        Args:
            logger: Optional logger for error reporting. If provided, subscriber
                errors will be logged. If None, errors will raise RuntimeError.
            cleanup_interval: Time in seconds between automatic cleanup of dead
                subscriber references. Default is 60 seconds.
            max_subscribers_before_cleanup: Maximum number of subscribers before
                triggering automatic cleanup. Default is 100.
        
        Example:
            Create publishers with different configurations::
            
                # Default configuration
                pub1 = Publisher()
                
                # With logging and custom cleanup
                import logging
                logger = logging.getLogger(__name__)
                pub2 = Publisher(
                    logger=logger,
                    cleanup_interval=30.0,
                    max_subscribers_before_cleanup=50
                )
        """
        self._logger: Optional[Logger] = logger
        StoresWeakReferences.__init__(self, cleanup_interval, max_subscribers_before_cleanup) # type: ignore

    def add_subscriber(self, subscriber: "Subscriber") -> None:
        """
        Add a subscriber to receive publications from this publisher.
        
        The subscriber is stored as a weak reference, so it will be automatically
        removed when garbage collected. This method also updates the subscriber's
        internal list of publishers (bidirectional reference).
        
        Args:
            subscriber: The Subscriber instance to add.
        
        Raises:
            No exceptions are raised. If cleanup thresholds are met, dead
            references are automatically cleaned up.
        
        Example:
            Add subscribers to a publisher::
            
                publisher = Publisher()
                subscriber1 = MySubscriber()
                subscriber2 = MySubscriber()
                
                publisher.add_subscriber(subscriber1)
                publisher.add_subscriber(subscriber2)
                
                # Now both will receive publications
                publisher.publish()
        """
        self._cleanup()
        subscriber._add_publisher_called_by_subscriber(self) # type: ignore
        self._references.add(weakref.ref(subscriber))

    def remove_subscriber(self, subscriber: "Subscriber") -> None:
        """
        Remove a subscriber so it no longer receives publications.
        
        This method removes the subscriber from both the publisher's subscriber
        list and the subscriber's publisher list (bidirectional cleanup).
        
        Args:
            subscriber: The Subscriber instance to remove.
        
        Raises:
            ValueError: If the subscriber is not currently subscribed to this
                publisher.
        
        Example:
            Remove a subscriber::
            
                publisher = Publisher()
                subscriber = MySubscriber()
                
                publisher.add_subscriber(subscriber)
                assert publisher.is_subscribed(subscriber)
                
                publisher.remove_subscriber(subscriber)
                assert not publisher.is_subscribed(subscriber)
        """
        self._cleanup()
        subscriber_ref_to_remove = None
        for subscriber_ref in self._references:
            sub = subscriber_ref()
            if sub is subscriber:
                subscriber_ref_to_remove = subscriber_ref
                break
        if subscriber_ref_to_remove is None:
            raise ValueError("Subscriber not found")
        self._references.remove(subscriber_ref_to_remove)
        subscriber._remove_publisher_called_by_subscriber(self) # type: ignore

    def is_subscribed(self, subscriber: "Subscriber") -> bool:
        """
        Check if a subscriber is currently subscribed to this publisher.
        
        Args:
            subscriber: The Subscriber instance to check.
        
        Returns:
            True if the subscriber is subscribed, False otherwise.
        
        Example:
            Check subscription status::
            
                publisher = Publisher()
                subscriber = MySubscriber()
                
                print(publisher.is_subscribed(subscriber))  # False
                
                publisher.add_subscriber(subscriber)
                print(publisher.is_subscribed(subscriber))  # True
        """
        self._cleanup()
        for subscriber_ref in self._references:
            sub = subscriber_ref()
            if sub is subscriber:
                return True

        return False

    def _handle_task_exception(self, task: asyncio.Task[None], subscriber: "Subscriber") -> None:
        """
        Handle exceptions that occur in subscriber reaction tasks.
        
        This callback is executed when an async subscriber task completes. If the
        task raised an exception, it will be logged (if a logger is configured)
        or re-raised as a RuntimeError (if no logger is configured).
        
        Args:
            task: The completed asyncio.Task.
            subscriber: The subscriber whose reaction raised an exception.
        
        Raises:
            RuntimeError: If the task failed and no logger is configured.
        
        Note:
            This is an internal method called automatically by asyncio task
            callbacks. It ensures that subscriber errors are never silently
            ignored.
        """
        try:
            task.result()  # This will raise the exception if one occurred
        except Exception as e:
            error_msg = f"Subscriber {subscriber} failed to react to publication: {e}"
            if self._logger:
                self._logger.error(error_msg, exc_info=True)
            else:
                # Re-raise if no logger is configured so the error isn't silently ignored
                raise RuntimeError(error_msg) from e

    def publish(self) -> None:
        """
        Publish an update to all subscribed subscribers asynchronously.
        
        This method triggers the `react_to_publication` method on each subscriber.
        All reactions execute asynchronously and independently - they do not block
        the publisher or each other.
        
        Dead subscriber references are automatically skipped. If cleanup thresholds
        are met, dead references are cleaned up before publishing.
        
        Error Handling:
            - If a subscriber's reaction raises an exception and a logger is
              configured, the error is logged and other subscribers continue.
            - If no logger is configured, the error raises a RuntimeError.
        
        Example:
            Publish to subscribers::
            
                publisher = Publisher(logger=logger)
                
                # Add subscribers
                publisher.add_subscriber(subscriber1)
                publisher.add_subscriber(subscriber2)
                
                # Publish - both subscribers react asynchronously
                publisher.publish()
                
                # The publish() method returns immediately
                # Subscribers react in the background
        
        Note:
            This method returns immediately. Subscriber reactions execute
            asynchronously in the event loop. Use `await asyncio.sleep(0)`
            or similar to allow reactions to complete if needed for testing.
        """
        # Check if we should do a full cleanup before publishing
        self._cleanup()
        
        for subscriber_ref in self._references:
            subscriber: Subscriber | None = subscriber_ref()
            if subscriber is not None:
                task: asyncio.Task[None] = subscriber.react_to_publication(self) # type: ignore
                task.add_done_callback(
                    lambda t, s=subscriber: self._handle_task_exception(t, s)
                )