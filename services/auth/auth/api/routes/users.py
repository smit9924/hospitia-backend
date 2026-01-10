from fastapi import APIRouter

from auth.api.dependencies import SessionDep, TokenValidateDep
from auth.api.services.user_service import validate_and_create_user
from auth.core.security import create_jwt_access_token
from auth.database.models.users import Users
from auth.schemas.auth_schemas import Token
from auth.schemas.user_schemas import UserSignup
from auth.types.enums import AuthType, UserType

router = APIRouter(tags=["users"])


@router.post("/signup")
async def signup(session: SessionDep, user_signup: UserSignup) -> Token:
    """
    Register a new OWNER user and authenticate them.

    Creates a new user account with OWNER user type using the provided
    registration details. Upon successful registration, the user is
    automatically authenticated and a JWT access token is returned.
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
        subject=
        {
            "user_guid": str(created_user.guid), # UUID is not JSON serializable, convert to string
            "role": created_user.role,
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer"
    )


@router.get("/list")
async def get_user_list(_token: TokenValidateDep):
    return "this is list of users"
