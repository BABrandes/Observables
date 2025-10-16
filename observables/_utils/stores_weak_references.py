from typing import Generic, TypeVar
import weakref
import time

T = TypeVar("T")

class StoresWeakReferences(Generic[T]):

    def __init__(
        self,
        cleanup_interval: float = 60.0,  # seconds
        max_references_before_cleanup: int = 1000
        ) -> None:

        self._references: set[weakref.ref[T]] = set()
        self._cleanup_interval = cleanup_interval
        self._max_references_before_cleanup = max_references_before_cleanup
        self._last_cleanup_time = time.time()

    def _cleanup(self) -> None:
        """
        Check if a cleanup is needed based on time or size thresholds.
        """
        time_threshold_reached = (time.time() - self._last_cleanup_time) >= self._cleanup_interval
        size_threshold_reached = len(self._references) >= self._max_references_before_cleanup
        
        if time_threshold_reached or size_threshold_reached:
            self._remove_dead_references()

    def _remove_dead_references(self) -> None:
        """
        Remove all dead references and update the last cleanup time.
        """
        dead_references: set[weakref.ref[T]] = set()
        for reference in self._references:
            referenced_value = reference()
            if referenced_value is None:
                dead_references.add(reference)
        self._references -= dead_references
        self._last_cleanup_time = time.time()