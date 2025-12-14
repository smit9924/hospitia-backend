from sqlmodel import Session

from auth.core.security import get_password_hash
from auth.database.models.users import Users


def create_user(session: Session, user: Users) -> Users:
    if user.password:
        user.password = get_password_hash(user.password)

    session.add(user)
    session.commit()
    return user
