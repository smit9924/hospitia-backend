from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class PublicEmailNotAllowedExceptionMetadata[T](BaseModel):
    field: str
    input: str
    data: T
