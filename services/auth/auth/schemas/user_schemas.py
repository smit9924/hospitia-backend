from pydantic import EmailStr

from .base_schemas import BaseSchema


class UserSignup(BaseSchema):
    email: EmailStr
    username: str
    password: str
