from auth.database.models import *
from auth.main import settings
from sqlmodel import create_engine

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))