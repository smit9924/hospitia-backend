from pydantic import EmailStr

from auth.types.enums import UserType

from .base_schemas import BaseSchema


class UserSignup(BaseSchema):
    first_name: str
    last_name: str
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
    is_email_verified: bool = False


class ProfileUpdate(BaseSchema):
    username: str
    first_name: str
    last_name: str


class ChangePassword(BaseSchema):
    current_password: str
    new_password: str


class VerifyEmailOtpRequest(BaseSchema):
    otp: str
