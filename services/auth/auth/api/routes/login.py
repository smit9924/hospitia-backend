from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from auth.api.dependencies import SessionDep, decode_jwt_token
from auth.api.services.login_service import authenticate_manual_user, forgot_password_user, reset_password_user
from auth.core.security import (create_jwt_access_token, create_jwt_refresh_token)
from auth.schemas.auth_schemas import ForgotPasswordRequest, JWTSubject, Token, TokenType, ResetPasswordRequest

router = APIRouter(tags=["login"])


@router.post("/access-token", response_model=Token)
async def login_access_token(session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """
    Authenticate a user and issue an OAuth2 access token.

    Validates the provided username/email and password using the OAuth2
    password grant flow. If authentication is successful, a JWT access
    token is generated and returned for use in subsequent authenticated
    requests.
    """
    authenticated_user = authenticate_manual_user(
        session=session,
        identifire=form_data.username,
        password=form_data.password,
    )

    if not authenticated_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not authenticated_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_jwt_access_token(
        subject=JWTSubject (
            user_guid=str(authenticated_user.guid), # UUID is not JSON serializable, convert to string
            role=authenticated_user.role,
        )
    )

    refresh_token = create_jwt_refresh_token(
        subject=JWTSubject (
            user_guid=str(authenticated_user.guid), # UUID is not JSON serializable, convert to
            role=authenticated_user.role,
        )
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/refresh-token", response_model=Token)
async def refresh_access_token(session: SessionDep, refresh_token: str) -> Token:
    """
    Refresh an expired access token using a valid refresh token.

    Validates the provided JWT refresh token and, if valid, issues a new
    JWT access token with updated expiration. This allows clients to
    maintain authenticated sessions without requiring users to re-enter
    credentials after access tokens expire.
    """
    parsed_payload = decode_jwt_token(refresh_token, expected_type=TokenType.REFRESH)

    new_access_token = create_jwt_access_token(
        subject=JWTSubject (
            user_guid=parsed_payload.parsed_subject.user_guid,
            role=parsed_payload.parsed_subject.role,
        )
    )

    new_refresh_token = create_jwt_refresh_token(
        subject=JWTSubject (
            user_guid=parsed_payload.parsed_subject.user_guid,
            role=parsed_payload.parsed_subject.role,
        )
    )

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )

@router.post("/forgot-password")
async def forgot_password(
    session: SessionDep,
    payload: ForgotPasswordRequest
):
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

@router.post("/reset-password")
async def reset_password(
    session: SessionDep,
    payload: ResetPasswordRequest
):
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