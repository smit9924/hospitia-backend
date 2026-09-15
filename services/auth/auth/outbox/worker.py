import logging
from threading import Event, Thread

from auth.core.config import settings
from auth.outbox.service import process_pending_user_outbox

log = logging.getLogger(__name__)

_stop_event = Event()
_worker_thread: Thread | None = None


def start_outbox_worker() -> None:
    """
    Start the users outbox worker thread if it is not already running.
    """
    global _worker_thread

    if _worker_thread is not None and _worker_thread.is_alive():
        log.info("Outbox worker already running")
        return

    _stop_event.clear()
    _worker_thread = Thread(
        target=_run_outbox_worker,
        name="users-outbox-worker",
        daemon=True,
    )
    _worker_thread.start()
    log.info("Outbox worker started")


def stop_outbox_worker() -> None:
    """
    Signal the users outbox worker to stop and wait for the thread to exit.
    """
    global _worker_thread

    _stop_event.set()
    if _worker_thread is not None:
        _worker_thread.join(timeout=settings.OUTBOX_POLL_INTERVAL_SECONDS + 5)
        _worker_thread = None
    log.info("Outbox worker stopped")


def _run_outbox_worker() -> None:
    """
    Poll unprocessed outbox rows until shutdown is requested.
    """
    while not _stop_event.is_set():
        try:
            process_pending_user_outbox()
        except Exception:
            log.exception("Outbox worker iteration failed")
        _stop_event.wait(settings.OUTBOX_POLL_INTERVAL_SECONDS)
