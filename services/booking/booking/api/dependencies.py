from collections.abc import Callable, Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from booking.api.services.organization_service import resolve_active_organization
from booking.core.config import settings
from booking.core.security import decode_jwt_token
from booking.database.db import engine
from booking.exceptions.definitions.security_exceptions import UserUnauthorizedException
from booking.exceptions.definitions.validation_exceptions import (
    ActiveOrganizationRequiredException,
)
from booking.schemas.auth_schemas import ParsedJWTPayload
from booking.schemas.organization_schemas import ActiveOrganization
from booking.types.constants import ACTIVE_ORGANIZATION_HEADER
from booking.types.enums import TokenType, UserType


def get_session() -> Generator[Session]:
	"""
	Yield a request-scoped SQLModel Session.

	Description:
		Open and yield a Session bound to the application's engine for use
		in FastAPI dependencies. The session is closed automatically when
		the generator exits.

	Parameters:
		None

	Returns:
		Generator[Session, None, None] -- yields a sqlmodel.Session
	"""
	with Session(engine) as session:
		yield session

# Database session dependency
# Intented across the application wherever a DB session is needed
SessionDep = Annotated[Session, Depends(get_session)]


# OAuth2 password bearer flow
oauth2_flow = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")

# OAuth2 token dependency
# Intended for use in routes that require authentication and authorization
TokenDep = Annotated[str, Depends(oauth2_flow)]


def RoleValidationDep(
    roles: list[UserType] | None = None,
    require_email_verified: bool = True,
) -> Callable:
    """
    Dependency factory for JWT validation and role-based authorization.

    Creates and returns a FastAPI dependency function that:
    - Decodes and validates a JWT access token
    - Authorizes the authenticated user against the provided role list
    - Optionally requires the user's email to be verified

    The returned dependency captures the `roles` and `require_email_verified`
    arguments via a closure, allowing role and email-verification requirements
    to be declared at route definition time while keeping the authorization
    logic centralized and stateless.

    Parameters
    ----------
    roles : list[UserType] | None
        List of allowed user roles. If None, only token validity is enforced.
    require_email_verified : bool
        When True (default), the user must have a verified email address.

    Returns
    -------
    Callable
        A FastAPI-compatible dependency function.
    """

    async def validate_jwt_token(token: TokenDep) -> ParsedJWTPayload:
        """
        Decode and validate a JWT access token and authorize the user by role.

        Description
        -----------
        Decodes the JWT access token and parses the payload into a
        strongly-typed schema. On successful validation, the user is authorized
        based on the role provided by the dependency. If no roles are provided,
        treat the route as public and skip token validation and role-based
        authorization checks.

        Parameters
        ----------
        token : str
            The encoded JWT access token.

        Returns
        -------
            None
        """
        if not roles:
            # If no roles are provided, treat user as unauthenticated
            raise UserUnauthorizedException()

        token_payload = decode_jwt_token(token, expected_type= TokenType.ACCESS)

        if (
            token_payload.parsed_subject.role not in roles
            or (require_email_verified and not token_payload.parsed_subject.email_verified)
        ):
            raise UserUnauthorizedException()

        return token_payload

    return validate_jwt_token


def ActiveOrganizationDep(
    roles: list[UserType] | None = None,
) -> Callable:
    """
    Dependency factory resolving the caller's active organization.

    Creates and returns a FastAPI dependency function that:
    - Authenticates and authorizes the caller via `RoleValidationDep(roles)`
    - Reads the active organization GUID from the
      `X-Active-Organization-Guid` request header
    - Validates that the organization exists, is active, and that the
      caller is actively mapped to it

    Endpoints opt in by depending on the returned function; the client's
    GUID is never trusted without this validation.

    Parameters
    ----------
    roles : list[UserType] | None
        Roles allowed to call the endpoint. Only OWNER and MANAGER users
        belong to organizations.

    Returns
    -------
    Callable
        A FastAPI-compatible dependency function returning
        `ActiveOrganization`.
    """

    validate_jwt_token = RoleValidationDep(roles)

    async def resolve_active_organization_dep(
        session: SessionDep,
        token: Annotated[ParsedJWTPayload, Depends(validate_jwt_token)],
        active_organization_guid: Annotated[str | None, Header(alias=ACTIVE_ORGANIZATION_HEADER)] = None,
    ) -> ActiveOrganization:
        """
        Parse the active organization header and resolve it for the caller.

        Raises
        ------
        ActiveOrganizationRequiredException
            If the header is missing or is not a valid UUID.
        ActiveOrganizationInvalidException
            If the organization cannot be used by the caller.
        """
        try:
            organization_guid = UUID((active_organization_guid or "").strip())
        except ValueError:
            raise ActiveOrganizationRequiredException()

        return resolve_active_organization(
            session=session,
            user_guid=token.parsed_subject.user_guid,
            organization_guid=organization_guid,
        )

    return resolve_active_organization_dep
