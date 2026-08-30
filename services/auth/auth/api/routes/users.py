import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from auth.api.dependencies import RoleValidationDep, SessionDep
from auth.api.services.user_service import (
    change_user_password,
    get_user_by_guid_and_role,
    get_user_profile_data,
    provision_user,
    request_email_verification_otp,
    signup_user,
    update_user_by_admin,
    update_user_profile,
    validate_username_uniqueness,
    verify_email_otp,
)
from auth.doc.not_found_exceptions_doc import NOT_FOUND_EXCEPTIONS_DOC
from auth.doc.security_exceptions_doc import SECURITY_EXCEPTION_DOC
from auth.doc.validation_exception_doc import VALIDATION_EXCEPTION_DOC
from auth.schemas.auth_schemas import ParsedJWTPayload, Token
from auth.schemas.user_schemas import (
    ChangePassword,
    ProfileData,
    ProfileUpdate,
    UserCreateRequest,
    UserSignup,
    UserUpdateRequest,
    VerifyEmailOtpRequest,
)
from auth.types.enums import UserType

log = logging.getLogger(__name__)

router = APIRouter(tags=["users"])

_ALL_ROLES = [UserType.ADMIN, UserType.OWNER, UserType.MANAGER, UserType.CUSTOMER]
_ADMIN_ONLY = [UserType.ADMIN]
_ADMIN_OWNER = [UserType.ADMIN, UserType.OWNER]
_ADMIN_OWNER_MANAGER = [UserType.ADMIN, UserType.OWNER, UserType.MANAGER]


_SIGNUP_RESPONSES = {
    **VALIDATION_EXCEPTION_DOC["UserWithEmailAlreadyExistsException"],
    **VALIDATION_EXCEPTION_DOC["UserWithUsernameAlreadyExistsException"],
    **VALIDATION_EXCEPTION_DOC["WeakPasswordException"],
    **VALIDATION_EXCEPTION_DOC["InvalidUsernameException"],
}

_CREATE_USER_RESPONSES = {
    **VALIDATION_EXCEPTION_DOC["UserWithEmailAlreadyExistsException"],
    **VALIDATION_EXCEPTION_DOC["UserWithUsernameAlreadyExistsException"],
    **VALIDATION_EXCEPTION_DOC["InvalidUsernameException"],
}

_UPDATE_USER_RESPONSES = {
    **NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"],
    **VALIDATION_EXCEPTION_DOC["UserWithUsernameAlreadyExistsException"],
}


@router.post("/signup", responses=_SIGNUP_RESPONSES)
async def signup(session: SessionDep, user_signup: UserSignup) -> Token:
    """
    Register a new OWNER user and authenticate them.

    Creates a new user account with OWNER user type using the provided
    registration details. Upon successful registration, the user is
    automatically authenticated and a JWT access token and refresh token are returned.
    """
    log.info("Started")
    return signup_user(session=session, user_signup=user_signup, role=UserType.OWNER)


@router.post("/signup-customer", responses=_SIGNUP_RESPONSES)
async def signup_customer(session: SessionDep, user_signup: UserSignup) -> Token:
    """
    Register a new CUSTOMER user and authenticate them.

    Creates a new user account with CUSTOMER user type using the provided
    registration details. Upon successful registration, the user is
    automatically authenticated and a JWT access token and refresh token are returned.
    """
    log.info("Started")
    return signup_user(session=session, user_signup=user_signup, role=UserType.CUSTOMER)


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


# ############################
# Admin users
# ############################


