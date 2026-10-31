from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field

from booking.types.enums import OrganizationRole

from .base_schemas import BaseSchema
from .organization_type_schemas import OrganizationTypeResponse


class AddressInput(BaseSchema):
    address_line_1: str = Field(min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    landmark: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    postal_code: int = Field(strict=True, ge=1, le=9_999_999)


class AddressResponse(AddressInput):
    guid: UUID


class OrganizationMemberSummary(BaseSchema):
    guid: UUID
    first_name: str | None
    last_name: str | None
    username: str
    email: EmailStr


class OrganizationCreateAdminRequest(BaseSchema):
    """
    Request payload for creating or updating an organization as an Admin.

    When `guid` is omitted, a new organization is created and `owner_user_guid`
    is required to establish the initial OWNER mapping. When `guid` is
    present, the organization is updated; `owner_user_guid` is ignored on
    update (ownership transfer is performed via `/organization/owner`).
    """

    guid: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    organization_type_guid: UUID
    address: AddressInput
    owner_user_guid: UUID
    is_active: bool = True


class OrganizationCreateOwnerRequest(BaseSchema):
    """
    Request payload for an Owner to create or update their own organization.
    The authenticated Owner is automatically associated as OWNER on create.
    """

    guid: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    organization_type_guid: UUID
    address: AddressInput
    is_active: bool = True


class OrganizationResponse(BaseSchema):
    guid: UUID
    name: str
    description: str | None
    is_active: bool
    organization_type: OrganizationTypeResponse
    address: AddressResponse
    owner: OrganizationMemberSummary | None
    created_by: OrganizationMemberSummary | None
    updated_by: OrganizationMemberSummary | None
    created_at: datetime
    updated_at: datetime


class OrganizationOwnerMappingRequest(BaseSchema):
    """
    Assign or replace the OWNER mapping on an organization. Admin-only.
    """

    organization_guid: UUID
    owner_user_guid: UUID


class OrganizationManagerMappingRequest(BaseSchema):
    """
    Assign (`is_active=True`) or remove (`is_active=False`) a MANAGER
    mapping on an organization.
    """

    organization_guid: UUID
    manager_user_guid: UUID
    is_active: bool = True


class OrganizationAdminMappingRequest(BaseSchema):
    """
    Admin-only umbrella endpoint: assign/replace the OWNER or MANAGER
    mapping on any organization.
    """

    organization_guid: UUID
    user_guid: UUID
    role: OrganizationRole
    is_active: bool = True


class OrganizationMappingResponse(BaseSchema):
    guid: UUID
    organization_guid: UUID
    user: OrganizationMemberSummary
    role: OrganizationRole
    is_active: bool


class OrganizationListQueryParams(BaseSchema):
    """
    Query parameters for the paginated organization listing endpoints.
    """

    search_term: str | None = None
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Literal["name", "createdAt", "updatedAt"] = "name"
    sort_direction: Literal["asc", "desc"] = "asc"
    page_number: int = Field(default=1, ge=1)


class OrganizationListItem(BaseSchema):
    guid: UUID
    name: str
    organization_type_name: str
    owner_display_name: str | None
    address_line_1: str
    city: str
    state: str
    country: str
    is_active: bool
    created_by_display_name: str | None
    created_at: datetime
    updated_by_display_name: str | None
    updated_at: datetime


class OrganizationListResponse(BaseSchema):
    items: list[OrganizationListItem]
    total_count: int
    page_number: int
    page_size: int


class OrganizationMembershipSummary(BaseSchema):
    """
    Lightweight view of an organization the caller is actively mapped to.
    Used to resolve and display the caller's active organization.
    """

    guid: UUID
    name: str
    organization_type_name: str
    city: str | None


class OrganizationMembershipListResponse(BaseSchema):
    items: list[OrganizationMembershipSummary]


class ActiveOrganization(BaseSchema):
    """
    Active organization resolved by `ActiveOrganizationDep` for the current
    request. Internal use only: `id` must never be exposed through the API.
    """

    id: int
    guid: UUID


class OrganizationScopedActor(BaseSchema):
    """
    Caller of an endpoint that serves both admins and organization members,
    resolved by `OrganizationScopedActorDep`. Internal use only.

    Attributes
    ----------
    user_id : int
        Internal ID of the caller's user replica.
    is_admin : bool
        Whether the caller is an admin. Admins are not tied to an
        organization and may act on any organization.
    active_organization : ActiveOrganization | None
        The caller's validated active organization; ``None`` for admins.
    """

    user_id: int
    is_admin: bool
    active_organization: ActiveOrganization | None
