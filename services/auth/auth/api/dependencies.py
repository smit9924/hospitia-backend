from collections.abc import Callable, Generator
from tokenize import Token
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from auth.core.config import settings
from auth.core.security import authorize_user, decode_jwt_token
from auth.database.db import engine
from auth.types.enums import TokenType, UserType


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
) -> Callable:
    """
    Dependency factory for JWT validation and role-based authorization.

    Creates and returns a FastAPI dependency function that:
    - Decodes and validates a JWT access token
    - Authorizes the authenticated user against the provided role list

    The returned dependency captures the `roles` argument via a closure,
    allowing role requirements to be declared at route definition time
    while keeping the authorization logic centralized and stateless.

    Parameters
    ----------
    roles : list[UserType] | None
        List of allowed user roles. If None, only token validity is enforced.

    Returns
    -------
    Callable
        A FastAPI-compatible dependency function.
    """

    async def validate_jwt_token(
        token: TokenDep,
        session: SessionDep,
    ) -> None:
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
            # If no roles are provided, treat the route as public
            # and skip role-based authorization checks
            return

        token_payload = decode_jwt_token(token, expected_type= TokenType.ACCESS)
        authorize_user(
            token_payload=token_payload,
            session=session,
            roles=roles,
        )

    return validate_jwt_token