@router.post(
    "/admins",
    responses=_CREATE_USER_RESPONSES,
)
async def create_admin(
    session: SessionDep,
    user_create: UserCreateRequest,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> ProfileData:
    """Create a new ADMIN user. Password is generated and emailed."""
    return provision_user(session=session, user_create=user_create, role=UserType.ADMIN)


@router.get(
    "/admins/{guid}",
    responses={**NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"]},
)
async def get_admin(
    guid: UUID,
    session: SessionDep,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> ProfileData:
    """Retrieve an ADMIN user by GUID."""
    return get_user_by_guid_and_role(
        session=session,
        user_guid=str(guid),
        expected_role=UserType.ADMIN,
    )


@router.put(
    "/admins",
    responses=_UPDATE_USER_RESPONSES,
)
async def update_admin(
    session: SessionDep,
    user_update: UserUpdateRequest,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> ProfileData:
    """Update an ADMIN user's profile fields."""
    return update_user_by_admin(
        session=session,
        expected_role=UserType.ADMIN,
        user_update=user_update,
    )

# ############################
# Owner users
# ############################

@router.post(
    "/owners",
    responses=_CREATE_USER_RESPONSES,
)
async def create_owner(
    session: SessionDep,
    user_create: UserCreateRequest,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> ProfileData:
    """Create a new OWNER user. Password is generated and emailed."""
    return provision_user(session=session, user_create=user_create, role=UserType.OWNER)


@router.get(
    "/owners/{guid}",
    responses={**NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"]},
)
async def get_owner(
    guid: UUID,
    session: SessionDep,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> ProfileData:
    """Retrieve an OWNER user by GUID."""
    return get_user_by_guid_and_role(
        session=session,
        user_guid=str(guid),
        expected_role=UserType.OWNER,
    )


@router.put(
    "/owners",
    responses=_UPDATE_USER_RESPONSES,
)
async def update_owner(
    session: SessionDep,
    user_update: UserUpdateRequest,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_ONLY))],
) -> ProfileData:
    """Update an OWNER user's profile fields."""
    return update_user_by_admin(
        session=session,
        expected_role=UserType.OWNER,
        user_update=user_update,
    )


# ############################
# Manager users
# ############################


@router.post(
    "/managers",
    responses=_CREATE_USER_RESPONSES,
)
async def create_manager(
    session: SessionDep,
    user_create: UserCreateRequest,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER))],
) -> ProfileData:
    """Create a new MANAGER user. Password is generated and emailed."""
    return provision_user(session=session, user_create=user_create, role=UserType.MANAGER)


@router.get(
    "/managers/{guid}",
    responses={**NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"]},
)
async def get_manager(
    guid: UUID,
    session: SessionDep,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER))],
) -> ProfileData:
    """Retrieve a MANAGER user by GUID."""
    return get_user_by_guid_and_role(
        session=session,
        user_guid=str(guid),
        expected_role=UserType.MANAGER,
    )


@router.put(
    "/managers",
    responses=_UPDATE_USER_RESPONSES,
)
async def update_manager(
    session: SessionDep,
    user_update: UserUpdateRequest,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER))],
) -> ProfileData:
    """Update a MANAGER user's profile fields."""
    return update_user_by_admin(
        session=session,
        expected_role=UserType.MANAGER,
        user_update=user_update,
    )


# ############################
# Customer users
# ############################


@router.post(
    "/customers",
    responses=_CREATE_USER_RESPONSES,
)
async def create_customer(
    session: SessionDep,
    user_create: UserCreateRequest,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER_MANAGER))],
) -> ProfileData:
    """Create a new CUSTOMER user. Password is generated and emailed."""
    return provision_user(session=session, user_create=user_create, role=UserType.CUSTOMER)


@router.get(
    "/customers/{guid}",
    responses={**NOT_FOUND_EXCEPTIONS_DOC["UserNotFoundException"]},
)
async def get_customer(
    guid: UUID,
    session: SessionDep,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER_MANAGER))],
) -> ProfileData:
    """Retrieve a CUSTOMER user by GUID."""
    return get_user_by_guid_and_role(
        session=session,
        user_guid=str(guid),
        expected_role=UserType.CUSTOMER,
    )


@router.put(
    "/customers",
    responses=_UPDATE_USER_RESPONSES,
)
async def update_customer(
    session: SessionDep,
    user_update: UserUpdateRequest,
    _token: Annotated[ParsedJWTPayload, Depends(RoleValidationDep(_ADMIN_OWNER_MANAGER))],
) -> ProfileData:
    """Update a CUSTOMER user's profile fields."""
    return update_user_by_admin(
        session=session,
        expected_role=UserType.CUSTOMER,
        user_update=user_update,
    )
