from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from uuid import UUID

from sqlalchemy import ColumnElement, Sequence, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.selectable import SelectBase
from sqlmodel import Session, col, func, select

from booking.database.models.booking import Booking
from booking.database.models.booking_guest_mapping import BookingGuestMapping
from booking.database.models.guest_detail import GuestDetail
from booking.database.models.organization import Organization
from booking.database.models.room import Room
from booking.database.models.room_type import RoomType
from booking.schemas.booking_schemas import BookingListQueryParams
from booking.types.enums import BookingStatus, RoomStatus

# Numbers the "BK-<year>-<number>" references (created by the migration).
_BOOKING_REFERENCE_SEQUENCE = Sequence("booking_reference_seq")

# Bookings that hold their room for their dates.
_ACTIVE_STATUSES = (BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN)

_SORT_COLUMNS = {
    "checkInDate": Booking.check_in_date,
    "createdAt": Booking.created_at,
}

# Everything a booking response shows, loaded with the booking.
_BOOKING_LOAD_OPTIONS = (
    selectinload(Booking.organization),  # type: ignore[arg-type]
    selectinload(Booking.room).selectinload(Room.room_type),  # type: ignore[arg-type]
    selectinload(Booking.currency_unit),  # type: ignore[arg-type]
    selectinload(Booking.booker),  # type: ignore[arg-type]
    selectinload(Booking.checked_in_user),  # type: ignore[arg-type]
    selectinload(Booking.checked_out_user),  # type: ignore[arg-type]
    selectinload(Booking.cancelled_user),  # type: ignore[arg-type]
)


def next_booking_reference_number(*, session: Session) -> int:
    """Return the next booking number from the reference sequence.

    Parameters
    ----------
    session : Session
        Active database session.

    Returns
    -------
    int
        A number never handed out before.
    """
    return int(session.exec(select(_BOOKING_REFERENCE_SEQUENCE.next_value())).one())  # type: ignore[call-overload]


@contextmanager
def room_booking_lock(*, session: Session, room_id: int) -> Iterator[None]:
    """Hold the room's row lock while a booking for it is checked and saved.

    Saving a booking checks for overlapping stays and then writes; holding
    the room lock in between makes concurrent saves for the same room run
    one after another, so two overlapping stays can never both be saved.
    The block must end by committing (which releases the lock); if it raises,
    the transaction is rolled back here so the lock is released at once.

    Parameters
    ----------
    session : Session
        Active database session.
    room_id : int
        Internal ID of the room being booked.
    """
    session.exec(select(Room.id).where(Room.id == room_id).with_for_update()).first()
    try:
        yield
    except BaseException:
        session.rollback()
        raise


def _overlaps(check_in_date: date, check_out_date: date) -> ColumnElement[bool]:
    """SQL condition: the booking's stay overlaps [check_in_date, check_out_date)."""
    return and_(Booking.check_in_date < check_out_date, Booking.check_out_date > check_in_date)


def has_overlapping_booking(
    *,
    session: Session,
    room_id: int,
    check_in_date: date,
    check_out_date: date,
    exclude_booking_id: int | None,
) -> bool:
    """Check whether another confirmed or checked-in booking of the room overlaps the stay.

    Stays are half-open, so a stay ending on a day does not overlap one
    starting that day.

    Parameters
    ----------
    session : Session
        Active database session.
    room_id : int
        Internal ID of the room.
    check_in_date, check_out_date : date
        The stay to check.
    exclude_booking_id : int | None
        Internal ID of the booking being edited, which may keep its own room.

    Returns
    -------
    bool
        ``True`` when the room is already taken for part of the stay.
    """
    filters: list[ColumnElement[bool]] = [
        Booking.room_id == room_id,
        col(Booking.status).in_(_ACTIVE_STATUSES),
        _overlaps(check_in_date, check_out_date),
    ]
    if exclude_booking_id is not None:
        filters.append(Booking.id != exclude_booking_id)
    return session.exec(select(func.count()).select_from(Booking).where(*filters)).one() > 0


def has_active_bookings_for_room(*, session: Session, room_id: int) -> bool:
    """Check whether the room still has a confirmed or checked-in booking.

    Parameters
    ----------
    session : Session
        Active database session.
    room_id : int
        Internal ID of the room.

    Returns
    -------
    bool
        ``True`` when at least one such booking exists.
    """
    statement = (
        select(func.count())
        .select_from(Booking)
        .where(Booking.room_id == room_id, col(Booking.status).in_(_ACTIVE_STATUSES))
    )
    return session.exec(statement).one() > 0


