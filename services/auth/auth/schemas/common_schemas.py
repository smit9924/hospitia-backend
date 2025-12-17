from typing import Generic, TypeVar
from pydantic import BaseModel


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    data: T
    success: bool
    message: str
    exception: str