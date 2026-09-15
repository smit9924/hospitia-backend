from typing import Annotated

from fastapi import APIRouter, Depends, Query

from dashboard.api.dependencies import RoleValidationDep, SessionDep
from dashboard.api.services.user_listing_service import (
    list_admins,
    list_customers,
    list_managers,
    list_owners,
)
from dashboard.schemas.auth_schemas import ParsedJWTPayload
from dashboard.schemas.user_schemas import UserListQueryParams, UserListResponse
from dashboard.types.enums import UserType

router = APIRouter(tags=["users"])


@router.get("/admins")
def get_admins(
    session: SessionDep,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep([UserType.ADMIN]))],
    query: Annotated[UserListQueryParams, Query()],
) -> UserListResponse:
    """Return a paginated list of admin users."""
    return list_admins(session=session, query=query)


@router.get("/owners")
def get_owners(
    session: SessionDep,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep([UserType.ADMIN]))],
    query: Annotated[UserListQueryParams, Query()],
) -> UserListResponse:
    """Return a paginated list of owner users."""
    return list_owners(session=session, query=query)


@router.get("/managers")
def get_managers(
    session: SessionDep,
    _token: Annotated[
        ParsedJWTPayload,
        Depends(RoleValidationDep([UserType.ADMIN, UserType.OWNER])),
    ],
    query: Annotated[UserListQueryParams, Query()],
) -> UserListResponse:
    """Return a paginated list of manager users."""
    return list_managers(session=session, query=query)


@router.get("/customers")
def get_customers(
    session: SessionDep,
    _token: Annotated[
        ParsedJWTPayload,
        Depends(RoleValidationDep([UserType.ADMIN, UserType.OWNER, UserType.MANAGER])),
    ],
    query: Annotated[UserListQueryParams, Query()],
) -> UserListResponse:
    """Return a paginated list of customer users."""
    return list_customers(session=session, query=query)
