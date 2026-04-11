from datetime import datetime

from auth.types.enums import TokenType, UserType

from .base_schemas import BaseSchema


class Token(BaseSchema):
    """
    Authentication token response schema.

    Represents the access token issued after successful authentication.

    Attributes
    ----------
    access_token : str
        JWT access token used for authenticated requests.
    access_token_expiry : datetime
        Expiration timestamp of the access token (UTC).
    refresh_token : str
        JWT refresh token used to obtain new access tokens after expiration.
    refresh_token_expiry : datetime
        Expiration timestamp of the refresh token (UTC).
    token_type : str
        Token scheme used for authentication (e.g., "bearer").
    """
    access_token: str
    access_token_expiry: datetime
    refresh_token: str
    refresh_token_expiry: datetime
    token_type: str


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

