from uuid import UUID

from sqlmodel import Session

from booking.api.repositories.organization_type_repository import (
    create_organization_type,
    get_organization_type_by_guid,
    get_organization_type_by_name,
    has_active_organizations_of_type,
    update_organization_type,
)
from booking.api.repositories.organization_type_repository import (
    delete_organization_type as delete_organization_type_repo,
)
from booking.api.repositories.organization_type_repository import (
    list_organization_types as list_organization_types_repo,
)
from booking.exceptions.definitions.not_found_exceptions import (
    OrganizationTypeNotFoundException,
)
from booking.exceptions.definitions.validation_exceptions import (
    OrganizationTypeAlreadyExistsException,
    OrganizationTypeHasActiveOrganizationsException,
)
from booking.schemas.organization_type_schemas import (
    OrganizationTypeListQueryParams,
    OrganizationTypeListResponse,
    OrganizationTypeResponse,
    OrganizationTypeUpsertRequest,
)


def upsert_organization_type(
    *,
    session: Session,
    payload: OrganizationTypeUpsertRequest,
    actor_user_id: int,
) -> OrganizationTypeResponse:
    """
    Create a new organization type, or update an existing one identified by
    `payload.guid`.
    """
    if payload.guid is None:
        if get_organization_type_by_name(session=session, name=payload.name):
            raise OrganizationTypeAlreadyExistsException()
        organization_type = create_organization_type(
            session=session,
            name=payload.name,
            description=payload.description,
            actor_id=actor_user_id,
        )
    else:
        organization_type = get_organization_type_by_guid(session=session, guid=payload.guid)
        if organization_type is None:
            raise OrganizationTypeNotFoundException()

        name_owner = get_organization_type_by_name(session=session, name=payload.name)
        if name_owner is not None and name_owner.id != organization_type.id:
            raise OrganizationTypeAlreadyExistsException()

        organization_type = update_organization_type(
            session=session,
            organization_type=organization_type,
            name=payload.name,
            description=payload.description,
            actor_id=actor_user_id,
        )

    return OrganizationTypeResponse.model_validate(organization_type, from_attributes=True)


def get_organization_type(*, session: Session, guid: UUID) -> OrganizationTypeResponse:
    organization_type = get_organization_type_by_guid(session=session, guid=guid)
    if organization_type is None:
        raise OrganizationTypeNotFoundException()
    return OrganizationTypeResponse.model_validate(organization_type, from_attributes=True)


def delete_organization_type(*, session: Session, guid: UUID) -> None:
    """
    Delete an organization type, validating it exists and is not still
    referenced by an active organization.
    """
    organization_type = get_organization_type_by_guid(session=session, guid=guid)
    if organization_type is None:
        raise OrganizationTypeNotFoundException()

    if has_active_organizations_of_type(session=session, organization_type_id=organization_type.id):
        raise OrganizationTypeHasActiveOrganizationsException()

    delete_organization_type_repo(session=session, organization_type=organization_type)


def list_organization_types(
    *,
    session: Session,
    query: OrganizationTypeListQueryParams,
) -> OrganizationTypeListResponse:
    return list_organization_types_repo(session=session, query=query)
