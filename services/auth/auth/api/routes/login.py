import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from auth.api.dependencies import SessionDep
from auth.api.services.login_service import (
    forgot_password_user,
    login,
    reset_password_user,
)
from auth.api.services.login_service import (
    refresh_access_token as refresh_access_token_service,
)
from auth.doc.security_exceptions_doc import SECURITY_EXCEPTION_DOC
from auth.doc.validation_exception_doc import VALIDATION_EXCEPTION_DOC
from auth.schemas.auth_schemas import (
    AccessToken,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    Token,
)

router = APIRouter(tags=["login"])
log = logging.getLogger(__name__)

@router.post("", response_model=Token, responses={**SECURITY_EXCEPTION_DOC["UserInactiveException"], **SECURITY_EXCEPTION_DOC["InvalidCredentialsException"],})
async def login_user(session: SessionDep, form_data: Annotated[LoginRequest, Depends()]) -> Token:
    """
    Authenticate a user and issue an OAuth2 access token.
    """
    token = login(
        session=session,
        username=form_data.username,
        password=form_data.password,
        remember_me=form_data.remember_me,
    )

    return token


@router.post("/access-token", response_model=Token, response_model_by_alias=False, responses={**SECURITY_EXCEPTION_DOC["UserInactiveException"], **SECURITY_EXCEPTION_DOC["InvalidCredentialsException"],})
async def login_access_token(session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """
    Authenticate a user and return an OAuth2 access token.

    Notes:
    ------
    - This endpoint follows OAuth2 specifications, which require certain fields
    to use standard naming conventions(specifically in camel-case).
    - It is kept separate primarily for compatibility with Swagger UI and
    OAuth2 form-based authentication flow.
    """
    token = login(
        session=session,
        username=form_data.username,
        password=form_data.password,
    )

    return token


@router.post("/refresh-token", response_model=AccessToken, responses={**SECURITY_EXCEPTION_DOC["InvalidTokenException"], **SECURITY_EXCEPTION_DOC["UserUnauthorizedException"]})
async def refresh_access_token(session: SessionDep, payload: RefreshTokenRequest) -> AccessToken:
    """
    Refresh an expired access token using a valid refresh token.

    Validates the provided JWT refresh token and, if valid, issues a new
    JWT access token with updated expiration. Claims are built from the
    user's current state, so role or email verification changes apply on
    the next refresh. Missing, deleted or inactive users are rejected.
    """
    return refresh_access_token_service(session=session, refresh_token=payload.refresh_token)


@router.post("/forgot-password")
async def forgot_password(
    session: SessionDep,
    payload: ForgotPasswordRequest
) -> dict[str, str]:
    """
    Handle user requests for password reset.

    This endpoint initiates the password reset process by accepting a user's
    email address or username. It verifies the existence of the user and,
    if found, triggers the sending of a password reset email containing a
    secure, time-limited token. This allows users to securely reset their
    passwords without exposing sensitive information.
    """
    forgot_password_user(session=session, email=payload.email)
    return {"message": "A reset link has been sent to your email "}


@router.post(
    "/reset-password",
    responses={
        **SECURITY_EXCEPTION_DOC["InvalidTokenException"],
        **VALIDATION_EXCEPTION_DOC["WeakPasswordException"],
    },
)
async def reset_password(
    session: SessionDep,
    payload: ResetPasswordRequest
)   -> dict[str, str]:
    """
    Handle user requests to reset their password.

    This endpoint accepts a secure token and a new password. It validates the
    token to ensure it is valid, not expired, and has not been used. If the
    token is valid, the user's password is updated to the new password, and
    the token is marked as used to prevent reuse. This allows users to securely
    reset their passwords while ensuring that tokens cannot be exploited.
    """
    reset_password_user(
        session=session,
        reset_token=payload.token,
        new_password=payload.new_password,
    )

    return {"message": "Password has been reset successfully"}
