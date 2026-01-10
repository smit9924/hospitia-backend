from datetime import datetime
from pydantic import BaseModel

from auth.types.enums import UserType


class Token(BaseModel):
    access_token: str
    token_type: str


class JWTSubject(BaseModel):
    user_guid: str
    role: UserType


class JWTAccessTokenPayload(BaseModel):
    exp: datetime
    sub: str


class ParsedJWTAccessTokenPayload(JWTAccessTokenPayload):
    """
    JWT payload with parsed subject data.
    """

    parsed_subject: JWTSubject