from typing import TypeVar

from .base_schemas import BaseSchema

T = TypeVar("T")

class PublicEmailNotAllowedExceptionMetadata[T](BaseSchema):
    field: str
    input: str
    data: T
