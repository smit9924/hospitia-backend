# Notification service

Sends emails from RabbitMQ messages using Jinja templates. It has no HTTP API. Part of [Hospitia](https://github.com/smit9924/hospitia-master).

**Documentation:** [Notification service](https://github.com/smit9924/hospitia-master/blob/main/docs/backend/notification.md)

```bash
uv sync
uv run uvicorn notification.main:app --reload --reload-dir notification --port 8002
uv run ruff check .
```
