from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from .base_schemas import BaseSchema


class OrganizationTypeUpsertRequest(BaseSchema):
    """
    Request payload for creating or updating an organization type.

    When `guid` is omitted (or null), a new organization type is created.
    When `guid` is present, the existing organization type identified by
    that guid is updated.
    """

    guid: UUID | None = None
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class OrganizationTypeResponse(BaseSchema):
    guid: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class OrganizationTypeListQueryParams(BaseSchema):
    """
    Query parameters for the paginated organization type listing endpoint.
    """

    search_term: str | None = None
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Literal["name", "createdAt", "updatedAt"] = "name"
    sort_direction: Literal["asc", "desc"] = "asc"
    page_number: int = Field(default=1, ge=1)


class OrganizationTypeListResponse(BaseSchema):
    items: list[OrganizationTypeResponse]
    total_count: int
    page_number: int
    page_size: int
