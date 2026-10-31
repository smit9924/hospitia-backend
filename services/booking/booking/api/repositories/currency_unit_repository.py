from uuid import UUID

from sqlmodel import Session, col, func, or_, select

from booking.api.repositories.list_query_helpers import (
    apply_sorting_and_pagination,
    build_contains_pattern,
)
from booking.database.models.currency_unit import CurrencyUnit
from booking.schemas.currency_unit_schemas import (
    CurrencyUnitListQueryParams,
    CurrencyUnitListResponse,
    CurrencyUnitResponse,
)

_SORT_COLUMNS = {
    "currencyCode": CurrencyUnit.currency_code,
    "numericCode": CurrencyUnit.numeric_code,
    "currencyName": CurrencyUnit.currency_name,
    "createdAt": CurrencyUnit.created_at,
    "updatedAt": CurrencyUnit.updated_at,
}


def get_active_currency_unit_by_guid(*, session: Session, guid: UUID | str) -> CurrencyUnit | None:
    """Fetch an active currency unit by its public globally unique identifier.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    guid : UUID | str
        Currency unit GUID to look up.

    Returns
    -------
    CurrencyUnit | None
        Matching active currency unit, or ``None`` if it does not exist or
        was deleted.
    """
    return session.exec(
        select(CurrencyUnit).where(
            CurrencyUnit.guid == guid,
            CurrencyUnit.is_active == True,  # noqa: E712
        )
    ).first()


def get_active_currency_unit_by_currency_code(*, session: Session, currency_code: str) -> CurrencyUnit | None:
    """Fetch the active currency unit that uses an ISO 4217 alphabetic code.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    currency_code : str
        Uppercase ISO 4217 alphabetic code (e.g. "INR").

    Returns
    -------
    CurrencyUnit | None
        Matching active currency unit, or ``None`` if the code is free.
    """
    return session.exec(
        select(CurrencyUnit).where(
            CurrencyUnit.currency_code == currency_code,
            CurrencyUnit.is_active == True,  # noqa: E712
        )
    ).first()


def get_active_currency_unit_by_numeric_code(*, session: Session, numeric_code: str) -> CurrencyUnit | None:
    """Fetch the active currency unit that uses an ISO 4217 numeric code.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.
    numeric_code : str
        Three-digit ISO 4217 numeric code (e.g. "356").

    Returns
    -------
    CurrencyUnit | None
        Matching active currency unit, or ``None`` if the code is free.
    """
    return session.exec(
        select(CurrencyUnit).where(
            CurrencyUnit.numeric_code == numeric_code,
            CurrencyUnit.is_active == True,  # noqa: E712
        )
    ).first()


def create_currency_unit(
    *,
    session: Session,
    currency_code: str,
    numeric_code: str,
    currency_name: str,
    minor_unit: int | None,
    actor_id: int | None,
) -> CurrencyUnit:
    """Create and commit a currency unit.

    Parameters
    ----------
    session : Session
        Active database session used to persist the currency unit.
    currency_code : str
        Uppercase ISO 4217 alphabetic code.
    numeric_code : str
        Three-digit ISO 4217 numeric code.
    currency_name : str
        Human-readable currency name.
    minor_unit : int | None
        Number of decimal places, or ``None`` when not applicable.
    actor_id : int | None
        Internal ID of the user performing the operation, if available.

    Returns
    -------
    CurrencyUnit
        Newly created and refreshed currency unit.
    """
    currency_unit = CurrencyUnit(
        currency_code=currency_code,
        numeric_code=numeric_code,
        currency_name=currency_name,
        minor_unit=minor_unit,
        # Pylance does not recognize inherited properties from AuditMixin.
        created_by=actor_id,  # type: ignore[call-arg]
        updated_by=actor_id,  # type: ignore[call-arg]
    )
    session.add(currency_unit)
    session.commit()
    session.refresh(currency_unit)
    return currency_unit


