from typing import TypeVar

from auth.types.error_codes import ErrorCodes

from .base_schemas import BaseSchema

T = TypeVar("T")


class ApiErrorResponse[T](BaseSchema):
    metadata: T
    message: str
    errorCode: ErrorCodes
