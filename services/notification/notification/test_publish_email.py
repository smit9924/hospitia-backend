import json

import pika

from notification.core.config import settings


def publish_test_email():
    credentials = pika.PlainCredentials(
        settings.rabbitmq_username,
        settings.rabbitmq_password,
    )

    # Pika internally expects arguments typed as type[_DEFAULT], which causes
    # type-checking conflicts with the provided settings values. Therefore,
    # type checking is ignored for these parameters.
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.rabbitmq_host, #type: ignore[arg-type]
            port=settings.rabbitmq_port, #type: ignore[arg-type]
            credentials=credentials, #type: ignore[arg-type]
        )
    )

    channel = connection.channel()

    message = {
        "channel": "email",
        "priority": 5,
        "payload": {
            "to": ["smitpatel2301322002@gmail.com"],
            "subject": "Manual Test Email 🚀",
            "template": "otp_login",
            "data": {
                "otp": "483921"
            }
        }
    }

    channel.basic_publish(
        exchange=settings.notification_exchange,
        routing_key=settings.email_routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            priority=5,
            content_type="application/json",
        ),
    )

    connection.close()


if __name__ == "__main__":
    publish_test_email()
