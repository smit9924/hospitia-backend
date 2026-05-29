from typing import Annotated

from fastapi import APIRouter, Depends

from auth.api.dependencies import RoleValidationDep, SessionDep
from auth.api.services.user_service import (
    get_user_profile_data,
    signupUser,
    validate_username_uniqueness,
)
from auth.database.models.users import Users
from auth.doc.not_found_exceptions_doc import NOT_FOUND_EXCEPTIONS_DOC
from auth.doc.validation_exception_doc import VALIDATION_EXCEPTION_DOC
from auth.schemas.auth_schemas import ParsedJWTPayload, Token
from auth.schemas.user_schemas import (
    ProfileData,
    UsernameAvailabilityRequest,
    UserSignup,
)
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

    return signupUser(session=session, user=user)


@router.get("/list")
async def get_user_list(
    _token: Annotated[
        ParsedJWTPayload,
        Depends(RoleValidationDep([UserType.ADMIN, UserType.OWNER])),
    ],
):
    return "this is list of users"


@router.get("/profile", responses={**NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"],})
async def get_profile_data(
    token: Annotated[
        ParsedJWTPayload,
        Depends(RoleValidationDep([
            UserType.ADMIN,
            UserType.OWNER,
            UserType.MANAGER,
            UserType.CUSTOMER
        ])),
    ],
    session: SessionDep,
) -> ProfileData:
    """
    Retrieve the profile data for the authenticated user.
    """
    return get_user_profile_data(session=session, user_guid=token.parsed_subject.user_guid)



@router.post("/check-username-availability", responses={**VALIDATION_EXCEPTION_DOC["UserWithUsernameAlreadyExistsException"]})
async def check_username_availability(session: SessionDep, username_req: UsernameAvailabilityRequest) -> None:
    """
    Check if a username is available for registration.
    """
    validate_username_uniqueness(session=session, username=username_req.username)
