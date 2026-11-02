# Payment service

Payments (skeleton: user replica and health check). Part of [Hospitia](https://github.com/smit9924/hospitia-master).

**Documentation:** [Payment service](https://github.com/smit9924/hospitia-master/blob/main/docs/backend/payment.md) · [API reference](https://github.com/smit9924/hospitia-master/blob/main/docs/reference/api/payment.md)

```bash
uv sync
uv run uvicorn payment.main:app --reload --reload-dir payment --port 8006
uv run ruff check .
```

Apply migrations: `uv run alembic -c ./payment/database/alembic.ini upgrade head`
