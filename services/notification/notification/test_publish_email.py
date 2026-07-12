import json

import pika

from notification.core.config import settings


def publish_test_email():
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USERNAME,
        settings.RABBITMQ_PASSWORD,
    )

    # Pika internally expects arguments typed as type[_DEFAULT], which causes
    # type-checking conflicts with the provided settings values. Therefore,
    # type checking is ignored for these parameters.
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST, #type: ignore[arg-type]
            port=settings.RABBITMQ_PORT, #type: ignore[arg-type]
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
        exchange=settings.EMAIL_NOTIFICATION_EXCHANGE,
        routing_key=settings.FORGOT_PASSWORD_EMAIL_QUEUE_ROUTING_KEY,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            priority=5,
            content_type="application/json",
        ),
    )

    connection.close()


if __name__ == "__main__":
    publish_test_email()
