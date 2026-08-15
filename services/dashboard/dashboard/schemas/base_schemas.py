from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """
    Base schema for all Pydantic models in the dashboard service.
    This class provides common configuration for all derived schemas

    applied configuration includes:
    -------------------------------
    - alias_generator: to_camel (converts snake_case field names to camelCase in JSON)
    - populate_by_name: True (allows population of fields by their Python names)
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