def update_currency_unit(
    *,
    session: Session,
    currency_unit: CurrencyUnit,
    currency_code: str,
    numeric_code: str,
    currency_name: str,
    minor_unit: int | None,
    actor_id: int | None,
) -> CurrencyUnit:
    """Update and commit a currency unit.

    Parameters
    ----------
    session : Session
        Active database session used to persist the update.
    currency_unit : CurrencyUnit
        Currency unit instance to update.
    currency_code, numeric_code, currency_name, minor_unit
        Replacement values, see `create_currency_unit`.
    actor_id : int | None
        Internal ID of the user performing the update, if available.

    Returns
    -------
    CurrencyUnit
        Updated and refreshed currency unit.
    """
    currency_unit.currency_code = currency_code
    currency_unit.numeric_code = numeric_code
    currency_unit.currency_name = currency_name
    currency_unit.minor_unit = minor_unit
    currency_unit.updated_by = actor_id

    session.add(currency_unit)
    session.commit()
    session.refresh(currency_unit)
    return currency_unit


def soft_delete_currency_unit(*, session: Session, currency_unit: CurrencyUnit, actor_id: int | None) -> None:
    """Soft-delete a currency unit by marking it inactive.

    The row is kept so records that still reference it keep a valid
    foreign key.

    Parameters
    ----------
    session : Session
        Active database session used to commit the change.
    currency_unit : CurrencyUnit
        Currency unit to deactivate.
    actor_id : int | None
        Internal ID of the user performing the deletion, if available.
    """
    currency_unit.is_active = False
    currency_unit.updated_by = actor_id
    session.add(currency_unit)
    session.commit()


def list_active_currency_units_sorted_by_code(*, session: Session) -> list[CurrencyUnit]:
    """List every active currency unit ordered by alphabetic code.

    Used to fill currency drop-downs, so it is not paginated.

    Parameters
    ----------
    session : Session
        Active database session used to execute the query.

    Returns
    -------
    list[CurrencyUnit]
        Active currency units ordered by ``currency_code``.
    """
    return list(
        session.exec(
            select(CurrencyUnit)
            .where(CurrencyUnit.is_active == True)  # noqa: E712
            .order_by(col(CurrencyUnit.currency_code).asc())
        ).all()
    )


def list_currency_units(
    *,
    session: Session,
    query: CurrencyUnitListQueryParams,
) -> CurrencyUnitListResponse:
    """List active currency units with search, sorting, and pagination.

    Parameters
    ----------
    session : Session
        Active database session used to execute the queries.
    query : CurrencyUnitListQueryParams
        Search, sorting, and pagination options.

    Returns
    -------
    CurrencyUnitListResponse
        Paginated currency units and the total matching count.
    """
    active_filter = CurrencyUnit.is_active == True  # noqa: E712
    statement = select(CurrencyUnit).where(active_filter)
    count_statement = select(func.count()).select_from(CurrencyUnit).where(active_filter)

    search_pattern = build_contains_pattern(query.search_term)
    if search_pattern:
        search_filter = or_(
            col(CurrencyUnit.currency_code).ilike(search_pattern),
            col(CurrencyUnit.numeric_code).ilike(search_pattern),
            col(CurrencyUnit.currency_name).ilike(search_pattern),
        )
        statement = statement.where(search_filter)
        count_statement = count_statement.where(search_filter)

    statement = apply_sorting_and_pagination(
        statement=statement,
        sort_column=_SORT_COLUMNS[query.sort_by],
        sort_direction=query.sort_direction,
        page_number=query.page_number,
        page_size=query.page_size,
    )

    total_count = session.exec(count_statement).one()
    currency_units = session.exec(statement).all()

    return CurrencyUnitListResponse(
        items=[
            CurrencyUnitResponse.model_validate(currency_unit, from_attributes=True)
            for currency_unit in currency_units
        ],
        total_count=total_count,
        page_number=query.page_number,
        page_size=query.page_size,
    )
