import json
import pika

from backend.services.notification.notification.core.config import settings

def publish_test_email():
    credentials = pika.PlainCredentials(
        settings.rabbitmq_username,
        settings.rabbitmq_password,
    )

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            credentials=credentials,
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

    print("✅ Message published")
    connection.close()


if __name__ == "__main__":
    publish_test_email()
