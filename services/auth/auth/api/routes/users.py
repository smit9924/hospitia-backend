from typing import Annotated

from fastapi import APIRouter, Depends, Query

from auth.api.dependencies import RoleValidationDep, SessionDep
from auth.api.services.user_service import (
    change_user_password,
    get_user_profile_data,
    request_email_verification_otp,
    signupUser,
    update_user_profile,
    validate_username_uniqueness,
    verify_email_otp,
)
from auth.database.models.users import Users
from auth.doc.not_found_exceptions_doc import NOT_FOUND_EXCEPTIONS_DOC
from auth.doc.security_exceptions_doc import SECURITY_EXCEPTION_DOC
from auth.doc.validation_exception_doc import VALIDATION_EXCEPTION_DOC
from auth.schemas.auth_schemas import ParsedJWTPayload, Token
from auth.schemas.user_schemas import (
    ChangePassword,
    ProfileData,
    ProfileUpdate,
    UserSignup,
    VerifyEmailOtpRequest,
)
from auth.types.enums import AuthType, UserType

router = APIRouter(tags=["users"])

_ALL_ROLES = [UserType.ADMIN, UserType.OWNER, UserType.MANAGER, UserType.CUSTOMER]


@router.post("/signup", responses={**VALIDATION_EXCEPTION_DOC["UserWithEmailAlreadyExistsException"], **VALIDATION_EXCEPTION_DOC["UserWithUsernameAlreadyExistsException"], **VALIDATION_EXCEPTION_DOC["WeakPasswordException"], **VALIDATION_EXCEPTION_DOC["InvalidUsernameException"]})
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
        first_name=user_signup.first_name,
        last_name=user_signup.last_name,
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
        Depends(RoleValidationDep(_ALL_ROLES, require_email_verified=False)),
    ],
    session: SessionDep,
) -> ProfileData:
    """
    Retrieve the profile data for the authenticated user.
    """
    return get_user_profile_data(session=session, user_guid=token.parsed_subject.user_guid)


@router.post("/profile", responses={**NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **VALIDATION_EXCEPTION_DOC["UserWithEmailAlreadyExistsException"], **VALIDATION_EXCEPTION_DOC["UserWithUsernameAlreadyExistsException"]})
async def update_profile_data(
    token: Annotated[
        ParsedJWTPayload,
        Depends(RoleValidationDep(_ALL_ROLES)),
    ],
    session: SessionDep,
    profile_update: ProfileUpdate
) -> ProfileData:
    """
    Update the profile data for the authenticated user.
    """
    return update_user_profile(session=session, user_guid=token.parsed_subject.user_guid, profile_data=profile_update)


@router.get("/check-username-availability", responses={**VALIDATION_EXCEPTION_DOC["UserWithUsernameAlreadyExistsException"], **VALIDATION_EXCEPTION_DOC["InvalidUsernameException"]})
async def check_username_availability(session: SessionDep, username: str = Query(...)) -> None:
    """
    Check if a username is available for registration.
    """
    validate_username_uniqueness(session=session, username=username)


@router.put("/change-password", responses={**SECURITY_EXCEPTION_DOC["InvalidCredentialsException"], **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"], **VALIDATION_EXCEPTION_DOC["WeakPasswordException"]})
async def change_password(
    token: Annotated[
        ParsedJWTPayload,
        Depends(RoleValidationDep(_ALL_ROLES)),
    ],
    session: SessionDep,
    change_password_data: ChangePassword
) -> None:
    """
    Change the password for the authenticated user.
    """
    change_user_password(
        session=session,
        user_guid=token.parsed_subject.user_guid,
        change_password_data=change_password_data
    )


@router.post(
    "/request-email-verification-otp",
    responses={
        **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"],
        **VALIDATION_EXCEPTION_DOC["EmailAlreadyVerifiedException"],
        **SECURITY_EXCEPTION_DOC["UserUnauthorizedException"],
    },
)
async def request_email_verification_otp_endpoint(
    token: Annotated[
        ParsedJWTPayload,
        Depends(RoleValidationDep(_ALL_ROLES, require_email_verified=False)),
    ],
    session: SessionDep,
) -> dict[str, str]:
    """
    Request an OTP for verifying the authenticated user's email address.
    """
    return request_email_verification_otp(
        session=session,
        user_guid=token.parsed_subject.user_guid,
    )


@router.post(
    "/verify-email-otp",
    responses={
        **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"],
        **VALIDATION_EXCEPTION_DOC["EmailAlreadyVerifiedException"],
        **VALIDATION_EXCEPTION_DOC["InvalidOtpException"],
        **SECURITY_EXCEPTION_DOC["UserUnauthorizedException"],
    },
)
async def verify_email_otp_endpoint(
    token: Annotated[
        ParsedJWTPayload,
        Depends(RoleValidationDep(_ALL_ROLES, require_email_verified=False)),
    ],
    session: SessionDep,
    payload: VerifyEmailOtpRequest,
) -> dict[str, str]:
    """
    Verify the authenticated user's email address using an OTP.
    """
    return verify_email_otp(
        session=session,
        user_guid=token.parsed_subject.user_guid,
        otp=payload.otp,
    )
