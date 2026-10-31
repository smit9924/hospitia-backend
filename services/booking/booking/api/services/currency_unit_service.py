from uuid import UUID

from sqlmodel import Session

from booking.api.repositories.currency_unit_repository import (
    create_currency_unit,
    get_active_currency_unit_by_currency_code,
    get_active_currency_unit_by_guid,
    get_active_currency_unit_by_numeric_code,
    list_active_currency_units_sorted_by_code,
    soft_delete_currency_unit,
    update_currency_unit,
)
from booking.api.repositories.currency_unit_repository import (
    list_currency_units as list_currency_units_repo,
)
from booking.api.repositories.room_type_repository import (
    has_active_room_types_using_currency_unit,
)
from booking.database.models.currency_unit import CurrencyUnit
from booking.exceptions.definitions.not_found_exceptions import (
    CurrencyUnitNotFoundException,
)
from booking.exceptions.definitions.validation_exceptions import (
    CurrencyUnitAlreadyExistsException,
    CurrencyUnitInUseException,
)
from booking.schemas.currency_unit_schemas import (
    CurrencyUnitListQueryParams,
    CurrencyUnitListResponse,
    CurrencyUnitOption,
    CurrencyUnitResponse,
    CurrencyUnitUpsertRequest,
)


def get_active_currency_unit_or_raise(*, session: Session, guid: UUID) -> CurrencyUnit:
    """Fetch an active currency unit, raising when it is missing.

    Also used by other services (e.g. room types) to validate a selected
    currency.

    Parameters
    ----------
    session : Session
        Active database session.
    guid : UUID
        Currency unit GUID to look up.

    Returns
    -------
    CurrencyUnit
        The active currency unit.

    Raises
    ------
    CurrencyUnitNotFoundException
        If no active currency unit has this GUID.
    """
    currency_unit = get_active_currency_unit_by_guid(session=session, guid=guid)
    if currency_unit is None:
        raise CurrencyUnitNotFoundException()
    return currency_unit


def _ensure_currency_codes_are_free(
    *,
    session: Session,
    currency_code: str,
    numeric_code: str,
    currency_unit_id_being_updated: int | None,
) -> None:
    """Make sure no other active currency unit uses the same ISO 4217 codes.

    Parameters
    ----------
    session : Session
        Active database session.
    currency_code : str
        Uppercase alphabetic code being saved.
    numeric_code : str
        Numeric code being saved.
    currency_unit_id_being_updated : int | None
        Internal ID of the currency unit being updated, so it does not
        conflict with itself; ``None`` on create.

    Raises
    ------
    CurrencyUnitAlreadyExistsException
        If another active currency unit already uses either code.
    """
    currency_code_owner = get_active_currency_unit_by_currency_code(session=session, currency_code=currency_code)
    if currency_code_owner is not None and currency_code_owner.id != currency_unit_id_being_updated:
        raise CurrencyUnitAlreadyExistsException(message="A currency unit with this currency code already exists.")

    numeric_code_owner = get_active_currency_unit_by_numeric_code(session=session, numeric_code=numeric_code)
    if numeric_code_owner is not None and numeric_code_owner.id != currency_unit_id_being_updated:
        raise CurrencyUnitAlreadyExistsException(message="A currency unit with this numeric code already exists.")


def upsert_currency_unit(
    *,
    session: Session,
    payload: CurrencyUnitUpsertRequest,
    actor_user_id: int,
) -> CurrencyUnitResponse:
    """Create a currency unit, or update the one identified by `payload.guid`.

    Parameters
    ----------
    session : Session
        Active database session.
    payload : CurrencyUnitUpsertRequest
        Validated currency unit fields.
    actor_user_id : int
        Internal ID of the admin performing the operation.

    Returns
    -------
    CurrencyUnitResponse
        The saved currency unit.

    Raises
    ------
    CurrencyUnitNotFoundException
        On update, if `payload.guid` does not match an active currency unit.
    CurrencyUnitAlreadyExistsException
        If another active currency unit already uses either ISO 4217 code.
    """
    existing_currency_unit = None
    if payload.guid is not None:
        existing_currency_unit = get_active_currency_unit_or_raise(session=session, guid=payload.guid)

    _ensure_currency_codes_are_free(
        session=session,
        currency_code=payload.currency_code,
        numeric_code=payload.numeric_code,
        currency_unit_id_being_updated=existing_currency_unit.id if existing_currency_unit else None,
    )

    if existing_currency_unit is None:
        currency_unit = create_currency_unit(
            session=session,
            currency_code=payload.currency_code,
            numeric_code=payload.numeric_code,
            currency_name=payload.currency_name,
            minor_unit=payload.minor_unit,
            actor_id=actor_user_id,
        )
    else:
        currency_unit = update_currency_unit(
            session=session,
            currency_unit=existing_currency_unit,
            currency_code=payload.currency_code,
            numeric_code=payload.numeric_code,
            currency_name=payload.currency_name,
            minor_unit=payload.minor_unit,
            actor_id=actor_user_id,
        )

    return CurrencyUnitResponse.model_validate(currency_unit, from_attributes=True)


def get_currency_unit(*, session: Session, guid: UUID) -> CurrencyUnitResponse:
    """Return a single active currency unit.

    Raises
    ------
    CurrencyUnitNotFoundException
        If no active currency unit has this GUID.
    """
    currency_unit = get_active_currency_unit_or_raise(session=session, guid=guid)
    return CurrencyUnitResponse.model_validate(currency_unit, from_attributes=True)


def ensure_currency_unit_is_not_in_use(*, session: Session, currency_unit_id: int) -> None:
    """Block deleting a currency unit that active records still reference.

    Add one check per referencing table here as new tables reference
    currency units.

    Parameters
    ----------
    session : Session
        Active database session.
    currency_unit_id : int
        Internal ID of the currency unit to validate.

    Raises
    ------
    CurrencyUnitInUseException
        If an active room type is priced in the currency unit.
    """
    if has_active_room_types_using_currency_unit(session=session, currency_unit_id=currency_unit_id):
        raise CurrencyUnitInUseException(message="Cannot delete a currency unit that active room types use.")


def delete_currency_unit(*, session: Session, guid: UUID, actor_user_id: int) -> None:
    """Soft-delete a currency unit that nothing active references.

    Parameters
    ----------
    session : Session
        Active database session.
    guid : UUID
        Currency unit GUID to delete.
    actor_user_id : int
        Internal ID of the admin performing the deletion.

    Raises
    ------
    CurrencyUnitNotFoundException
        If no active currency unit has this GUID.
    CurrencyUnitInUseException
        If an active record still references the currency unit.
    """
    currency_unit = get_active_currency_unit_or_raise(session=session, guid=guid)
    ensure_currency_unit_is_not_in_use(session=session, currency_unit_id=currency_unit.id)
    soft_delete_currency_unit(session=session, currency_unit=currency_unit, actor_id=actor_user_id)


def list_currency_units(
    *,
    session: Session,
    query: CurrencyUnitListQueryParams,
) -> CurrencyUnitListResponse:
    """Return a paginated, sortable, searchable list of active currency units."""
    return list_currency_units_repo(session=session, query=query)


def list_currency_unit_options(*, session: Session) -> list[CurrencyUnitOption]:
    """Return every active currency unit in drop-down form, ordered by code."""
    return [
        CurrencyUnitOption.model_validate(currency_unit, from_attributes=True)
        for currency_unit in list_active_currency_units_sorted_by_code(session=session)
    ]
