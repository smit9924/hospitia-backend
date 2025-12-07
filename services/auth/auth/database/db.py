from sqlmodel import create_engine

from auth.core.config import settings
from auth.database.models import *  # noqa: F403

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
