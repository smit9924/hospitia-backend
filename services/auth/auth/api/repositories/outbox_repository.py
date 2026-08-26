from sqlmodel import Session, select

from auth.database.models.users import Users
from auth.database.models.users_outbox import UsersOutbox


def add_user_created_outbox(*, session: Session, user: Users) -> UsersOutbox:
    """
    Persist a user-created outbox snapshot in the current transaction.

    Note: This function does not commit the session.
    """
    outbox_entry = UsersOutbox(
        user_id=user.id,
        guid=user.guid,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_processed=False,
    )
    session.add(outbox_entry)
    session.flush()
    return outbox_entry


def claim_unprocessed_user_outbox(
    *,
    session: Session,
    batch_size: int,
) -> list[UsersOutbox]:
    """
    Load unprocessed outbox rows and lock them for this worker.
    """
    statement = (
        select(UsersOutbox)
        .where(UsersOutbox.is_processed.is_(False))
        .order_by(UsersOutbox.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    return list(session.exec(statement).all())


def mark_user_outbox_processed(*, session: Session, outbox_entry: UsersOutbox) -> None:
    """
    Mark an outbox row as processed. Does not commit the session.
    """
    outbox_entry.is_processed = True
    session.add(outbox_entry)
