from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from auth.core.config import settings
from auth.core.security import decode_jwt_token
from auth.database.db import engine


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


def validate_jwt_token(token: TokenDep):
    """
    Validate and decode a JWT access token.

    Description
    -----------
    Attempts to decode and validate the provided JWT access token.
    - If the token is valid, the decoded payload is returned.
    - If a PyJWT-related validation error occurs, the exception is
      propagated as-is so that registered JWT exception handlers
      can generate the appropriate authentication response.
    - Any unexpected exception is converted into a generic
      authentication failure for security reasons.

    Parameters
    ----------
    token : TokenDep
        The JWT access token extracted from the request.

    Returns
    -------
    dict
        The decoded JWT payload if the token is valid.

    Raises
    ------
    InvalidTokenError
        If the JWT is expired, malformed, or fails validation.
    UserUnauthorizedException
        If an unexpected error occurs during token validation.
    """
    return decode_jwt_token(token)

TokenValidateDep = Annotated[str, Depends(validate_jwt_token)]
