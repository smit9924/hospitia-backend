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

## Bookings

Admins, owners and managers book one room of an organization for a stay
(`check_in_date` up to, not including, `check_out_date`) with exactly one
primary guest and secondary guests up to the room type's capacity. Owners and
managers work in their active organization; admins pass `organizationGuid`.

| Method | Path | Access | Purpose |
|---|---|---|---|
| `POST` | `/booking/create` | Admin, Owner, Manager | Create a booking with its guests (`recordAsCompletedStay` saves an ended stay as checked out). |
| `PUT` | `/booking/update` | Admin, Owner, Manager | Update a booking and its complete guest list; what may change depends on the status. |
| `GET` | `/booking` | Admin, Owner, Manager | Paginated listing: search (reference, primary guest name/phone, room number), status and stay-date filters. ID numbers are masked. |
| `GET` | `/booking/detail` | Admin, Owner, Manager | One booking with its guests (full ID numbers) and status history. |
| `GET` | `/booking/available-rooms` | Admin, Owner, Manager | Available rooms free for a stay, with capacity and nightly cost. |
| `POST` | `/booking/check-in`, `/booking/check-out`, `/booking/cancel` | Admin, Owner, Manager | Lifecycle: confirmed → checked in → checked out, or confirmed → cancelled. |
| `GET` | `/booking/today-summary` | Owner, Manager | Arrivals, departures and in-house counts for the dashboard. |
| `GET` | `/room/floor-overview?onDate=` | Owner, Manager | Each room also carries the booking occupying it that day. |

- The pure rules (dates, price, capacity, transitions, masking, occupancy) live in
  `booking.api.services.booking_rules`; `booking_service` applies them.
- A room never holds two confirmed or checked-in bookings for overlapping stays:
  the overlap check and the save run under the room's row lock
  (`booking_repository.room_booking_lock`).
- Confirmation, update and cancellation emails go to the primary guest through
  the notification service. They are published by `BackgroundPublisher`
  (`booking.messaging.background_publisher`) after the response, so a broker
  outage never slows or fails a booking.
- A room with confirmed or checked-in bookings can't be deleted.

## Tests

```bash
uv run pytest
```

Tests need no running Postgres or RabbitMQ. The booking rules and request
schemas are covered in `tests/`.
