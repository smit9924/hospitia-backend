from pydantic import EmailStr
from sqlmodel import Field
from .base import SQLModel
import uuid


# Database model, database table inferred from class name
class Users(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    hashed_password: str


# List all database model classes defined in this file.
# These models are imported when the database module is loaded,
# registering their tables in SQLModel.metadata.
# This is required for Alembic to automatically detect schema changes
# and generate migrations.
__all__ = [
    "Users"
]
