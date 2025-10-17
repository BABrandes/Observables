from typing import Callable, Literal, Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from .subscriber import Subscriber

@runtime_checkable
class PublisherLike(Protocol):

    def add_subscriber(self, subscriber: "Subscriber") -> None:
        """
        Add a subscriber to receive publications from this publisher.
        """
        ...

    def add_callback(self, callback: Callable[[], None]) -> None:
        """
        Add a callback to be called when the publisher publishes.
        """
        ...

    def remove_subscriber(self, subscriber: "Subscriber") -> None:
        """
        Remove a subscriber so it no longer receives publications.
        """
        ...

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """
        Remove a callback from being called when the publisher publishes.
        """
        ...

    def publish(self, mode: Literal["async", "sync"] = "async") -> None:
        """
        Publish an update to all subscribed subscribers asynchronously.
        """
        ...