from typing import Annotated

from fastapi import APIRouter, Depends

from auth.api.dependencies import RoleValidationDep, SessionDep
from auth.core.security import create_jwt_refresh_token
from auth.api.services.user_service import validate_and_create_user
from auth.core.security import create_jwt_access_token
from auth.database.models.users import Users
from auth.schemas.auth_schemas import JWTSubject, ParsedJWTPayload, Token
from auth.schemas.user_schemas import UserSignup
from auth.types.enums import AuthType, UserType

router = APIRouter(tags=["users"])


@router.post("/signup")
async def signup(session: SessionDep, user_signup: UserSignup) -> Token:
    """
    Register a new OWNER user and authenticate them.

    Creates a new user account with OWNER user type using the provided
    registration details. Upon successful registration, the user is
    automatically authenticated and a JWT access token and refresh token are returned.
    """

    user = Users(
        email=user_signup.email,
        username=user_signup.username,
        password=user_signup.password,
        auth_type=AuthType.MANUAL,
        role=UserType.OWNER,
    )

    created_user = validate_and_create_user(session, user)

    access_token = create_jwt_access_token(
        subject=JWTSubject (
            user_guid=str(created_user.guid), # UUID is not JSON serializable, convert to string
            role=created_user.role,
        )
    )

    refresh_token = create_jwt_refresh_token(
        subject=JWTSubject (
            user_guid=str(created_user.guid), # UUID is not JSON serializable, convert to string
            role=created_user.role,
        )
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.get("/list")
async def get_user_list(
    _token: Annotated[
        ParsedJWTPayload,
        Depends(RoleValidationDep([UserType.ADMIN, UserType.OWNER])),
    ],
):
    return "this is list of users"
