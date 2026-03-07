# Import all database model modules here.
# Each module exposes its models through __all__, ensuring they are loaded
# and their tables are registered in SQLModel.metadata.
# This is required for automatic schema generation, migrations, and metadata discovery.
from .base import SQLModel
from .secure_token import *  # noqa: F403
from .users import *  # noqa: F403

__all__ = ["SQLModel"]