def get_booking_by_guid(*, session: Session, guid: UUID | str) -> Booking | None:
    """Fetch a booking, with everything its response shows, by GUID.

    Parameters
    ----------
    session : Session
        Active database session.
    guid : UUID | str
        Booking GUID to look up.

    Returns
    -------
    Booking | None
        The booking, or ``None`` if it does not exist.
    """
    return session.exec(select(Booking).options(*_BOOKING_LOAD_OPTIONS).where(Booking.guid == guid)).first()


def add_booking(*, session: Session, booking: Booking) -> Booking:
    """Stage a new booking and assign its ID without committing.

    Parameters
    ----------
    session : Session
        Active database session.
    booking : Booking
        The booking to insert.

    Returns
    -------
    Booking
        The same booking, flushed so its `id` is set.
    """
    session.add(booking)
    session.flush()
    return booking


def save_booking(*, session: Session, booking: Booking) -> Booking:
    """Commit the booking with every change staged in the session and reload it.

    Parameters
    ----------
    session : Session
        Active database session holding the booking and its guest changes.
    booking : Booking
        The booking to save.

    Returns
    -------
    Booking
        The saved booking with its relationships loaded.
    """
    session.add(booking)
    session.commit()
    saved = get_booking_by_guid(session=session, guid=booking.guid)  # type: ignore[arg-type]
    assert saved is not None
    return saved


def _primary_guest_join_condition() -> ColumnElement[bool]:
    """Join condition from a booking to its primary guest mapping."""
    return and_(BookingGuestMapping.booking_id == Booking.id, col(BookingGuestMapping.is_primary).is_(True))


def _join_room_and_primary_guest[T: SelectBase](statement: T) -> T:
    """Join a booking statement to its room and primary guest, which the listing search reads."""
    return (
        statement.join(Room, Room.id == Booking.room_id)  # type: ignore[attr-defined, arg-type]
        .outerjoin(BookingGuestMapping, _primary_guest_join_condition())
        .outerjoin(GuestDetail, GuestDetail.id == BookingGuestMapping.guest_id)  # type: ignore[arg-type]
    )


def list_bookings_page(
    *,
    session: Session,
    query: BookingListQueryParams,
    organization_id: int | None,
) -> tuple[list[Booking], int]:
    """List bookings with search, filters, sorting and pagination.

    Parameters
    ----------
    session : Session
        Active database session.
    query : BookingListQueryParams
        Search, filters, sorting and pagination options.
    organization_id : int | None
        Restricts the list to one organization; ``None`` lists the bookings
        of every active organization (admin view).

    Returns
    -------
    tuple[list[Booking], int]
        The page of bookings (relationships loaded) and the total matching
        count.
    """
    filters: list[ColumnElement[bool]] = []
    if organization_id is None:
        active_organization_ids = select(Organization.id).where(Organization.is_active == True)  # noqa: E712
        filters.append(col(Booking.organization_id).in_(active_organization_ids))
    else:
        filters.append(Booking.organization_id == organization_id)

    if query.statuses:
        filters.append(col(Booking.status).in_(query.statuses))
    # A stay [check-in, check-out) overlaps the inclusive range [from, to].
    if query.from_date is not None:
        filters.append(Booking.check_out_date > query.from_date)
    if query.to_date is not None:
        filters.append(Booking.check_in_date <= query.to_date)

    search_term = (query.search_term or "").strip()
    if search_term:
        pattern = f"%{_escape_like(search_term)}%"
        full_name = func.concat(GuestDetail.first_name, " ", GuestDetail.last_name)
        filters.append(
            or_(
                col(Booking.reference).ilike(pattern, escape="\\"),
                col(Room.room_number).ilike(pattern, escape="\\"),
                full_name.ilike(pattern, escape="\\"),
                col(GuestDetail.phone).ilike(pattern, escape="\\"),
            )
        )

    statement = _join_room_and_primary_guest(select(Booking).options(*_BOOKING_LOAD_OPTIONS)).where(*filters)
    sort_column = col(_SORT_COLUMNS[query.sort_by])
    # Secondary order by reference keeps pages stable for equal dates.
    if query.sort_direction == "desc":
        statement = statement.order_by(sort_column.desc(), col(Booking.reference).desc())
    else:
        statement = statement.order_by(sort_column.asc(), col(Booking.reference).asc())
    statement = statement.offset((query.page_number - 1) * query.page_size).limit(query.page_size)

    count_statement = _join_room_and_primary_guest(select(func.count(col(Booking.id))).select_from(Booking)).where(*filters)
    return list(session.exec(statement).all()), session.exec(count_statement).one()


