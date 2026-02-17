from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from auth.api.dependencies import SessionDep, decode_jwt_token
from auth.api.services.login_service import authenticate_manual_user
from auth.core.security import (create_jwt_access_token, create_jwt_refresh_token)
from auth.schemas.auth_schemas import JWTSubject, Token, TokenType

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