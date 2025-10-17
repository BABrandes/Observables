"""
ObservableSubscriber module for reactive observable integration.

This module provides the ObservableSubscriber class, which combines the Publisher-
Subscriber pattern with the Observable framework. It automatically updates its
observable values in response to publications from Publishers.

Example:
    Basic usage with a single publisher::

        from observables import Publisher, ObservableSubscriber
        
        # Create a publisher
        data_source = Publisher()
        
        # Create an observable that reacts to publications
        def get_data(publisher):
            if publisher is None:
                return {"value": 0}  # Initial value
            # Fetch actual data when publisher publishes
            return fetch_current_data()
        
        observable = ObservableSubscriber(
            publisher=data_source,
            on_publication_callback=get_data
        )
        
        # Now when data_source publishes, observable updates automatically
        data_source.publish()
"""

from typing import Generic, TypeVar, Callable, Mapping, Optional, Literal
from logging import Logger

from .._utils.base_observable import BaseObservable
from .._utils.publisher import Publisher
from .._utils.subscriber import Subscriber
from .._utils.nexus_manager import NexusManager
from .._utils.default_nexus_manager import DEFAULT_NEXUS_MANAGER

HK = TypeVar("HK")
HV = TypeVar("HV")


class ObservableSubscriber(BaseObservable[HK, None, HV, None, "ObservableSubscriber"], Subscriber, Generic[HK, HV]):
    """
    An Observable that automatically updates in response to Publisher publications.
    
    ObservableSubscriber bridges the Publisher-Subscriber pattern with the Observable
    framework. It subscribes to one or more Publishers and updates its observable
    values whenever any of them publishes an update, using a callback function to
    determine the new values.
    
    This is particularly useful for creating reactive data flows where observables
    need to react to external events or data sources.
    
    Type Parameters:
        HK: The type of keys in the observable's value mapping.
        HV: The type of values in the observable's value mapping.
    
    Attributes:
        _on_publication_callback: Callback function that generates new values.
        All BaseObservable and Subscriber attributes are also available.
    
    Example:
        Simple reactive observable::
        
            from observables import Publisher, ObservableSubscriber
            
            # Create a data source
            temperature_sensor = Publisher()
            
            # Create observable that updates with sensor data
            def read_temperature(publisher):
                if publisher is None:
                    return {"celsius": 20.0}  # Initial value
                # Read actual temperature when published
                return {"celsius": get_sensor_reading()}
            
            temperature = ObservableSubscriber(
                publisher=temperature_sensor,
                on_publication_callback=read_temperature
            )
            
            # Access current temperature
            print(temperature["celsius"])  # 20.0
            
            # Sensor publishes update
            temperature_sensor.publish()
            print(temperature["celsius"])  # Updated value
        
        Multiple publishers::
        
            # Create multiple data sources
            source1 = Publisher()
            source2 = Publisher()
            source3 = Publisher()
            
            # Observable reacts to any of them
            def aggregate_data(publisher):
                if publisher is None:
                    return {"count": 0}
                # Can check which publisher triggered the update
                if publisher is source1:
                    return {"count": get_count_from_source1()}
                else:
                    return {"count": get_count_from_others()}
            
            data = ObservableSubscriber(
                publisher={source1, source2, source3},
                on_publication_callback=aggregate_data
            )
            
            # Any publisher can trigger an update
            source1.publish()  # Updates data
            source2.publish()  # Also updates data
    
    Note:
        - The callback is called with `None` during initialization to get initial values
        - The callback is called with the publishing Publisher during updates
        - All updates happen asynchronously
        - The observable can be bound to other observables like any other observable
    """

    def __init__(
        self,
        publisher: Publisher|set[Publisher],
        on_publication_callback: Callable[[None|Publisher], Mapping[HK, HV]],
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
    ) -> None:
        """
        Initialize a new ObservableSubscriber.
        
        The subscriber automatically subscribes to the provided publisher(s) and
        will update its values whenever any of them publishes. The callback function
        is used to determine what values the observable should contain.
        
        Args:
            publisher: A single Publisher or a set of Publishers to subscribe to.
                The observable will react to publications from any of them.
            on_publication_callback: A function that takes an Optional[Publisher]
                and returns a Mapping of observable values. It's called with None
                during initialization and with the publishing Publisher during updates.
            logger: Optional logger for error reporting. Passed to the base Observable.
            nexus_manager: The NexusManager to use for hook management. Defaults to
                the global DEFAULT_NEXUS_MANAGER.
        
        Example:
            With a single publisher::
            
                def get_values(pub):
                    if pub is None:
                        return {"x": 0, "y": 0}
                    return {"x": current_x(), "y": current_y()}
                
                observable = ObservableSubscriber(
                    publisher=my_publisher,
                    on_publication_callback=get_values
                )
            
            With multiple publishers::
            
                def get_values(pub):
                    if pub is None:
                        return {"status": "idle"}
                    # Different behavior based on which publisher triggered
                    if pub is pub1:
                        return {"status": "active"}
                    else:
                        return {"status": "processing"}
                
                observable = ObservableSubscriber(
                    publisher={pub1, pub2, pub3},
                    on_publication_callback=get_values,
                    logger=my_logger
                )
        
        Note:
            The callback is immediately called with `None` to get initial values.
            This happens before the observable is fully initialized, so the callback
            should handle the None case appropriately.
        """

        self._on_publication_callback = on_publication_callback

        initial_values: Mapping[HK, HV] = self._on_publication_callback(None)
        
        Subscriber.__init__(self)
        BaseObservable.__init__( # type: ignore
            self,
            initial_values,
            None,
            {},
            None,
            None,
            logger,
            nexus_manager)
        
        # Subscribe to publisher(s)
        if isinstance(publisher, Publisher):
            publisher.add_subscriber(self)
        else:
            for pub in publisher:
                pub.add_subscriber(self)

    def _react_to_publication(self, publisher: Publisher, mode: Literal["async", "sync", "direct"]) -> None:
        """
        React to a publication by updating the observable's values.
        
        This method is called asynchronously when any subscribed Publisher publishes.
        It invokes the callback function with the publisher that triggered the update,
        then submits the returned values to update the observable.
        
        Args:
            publisher: The Publisher that triggered this update.
            mode: The mode of publication.
        
        Raises:
            Any exception raised by the callback function or submit_values will
            propagate and be handled by the Publisher's error handling mechanism.
        
        Example:
            The flow when a publisher publishes::
            
                publisher.publish()
                  ↓
                ObservableSubscriber._react_to_publication(publisher)
                  ↓
                values = on_publication_callback(publisher)
                  ↓
                submit_values(values)
                  ↓
                Observable updates, hooks trigger, bindings propagate
        
        Note:
            This is an internal method called automatically by the Subscriber
            base class. Users don't need to call it directly.
        """
        values: Mapping[HK, HV] = self._on_publication_callback(publisher)
        self.submit_values(values) # type: ignore