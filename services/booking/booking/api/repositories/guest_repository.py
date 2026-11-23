from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, delete, select

from booking.database.models.booking import Booking
from booking.database.models.booking_guest_mapping import BookingGuestMapping
from booking.database.models.guest_detail import GuestDetail
from booking.schemas.booking_schemas import BookingGuestInput


@dataclass(frozen=True)
class BookingGuestEntry:
    """
    One guest of a booking to save.

    Attributes
    ----------
    data : BookingGuestInput
        The validated guest fields. `data.guid` names an existing guest of
        the booking to update; otherwise a new guest is created.
    is_primary : bool
        Whether this is the booking's primary guest.
    """

    data: BookingGuestInput
    is_primary: bool


def list_booking_guests(*, session: Session, booking_ids: Sequence[int]) -> list[BookingGuestMapping]:
    """List the guests of bookings in display order (primary guest first).

    Parameters
    ----------
    session : Session
        Active database session.
    booking_ids : Sequence[int]
        Internal IDs of the bookings.

    Returns
    -------
    list[BookingGuestMapping]
        Mappings with their guest loaded, ordered by booking then position.
    """
    if not booking_ids:
        return []
    statement = (
        select(BookingGuestMapping)
        .options(selectinload(BookingGuestMapping.guest))  # type: ignore[arg-type]
        .where(col(BookingGuestMapping.booking_id).in_(booking_ids))
        .order_by(col(BookingGuestMapping.booking_id), col(BookingGuestMapping.position))
    )
    return list(session.exec(statement).all())


def _apply_guest_fields(guest: GuestDetail, data: BookingGuestInput) -> None:
    """Copy the validated guest fields onto a guest row."""
    guest.first_name = data.first_name
    guest.last_name = data.last_name
    guest.gender = data.gender
    guest.date_of_birth = data.date_of_birth
    guest.phone = data.phone
    guest.email = str(data.email) if data.email is not None else None
    guest.id_proof_type = data.id_proof_type
    guest.id_proof_number = data.id_proof_number
    guest.address = data.address
    guest.nationality = data.nationality


def replace_booking_guests(
    *,
    session: Session,
    booking: Booking,
    guests: Sequence[BookingGuestEntry],
    actor_id: int,
) -> None:
    """Stage the booking's complete guest list without committing.

    Guests of the booking named by GUID are updated in place and keep their
    identity; guests without a known GUID are created; the booking's other
    guests are deleted (a guest belongs to one booking only). The mappings
    are rebuilt in the given order, the primary guest first.

    Parameters
    ----------
    session : Session
        Active database session; the caller commits.
    booking : Booking
        The booking, already flushed so it has an ID.
    guests : Sequence[BookingGuestEntry]
        Every guest the booking should have, in display order.
    actor_id : int
        Internal ID of the user making the change.
    """
    existing_mappings = list_booking_guests(session=session, booking_ids=[booking.id])  # type: ignore[list-item]
    existing_by_guid = {mapping.guest.guid: mapping.guest for mapping in existing_mappings}

    # Remove the old mappings first so positions can be reassigned freely.
    session.exec(delete(BookingGuestMapping).where(col(BookingGuestMapping.booking_id) == booking.id))  # type: ignore[call-overload]
    session.flush()

    kept_guest_ids: set[int] = set()
    for position, entry in enumerate(guests):
        guest = existing_by_guid.get(entry.data.guid) if entry.data.guid is not None else None
        if guest is None:
            guest = GuestDetail(
                organization_id=booking.organization_id,
                first_name=entry.data.first_name,
                last_name=entry.data.last_name,
                gender=entry.data.gender,
                date_of_birth=entry.data.date_of_birth,
                created_by=actor_id,  # type: ignore[call-arg]
            )
        _apply_guest_fields(guest, entry.data)
        guest.updated_by = actor_id
        session.add(guest)
        session.flush()
        kept_guest_ids.add(guest.id)  # type: ignore[arg-type]
        session.add(
            BookingGuestMapping(
                booking_id=booking.id,  # type: ignore[arg-type]
                guest_id=guest.id,  # type: ignore[arg-type]
                is_primary=entry.is_primary,
                position=position,
                created_by=actor_id,  # type: ignore[call-arg]
                updated_by=actor_id,  # type: ignore[call-arg]
            )
        )

    for guest in existing_by_guid.values():
        if guest.id not in kept_guest_ids:
            session.delete(guest)
    session.flush()


__all__ = [
    "BookingGuestEntry",
    "list_booking_guests",
    "replace_booking_guests",
]
