"""
Publishes messages after the HTTP response, on a dedicated worker thread.

Some messages (e.g. booking emails) are informative: the request that
triggers them must not wait for the broker, nor fail when it is down. They
are handed to `BackgroundPublisher.submit`, which returns at once; a single
daemon thread publishes them in order through its own MQ client (broker
connections are not thread-safe, so it never shares the request client).
"""

import logging
import queue
import threading
from dataclasses import dataclass

from booking.messaging.base import MQClient
from booking.messaging.general import create_mq_client
from booking.schemas.base_schemas import BaseSchema

log = logging.getLogger(__name__)

# How long shutdown waits for queued messages to be published.
_SHUTDOWN_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class _PendingMessage:
    """A message waiting to be published, with a log-safe label (no personal data)."""

    destination: str
    message: BaseSchema
    log_label: str


class BackgroundPublisher:
    """
    Publishes submitted messages on one background thread, in submission order.

    The thread and its MQ client start lazily on the first submission.
    Failed publishes are logged with the message's label and dropped.
    """

    def __init__(self) -> None:
        self._pending: queue.Queue[_PendingMessage | None] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._client: MQClient | None = None
        self._lock = threading.Lock()

    def submit(self, *, destination: str, message: BaseSchema, log_label: str) -> None:
        """
        Queue a message for publishing and return immediately.

        Args:
            destination: Registered queue (or exchange) name.
            message: Message payload.
            log_label: Short, non-personal description for logs (e.g. a booking reference).
        """
        self._ensure_worker()
        self._pending.put(_PendingMessage(destination=destination, message=message, log_label=log_label))

    def shutdown(self) -> None:
        """Publish what is queued (up to a timeout), stop the thread and close its client."""
        with self._lock:
            worker = self._worker
            self._worker = None
        if worker is None:
            return
        self._pending.put(None)
        worker.join(timeout=_SHUTDOWN_TIMEOUT_SECONDS)
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                log.warning("Background publisher client did not close cleanly")

    def _ensure_worker(self) -> None:
        """Start the worker thread if it is not running."""
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                return
            self._worker = threading.Thread(target=self._run, name="background-publisher", daemon=True)
            self._worker.start()

    def _run(self) -> None:
        """Publish queued messages until the stop marker arrives."""
        while (pending := self._pending.get()) is not None:
            try:
                if self._client is None:
                    self._client = create_mq_client()
                self._client.publish(pending.destination, pending.message)
                log.info("Background message published destination=%s %s", pending.destination, pending.log_label)
            except Exception:
                log.warning("Background message not published destination=%s %s", pending.destination, pending.log_label)


_background_publisher = BackgroundPublisher()


def get_background_publisher() -> BackgroundPublisher:
    """Return the shared background publisher."""
    return _background_publisher


__all__ = ["BackgroundPublisher", "get_background_publisher"]
