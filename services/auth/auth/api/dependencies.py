from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from auth.core.config import settings
from auth.core.security import decode_jwt_token
from auth.database.db import engine
from auth.schemas.auth_schemas import ParsedJWTAccessTokenPayload


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


def validate_jwt_token(token: TokenDep, session: SessionDep) -> ParsedJWTAccessTokenPayload:
    """
    Decode and validate a JWT access token and authorize the user by role.

    Description
    -----------
    Decodes the JWT access token and parses the payload into a
    strongly-typed schema. On successful validation, the user is authorized
    based on the role provided by the dependency.

    Parameters
    ----------
    token : str
        The encoded JWT access token.

    Returns
    -------
    ParsedJWTAccessTokenPayload
        The validated JWT payload containing expiration details and the
        parsed subject data.
    """
    return decode_jwt_token(token)



# Dependencies to validate JWT token and authorize user based on role provided
TokenValidateDep = Annotated[ParsedJWTAccessTokenPayload, Depends(validate_jwt_token)]
