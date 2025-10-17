from typing import Callable, Literal, Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from .subscriber import Subscriber

@runtime_checkable
class PublisherLike(Protocol):

    def add_subscriber(self, subscriber: "Subscriber|Callable[[], None]") -> None:
        """
        Add a subscriber or callback to receive publications from this publisher.
        """
        ...

    def remove_subscriber(self, subscriber: "Subscriber|Callable[[], None]") -> None:
        """
        Remove a subscriber or callback so it no longer receives publications.
        """
        ...

    def publish(self, mode: Literal["async", "sync"] = "async") -> None:
        """
        Publish an update to all subscribed subscribers asynchronously.
        """
        ...