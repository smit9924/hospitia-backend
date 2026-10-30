# Auth Service

## Provisioning managers

`POST /users/managers` (admin, owner) requires `organizationGuid` in addition to
the usual user fields. Auth doesn't validate it, because it holds no
organization data. It stores the GUID, together with the creator's GUID, on the
`users_outbox` row, and both travel to the booking service in the user-created
event (`organization_guid`, `created_by_guid`). The booking service then maps
the new manager to that organization.

## Tests

```bash
uv run pytest
```

Tests run on in-memory SQLite and need no running Postgres or RabbitMQ.
