# Dashboard service

User listings for the role dashboards. Part of [Hospitia](https://github.com/smit9924/hospitia-master).

**Documentation:** [Dashboard service](https://github.com/smit9924/hospitia-master/blob/main/docs/backend/dashboard.md) · [API reference](https://github.com/smit9924/hospitia-master/blob/main/docs/reference/api/dashboard.md)

```bash
uv sync
uv run uvicorn dashboard.main:app --reload --reload-dir dashboard --port 8005
uv run ruff check .
```

Apply migrations: `uv run alembic -c ./dashboard/database/alembic.ini upgrade head`
