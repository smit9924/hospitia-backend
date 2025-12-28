from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from auth.api.dependencies import SessionDep
from auth.api.services.login_service import authenticate_manual_user
from auth.core.security import create_jwt_access_token
from auth.schemas.auth_schemas import Token

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
    authenticated_user = authenticate_manual_user(session=session, email_or_username=form_data.username, password=form_data.password)

    if not authenticated_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not authenticated_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_jwt_access_token(
        subject=
        {
            "user_guid": str(authenticated_user.guid), # UUID is not JSON serializable, convert to string
            "role": authenticated_user.role,
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer"
    )
