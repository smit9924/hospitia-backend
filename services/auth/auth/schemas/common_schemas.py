from typing import TypeVar

from pydantic import BaseModel

from auth.types.error_codes import ErrorCodes

T = TypeVar("T")


class ApiErrorResponse[T](BaseModel):
    data: T
    field: str
    input: str
    message: str
    errorCode: ErrorCodes
