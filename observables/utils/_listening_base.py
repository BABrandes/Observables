from typing import Callable

class ListeningBase():

    def __init__(self):
        self._listeners: set[Callable[[], None]] = set()

    @property
    def listeners(self) -> set[Callable[[], None]]:
        """
        Returns a copy of the listeners.
        """
        return self._listeners.copy()

    def add_listeners(self, *callbacks: Callable[[], None]) -> None:
        """
        Add listeners to the observable.

        Args:
            callbacks: The callbacks to be called when the value changes.
        """
        # Prevent duplicate listeners
        for callback in callbacks:
            if callback not in self._listeners:
                self._listeners.add(callback)

    def remove_listeners(self, *callbacks: Callable[[], None]) -> None:
        """
        Remove listeners from the observable.
        """
        for callback in callbacks:
            try:
                self._listeners.remove(callback)
            except KeyError:
                # Ignore if callback doesn't exist
                pass

    def remove_all_listeners(self) -> set[Callable[[], None]]:
        """
        Remove all listeners from the observable.
        """
        removed_listeners = self._listeners
        self._listeners = set()
        return removed_listeners

    def _notify_listeners(self):
        # Notify regular listeners
        for callback in self._listeners:
            callback()
    
    def is_listening_to(self, callback: Callable[[], None]) -> bool:
        return callback in self._listeners