# Booking Service

## Active organization

Owners and managers work within one **active organization** per login session.
The client stores the selection and sends it on every booking request in the
`X-Active-Organization-Guid` header (`booking.types.constants.ACTIVE_ORGANIZATION_HEADER`).
The backend never trusts that value without validating it.

### Endpoints

| Method | Path | Access | Purpose |
|---|---|---|---|
| `GET` | `/organization/memberships` | Owner, Manager | Every active organization the caller is actively mapped to, sorted by name. Not paginated; no header required. |
| `GET` | `/organization/active` | Owner, Manager | Validates the header and returns the organization summary. |

### Scoping an endpoint to the active organization

Depend on `ActiveOrganizationDep` (`booking.api.dependencies`). It authenticates
the caller like `RoleValidationDep` and returns the resolved `ActiveOrganization`
(internal `id` plus `guid`):

```python
@router.get("/example")
async def example_route(
    session: SessionDep,
    active_organization: Annotated[ActiveOrganization, Depends(ActiveOrganizationDep([UserType.OWNER, UserType.MANAGER]))],
) -> ...:
    ...
```

| Status | Error code | When |
|---|---|---|
| 400 | `ACTIVE_ORGANIZATION_REQUIRED` (2012) | Header missing or not a UUID. |
| 403 | `ACTIVE_ORGANIZATION_INVALID` (2013) | Organization not found, inactive, or the caller has no active mapping to it. One code for all three so the response never reveals whether an organization exists. |

### Managers created with an organization

The auth service's user-created event carries `organization_guid` and
`created_by_guid` when a manager is provisioned. `user_created_handler` upserts
the replica, then maps the manager to that organization if it exists, is
active, and the creator is an admin or an active owner of it. Otherwise the
mapping is skipped with a warning and an admin can map the manager later
through `POST /organization/manager`.

## Tests

```bash
uv run pytest
```

Tests run on in-memory SQLite and need no running Postgres or RabbitMQ.
