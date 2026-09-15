
from sqlalchemy import or_
from sqlmodel import Session, col, func, select

from dashboard.database.models.users import UsersReplica
from dashboard.schemas.mq_schemas import MqUserCreatedPayload
from dashboard.schemas.user_schemas import (
    UserListItem,
    UserListQueryParams,
    UserListResponse,
)
from dashboard.types.enums import UserType

_SORT_COLUMNS = {
    "firstName": UsersReplica.first_name,
    "lastName": UsersReplica.last_name,
    "username": UsersReplica.username,
    "email": UsersReplica.email,
}


def upsert_user_replica(*, session: Session, payload: MqUserCreatedPayload) -> UsersReplica:
    """
    Insert or update a local user replica using email as the stable identity.
    """
    replica = session.exec(
        select(UsersReplica).where(UsersReplica.email == payload.email)
    ).first()

    if replica is None:
        replica = session.exec(
            select(UsersReplica).where(UsersReplica.guid == payload.guid)
        ).first()

    if replica is None:
        replica = session.exec(
            select(UsersReplica).where(UsersReplica.username == payload.username)
        ).first()

    if replica is None:
        replica = UsersReplica(
            user_id=payload.id,
            guid=payload.guid,
            email=payload.email,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            role=payload.role,
        )
    else:
        replica.user_id = payload.id
        replica.guid = payload.guid
        replica.email = payload.email
        replica.username = payload.username
        replica.first_name = payload.first_name
        replica.last_name = payload.last_name
        replica.role = payload.role

    session.add(replica)
    session.commit()
    session.refresh(replica)
    return replica


def list_users_by_role(
    *,
    session: Session,
    role: UserType,
    query: UserListQueryParams,
) -> UserListResponse:
    """
    Return a paginated, filtered, and sorted list of replica users for a role.
    """
    statement = select(UsersReplica).where(UsersReplica.role == role)
    count_statement = select(func.count()).select_from(UsersReplica).where(UsersReplica.role == role)

    search_term = (query.search_term or "").strip()
    if search_term:
        pattern = f"%{search_term}%"
        search_filter = or_(
            col(UsersReplica.first_name).ilike(pattern),
            col(UsersReplica.last_name).ilike(pattern),
            col(UsersReplica.username).ilike(pattern),
        )
        statement = statement.where(search_filter)
        count_statement = count_statement.where(search_filter)

    sort_column = _SORT_COLUMNS[query.sort_by]
    if query.sort_direction == "desc":
        statement = statement.order_by(col(sort_column).desc())
    else:
        statement = statement.order_by(col(sort_column).asc())

    offset = (query.page_number - 1) * query.page_size
    statement = statement.offset(offset).limit(query.page_size)

    total_count = session.exec(count_statement).one()
    users = session.exec(statement).all()

    return UserListResponse(
        items=[
            UserListItem(
                guid=user.guid,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
                email=user.email,
            )
            for user in users
        ],
        total_count=total_count,
        page_number=query.page_number,
        page_size=query.page_size,
    )
