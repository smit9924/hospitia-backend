from datetime import datetime
from typing import Annotated

from annotated_doc import Doc
from fastapi import Depends, Form
from fastapi.security import OAuth2PasswordRequestForm

from auth.types.enums import TokenType, UserType

from .base_schemas import BaseSchema


class AccessToken(BaseSchema):
    """
    Access token response schema.

    Represents the access token issued after successful authentication.

    Attributes
    ----------
    access_token : str
        JWT access token used for authenticated requests.
    access_token_expiry : datetime
        Expiration timestamp of the access token (UTC).
    token_type : str
        Token scheme used for authentication (e.g., "bearer").
    """
    access_token: str
    access_token_expiry: datetime
    token_type: str


class Token(AccessToken):
    """
    Authentication token response schema.

    Represents the access token issued after successful authentication.

    Attributes
    ----------
    access_token : str
        JWT access token used for authenticated requests (from parent class AccessToken).
    access_token_expiry : datetime
        Expiration timestamp of the access token (UTC) (from parent class AccessToken).
    refresh_token : str
        JWT refresh token used to obtain new access tokens after expiration.
    refresh_token_expiry : datetime
        Expiration timestamp of the refresh token (UTC).
    token_type : str
        Token scheme used for authentication (e.g., "bearer") (from parent class AccessToken).
    """
    refresh_token: str
    refresh_token_expiry: datetime


class JWTSubject(BaseSchema):
    """
    Subject information embedded within a JWT access token.

    Contains user identity and role details used for authorization.

    Attributes
    ----------
    user_guid : str
        Globally unique identifier of the authenticated user.
    role : UserType
        Role assigned to the user for access control.
    """
    user_guid: str
    role: UserType


class JWTPayload(BaseSchema):
    """
    Decoded JWT token payload.

    Holds standard JWT claims required for token validation and processing.

    Attributes
    ----------
    exp : datetime
        Expiration timestamp of the token (UTC).
    sub : str
        Serialized subject containing user identity and role information.
    type : str
        Token type (e.g., "access" or "refresh") for distinguishing token purposes.
    """
    exp: datetime
    sub: str
    type: TokenType


class ParsedJWTPayload(JWTPayload):
    """
    JWT token payload with parsed subject data.

    Extends the base JWT payload by converting the serialized subject (`sub`)
    claim into a strongly-typed subject model for easier access and
    authorization logic.

    Attributes
    ----------
    parsed_subject : JWTSubject
        Parsed subject containing user identity and role information.
    """

    parsed_subject: JWTSubject

class ForgotPasswordRequest(BaseSchema):
    """
    Schema for forgot password request.

    Represents the payload required to initiate a password reset process.

    Attributes
    ----------
    email : str
        The email address of the user requesting a password reset.
    """
    email: str

class ResetPasswordRequest(BaseSchema):
    """
    Schema for reset password request.

    Represents the payload required to complete a password reset process.

    Attributes
    ----------
    token : str
        The password reset token sent to the user's email.
    new_password : str
        The new password that the user wants to set.
    """
    token: str
    new_password: str


class LoginRequest:
    """
    Login request wrapper for OAuth2 password flow with additional fields.

    This class extends the standard OAuth2 password form by combining
    `OAuth2PasswordRequestForm` data with an additional `remember_me` flag.
    It is designed to be used as a FastAPI dependency for handling login requests.

    Attributes
    ----------
    form_data : OAuth2PasswordRequestForm
        Injected dependency containing standard OAuth2 fields:
        - username: User's login identifier
        - password: User's password
        - grant_type: OAuth2 grant type (typically "password")
        - scopes: List of requested scopes
        - client_id: Optional client identifier
        - client_secret: Optional client secret

    remember_me : bool, optional
        Indicates whether the user wants an extended session.
        If True, refresh token expiry is extended (e.g., 7 days);
        otherwise, a shorter expiry is used (e.g., 12 hours).
        Defaults to False.
    """
    def __init__(
        self,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        remember_me: Annotated[
            bool,
            Form(),
            Doc(
                """
                `remember_me` boolean. If true, refresh token expiry is longer
                `remember_me`.
                """
            ),
        ] = False,
    ) -> None:
        self.username = form_data.username
        self.password = form_data.password
        self.grant_type = form_data.grant_type
        self.scopes = form_data.scopes
        self.client_id = form_data.client_id
        self.client_secret = form_data.client_secret
        self.remember_me = remember_me


class RefreshTokenRequest(BaseSchema):
    """
    Refresh token request schema.

    Represents the payload required to refresh an access token using a valid refresh token.

    Attributes
    ----------
    refresh_token : str
        The JWT refresh token used to obtain a new access token.
    """
    refresh_token: str