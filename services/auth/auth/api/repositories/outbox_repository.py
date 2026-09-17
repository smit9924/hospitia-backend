from sqlmodel import Session, select

from auth.database.models.users import Users
from auth.database.models.users_outbox import UsersOutbox


def add_user_created_outbox(
    *,
    session: Session,
    user: Users,
    initial_password: str | None = None,
) -> UsersOutbox:
    """
    Persist a user-created outbox snapshot in the current transaction.

    Note: This function does not commit the session.
    """
    if user.id is None or user.guid is None:
        raise ValueError("Cannot create outbox entry: user.id is None (user not yet persisted).")

    outbox_entry = UsersOutbox(
        user_id=user.id,
        guid=user.guid,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        initial_password=initial_password,
        is_processed=False,
    )
    session.add(outbox_entry)
    session.flush()
    session.refresh(outbox_entry)
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
        .where(UsersOutbox.is_processed.is_(False))  # type: ignore[attr-defined]
        .order_by(UsersOutbox.id)  # type: ignore[arg-type]
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    return list(session.exec(statement).all())


def mark_user_outbox_processed(*, session: Session, outbox_entry: UsersOutbox) -> None:
    """
    Mark an outbox row as processed and clear the initial password. Does not commit.
    """
    outbox_entry.is_processed = True
    outbox_entry.initial_password = None
    session.add(outbox_entry)
