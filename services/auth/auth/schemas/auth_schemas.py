from datetime import datetime

from pydantic import BaseModel

from auth.types.enums import UserType


class Token(BaseModel):
    """
    Authentication token response schema.

    Represents the access token issued after successful authentication.

    Attributes
    ----------
    access_token : str
        JWT access token used for authenticated requests.
    token_type : str
        Token scheme used for authentication (e.g., "bearer").
    """
    access_token: str
    token_type: str


class JWTSubject(BaseModel):
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


class JWTAccessTokenPayload(BaseModel):
    """
    Decoded JWT access token payload.

    Holds standard JWT claims required for token validation and processing.

    Attributes
    ----------
    exp : datetime
        Expiration timestamp of the token (UTC).
    sub : str
        Serialized subject containing user identity and role information.
    """
    exp: datetime
    sub: str


class ParsedJWTAccessTokenPayload(JWTAccessTokenPayload):
    """
    JWT access token payload with parsed subject data.

    Extends the base JWT payload by converting the serialized subject (`sub`)
    claim into a strongly-typed subject model for easier access and
    authorization logic.

    Attributes
    ----------
    parsed_subject : JWTSubject
        Parsed subject containing user identity and role information.
    """

    parsed_subject: JWTSubject