def _escape_like(text: str) -> str:
    """Escape LIKE wildcards so the search term is matched literally."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def list_available_rooms(
    *,
    session: Session,
    organization_id: int,
    check_in_date: date,
    check_out_date: date,
    exclude_booking_id: int | None,
) -> list[Room]:
    """List the organization's rooms that can be booked for the stay.

    A room qualifies when it is active, its status is available, and no other
    confirmed or checked-in booking overlaps the stay.

    Parameters
    ----------
    session : Session
        Active database session.
    organization_id : int
        Internal ID of the organization.
    check_in_date, check_out_date : date
        The stay.
    exclude_booking_id : int | None
        Internal ID of the booking being edited, which may keep its room.

    Returns
    -------
    list[Room]
        Rooms with their room type and its currency loaded, ordered by
        floor (top first) then room number.
    """
    overlap_filters: list[ColumnElement[bool]] = [
        Booking.room_id == Room.id,
        col(Booking.status).in_(_ACTIVE_STATUSES),
        _overlaps(check_in_date, check_out_date),
    ]
    if exclude_booking_id is not None:
        overlap_filters.append(Booking.id != exclude_booking_id)
    taken = select(Booking.id).where(*overlap_filters).exists()

    statement = (
        select(Room)
        .options(selectinload(Room.room_type).selectinload(RoomType.currency_unit))  # type: ignore[arg-type]
        .where(
            Room.organization_id == organization_id,
            Room.is_active == True,  # noqa: E712
            Room.status == RoomStatus.AVAILABLE,
            ~taken,
        )
        .order_by(col(Room.floor).desc(), func.lower(Room.room_number))
    )
    return list(session.exec(statement).all())


def count_today(*, session: Session, organization_id: int, on_date: date) -> tuple[int, int, int]:
    """Count today's arrivals, departures and in-house bookings of an organization.

    Parameters
    ----------
    session : Session
        Active database session.
    organization_id : int
        Internal ID of the organization.
    on_date : date
        The day to look at.

    Returns
    -------
    tuple[int, int, int]
        Arrivals (confirmed, checking in on the day), departures (checked
        in, checking out on the day) and in-house (checked in) counts.
    """

    def _count(*conditions: ColumnElement[bool]) -> int:
        statement = (
            select(func.count()).select_from(Booking).where(Booking.organization_id == organization_id, *conditions)
        )
        return session.exec(statement).one()

    return (
        _count(Booking.status == BookingStatus.CONFIRMED, Booking.check_in_date == on_date),
        _count(Booking.status == BookingStatus.CHECKED_IN, Booking.check_out_date == on_date),
        _count(Booking.status == BookingStatus.CHECKED_IN),
    )


def list_bookings_around_date(*, session: Session, organization_id: int, on_date: date) -> list[Booking]:
    """List the organization's active bookings that may occupy a room on a date.

    Returns every confirmed or checked-in booking whose stay includes the
    date or ends on it; `booking_rules.find_occupancy` decides which one
    occupies each room.

    Parameters
    ----------
    session : Session
        Active database session.
    organization_id : int
        Internal ID of the organization.
    on_date : date
        The day to look at.

    Returns
    -------
    list[Booking]
        Candidate bookings.
    """
    statement = select(Booking).where(
        Booking.organization_id == organization_id,
        col(Booking.status).in_(_ACTIVE_STATUSES),
        Booking.check_in_date <= on_date,
        Booking.check_out_date >= on_date,
    )
    return list(session.exec(statement).all())


__all__ = [
    "add_booking",
    "count_today",
    "get_booking_by_guid",
    "has_active_bookings_for_room",
    "has_overlapping_booking",
    "list_available_rooms",
    "list_bookings_around_date",
    "list_bookings_page",
    "next_booking_reference_number",
    "room_booking_lock",
    "save_booking",
]
