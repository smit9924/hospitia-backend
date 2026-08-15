from datetime import datetime

from payment.types.enums import TokenType, UserType

from .base_schemas import BaseSchema



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
    email_verified: bool


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
