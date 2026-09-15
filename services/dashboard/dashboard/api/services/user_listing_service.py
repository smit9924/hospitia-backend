from sqlmodel import Session

from dashboard.api.repositories.user_repository import list_users_by_role
from dashboard.schemas.user_schemas import UserListQueryParams, UserListResponse
from dashboard.types.enums import UserType


def list_admins(*, session: Session, query: UserListQueryParams) -> UserListResponse:
    """List admin users. Org scoping is not applied for admins."""
    return list_users_by_role(session=session, role=UserType.ADMIN, query=query)


def list_owners(*, session: Session, query: UserListQueryParams) -> UserListResponse:
    """List owner users. Org scoping can be added here later."""
    return list_users_by_role(session=session, role=UserType.OWNER, query=query)


def list_managers(*, session: Session, query: UserListQueryParams) -> UserListResponse:
    """List manager users. Org scoping can be added here later."""
    return list_users_by_role(session=session, role=UserType.MANAGER, query=query)


def list_customers(*, session: Session, query: UserListQueryParams) -> UserListResponse:
    """List customer users. Org scoping can be added here later."""
    return list_users_by_role(session=session, role=UserType.CUSTOMER, query=query)
