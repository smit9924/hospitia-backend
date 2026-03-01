import logging
import signal
import sys
from notification.messaging.connection import RabbitMQClient
from notification.messaging.consumer import run_consumer

def shutdown_handler(signum, frame):
    """Signal handler for graceful shutdown."""
    logging.info("Shutdown signal received. Stopping consumer...")
    RabbitMQClient.stop_consumer()

if __name__ == "__main__":
    """
    Starts the notification consumer process responsible for
    receiving and processing messaging events from RabbitMQ.
    """
    signal.signal(signal.SIGINT, shutdown_handler) # Handle Ctrl+C
    signal.signal(signal.SIGTERM, shutdown_handler) # Handle termination signals

    try:
        logging.info("starting notification consumer...")
        run_consumer()
    except Exception as exc:
        logging.exception("Consumer encountered an error: %s", exc)
        sys.exit(1)
    finally:
        logging.info("cleaning up resources...")
        RabbitMQClient.close_connection()
        logging.info("notification consumer shutdown complete.")
        sys.exit(0)
        
