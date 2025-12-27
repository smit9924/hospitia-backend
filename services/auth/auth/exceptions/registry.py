from typing import Any

from auth.exceptions.definitions.validation_exceptions import (
    PublicEmailNotAllowedException,
)
from auth.exceptions.handlers.validation_exception_handlers import (
    public_email_not_allowed_exception_handler,
)


def get_exception_handlers() -> dict[Any, Any]:
    """
    Returns a mapping of custom exception types to their corresponding
    FastAPI exception handler callables.
    """
    return {
        PublicEmailNotAllowedException: public_email_not_allowed_exception_handler,
    }
