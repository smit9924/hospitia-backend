from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field

from dashboard.schemas.base_schemas import BaseSchema


class UserListQueryParams(BaseSchema):
    """Query parameters for paginated user listing endpoints."""

    search_term: str | None = None
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Literal["firstName", "lastName", "username", "email"] = "firstName"
    sort_direction: Literal["asc", "desc"] = "asc"
    page_number: int = Field(default=1, ge=1)


class UserListItem(BaseSchema):
    guid: UUID
    first_name: str | None = None
    last_name: str | None = None
    username: str
    email: EmailStr


class UserListResponse(BaseSchema):
    items: list[UserListItem]
    total_count: int
    page_number: int
    page_size: int
