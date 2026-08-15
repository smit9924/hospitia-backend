from sqlmodel import create_engine

from dashboard.core.config import settings
from dashboard.database.models import *  # noqa: F403

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
