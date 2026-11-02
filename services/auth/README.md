# Auth service

Users, sign-in, tokens, email verification, password reset and user provisioning. Part of [Hospitia](https://github.com/smit9924/hospitia-master).

**Documentation:** [Auth service](https://github.com/smit9924/hospitia-master/blob/main/docs/backend/auth.md) · [API reference](https://github.com/smit9924/hospitia-master/blob/main/docs/reference/api/auth.md)

```bash
uv sync
uv run uvicorn auth.main:app --reload --reload-dir auth --port 8000
uv run ruff check .
```

Apply migrations: `uv run alembic -c ./auth/database/alembic.ini upgrade head`
