from pydantic import EmailStr

from auth.types.enums import UserType

from .base_schemas import BaseSchema


class UserSignup(BaseSchema):
    email: EmailStr
    username: str
    password: str


class ProfileData(BaseSchema):
    email: EmailStr
    username: str
    role: UserType
    guid: str
    first_name: str | None = None
    last_name: str | None = None


class UsernameAvailabilityRequest(BaseSchema):
    username: str
