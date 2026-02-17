from notification.messaging.consumer import run_consumer

if __name__ == "__main__":
    """
    Starts the notification consumer process responsible for
    receiving and processing messaging events from RabbitMQ.
    """
    run_consumer()
