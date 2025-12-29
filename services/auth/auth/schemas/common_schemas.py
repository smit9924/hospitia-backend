from typing import TypeVar

from pydantic import BaseModel

from auth.types.error_codes import ErrorCodes

T = TypeVar("T")


class ApiErrorResponse[T](BaseModel):
    metadata: T
    message: str
    errorCode: ErrorCodes
