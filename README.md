# hospitia-backend

The backend services of [Hospitia](https://github.com/smit9924/hospitia-master), a guest house management system for NGOs: Python 3.13 FastAPI services managed with uv.

This repository is used inside the `hospitia-master` workspace, cloned into `hospitia-master/backend`. **All documentation lives in hospitia-master:** start with the [Backend overview](https://github.com/smit9924/hospitia-master/blob/main/docs/backend/index.md) and [Getting started](https://github.com/smit9924/hospitia-master/blob/main/docs/getting-started/index.md).

| Service | Purpose | Local port | Docs |
|---|---|---|---|
| `services/auth` | Users, sign-in, tokens, roles | 8000 | [Auth](https://github.com/smit9924/hospitia-master/blob/main/docs/backend/auth.md) |
| `services/booking` | Organizations and room setup | 8004 | [Booking](https://github.com/smit9924/hospitia-master/blob/main/docs/backend/booking.md) |
| `services/dashboard` | User listings | 8005 | [Dashboard](https://github.com/smit9924/hospitia-master/blob/main/docs/backend/dashboard.md) |
| `services/payment` | Payments (skeleton) | 8006 | [Payment](https://github.com/smit9924/hospitia-master/blob/main/docs/backend/payment.md) |
| `services/notification` | Emails (no HTTP API) | 8002 | [Notification](https://github.com/smit9924/hospitia-master/blob/main/docs/backend/notification.md) |

```bash
cd services/<service>
uv sync
uv run uvicorn <service>.main:app --reload --reload-dir <service> --port <port>
uv run ruff check .
```

`scripts/create_migration.sh` generates Alembic migrations; see [Database migrations](https://github.com/smit9924/hospitia-master/blob/main/docs/guides/database-migrations.md).

Contributing: [CONTRIBUTING.md](CONTRIBUTING.md) · Security: [SECURITY.md](SECURITY.md)
