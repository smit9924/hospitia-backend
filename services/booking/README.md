# Booking service

Organizations, memberships, currency units, room amenities, room types and rooms. Part of [Hospitia](https://github.com/smit9924/hospitia-master).

**Documentation:** [Booking service](https://github.com/smit9924/hospitia-master/blob/main/docs/backend/booking.md) · [API reference](https://github.com/smit9924/hospitia-master/blob/main/docs/reference/api/booking.md)

```bash
uv sync
uv run uvicorn booking.main:app --reload --reload-dir booking --port 8004
uv run ruff check .
```

Apply migrations: `uv run alembic -c ./booking/database/alembic.ini upgrade head`
