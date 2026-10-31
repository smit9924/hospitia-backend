from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from booking.api.dependencies import RoleValidationDep, SessionDep
from booking.api.services.currency_unit_service import (
    delete_currency_unit,
    get_currency_unit,
    list_currency_unit_options,
    list_currency_units,
    upsert_currency_unit,
)
from booking.api.services.organization_service import get_user_id_from_user_guid
from booking.doc.not_found_exceptions_doc import NOT_FOUND_EXCEPTIONS_DOC
from booking.doc.security_exceptions_doc import SECURITY_EXCEPTION_DOC
from booking.doc.validation_exception_doc import VALIDATION_EXCEPTION_DOC
from booking.schemas.auth_schemas import ParsedJWTPayload
from booking.schemas.currency_unit_schemas import (
    CurrencyUnitListQueryParams,
    CurrencyUnitListResponse,
    CurrencyUnitOption,
    CurrencyUnitResponse,
    CurrencyUnitUpsertRequest,
)
from booking.types.enums import UserType

_ADMIN_ONLY = [UserType.ADMIN]
_ADMIN_OWNER_MANAGER = [UserType.ADMIN, UserType.OWNER, UserType.MANAGER]

router = APIRouter(tags=["currency-unit"])

_AUTH_RESPONSES = {
    **SECURITY_EXCEPTION_DOC["UserUnauthorizedException"],
    **SECURITY_EXCEPTION_DOC["InvalidTokenException"],
}


@router.post("/create", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["CurrencyUnitNotFoundException"], **VALIDATION_EXCEPTION_DOC["CurrencyUnitAlreadyExistsException"]})
@router.put("/create", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["CurrencyUnitNotFoundException"], **VALIDATION_EXCEPTION_DOC["CurrencyUnitAlreadyExistsException"]})
async def upsert_currency_unit_route(
    session: SessionDep,
    payload: CurrencyUnitUpsertRequest,
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> CurrencyUnitResponse:
    """
    Create a new currency unit, or update an existing one when `guid` is
    supplied. Admin-only.
    """
    actor_user_id = get_user_id_from_user_guid(session=session, guid=token.parsed_subject.user_guid)
    return upsert_currency_unit(session=session, payload=payload, actor_user_id=actor_user_id)


@router.delete("/delete", status_code=204, responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **NOT_FOUND_EXCEPTIONS_DOC["CurrencyUnitNotFoundException"], **VALIDATION_EXCEPTION_DOC["CurrencyUnitInUseException"]})
async def delete_currency_unit_route(
    session: SessionDep,
    guid: Annotated[UUID, Query()],
    token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> None:
    """
    Soft-delete a currency unit identified by `guid`. Rejected while an
    active record still uses it. Admin-only.
    """
    actor_user_id = get_user_id_from_user_guid(session=session, guid=token.parsed_subject.user_guid)
    delete_currency_unit(session=session, guid=guid, actor_user_id=actor_user_id)


@router.get("", responses={**_AUTH_RESPONSES})
async def list_currency_units_route(
    session: SessionDep,
    query: Annotated[CurrencyUnitListQueryParams, Query()],
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> CurrencyUnitListResponse:
    """
    Return a paginated, sortable, searchable list of active currency
    units. Admin-only.
    """
    return list_currency_units(session=session, query=query)


@router.get("/options", responses={**_AUTH_RESPONSES})
async def list_currency_unit_options_route(
    session: SessionDep,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER_MANAGER))],
) -> list[CurrencyUnitOption]:
    """
    Return every active currency unit, ordered by code, for currency
    drop-downs. Not paginated. Admin, Owner and Manager.
    """
    return list_currency_unit_options(session=session)


@router.get("/{guid}", responses={**_AUTH_RESPONSES, **NOT_FOUND_EXCEPTIONS_DOC["CurrencyUnitNotFoundException"]})
async def get_currency_unit_route(
    session: SessionDep,
    guid: UUID,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> CurrencyUnitResponse:
    """
    Fetch a single active currency unit by guid. Admin-only.
    """
    return get_currency_unit(session=session, guid=guid)
