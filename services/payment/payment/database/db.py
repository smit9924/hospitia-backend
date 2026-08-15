from sqlmodel import create_engine

from payment.core.config import settings
from payment.database.models import *  # noqa: F403

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
